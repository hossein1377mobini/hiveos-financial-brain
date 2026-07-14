"""
HiveOS Migration System — schema versioning for SQLite StorageEngine.

Each migration is a versioned callable that receives a SQLite connection.
The MigrationRunner tracks which migrations have been applied and runs
pending ones automatically when StorageEngine connects.

Usage:
    from hiveos.storage.migrations import MigrationRunner, Migration

    def add_widgets_table(conn):
        conn.execute("CREATE TABLE IF NOT EXISTS widgets (id INTEGER PRIMARY KEY)")

    runner = MigrationRunner(conn)
    runner.register(Migration(2, "create_widgets", add_widgets_table))
    runner.run_all()  # runs version 2 if only version 1 was applied
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, List, Optional
from sqlite3 import Connection


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class Migration:
    """A single schema migration.

    Attributes:
        version:   Monotonically increasing integer (must be unique).
        name:      Human-readable description (e.g. \"create_gates_table\").
        apply_fn:  Callable that receives a sqlite3.Connection and runs DDL/DML.
    """
    version: int
    name: str
    apply_fn: Callable[[Connection], None]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class MigrationRunner:
    """Checks which migrations have been applied and runs pending ones."""

    def __init__(self, conn: Connection):
        self._conn = conn
        self._migrations: List[Migration] = []
        self._ensure_migrations_table()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, migration: Migration) -> None:
        """Register a single migration. Duplicate versions are ignored."""
        existing = {m.version for m in self._migrations}
        if migration.version not in existing:
            self._migrations.append(migration)

    def register_all(self, migrations: List[Migration]) -> None:
        """Register a list of migrations."""
        for m in migrations:
            self.register(m)

    def applied_versions(self) -> List[int]:
        """Return sorted list of already-applied version numbers."""
        rows = self._conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        return [r[0] for r in rows]

    def pending(self) -> List[Migration]:
        """Return registered migrations that have NOT been applied yet."""
        applied = set(self.applied_versions())
        return sorted(
            [m for m in self._migrations if m.version not in applied],
            key=lambda m: m.version,
        )

    def run_all(self) -> List[int]:
        """Apply every pending migration.

        Each migration runs inside its own transaction. If a migration
        raises, the error is surfaced immediately (already-applied
        migrations remain applied).

        Returns the list of version numbers that were applied.
        """
        applied = []
        for migration in self.pending():
            self._apply_one(migration)
            applied.append(migration.version)
        return applied

    def run_to(self, target_version: int) -> List[int]:
        """Apply pending migrations up to (and including) *target_version*."""
        applied = []
        for migration in self.pending():
            if migration.version > target_version:
                break
            self._apply_one(migration)
            applied.append(migration.version)
        return applied

    def reset(self) -> None:
        """⚠️  Drop the migrations table (dev/test helper)."""
        self._conn.execute("DROP TABLE IF EXISTS schema_migrations")
        self._conn.commit()
        self._ensure_migrations_table()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_migrations_table(self) -> None:
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                version     INTEGER PRIMARY KEY,
                name        TEXT    NOT NULL,
                applied_at  TEXT    NOT NULL
            )"""
        )
        self._conn.commit()

    def _apply_one(self, migration: Migration) -> None:
        try:
            migration.apply_fn(self._conn)
            self._conn.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (migration.version, migration.name, _now()),
            )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise


# ---------------------------------------------------------------------------
# Built-in migrations — registered by StorageEngine on first connect
# ---------------------------------------------------------------------------

_BUILTIN_MIGRATIONS: List[Migration] = []


def _register_builtin(migration: Migration) -> None:
    _BUILTIN_MIGRATIONS.append(migration)


def get_builtin_migrations() -> List[Migration]:
    """Return a copy of the built-in migration list."""
    return list(_BUILTIN_MIGRATIONS)


# --- Migration 1: Initial schema ---
def _m001_initial(conn: Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS kv_store (
            namespace  TEXT NOT NULL,
            key        TEXT NOT NULL,
            value      TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (namespace, key)
        )"""
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_kv_namespace ON kv_store(namespace)"
    )


_register_builtin(Migration(1, "initial_schema", _m001_initial))


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
