"""HiveOS Storage Engine — SQLite-based persistence layer.

Provides a generic key-value store with JSON serialisation so every
in-memory module (Brain, Learning, Playground) can save/restore state
across restarts with zero schema migrations.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from hiveos.storage.migrations import MigrationRunner, get_builtin_migrations


class StorageEngine:
    """Thin SQLite wrapper — each namespace is a key→JSON-value table.

    Thread-safe via an exclusive lock. Schema migrations run automatically
    on first connect.
    """

    def __init__(self, db_path: Optional[Path | str] = None):
        self._db_path = Path(db_path or self._default_path())
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self.migration_runner: Optional[MigrationRunner] = None
        self._connect()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upsert(self, namespace: str, key: str, data: dict) -> None:
        """Insert or replace a record in *namespace* with *key*."""
        raw = json.dumps(data, ensure_ascii=False, default=str)
        now = _now()
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO kv_store
                   (namespace, key, value, created_at, updated_at)
                   VALUES (?, ?, ?,
                       COALESCE((SELECT created_at FROM kv_store
                                  WHERE namespace=? AND key=?), ?),
                       ?)""",
                (namespace, key, raw, namespace, key, now, now),
            )
            self._conn.commit()

    def load(self, namespace: str, key: str) -> Optional[dict]:
        """Return a single record, or *None*."""
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM kv_store WHERE namespace=? AND key=?",
                (namespace, key),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def load_all(self, namespace: str) -> List[dict]:
        """Return every record in *namespace*."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT key, value FROM kv_store WHERE namespace=? ORDER BY key",
                (namespace,),
            ).fetchall()
        return [json.loads(r[1]) for r in rows]

    def load_all_with_keys(self, namespace: str) -> Dict[str, dict]:
        """Return *{key: data}* for every record in *namespace*."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT key, value FROM kv_store WHERE namespace=? ORDER BY key",
                (namespace,),
            ).fetchall()
        return {r[0]: json.loads(r[1]) for r in rows}

    def delete(self, namespace: str, key: str) -> None:
        """Delete a single record."""
        with self._lock:
            self._conn.execute(
                "DELETE FROM kv_store WHERE namespace=? AND key=?",
                (namespace, key),
            )
            self._conn.commit()

    def clear(self, namespace: str) -> None:
        """Delete every record in *namespace*."""
        with self._lock:
            self._conn.execute(
                "DELETE FROM kv_store WHERE namespace=?", (namespace,)
            )
            self._conn.commit()

    def count(self, namespace: str) -> int:
        """Number of records in *namespace*."""
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM kv_store WHERE namespace=?", (namespace,)
            ).fetchone()
        return row[0] if row else 0

    def vacuum(self) -> None:
        """Recover disk space."""
        with self._lock:
            self._conn.execute("VACUUM")

    def __del__(self):
        self.close()

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.executescript(
            """CREATE TABLE IF NOT EXISTS kv_store (
                namespace  TEXT NOT NULL,
                key        TEXT NOT NULL,
                value      TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (namespace, key)
            );
            CREATE INDEX IF NOT EXISTS idx_kv_namespace ON kv_store(namespace);
            """
        )
        self._conn.commit()
        # Run schema migrations
        self.migration_runner = MigrationRunner(self._conn)
        self.migration_runner.register_all(get_builtin_migrations())
        self.migration_runner.run_all()

    @staticmethod
    def _default_path() -> Path:
        return Path.home() / ".hiveos" / "data" / "hiveos.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
