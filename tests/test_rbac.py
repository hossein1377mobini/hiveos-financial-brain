"""Tests for RBAC system — models, manager, permission checks."""

from pathlib import Path
import pytest
from src.hiveos.rbac.models import (
    Resource, Action, Permission, Role, User,
    get_builtin_roles,
)
from src.hiveos.rbac.manager import RBACManager


class TestPermission:
    """Permission data model tests."""

    def test_from_str_valid(self):
        p = Permission.from_str("flow:execute")
        assert p.resource == Resource.FLOW
        assert p.action == Action.EXECUTE

    def test_from_str_invalid(self):
        with pytest.raises(ValueError):
            Permission.from_str("invalid-format")

    def test_from_str_invalid_resource(self):
        with pytest.raises(ValueError):
            Permission.from_str("unknown:read")

    def test_to_str(self):
        p = Permission(Resource.AGENT, Action.CREATE)
        assert p.to_str() == "agent:create"

    def test_equality(self):
        p1 = Permission(Resource.FLOW, Action.READ)
        p2 = Permission(Resource.FLOW, Action.READ)
        p3 = Permission(Resource.FLOW, Action.EXECUTE)
        assert p1 == p2
        assert p1 != p3

    def test_hashable(self):
        s = {Permission(Resource.FLOW, Action.READ)}
        s.add(Permission(Resource.FLOW, Action.READ))
        assert len(s) == 1


class TestRole:
    """Role data model tests."""

    def test_role_creation(self):
        role = Role(
            name="test-role",
            description="A test role",
            permissions={
                Permission(Resource.FLOW, Action.READ),
                Permission(Resource.FLOW, Action.EXECUTE),
            },
        )
        assert role.name == "test-role"
        assert len(role.permissions) == 2

    def test_has_permission(self):
        role = Role(name="reader", permissions={
            Permission(Resource.FLOW, Action.READ),
            Permission(Resource.AGENT, Action.READ),
        })
        assert role.has_permission(Resource.FLOW, Action.READ)
        assert not role.has_permission(Resource.FLOW, Action.CREATE)
        assert not role.has_permission(Resource.PACKAGE, Action.READ)

    def test_add_remove_permission(self):
        role = Role(name="dynamic")
        assert len(role.permissions) == 0
        role.add_permission(Permission(Resource.FLOW, Action.READ))
        assert len(role.permissions) == 1
        role.remove_permission(Permission(Resource.FLOW, Action.READ))
        assert len(role.permissions) == 0

    def test_to_dict_roundtrip(self):
        role = Role(
            name="custom",
            description="Custom role",
            permissions={
                Permission(Resource.FLOW, Action.READ),
                Permission(Resource.AGENT, Action.EXECUTE),
            },
        )
        d = role.to_dict()
        assert d["name"] == "custom"
        assert d["description"] == "Custom role"
        assert "flow:read" in d["permissions"]
        assert "agent:execute" in d["permissions"]

        restored = Role.from_dict(d)
        assert restored.name == role.name
        assert restored.description == role.description
        assert restored.permissions == role.permissions
        assert not restored.is_builtin


class TestUser:
    """User data model tests."""

    def test_user_creation(self):
        user = User(username="test-user", role="operator", api_key="my-key")
        assert user.username == "test-user"
        assert user.role == "operator"
        assert user.api_key == "my-key"
        assert user.enabled is True
        assert user.created_at != ""

    def test_to_dict_roundtrip(self):
        user = User(username="jdoe", role="admin", api_key="adm-key", email="j@doe.com")
        d = user.to_dict()
        assert d["username"] == "jdoe"
        assert d["role"] == "admin"
        assert d["api_key"] == "adm-key"
        assert d["email"] == "j@doe.com"

        restored = User.from_dict(d)
        assert restored.username == user.username
        assert restored.role == user.role
        assert restored.api_key == user.api_key


