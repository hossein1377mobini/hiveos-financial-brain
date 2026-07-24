"""File Watch Folder models — per-customer drop folders with auto-ingest."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class WatchFolderStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class FileEventKind(str, Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    INGESTED = "ingested"
    INGEST_FAILED = "ingest_failed"


@dataclass
class WatchFolder:
    """A customer's drop folder that auto-ingests files into the knowledge index."""

    folder_id: str
    name: str
    path: str  # absolute path to the watched directory
    source_type: str = "customer"  # prefix for knowledge index source_type
    status: WatchFolderStatus = WatchFolderStatus.ACTIVE
    supported_extensions: List[str] = field(
        default_factory=lambda: [".md", ".txt", ".pdf", ".csv", ".json"]
    )
    tags: List[str] = field(default_factory=list)  # auto-applied to all ingested docs
    customer_id: str = ""  # optional customer identifier
    created_at: str = ""
    updated_at: str = ""
    last_scan_at: Optional[str] = None
    total_files_ingested: int = 0

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def accepts_file(self, file_path: Path) -> bool:
        """Check if a file should be processed based on extension."""
        return file_path.suffix.lower() in self.supported_extensions

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "WatchFolder":
        status_str = data.get("status", "active")
        try:
            status = WatchFolderStatus(status_str)
        except ValueError:
            status = WatchFolderStatus.ACTIVE
        return cls(
            folder_id=data["folder_id"],
            name=data.get("name", data["folder_id"]),
            path=data["path"],
            source_type=data.get("source_type", "customer"),
            status=status,
            supported_extensions=data.get("supported_extensions", [".md", ".txt", ".pdf", ".csv", ".json"]),
            tags=data.get("tags", []),
            customer_id=data.get("customer_id", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            last_scan_at=data.get("last_scan_at"),
            total_files_ingested=data.get("total_files_ingested", 0),
        )


@dataclass
class FileEvent:
    """Record of a file system event detected by the watcher."""

    event_id: str = ""
    folder_id: str = ""
    file_path: str = ""
    event_kind: FileEventKind = FileEventKind.CREATED
    chunks_ingested: int = 0
    error_message: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.event_id:
            self.event_id = uuid.uuid4().hex[:12]
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "folder_id": self.folder_id,
            "file_path": self.file_path,
            "event_kind": self.event_kind.value,
            "chunks_ingested": self.chunks_ingested,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }


def generate_folder_id(name: str) -> str:
    """Generate a URL-safe folder ID from a name."""
    import re
    safe = re.sub(r"[^a-zA-Z0-9\-]", "-", name.lower().strip())
    safe = re.sub(r"-+", "-", safe).strip("-")
    if not safe:
        safe = uuid.uuid4().hex[:8]
    return f"wf-{safe}"
