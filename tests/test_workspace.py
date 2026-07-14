"""
Tests for HiveOS Workspace Manager — multi-tenant isolation.

Covers:
- Workspace models (creation, serialization, member management)
- WorkspaceManager CRUD (create, list, get, update, remove)
- Data isolation (directory structure per workspace)
- Member management
- RBAC integration (User.workspace field)
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def temp_dir():
    """Temporary directory for workspace storage."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def ws_manager(temp_dir):
    """WorkspaceManager with temp base directory."""
    from hiveos.workspace import WorkspaceManager
    mgr = WorkspaceManager(base_dir=temp_dir)
    return mgr


@pytest.fixture
def sample_workspace(ws_manager):
    """Create a sample workspace for tests."""
    return ws_manager.create_workspace(
        name="Test Workspace",
        description="A test workspace",
        owner="admin",
    )


# ── Model Tests ──────────────────────────────────────────────────────


class TestWorkspaceModels:
    """Test Workspace dataclass."""

    def test_create_minimal(self):
        """Workspace can be created with minimal fields."""
        from hiveos.workspace import Workspace
        ws = Workspace(workspace_id="test", name="Test")
        assert ws.workspace_id == "test"
        assert ws.name == "Test"
        assert ws.active is True
        assert ws.members == []
        assert ws.created_at != ""

    def test_generate_id(self):
        """generate_workspace_id creates URL-safe IDs."""
        from hiveos.workspace.models import generate_workspace_id
        assert generate_workspace_id("Hello World") == "hello-world"
        assert generate_workspace_id("My Team!@#") == "my-team"
        assert generate_workspace_id("  Spaces  ") == "spaces"

    def test_add_member(self):
        """Members can be added to workspace."""
        from hiveos.workspace import Workspace, WorkspaceRole
        ws = Workspace(workspace_id="t", name="Test")
        ws.add_member("alice", WorkspaceRole.ADMIN)
        assert len(ws.members) == 1
        assert ws.members[0].username == "alice"
        assert ws.members[0].workspace_role == WorkspaceRole.ADMIN

    def test_remove_member(self):
        """Members can be removed from workspace."""
        from hiveos.workspace import Workspace, WorkspaceRole
        ws = Workspace(workspace_id="t", name="Test")
        ws.add_member("alice", WorkspaceRole.ADMIN)
        ws.add_member("bob", WorkspaceRole.VIEWER)
        assert ws.member_count == 2
        assert ws.remove_member("alice") is True
        assert ws.member_count == 1
        assert ws.has_member("bob") is True
        assert ws.has_member("alice") is False

    def test_get_member(self):
        """get_member returns correct member or None."""
        from hiveos.workspace import Workspace, WorkspaceRole
        ws = Workspace(workspace_id="t", name="Test")
        ws.add_member("alice", WorkspaceRole.OWNER)
        member = ws.get_member("alice")
        assert member is not None
        assert member.username == "alice"
        assert ws.get_member("bob") is None

    def test_get_member_role(self):
        """get_member_role returns the correct role."""
        from hiveos.workspace import Workspace, WorkspaceRole
        ws = Workspace(workspace_id="t", name="Test")
        ws.add_member("alice", WorkspaceRole.OPERATOR)
        assert ws.get_member_role("alice") == WorkspaceRole.OPERATOR
        assert ws.get_member_role("bob") is None

    def test_check_permission_hierarchy(self):
        """check_permission uses role hierarchy."""
        from hiveos.workspace import Workspace, WorkspaceRole
        ws = Workspace(workspace_id="t", name="Test")
        ws.add_member("owner", WorkspaceRole.OWNER)
        ws.add_member("admin", WorkspaceRole.ADMIN)
        ws.add_member("viewer", WorkspaceRole.VIEWER)

        # Owner can do everything
        assert ws.check_permission("owner", WorkspaceRole.VIEWER) is True
        assert ws.check_permission("owner", WorkspaceRole.OWNER) is True

        # Admin can do operator tasks
        assert ws.check_permission("admin", WorkspaceRole.OPERATOR) is True
        assert ws.check_permission("admin", WorkspaceRole.ADMIN) is True
        assert ws.check_permission("admin", WorkspaceRole.OWNER) is False

        # Viewer can only do viewer tasks
        assert ws.check_permission("viewer", WorkspaceRole.VIEWER) is True
        assert ws.check_permission("viewer", WorkspaceRole.CONTRIBUTOR) is False

    def test_serialization_roundtrip(self):
        """Workspace to_dict and from_dict preserve all fields."""
        from hiveos.workspace import Workspace, WorkspaceRole, WorkspaceSettings
        ws = Workspace(
            workspace_id="test-1",
            name="Test Workspace",
            description="Description",
            owner="admin",
            settings=WorkspaceSettings(max_agents=100, retention_days=30),
        )
        ws.add_member("alice", WorkspaceRole.ADMIN)
        ws.add_member("bob", WorkspaceRole.VIEWER)

        restored = Workspace.from_dict(ws.to_dict())
        assert restored.workspace_id == "test-1"
        assert restored.name == "Test Workspace"
        assert restored.owner == "admin"
        assert restored.member_count == 2
        assert restored.settings.max_agents == 100
        assert restored.settings.retention_days == 30

    def test_workspace_role_enum_values(self):
        """WorkspaceRole enum has correct values."""
        from hiveos.workspace import WorkspaceRole
        assert WorkspaceRole.OWNER.value == "owner"
        assert WorkspaceRole.ADMIN.value == "admin"
        assert WorkspaceRole.OPERATOR.value == "operator"
        assert WorkspaceRole.CONTRIBUTOR.value == "contributor"
        assert WorkspaceRole.VIEWER.value == "viewer"

    def test_workspace_role_hierarchy(self):
        """Role hierarchy has correct ordering."""
        from hiveos.workspace import WorkspaceRole
        hier = WorkspaceRole.hierarchy()
        assert hier[WorkspaceRole.VIEWER] < hier[WorkspaceRole.CONTRIBUTOR]
        assert hier[WorkspaceRole.CONTRIBUTOR] < hier[WorkspaceRole.OPERATOR]
        assert hier[WorkspaceRole.OPERATOR] < hier[WorkspaceRole.ADMIN]
        assert hier[WorkspaceRole.ADMIN] < hier[WorkspaceRole.OWNER]