class TestBuiltinRoles:
    """Built-in role definitions."""

    def test_admin_has_all_permissions(self):
        roles = get_builtin_roles()
        admin = roles["admin"]
        for res in Resource:
            for act in Action:
                assert admin.has_permission(res, act), \
                    f"Admin missing {res.value}:{act.value}"

    def test_viewer_readonly(self):
        roles = get_builtin_roles()
        viewer = roles["viewer"]
        for res in Resource:
            assert viewer.has_permission(res, Action.READ)
            assert not viewer.has_permission(res, Action.CREATE)
            assert not viewer.has_permission(res, Action.DELETE)
            assert not viewer.has_permission(res, Action.UPDATE)
            if res != Resource.FLOW:
                assert not viewer.has_permission(res, Action.EXECUTE)

    def test_operator_has_flow_access(self):
        roles = get_builtin_roles()
        op = roles["operator"]
        assert op.has_permission(Resource.FLOW, Action.CREATE)
        assert op.has_permission(Resource.FLOW, Action.READ)
        assert op.has_permission(Resource.FLOW, Action.EXECUTE)
        assert not op.has_permission(Resource.USER, Action.READ)
        assert not op.has_permission(Resource.RBAC, Action.READ)

    def test_deployer_can_deploy_only(self):
        roles = get_builtin_roles()
        dep = roles["deployer"]
        assert dep.has_permission(Resource.FLOW, Action.READ)
        assert dep.has_permission(Resource.FLOW, Action.EXECUTE)
        assert not dep.has_permission(Resource.FLOW, Action.CREATE)
        assert not dep.has_permission(Resource.FLOW, Action.DELETE)
        assert dep.has_permission(Resource.PACKAGE, Action.READ)
        assert not dep.has_permission(Resource.PACKAGE, Action.CREATE)

    def test_four_builtin_roles(self):
        roles = get_builtin_roles()
        assert set(roles.keys()) == {"admin", "operator", "viewer", "deployer"}
        for r in roles.values():
            assert r.is_builtin is True


