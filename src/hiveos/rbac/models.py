"""
RBAC data models — Resource, Action, Permission, Role, User.

Designed for YAML serialization and strict permission checks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum


# ── Resource / Action ───────────────────────────────────────────────

class Resource(str, Enum):
    """Resources that can be protected by RBAC."""
    FLOW = "flow"
    AGENT = "agent"
    PACKAGE = "package"
    REGISTRY = "registry"
    MOTHERSHIP = "mothership"
    USER = "user"
    AUDIT = "audit"
    WORKSPACE = "workspace"
    RBAC = "rbac"  # role/permission self-management


class Action(str, Enum):
    """Actions that can be performed on a resource."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"


# ── Permission ──────────────────────────────────────────────────────

@dataclass
class Permission:
    """A (resource, action) pair defining an allowed operation."""
    resource: Resource
    action: Action

    @classmethod
    def from_str(cls, raw: str) -> "Permission":
        """Parse from 'resource:action' string, e.g. 'flow:execute'."""
        parts = raw.strip().split(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid permission format '{raw}', expected 'resource:action'")
        return cls(resource=Resource(parts[0].strip()),
                   action=Action(parts[1].strip()))

    def to_str(self) -> str:
        return f"{self.resource.value}:{self.action.value}"

    def __hash__(self):
        return hash((self.resource.value, self.action.value))

    def __eq__(self, other):
        if not isinstance(other, Permission):
            return NotImplemented
        return self.resource == other.resource and self.action == other.action


# ── Role ────────────────────────────────────────────────────────────

@dataclass
class Role:
    """A named set of permissions."""
    name: str
    description: str = ""
    permissions: Set[Permission] = field(default_factory=set)
    is_builtin: bool = False  # built-in roles cannot be deleted

    def has_permission(self, resource: Resource, action: Action) -> bool:
        return Permission(resource=resource, action=action) in self.permissions

    def add_permission(self, permission: Permission):
        self.permissions.add(permission)

    def remove_permission(self, permission: Permission):
        self.permissions.discard(permission)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "permissions": sorted(p.to_str() for p in self.permissions),
            "is_builtin": self.is_builtin,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Role":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            permissions={Permission.from_str(p) for p in data.get("permissions", [])},
            is_builtin=data.get("is_builtin", False),
        )


# ── User ────────────────────────────────────────────────────────────

@dataclass
class User:
    """A user identity with assigned role(s), API key, and workspace scope."""
    username: str
    role: str = "viewer"  # role name (references Role.name)
    api_key: str = ""
    enabled: bool = True
    email: str = ""
    workspace: str = "default"  # workspace scope
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "role": self.role,
            "api_key": self.api_key,
            "enabled": self.enabled,
            "email": self.email,
            "workspace": self.workspace,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            username=data["username"],
            role=data.get("role", "viewer"),
            api_key=data.get("api_key", ""),
            enabled=data.get("enabled", True),
            email=data.get("email", ""),
            workspace=data.get("workspace", "default"),
            created_at=data.get("created_at", ""),
        )


# ── Built-in role definitions ───────────────────────────────────────

def _builtin_role_admin() -> Role:
    """Administrator — full access to everything."""
    permissions = set()
    for res in Resource:
        for act in Action:
            permissions.add(Permission(resource=res, action=act))
    return Role(
        name="admin",
        description="Full access to all resources and actions",
        permissions=permissions,
        is_builtin=True,
    )


def _builtin_role_operator() -> Role:
    """Operator — can manage flows, agents, packages; cannot manage users/RBAC."""
    return Role(
        name="operator",
        description="Can run flows, manage agents, view everything except RBAC and users",
        permissions={
            # Flows
            Permission(Resource.FLOW, Action.CREATE),
            Permission(Resource.FLOW, Action.READ),
            Permission(Resource.FLOW, Action.UPDATE),
            Permission(Resource.FLOW, Action.DELETE),
            Permission(Resource.FLOW, Action.EXECUTE),
            # Agents
            Permission(Resource.AGENT, Action.CREATE),
            Permission(Resource.AGENT, Action.READ),
            Permission(Resource.AGENT, Action.UPDATE),
            Permission(Resource.AGENT, Action.DELETE),
            Permission(Resource.AGENT, Action.EXECUTE),
            # Packages
            Permission(Resource.PACKAGE, Action.CREATE),
            Permission(Resource.PACKAGE, Action.READ),
            Permission(Resource.PACKAGE, Action.UPDATE),
            Permission(Resource.PACKAGE, Action.DELETE),
            Permission(Resource.PACKAGE, Action.EXECUTE),
            # Registry
            Permission(Resource.REGISTRY, Action.READ),
            Permission(Resource.REGISTRY, Action.EXECUTE),
            # Mothership config
            Permission(Resource.MOTHERSHIP, Action.READ),
            Permission(Resource.MOTHERSHIP, Action.UPDATE),
            # Audit
            Permission(Resource.AUDIT, Action.READ),
        },
        is_builtin=True,
    )


def _builtin_role_viewer() -> Role:
    """Viewer — read-only access to everything."""
    permissions = set()
    for res in Resource:
        permissions.add(Permission(resource=res, action=Action.READ))
    return Role(
        name="viewer",
        description="Read-only access to all resources",
        permissions=permissions,
        is_builtin=True,
    )


def _builtin_role_deployer() -> Role:
    """Deployer — can deploy flows and manage agents, no package/registry write."""
    return Role(
        name="deployer",
        description="Can deploy flows and manage agents in production",
        permissions={
            Permission(Resource.FLOW, Action.READ),
            Permission(Resource.FLOW, Action.EXECUTE),
            Permission(Resource.AGENT, Action.READ),
            Permission(Resource.AGENT, Action.UPDATE),
            Permission(Resource.AGENT, Action.EXECUTE),
            Permission(Resource.PACKAGE, Action.READ),
            Permission(Resource.REGISTRY, Action.READ),
            Permission(Resource.MOTHERSHIP, Action.READ),
            Permission(Resource.AUDIT, Action.READ),
        },
        is_builtin=True,
    )


def get_builtin_roles() -> Dict[str, Role]:
    """Return all built-in roles keyed by name."""
    return {
        "admin": _builtin_role_admin(),
        "operator": _builtin_role_operator(),
        "viewer": _builtin_role_viewer(),
        "deployer": _builtin_role_deployer(),
    }