# ── Manager Tests ────────────────────────────────────────────────────


class TestWorkspaceManager:
    """Test WorkspaceManager CRUD."""

    def test_create_workspace(self, ws_manager):
        """create_workspace creates a workspace with metadata."""
        ws = ws_manager.create_workspace(
            name="Engineering",
            description="Engineering team workspace",
            owner="ali",
        )
        assert ws.workspace_id == "engineering"
        assert ws.name == "Engineering"
        assert ws.owner == "ali"
        assert ws.active is True
        assert ws.member_count == 1  # owner auto-added

    def test_create_workspace_creates_dirs(self, ws_manager):
        """create_workspace creates isolated directories."""
        ws = ws_manager.create_workspace(name="Dev", owner="admin")
        base = ws_manager._workspace_path(ws.workspace_id)
        assert (base / "agents").is_dir()
        assert (base / "flows").is_dir()
        assert (base / "audit").is_dir()
        assert (base / "config").is_dir()

    def test_create_workspace_persists_yaml(self, ws_manager):
        """create_workspace saves workspace.yaml to disk."""
        ws = ws_manager.create_workspace(name="Data Science", owner="admin")
        meta_path = ws_manager._metadata_path(ws.workspace_id)
        assert meta_path.exists()
        data = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        assert data["name"] == "Data Science"
        assert data["owner"] == "admin"

    def test_get_workspace(self, ws_manager):
        """get_workspace returns workspace by ID."""
        ws = ws_manager.create_workspace(name="Finance", owner="admin")
        found = ws_manager.get_workspace(ws.workspace_id)
        assert found is not None
        assert found.name == "Finance"

    def test_get_workspace_not_found(self, ws_manager):
        """get_workspace returns None for missing workspace."""
        assert ws_manager.get_workspace("nonexistent") is None

    def test_list_workspaces(self, ws_manager):
        """list_workspaces returns all active workspaces."""
        ws_manager.create_workspace(name="Alpha", owner="admin")
        ws_manager.create_workspace(name="Beta", owner="user1")
        ws_manager.create_workspace(name="Gamma", owner="user2")
        workspaces = ws_manager.list_workspaces()
        assert len(workspaces) == 3

    def test_list_workspaces_excludes_inactive(self, ws_manager):
        """list_workspaces excludes deactivated workspaces by default."""
        ws = ws_manager.create_workspace(name="Temp", owner="admin")
        ws_manager.remove_workspace(ws.workspace_id)
        workspaces = ws_manager.list_workspaces()
        assert len(workspaces) == 0

    def test_list_workspaces_include_inactive(self, ws_manager):
        """list_workspaces with include_inactive=True includes deactivated."""
        ws = ws_manager.create_workspace(name="Temp", owner="admin")
        ws_manager.remove_workspace(ws.workspace_id)
        workspaces = ws_manager.list_workspaces(include_inactive=True)
        assert len(workspaces) == 1

    def test_update_workspace(self, ws_manager):
        """update_workspace modifies metadata."""
        ws = ws_manager.create_workspace(name="Old Name", owner="admin")
        updated = ws_manager.update_workspace(ws.workspace_id, name="New Name", description="Updated")
        assert updated is not None
        assert updated.name == "New Name"
        assert updated.description == "Updated"

    def test_update_workspace_not_found(self, ws_manager):
        """update_workspace returns None for missing workspace."""
        result = ws_manager.update_workspace("nonexistent", name="New")
        assert result is None

    def test_remove_workspace_deactivate(self, ws_manager):
        """remove_workspace with permanent=False deactivates."""
        ws = ws_manager.create_workspace(name="To Deactivate", owner="admin")
        assert ws.active is True
        ws_manager.remove_workspace(ws.workspace_id, permanent=False)
        ws = ws_manager.get_workspace(ws.workspace_id)
        assert ws is not None
        assert ws.active is False

    def test_remove_workspace_permanent(self, ws_manager):
        """remove_workspace with permanent=True deletes all data."""
        ws = ws_manager.create_workspace(name="To Delete", owner="admin")
        wid = ws.workspace_id
        ws_manager.remove_workspace(wid, permanent=True)
        assert ws_manager.get_workspace(wid) is None
        assert not ws_manager._workspace_path(wid).exists()

    def test_activate_workspace(self, ws_manager):
        """activate_workspace reactivates a deactivated workspace."""
        ws = ws_manager.create_workspace(name="Inactive", owner="admin")
        ws_manager.remove_workspace(ws.workspace_id)
        result = ws_manager.activate_workspace(ws.workspace_id)
        assert result is True
        ws = ws_manager.get_workspace(ws.workspace_id)
        assert ws.active is True

    def test_workspace_exists(self, ws_manager):
        """workspace_exists checks existence."""
        ws = ws_manager.create_workspace(name="Exists", owner="admin")
        assert ws_manager.workspace_exists(ws.workspace_id) is True
        assert ws_manager.workspace_exists("nonexistent") is False

    def test_workspace_dir(self, ws_manager):
        """workspace_dir returns correct path."""
        ws = ws_manager.create_workspace(name="Dir Test", owner="admin")
        agents_dir = ws_manager.workspace_dir(ws.workspace_id, "agents")
        assert agents_dir is not None
        assert agents_dir.name == "agents"

    def test_workspace_dir_not_found(self, ws_manager):
        """workspace_dir returns None for missing workspace."""
        assert ws_manager.workspace_dir("nonexistent", "agents") is None


