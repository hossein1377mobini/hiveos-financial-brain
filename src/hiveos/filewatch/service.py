"""File Watch Service — monitors customer drop folders and auto-ingests files.

Architecture:
    FileWatchService
        ├── watch folder CRUD (backed by SQLite via StorageEngine)
        ├── background watcher thread (watchdog)
        └── event log (SQLite table for audit)

The watcher runs a single background thread that monitors all active
folders. On file creation/modification it calls KnowledgeService.ingest_document
for each qualifying file, then logs the event.
"""

from __future__ import annotations

import logging
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .models import (
    WatchFolder,
    WatchFolderStatus,
    FileEvent,
    FileEventKind,
    generate_folder_id,
)

logger = logging.getLogger(__name__)

# ── DDL ────────────────────────────────────────────────────────────────

_WATCH_FOLDERS_DDL = """
CREATE TABLE IF NOT EXISTS watch_folders (
    folder_id           TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    path                TEXT NOT NULL,
    source_type         TEXT NOT NULL DEFAULT 'customer',
    status              TEXT NOT NULL DEFAULT 'active',
    supported_extensions TEXT NOT NULL DEFAULT '.md,.txt,.pdf,.csv,.json',
    tags                TEXT NOT NULL DEFAULT '',
    customer_id         TEXT NOT NULL DEFAULT '',
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    last_scan_at        TEXT,
    total_files_ingested INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_wf_status ON watch_folders(status);
CREATE INDEX IF NOT EXISTS idx_wf_customer ON watch_folders(customer_id);
"""

