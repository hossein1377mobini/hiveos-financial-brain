"""
Privacy Audit — Log all data egress attempts for compliance.

Provides audit trail for all outbound data transfers.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import DataClassification, PrivacyConfig

logger = logging.getLogger(__name__)


@dataclass
class EgressAuditEntry:
    """Audit entry for an egress event."""
    id: Optional[int] = None
    timestamp: datetime = None
    url: str = ""
    method: str = "GET"
    endpoint_id: Optional[str] = None
    data_types: List[DataClassification] = None
    allowed: bool = False
    reason: str = ""
    user_id: Optional[str] = None
    request_size_bytes: int = 0
    response_code: Optional[int] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.data_types is None:
            self.data_types = []


class PrivacyAuditTrail:
    """
    Audit trail for privacy-related events.
    
    Stores all egress attempts in SQLite for compliance and debugging.
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize audit database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS privacy_egress_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    url TEXT NOT NULL,
                    method TEXT NOT NULL,
                    endpoint_id TEXT,
                    data_types TEXT,
                    allowed INTEGER NOT NULL,
                    reason TEXT,
                    user_id TEXT,
                    request_size_bytes INTEGER,
                    response_code INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_egress_timestamp
                ON privacy_egress_audit(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_egress_allowed
                ON privacy_egress_audit(allowed)
            """)
    
    def log_egress(self, entry: EgressAuditEntry) -> int:
        """
        Log an egress attempt.
        
        Returns
        -------
        ID of the inserted audit entry.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                """
                INSERT INTO privacy_egress_audit
                (timestamp, url, method, endpoint_id, data_types, allowed, reason,
                 user_id, request_size_bytes, response_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.timestamp.isoformat(),
                    entry.url,
                    entry.method,
                    entry.endpoint_id,
                    json.dumps([dt.value for dt in entry.data_types]),
                    1 if entry.allowed else 0,
                    entry.reason,
                    entry.user_id,
                    entry.request_size_bytes,
                    entry.response_code,
                ),
            )
            return cursor.lastrowid
    
    def get_recent(
        self,
        limit: int = 100,
        allowed_only: Optional[bool] = None,
    ) -> List[EgressAuditEntry]:
        """
        Get recent audit entries.
        
        Parameters
        ----------
        limit:
            Maximum entries to return.
        allowed_only:
            Filter by allowed/blocked status.
        """
        query = "SELECT * FROM privacy_egress_audit"
        params: List[Any] = []
        
        if allowed_only is not None:
            query += " WHERE allowed = ?"
            params.append(1 if allowed_only else 0)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_blocked(self, limit: int = 100) -> List[EgressAuditEntry]:
        """Get blocked egress attempts."""
        return self.get_recent(limit=limit, allowed_only=False)
    
    def get_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get audit statistics.
        
        Parameters
        ----------
        days:
            Number of days to look back.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            
            # Total attempts
            total = conn.execute(
                "SELECT COUNT(*) as count FROM privacy_egress_audit"
            ).fetchone()["count"]
            
            # Allowed vs blocked
            allowed = conn.execute(
                "SELECT COUNT(*) as count FROM privacy_egress_audit WHERE allowed = 1"
            ).fetchone()["count"]
            blocked = total - allowed
            
            # By endpoint
            by_endpoint = conn.execute(
                """
                SELECT endpoint_id, COUNT(*) as count, SUM(allowed) as allowed_count
                FROM privacy_egress_audit
                GROUP BY endpoint_id
                """
            ).fetchall()
            
            return {
                "total_egress_attempts": total,
                "allowed": allowed,
                "blocked": blocked,
                "by_endpoint": {
                    row["endpoint_id"]: {
                        "total": row["count"],
                        "allowed": row["allowed_count"],
                    }
                    for row in by_endpoint
                },
            }
    
    def cleanup_old(self, retention_days: int = 90) -> int:
        """
        Remove audit entries older than retention_days.
        
        Returns
        -------
        Number of deleted entries.
        """
        cutoff = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        from datetime import timedelta
        cutoff = cutoff - timedelta(days=retention_days)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "DELETE FROM privacy_egress_audit WHERE timestamp < ?",
                (cutoff.isoformat(),),
            )
            return cursor.rowcount
    
    def _row_to_entry(self, row: sqlite3.Row) -> EgressAuditEntry:
        """Convert a database row to an audit entry."""
        data_types = json.loads(row["data_types"]) if row["data_types"] else []
        return EgressAuditEntry(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            url=row["url"],
            method=row["method"],
            endpoint_id=row["endpoint_id"],
            data_types=[DataClassification(dt) for dt in data_types],
            allowed=bool(row["allowed"]),
            reason=row["reason"],
            user_id=row["user_id"],
            request_size_bytes=row["request_size_bytes"],
            response_code=row["response_code"],
        )