# ── Member Tests ─────────────────────────────────────────────────────


class TestWorkspaceMembers:
    """Test workspace member management."""

    def test_add_member(self, ws_manager, sample_workspace):
        """add_member adds user to workspace."""
        from hiveos.workspace import WorkspaceRole
        result = ws_manager.add_member(sample_workspace.workspace_id, "alice", WorkspaceRole.ADMIN)
        assert result is True
        ws = ws_manager.get_workspace(sample_workspace.workspace_id)
        assert ws.has_member("alice") is True

    def test_add_member_duplicate(self, ws_manager, sample_workspace):
        """add_member prevents duplicate members."""
        from hiveos.workspace import WorkspaceRole
        ws_manager.add_member(sample_workspace.workspace_id, "alice", WorkspaceRole.VIEWER)
        result = ws_manager.add_member(sample_workspace.workspace_id, "alice", WorkspaceRole.ADMIN)
        assert result is False

    def test_remove_member(self, ws_manager, sample_workspace):
        """remove_member removes user from workspace."""
        from hiveos.workspace import WorkspaceRole
        ws_manager.add_member(sample_workspace.workspace_id, "alice", WorkspaceRole.VIEWER)
        result = ws_manager.remove_member(sample_workspace.workspace_id, "alice")
        assert result is True
        ws = ws_manager.get_workspace(sample_workspace.workspace_id)
        assert ws.has_member("alice") is False

    def test_remove_owner_blocked(self, ws_manager, sample_workspace):
        """remove_member cannot remove the owner."""
        result = ws_manager.remove_member(sample_workspace.workspace_id, "admin")
        assert result is False

    def test_remove_nonexistent_member(self, ws_manager, sample_workspace):
        """remove_member on non-member returns False."""
        result = ws_manager.remove_member(sample_workspace.workspace_id, "nobody")
        assert result is False

    def test_set_member_role(self, ws_manager, sample_workspace):
        """set_member_role changes a member's role."""
        from hiveos.workspace import WorkspaceRole
        ws_manager.add_member(sample_workspace.workspace_id, "alice", WorkspaceRole.VIEWER)
        result = ws_manager.set_member_role(sample_workspace.workspace_id, "alice", WorkspaceRole.ADMIN)
        assert result is True
        ws = ws_manager.get_workspace(sample_workspace.workspace_id)
        assert ws.get_member_role("alice") == WorkspaceRole.ADMIN

    def test_set_member_role_nonexistent(self, ws_manager, sample_workspace):
        """set_member_role on non-member returns False."""
        from hiveos.workspace import WorkspaceRole
        result = ws_manager.set_member_role(sample_workspace.workspace_id, "nobody", WorkspaceRole.ADMIN)
        assert result is False

    def test_get_workspaces_for_user(self, ws_manager):
        """get_workspaces_for_user returns all workspaces the user belongs to."""
        w1 = ws_manager.create_workspace(name="Workspace 1", owner="alice")
        w2 = ws_manager.create_workspace(name="Workspace 2", owner="bob")
        ws_manager.add_member(w2.workspace_id, "alice", "viewer")
        ws_manager.add_member(w1.workspace_id, "bob", "viewer")

        alice_workspaces = ws_manager.get_workspaces_for_user("alice")
        bob_workspaces = ws_manager.get_workspaces_for_user("bob")

        assert len(alice_workspaces) == 2  # owner of 1, member of 2
        assert len(bob_workspaces) == 2    # owner of 2, member of 1

    def test_load_persisted_workspaces(self, temp_dir):
        """WorkspaceManager loads previously persisted workspaces."""
        from hiveos.workspace import WorkspaceManager
        # Create workspaces with one manager
        mgr1 = WorkspaceManager(base_dir=temp_dir)
        mgr1.create_workspace(name="Persisted WS", owner="admin")
        mgr1.create_workspace(name="Another WS", owner="user")

        # New manager should load them
        mgr2 = WorkspaceManager(base_dir=temp_dir)
        workspaces = mgr2.list_workspaces()
        assert len(workspaces) == 2


# ── RBAC Integration ─────────────────────────────────────────────────


class TestRBACWorkspaceIntegration:
    """Test that User model supports workspace field."""

    def test_user_workspace_field(self):
        """User has workspace field with default 'default'."""
        from hiveos.rbac.models import User
        u = User(username="testuser", role="viewer")
        assert u.workspace == "default"

    def test_user_workspace_custom(self):
        """User can be created with custom workspace."""
        from hiveos.rbac.models import User
        u = User(username="alice", role="admin", workspace="engineering")
        assert u.workspace == "engineering"

    def test_user_workspace_serialization(self):
        """User workspace field is preserved in to_dict/from_dict."""
        from hiveos.rbac.models import User
        u = User(username="bob", role="operator", workspace="finance")
        data = u.to_dict()
        assert data["workspace"] == "finance"
        restored = User.from_dict(data)
        assert restored.workspace == "finance"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
