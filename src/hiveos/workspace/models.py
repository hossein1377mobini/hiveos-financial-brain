"""
Workspace data models — isolated tenant workspaces.

Each workspace represents a team/org with its own agents, flows,
configuration, audit trail, and member list.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set


class WorkspaceRole(str, Enum):
    """Role a user can have within a workspace."""
    OWNER = "owner"        # full workspace control
    ADMIN = "admin"        # manage members, config, all resources
    OPERATOR = "operator"  # run flows, manage agents
    CONTRIBUTOR = "contributor"  # create and run flows
    VIEWER = "viewer"      # read-only

    @classmethod
    def hierarchy(cls) -> Dict["WorkspaceRole", int]:
        """Role hierarchy (higher = more privileged)."""
        return {
            cls.VIEWER: 0,
            cls.CONTRIBUTOR: 1,
            cls.OPERATOR: 2,
            cls.ADMIN: 3,
            cls.OWNER: 4,
        }


@dataclass
class WorkspaceMember:
    """A member of a workspace with a specific role."""
    username: str
    workspace_role: WorkspaceRole = WorkspaceRole.VIEWER
    invited_at: str = ""
    joined_at: Optional[str] = None

    def __post_init__(self):
        if not self.invited_at:
            self.invited_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "workspace_role": self.workspace_role.value,
            "invited_at": self.invited_at,
            "joined_at": self.joined_at or "",
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkspaceMember":
        role_str = data.get("workspace_role", "viewer")
        try:
            role = WorkspaceRole(role_str)
        except ValueError:
            role = WorkspaceRole.VIEWER
        return cls(
            username=data["username"],
            workspace_role=role,
            invited_at=data.get("invited_at", ""),
            joined_at=data.get("joined_at") or None,
        )


@dataclass
class WorkspaceSettings:
    """Configurable settings for a workspace."""
    max_agents: int = 50
    max_flows: int = 100
    max_concurrent_flows: int = 5
    max_nodes: int = 10
    retention_days: int = 90           # audit log retention
    allow_public_flows: bool = False   # share flows across workspaces
    auto_approve_agents: bool = False  # skip admin approval for agent registration
    default_delivery: str = "origin"   # default delivery destination
    features: Dict[str, bool] = field(default_factory=lambda: {
        "dashboard": True,
        "audit_trail": True,
        "rbac": True,
        "domain_plugins": True,
        "multi_node": True,
        "knowledge_sync": True,
    })

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkspaceSettings":
        # Filter to known fields only
        known = {k: v for k, v in data.items() if k in [
            "max_agents", "max_flows", "max_concurrent_flows", "max_nodes",
            "retention_days", "allow_public_flows", "auto_approve_agents",
            "default_delivery", "features",
        ]}
        return cls(**known)


@dataclass
class Workspace:
    """
    An isolated tenant workspace.

    Each workspace has its own:
    - Data directory (~/.hiveos/workspaces/<id>/)
    - Agent registry
    - Flow storage
    - Audit trail
    - Configuration
    - Member list
    """
    workspace_id: str
    name: str
    description: str = ""
    owner: str = ""                  # username of the owner
    settings: WorkspaceSettings = field(default_factory=WorkspaceSettings)
    members: List[WorkspaceMember] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    active: bool = True

    def __post_init__(self):
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def active_members(self) -> List[WorkspaceMember]:
        return [m for m in self.members if m.joined_at is not None]

    def get_member(self, username: str) -> Optional[WorkspaceMember]:
        """Get a member by username."""
        for m in self.members:
            if m.username == username:
                return m
        return None

    def add_member(self, username: str, role: WorkspaceRole = WorkspaceRole.VIEWER) -> WorkspaceMember:
        """Add a member to the workspace."""
        member = WorkspaceMember(
            username=username,
            workspace_role=role,
            invited_at=datetime.utcnow().isoformat(),
        )
        self.members.append(member)
        self.updated_at = datetime.utcnow().isoformat()
        return member

    def remove_member(self, username: str) -> bool:
        """Remove a member from the workspace."""
        for i, m in enumerate(self.members):
            if m.username == username:
                self.members.pop(i)
                self.updated_at = datetime.utcnow().isoformat()
                return True
        return False

    def has_member(self, username: str) -> bool:
        """Check if username is a member."""
        return any(m.username == username for m in self.members)

    def get_member_role(self, username: str) -> Optional[WorkspaceRole]:
        """Get the role of a member."""
        m = self.get_member(username)
        return m.workspace_role if m else None

    def check_permission(self, username: str, required_role: WorkspaceRole) -> bool:
        """
        Check if a member has sufficient permissions.
        Uses role hierarchy: owner > admin > operator > contributor > viewer.
        """
        member = self.get_member(username)
        if not member:
            return False
        hier = WorkspaceRole.hierarchy()
        return hier.get(member.workspace_role, -1) >= hier.get(required_role, 0)

    def to_dict(self) -> dict:
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "settings": self.settings.to_dict(),
            "members": [m.to_dict() for m in self.members],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Workspace":
        members = [WorkspaceMember.from_dict(m) for m in data.get("members", [])]
        settings = WorkspaceSettings.from_dict(data.get("settings", {}))
        return cls(
            workspace_id=data["workspace_id"],
            name=data.get("name", data["workspace_id"]),
            description=data.get("description", ""),
            owner=data.get("owner", ""),
            settings=settings,
            members=members,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            active=data.get("active", True),
        )


def generate_workspace_id(name: str) -> str:
    """Generate a URL-safe workspace ID from a name."""
    import re
    safe = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower().strip())
    safe = re.sub(r'-+', '-', safe).strip('-')
    if not safe:
        import uuid
        safe = uuid.uuid4().hex[:8]
    return safe