_FILE_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS file_events (
    event_id        TEXT PRIMARY KEY,
    folder_id       TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    event_kind      TEXT NOT NULL,
    chunks_ingested INTEGER NOT NULL DEFAULT 0,
    error_message   TEXT,
    timestamp       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fe_folder ON file_events(folder_id);
CREATE INDEX IF NOT EXISTS idx_fe_time ON file_events(timestamp);
"""


def _ensure_tables(engine) -> None:
    """Create filewatch tables if missing."""
    with engine._lock:
        engine._conn.executescript(_WATCH_FOLDERS_DDL)
        engine._conn.executescript(_FILE_EVENTS_DDL)
        engine._conn.commit()


# ── File Watch Service ─────────────────────────────────────────────────

class FileWatchService:
    """Manages customer file watch folders with background auto-ingest."""

    def __init__(self, storage_engine, knowledge_service):
        self._engine = storage_engine
        self._knowledge = knowledge_service
        _ensure_tables(storage_engine)

        self._watchers: Dict[str, _FolderWatcher] = {}
        self._lock = threading.Lock()

    # ── CRUD ──────────────────────────────────────────────────────────

    def add_folder(
        self,
        name: str,
        path: str,
        source_type: str = "customer",
        customer_id: str = "",
        tags: Optional[List[str]] = None,
        supported_extensions: Optional[List[str]] = None,
    ) -> WatchFolder:
        """Register a new watch folder. Creates the directory if missing."""
        folder = WatchFolder(
            folder_id=generate_folder_id(name),
            name=name,
            path=str(Path(path).resolve()),
            source_type=source_type,
            customer_id=customer_id,
            tags=tags or [],
            supported_extensions=supported_extensions or [".md", ".txt", ".pdf", ".csv", ".json"],
        )

        # Ensure directory exists
        Path(folder.path).mkdir(parents=True, exist_ok=True)

        # Persist
        self._save_folder(folder)

        # Start watching
        self._start_watcher(folder)

        # Initial scan: ingest files already present
        self._scan_and_ingest(folder)
        folder = self.get_folder(folder.folder_id) or folder
        folder.last_scan_at = datetime.now(timezone.utc).isoformat()
        self._save_folder(folder)

        logger.info("Watch folder added: %s -> %s", folder.folder_id, folder.path)
        return folder

    def get_folder(self, folder_id: str) -> Optional[WatchFolder]:
        row = self._engine.fetch_one(
            "SELECT * FROM watch_folders WHERE folder_id = ?", (folder_id,)
        )
        return self._row_to_folder(row) if row else None

    def list_folders(self, customer_id: Optional[str] = None) -> List[WatchFolder]:
        if customer_id:
            rows = self._engine.fetch_all(
                "SELECT * FROM watch_folders WHERE customer_id = ? ORDER BY name",
                (customer_id,),
            )
        else:
            rows = self._engine.fetch_all(
                "SELECT * FROM watch_folders ORDER BY name"
            )
        return [self._row_to_folder(r) for r in rows]

    def update_folder(
        self,
        folder_id: str,
        name: Optional[str] = None,
        status: Optional[WatchFolderStatus] = None,
        tags: Optional[List[str]] = None,
        supported_extensions: Optional[List[str]] = None,
    ) -> Optional[WatchFolder]:
        folder = self.get_folder(folder_id)
        if not folder:
            return None

        if name is not None:
            folder.name = name
        if status is not None:
            old_status = folder.status
            folder.status = status
            # Handle pause/resume
            if old_status == WatchFolderStatus.ACTIVE and status == WatchFolderStatus.PAUSED:
                self._stop_watcher(folder_id)
            elif old_status == WatchFolderStatus.PAUSED and status == WatchFolderStatus.ACTIVE:
                self._start_watcher(folder)
        if tags is not None:
            folder.tags = tags
        if supported_extensions is not None:
            folder.supported_extensions = supported_extensions

        folder.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_folder(folder)
        return folder

    def remove_folder(self, folder_id: str) -> bool:
        """Stop watcher and delete folder record (does NOT delete files)."""
        self._stop_watcher(folder_id)
        row = self._engine.fetch_one(
            "SELECT folder_id FROM watch_folders WHERE folder_id = ?", (folder_id,)
        )
        if not row:
            return False
        with self._engine._lock:
            self._engine._conn.execute(
                "DELETE FROM watch_folders WHERE folder_id = ?", (folder_id,)
            )
            self._engine._conn.commit()
        logger.info("Watch folder removed: %s", folder_id)
        return True

    # ── Manual ingest ─────────────────────────────────────────────────

    def scan_folder(self, folder_id: str) -> int:
        """One-shot scan: ingest all eligible files in the folder. Returns count."""
        folder = self.get_folder(folder_id)
        if not folder:
            return 0
        count = self._scan_and_ingest(folder)
        # Reload from DB — _ingest_file already updated total_files_ingested
        folder = self.get_folder(folder_id)
        if folder:
            folder.last_scan_at = datetime.now(timezone.utc).isoformat()
            self._save_folder(folder)
        return count

    def get_events(
        self,
        folder_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[FileEvent]:
        """Return recent file events, newest first."""
        if folder_id:
            rows = self._engine.fetch_all(
                "SELECT * FROM file_events WHERE folder_id = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (folder_id, limit),
            )
        else:
            rows = self._engine.fetch_all(
                "SELECT * FROM file_events ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
        return [self._row_to_event(r) for r in rows]

    # ── Lifecycle ─────────────────────────────────────────────────────

    def start_all(self) -> None:
        """Start watchers for all active folders."""
        for folder in self.list_folders():
            if folder.status == WatchFolderStatus.ACTIVE:
                self._start_watcher(folder)

    def stop_all(self) -> None:
        """Stop all running watchers."""
        with self._lock:
            for watcher in self._watchers.values():
                watcher.stop()
            self._watchers.clear()

    # ── Internals ─────────────────────────────────────────────────────

    def _start_watcher(self, folder: WatchFolder) -> None:
        """Start a background watcher for one folder."""
        with self._lock:
            if folder.folder_id in self._watchers:
                return  # already running
            watcher = _FolderWatcher(folder, self)
            self._watchers[folder.folder_id] = watcher
            watcher.start()

    def _stop_watcher(self, folder_id: str) -> None:
        with self._lock:
            watcher = self._watchers.pop(folder_id, None)
            if watcher:
                watcher.stop()

    def _scan_and_ingest(self, folder: WatchFolder) -> int:
        """Scan a folder and ingest all eligible files."""
        folder_path = Path(folder.path)
        if not folder_path.exists():
            logger.warning("Watch folder path does not exist: %s", folder.path)
            return 0

        count = 0
        for file_path in folder_path.iterdir():
            if not file_path.is_file():
                continue
            if file_path.name.startswith("."):
                continue
            if not folder.accepts_file(file_path):
                continue
            chunks = self._ingest_file(folder, file_path)
            count += chunks

        return count

    def _ingest_file(self, folder: WatchFolder, file_path: Path) -> int:
        """Ingest a single file into the knowledge index."""
        source_type = f"{folder.source_type}:{folder.folder_id}"
        try:
            from hiveos.knowledge.ingestion import ingest_single_file
            count = ingest_single_file(self._engine, file_path, source_type)

            # Update counter
            with self._engine._lock:
                self._engine._conn.execute(
                    "UPDATE watch_folders SET total_files_ingested = total_files_ingested + ? WHERE folder_id = ?",
                    (count, folder.folder_id),
                )
                self._engine._conn.commit()

            # Log event
            event = FileEvent(
                folder_id=folder.folder_id,
                file_path=str(file_path),
                event_kind=FileEventKind.INGESTED,
                chunks_ingested=count,
            )
            self._log_event(event)

            logger.info(
                "Ingested %s: %d chunks", file_path.name, count
            )
            return count

        except Exception as exc:
            event = FileEvent(
                folder_id=folder.folder_id,
                file_path=str(file_path),
                event_kind=FileEventKind.INGEST_FAILED,
                error_message=str(exc),
            )
            self._log_event(event)
            logger.error("Failed to ingest %s: %s", file_path, exc)
            return 0

    def _log_event(self, event: FileEvent) -> None:
        """Persist a file event to the database."""
        with self._engine._lock:
            self._engine._conn.execute(
                "INSERT INTO file_events "
                "(event_id, folder_id, file_path, event_kind, chunks_ingested, error_message, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    event.event_id,
                    event.folder_id,
                    event.file_path,
                    event.event_kind.value,
                    event.chunks_ingested,
                    event.error_message,
                    event.timestamp,
                ),
            )
            self._engine._conn.commit()

    def _save_folder(self, folder: WatchFolder) -> None:
        """Persist a WatchFolder to the database."""
        with self._engine._lock:
            self._engine._conn.execute(
                """INSERT OR REPLACE INTO watch_folders
                   (folder_id, name, path, source_type, status, supported_extensions,
                    tags, customer_id, created_at, updated_at, last_scan_at, total_files_ingested)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    folder.folder_id,
                    folder.name,
                    folder.path,
                    folder.source_type,
                    folder.status.value,
                    ",".join(folder.supported_extensions),
                    ",".join(folder.tags),
                    folder.customer_id,
                    folder.created_at,
                    folder.updated_at,
                    folder.last_scan_at,
                    folder.total_files_ingested,
                ),
            )
            self._engine._conn.commit()

    @staticmethod
    def _row_to_folder(row: tuple) -> WatchFolder:
        return WatchFolder(
            folder_id=row[0],
            name=row[1],
            path=row[2],
            source_type=row[3],
            status=WatchFolderStatus(row[4]),
            supported_extensions=row[5].split(",") if row[5] else [],
            tags=row[6].split(",") if row[6] else [],
            customer_id=row[7] or "",
            created_at=row[8] or "",
            updated_at=row[9] or "",
            last_scan_at=row[10],
            total_files_ingested=row[11] or 0,
        )

    @staticmethod
    def _row_to_event(row: tuple) -> FileEvent:
        return FileEvent(
            event_id=row[0],
            folder_id=row[1],
            file_path=row[2],
            event_kind=FileEventKind(row[3]),
            chunks_ingested=row[4] or 0,
            error_message=row[5],
            timestamp=row[6] or "",
        )


