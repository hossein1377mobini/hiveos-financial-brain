"""
Audit Trail data models — Action, Resource, Entry.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any


class AuditAction(str, Enum):
    """Actions that can be audited."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    HEARTBEAT = "heartbeat"
    SYNC = "sync"
    CONFIG = "config"


class AuditResource(str, Enum):
    """Resources that can be audited."""
    AGENT = "agent"
    FLOW = "flow"
    PACKAGE = "package"
    REGISTRY = "registry"
    TASK = "task"
    USER = "user"
    ROLE = "role"
    MOTHERSHIP = "mothership"
    RBAC = "rbac"
    AUDIT = "audit"


class AuditResult(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"  # permission denied
    ERROR = "error"


@dataclass
class AuditEntry:
    """A single audit log entry."""
    timestamp: str = ""  # ISO-8601 (auto-set if empty)
    action: AuditAction = AuditAction.READ
    resource: AuditResource = AuditResource.MOTHERSHIP
    actor: str = "system"
    resource_id: str = ""  # specific resource identifier (e.g. agent name, task id)
    result: AuditResult = AuditResult.SUCCESS
    status_code: int = 200
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    ip: str = ""
    duration_ms: float = 0.0
    entry_id: str = ""

    def __post_init__(self):
        if not self.entry_id:
            import uuid
            self.entry_id = f"aud-{uuid.uuid4().hex[:12]}"
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "action": self.action.value,
            "resource": self.resource.value,
            "actor": self.actor,
            "resource_id": self.resource_id,
            "result": self.result.value,
            "status_code": self.status_code,
            "message": self.message,
            "details": self.details,
            "ip": self.ip,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AuditEntry:
        return cls(
            entry_id=data.get("entry_id", ""),
            timestamp=data.get("timestamp", ""),
            action=AuditAction(data["action"]),
            resource=AuditResource(data["resource"]),
            actor=data.get("actor", "unknown"),
            resource_id=data.get("resource_id", ""),
            result=AuditResult(data.get("result", "success")),
            status_code=data.get("status_code", 200),
            message=data.get("message", ""),
            details=data.get("details", {}),
            ip=data.get("ip", ""),
            duration_ms=data.get("duration_ms", 0.0),
        )

    @classmethod
    def from_json(cls, raw: str) -> AuditEntry:
        return cls.from_dict(json.loads(raw))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    def to_gbrain_markdown(self) -> str:
        """Format entry as markdown for gbrain import."""
        lines = [
            f"# Audit: {self.entry_id}",
            "",
            f"**Timestamp:** {self.timestamp}",
            f"**Actor:** {self.actor}",
            f"**Action:** {self.action.value}",
            f"**Resource:** {self.resource.value}",
            f"**Resource ID:** {self.resource_id or '-'}",
            f"**Result:** {self.result.value}",
            f"**Status:** {self.status_code}",
            f"**IP:** {self.ip or '-'}",
            f"**Duration:** {self.duration_ms:.1f}ms",
            "",
        ]
        if self.message:
            lines.append(f"**Message:** {self.message}")
            lines.append("")
        if self.details:
            lines.append("**Details:**")
            lines.append("")
            for k, v in self.details.items():
                lines.append(f"- **{k}:** {v}")
            lines.append("")
        lines.append("---")
        lines.append(f"*Logged at {self.timestamp}*")
        return "\n".join(lines)
