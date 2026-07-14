"""
RBACManager — YAML-backed role-based access control.

Loads/stores roles and users from a YAML file, provides
permission checks and CRUD for users and custom roles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

import yaml

from rich.console import Console

from .models import (
    Resource, Action, Permission, Role, User,
    get_builtin_roles,
)

console = Console()

DEFAULT_RBAC_CONFIG = {
    "version": "1.0",
    "roles": {},
    "users": {
        "admin": {
            "username": "admin",
            "role": "admin",
            "api_key": "hive-admin-key",
            "enabled": True,
            "email": "admin@hiveos.local",
            "created_at": datetime.utcnow().isoformat(),
        },
    },
}


class RBACManager:
    """
    Role-Based Access Control manager.

    Persists roles and users to a YAML file.
    Built-in roles (admin, operator, viewer, deployer) are always available
    and cannot be deleted or renamed.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else Path.home() / ".hiveos"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._path = self.data_dir / "rbac.yaml"

        # Built-in roles are always loaded
        self._builtin_roles: Dict[str, Role] = get_builtin_roles()
        # Custom roles from YAML
        self._custom_roles: Dict[str, Role] = {}
        # Users from YAML
        self._users: Dict[str, User] = {}
        # API key → username lookup cache
        self._api_key_map: Dict[str, str] = {}

        self.load()

    # ── Persistence ─────────────────────────────────────────────────

    def load(self):
        """Load RBAC data from YAML file."""
        if self._path.exists():
            with open(self._path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            self._custom_roles = {}
            for name, rdata in data.get("roles", {}).items():
                self._custom_roles[name] = Role.from_dict({"name": name, **rdata})
            self._users = {}
            for name, udata in data.get("users", {}).items():
                self._users[name] = User.from_dict(udata)
        else:
            # First run — create default admin user
            self._users = {}
            for uname, udata in DEFAULT_RBAC_CONFIG["users"].items():
                self._users[uname] = User.from_dict(udata)
            self._custom_roles = {}
            self.save()
            console.print(f"[dim]🆕 Created default RBAC: {self._path}[/dim]")

        self._rebuild_api_key_cache()

    def save(self):
        """Persist RBAC data to YAML file."""
        roles_data = {}
        for name, role in self._custom_roles.items():
            roles_data[name] = {
                "description": role.description,
                "permissions": sorted(p.to_str() for p in role.permissions),
            }
        users_data = {}
        for name, user in self._users.items():
            users_data[name] = user.to_dict()

        data = {
            "version": "1.0",
            "roles": roles_data,
            "users": users_data,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _rebuild_api_key_cache(self):
        self._api_key_map = {}
        for uname, user in self._users.items():
            if user.api_key and user.enabled:
                self._api_key_map[user.api_key] = uname

    # ── Role resolution ─────────────────────────────────────────────

    def get_role(self, name: str) -> Optional[Role]:
        """Get role by name (built-in or custom)."""
        if name in self._builtin_roles:
            return self._builtin_roles[name]
        return self._custom_roles.get(name)

    def list_roles(self) -> Dict[str, Role]:
        """Return all roles (built-in + custom)."""
        roles = dict(self._builtin_roles)
        roles.update(self._custom_roles)
        return roles

    def add_role(self, role: Role) -> bool:
        """Add a custom role. Returns False if name conflicts with built-in."""
        name = role.name
        if name in self._builtin_roles:
            console.print(f"[red]❌ Cannot override built-in role '{name}'[/red]")
            return False
        if name in self._custom_roles:
            console.print(f"[yellow]⚠️  Overwriting existing role '{name}'[/yellow]")
        self._custom_roles[name] = role
        self.save()
        return True

    def remove_role(self, name: str) -> bool:
        """Remove a custom role. Built-in roles cannot be removed."""
        if name in self._builtin_roles:
            console.print(f"[red]❌ Cannot remove built-in role '{name}'[/red]")
            return False
        if name not in self._custom_roles:
            return False
        # Check if any user is assigned this role
        users_with_role = [u.username for u in self._users.values() if u.role == name]
        if users_with_role:
            console.print(f"[yellow]⚠️  Users {users_with_role} still have role '{name}'. "
                          f"Re-assign them first.[/yellow]")
            return False
        del self._custom_roles[name]
        self.save()
        return True

    # ── User management ─────────────────────────────────────────────

    def add_user(self, user: User) -> bool:
        """Add or update a user. Returns True if new, False if updated."""
        exists = user.username in self._users
        self._users[user.username] = user
        self._rebuild_api_key_cache()
        self.save()
        return not exists

    def remove_user(self, username: str) -> bool:
        """Remove a user."""
        if username not in self._users:
            return False
        del self._users[username]
        self._rebuild_api_key_cache()
        self.save()
        return True

    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username)

    def list_users(self) -> Dict[str, User]:
        return dict(self._users)

    def update_user_role(self, username: str, role_name: str) -> bool:
        """Change a user's role. Validates role exists."""
        if username not in self._users:
            return False
        role = self.get_role(role_name)
        if not role:
            console.print(f"[red]❌ Role '{role_name}' does not exist[/red]")
            return False
        self._users[username].role = role_name
        self.save()
        return True

    def update_user_api_key(self, username: str, api_key: str) -> bool:
        """Update a user's API key."""
        if username not in self._users:
            return False
        self._users[username].api_key = api_key
        self._rebuild_api_key_cache()
        self.save()
        return True

    def enable_user(self, username: str, enabled: bool = True) -> bool:
        """Enable or disable a user."""
        if username not in self._users:
            return False
        self._users[username].enabled = enabled
        self._rebuild_api_key_cache()
        self.save()
        return True

    # ── Authentication & Authorization ──────────────────────────────

    def authenticate(self, api_key: str) -> Optional[User]:
        """Look up a user by API key. Returns None if key is invalid or user disabled."""
        username = self._api_key_map.get(api_key)
        if not username:
            return None
        user = self._users.get(username)
        if user and user.enabled:
            return user
        return None

    def check_permission(self, user: User, resource: Resource, action: Action) -> bool:
        """
        Check if a user has permission to perform an action on a resource.

        Resolution order:
        1. If user is admin → always True
        2. Look up user's role → check if permission is in role's set
        """
        role = self.get_role(user.role)
        if not role:
            return False
        return role.has_permission(resource, action)

    def assert_permission(self, user: User, resource: Resource, action: Action):
        """Raise PermissionError if check fails."""
        if not self.check_permission(user, resource, action):
            raise PermissionError(
                f"User '{user.username}' (role={user.role}) lacks permission "
                f"'{resource.value}:{action.value}'"
            )

    def require_role(self, user: User, *role_names: str) -> bool:
        """Check if a user has one of the specified roles."""
        return user.role in role_names

    def require_role_or_higher(self, user: User, minimum_role: str) -> bool:
        """
        Check if user has a role that is at least 'minimum_role'.
        Uses an implicit hierarchy: admin > operator > deployer > viewer.
        """
        hierarchy = ["viewer", "deployer", "operator", "admin"]
        if minimum_role not in hierarchy:
            return False
        # Custom roles are treated as operator-level
        user_role = user.role
        if user_role not in hierarchy:
            user_role = "operator" if user_role in self._custom_roles else "viewer"
        min_idx = hierarchy.index(minimum_role)
        user_idx = hierarchy.index(user_role) if user_role in hierarchy else -1
        return user_idx >= min_idx