class TestRBACManager:
    """RBACManager persistence and auth tests."""

    @pytest.fixture
    def mgr(self, tmp_path):
        """RBACManager with temp storage."""
        return RBACManager(data_dir=tmp_path)

    def test_init_creates_admin_user(self, mgr):
        users = mgr.list_users()
        assert "admin" in users
        assert users["admin"].role == "admin"
        assert users["admin"].enabled is True

    def test_init_creates_builtin_roles(self, mgr):
        roles = mgr.list_roles()
        assert "admin" in roles
        assert "operator" in roles
        assert "viewer" in roles
        assert "deployer" in roles

    def test_add_and_get_user(self, mgr):
        user = User(username="alice", role="operator", api_key="key-alice")
        mgr.add_user(user)
        ret = mgr.get_user("alice")
        assert ret is not None
        assert ret.role == "operator"
        assert ret.api_key == "key-alice"

    def test_remove_user(self, mgr):
        user = User(username="bob", role="viewer", api_key="key-bob")
        mgr.add_user(user)
        assert mgr.get_user("bob") is not None
        mgr.remove_user("bob")
        assert mgr.get_user("bob") is None

    def test_update_user_role(self, mgr):
        user = User(username="carol", role="viewer", api_key="key-carol")
        mgr.add_user(user)
        assert mgr.update_user_role("carol", "operator") is True
        assert mgr.get_user("carol").role == "operator"

    def test_update_user_role_invalid_role(self, mgr):
        user = User(username="dave", role="viewer", api_key="key-dave")
        mgr.add_user(user)
        assert mgr.update_user_role("dave", "nonexistent") is False

    def test_enable_disable_user(self, mgr):
        user = User(username="eve", role="viewer", api_key="key-eve")
        mgr.add_user(user)
        mgr.enable_user("eve", False)
        assert mgr.get_user("eve").enabled is False
        mgr.enable_user("eve", True)
        assert mgr.get_user("eve").enabled is True

    def test_add_custom_role(self, mgr):
        role = Role(name="custom-reader", permissions={
            Permission(Resource.FLOW, Action.READ),
        })
        assert mgr.add_role(role) is True
        assert mgr.get_role("custom-reader") is not None

    def test_cannot_override_builtin_role(self, mgr):
        role = Role(name="admin", permissions={Permission(Resource.FLOW, Action.READ)})
        assert mgr.add_role(role) is False

    def test_remove_custom_role(self, mgr):
        role = Role(name="temp", permissions={Permission(Resource.FLOW, Action.READ)})
        mgr.add_role(role)
        assert mgr.remove_role("temp") is True
        assert mgr.get_role("temp") is None

    def test_cannot_remove_builtin_role(self, mgr):
        assert mgr.remove_role("admin") is False
        assert mgr.remove_role("viewer") is False

    def test_authenticate_valid_key(self, mgr):
        user = User(username="frank", role="operator", api_key="frank-key")
        mgr.add_user(user)
        ret = mgr.authenticate("frank-key")
        assert ret is not None
        assert ret.username == "frank"

    def test_authenticate_invalid_key(self, mgr):
        ret = mgr.authenticate("nonexistent")
        assert ret is None

    def test_authenticate_disabled_user(self, mgr):
        user = User(username="grace", role="viewer", api_key="grace-key")
        mgr.add_user(user)
        mgr.enable_user("grace", False)
        ret = mgr.authenticate("grace-key")
        assert ret is None

    def test_check_permission_admin(self, mgr):
        user = mgr.get_user("admin")
        assert mgr.check_permission(user, Resource.FLOW, Action.EXECUTE) is True
        assert mgr.check_permission(user, Resource.RBAC, Action.DELETE) is True
        assert mgr.check_permission(user, Resource.USER, Action.CREATE) is True

    def test_check_permission_viewer(self, mgr):
        user = User(username="view", role="viewer", api_key="view-key")
        mgr.add_user(user)
        assert mgr.check_permission(user, Resource.FLOW, Action.READ) is True
        assert mgr.check_permission(user, Resource.FLOW, Action.CREATE) is False
        assert mgr.check_permission(user, Resource.AGENT, Action.DELETE) is False

    def test_permission_custom_role(self, mgr):
        role = Role(name="flow-only", permissions={
            Permission(Resource.FLOW, Action.READ),
            Permission(Resource.FLOW, Action.EXECUTE),
        })
        mgr.add_role(role)
        user = User(username="flowguy", role="flow-only", api_key="fg-key")
        mgr.add_user(user)
        assert mgr.check_permission(user, Resource.FLOW, Action.READ) is True
        assert mgr.check_permission(user, Resource.FLOW, Action.EXECUTE) is True
        assert mgr.check_permission(user, Resource.AGENT, Action.READ) is False

    def test_persistence_across_reload(self, tmp_path):
        mgr1 = RBACManager(data_dir=tmp_path)
        user = User(username="persist", role="operator", api_key="p-key")
        mgr1.add_user(user)
        role = Role(name="persist-role", permissions={
            Permission(Resource.PACKAGE, Action.READ),
        })
        mgr1.add_role(role)

        # Create new instance, data should persist
        mgr2 = RBACManager(data_dir=tmp_path)
        assert mgr2.get_user("persist") is not None
        assert mgr2.get_user("persist").role == "operator"
        assert mgr2.get_role("persist-role") is not None
        assert mgr2.authenticate("p-key") is not None

    def test_require_role_or_higher(self, mgr):
        user_admin = mgr.get_user("admin")
        user_op = User(username="op", role="operator", api_key="op-key")
        mgr.add_user(user_op)
        user_view = User(username="vw", role="viewer", api_key="vw-key")
        mgr.add_user(user_view)

        # Admin passes all
        assert mgr.require_role_or_higher(user_admin, "viewer") is True
        assert mgr.require_role_or_higher(user_admin, "admin") is True

        # Operator passes operator and below
        assert mgr.require_role_or_higher(user_op, "viewer") is True
        assert mgr.require_role_or_higher(user_op, "operator") is True
        assert mgr.require_role_or_higher(user_op, "admin") is False

        # Viewer passes viewer only
        assert mgr.require_role_or_higher(user_view, "viewer") is True
        assert mgr.require_role_or_higher(user_view, "operator") is False