# ── Background Watcher Thread ──────────────────────────────────────────

class _FolderWatcher(threading.Thread):
    """Lightweight polling watcher for a single folder.

    Uses polling instead of OS-level events (watchdog) for portability
    across Windows/Linux/macOS. Polls every `interval` seconds.
    """

    def __init__(
        self,
        folder: WatchFolder,
        service: FileWatchService,
        interval: float = 5.0,
    ):
        super().__init__(daemon=True, name=f"watcher-{folder.folder_id}")
        self._folder = folder
        self._service = service
        self._interval = interval
        self._stop_event = threading.Event()
        self._known_files: Dict[str, float] = {}  # path -> mtime

    def run(self) -> None:
        """Poll loop: detect new/modified files and ingest."""
        # Initial snapshot
        self._known_files = self._snapshot()

        while not self._stop_event.is_set():
            try:
                self._poll()
            except Exception as exc:
                logger.error(
                    "Watcher %s error: %s", self._folder.folder_id, exc
                )
            self._stop_event.wait(self._interval)

    def stop(self) -> None:
        self._stop_event.set()

    def _snapshot(self) -> Dict[str, float]:
        """Build a {path: mtime} map of eligible files."""
        result: Dict[str, float] = {}
        folder_path = Path(self._folder.path)
        if not folder_path.exists():
            return result
        for f in folder_path.iterdir():
            if f.is_file() and not f.name.startswith(".") and self._folder.accepts_file(f):
                try:
                    result[str(f)] = f.stat().st_mtime
                except OSError:
                    pass
        return result

    def _poll(self) -> None:
        """Compare current state against known files."""
        current = self._snapshot()

        # New files
        for fpath, mtime in current.items():
            if fpath not in self._known_files:
                logger.info(
                    "New file detected in %s: %s",
                    self._folder.folder_id,
                    fpath,
                )
                file_path = Path(fpath)
                self._service._ingest_file(self._folder, file_path)

        # Modified files
        for fpath, mtime in current.items():
            old_mtime = self._known_files.get(fpath)
            if old_mtime is not None and mtime > old_mtime:
                logger.info(
                    "Modified file detected in %s: %s",
                    self._folder.folder_id,
                    fpath,
                )
                file_path = Path(fpath)
                self._service._ingest_file(self._folder, file_path)

        self._known_files = current
