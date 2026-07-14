"""
AuditTrail — append-only audit log with gbrain PGLite sync.

Design:
- **Primary store:** JSONL files (one per day, fast append)
- **Search index:** gbrain PGLite via CLI (for semantic query)
- **Sync:** manual or cron-driven (gbrain import)
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator
from datetime import datetime, timezone, date as date_type
from collections import Counter

from rich.console import Console
from rich.table import Table

from .models import AuditEntry, AuditAction, AuditResource, AuditResult

console = Console()

GBRAIN_DIR = Path.home() / ".bun" / "install" / "global" / "node_modules" / "gbrain"
GBRAIN_CLI = GBRAIN_DIR / "src" / "cli.ts"


def _gbrain_available() -> bool:
    """Check if gbrain CLI is available."""
    return GBRAIN_CLI.exists()


def _gbrain_put(slug: str, content: str) -> bool:
    """Write a page to gbrain via CLI."""
    if not _gbrain_available():
        return False
    try:
        result = subprocess.run(
            ["bun", "run", str(GBRAIN_CLI), "put", slug],
            input=content.encode("utf-8"),
            capture_output=True,
            timeout=15,
            cwd=str(GBRAIN_DIR),
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _gbrain_search(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search gbrain for audit entries."""
    if not _gbrain_available():
        return []
    try:
        result = subprocess.run(
            ["bun", "run", str(GBRAIN_CLI), "search", query, "--json"],
            capture_output=True, timeout=15, cwd=str(GBRAIN_DIR),
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return []


def _gbrain_query(question: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Semantic query gbrain for audit entries."""
    if not _gbrain_available():
        return []
    try:
        result = subprocess.run(
            ["bun", "run", str(GBRAIN_CLI), "query", question, "--json"],
            capture_output=True, timeout=15, cwd=str(GBRAIN_DIR),
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return []


class AuditTrail:
    """
    Append-only audit log.

    Writes JSONL files to ~/.hiveos/audit/YYYY-MM-DD.jsonl.
    Supports gbrain sync for semantic search.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else Path.home() / ".hiveos" / "audit"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._buffer: List[AuditEntry] = []
        self._buffer_size = 0

    # ── Primary: JSONL persist ──────────────────────────────────────

    def _daily_file(self, dt: Optional[date_type] = None) -> Path:
        if dt is None:
            dt = date_type.today()
        return self.data_dir / f"{dt.isoformat()}.jsonl"

    def log(self, entry: AuditEntry) -> str:
        """Record a single audit entry. Fast append to daily JSONL."""
        if not entry.timestamp:
            entry.timestamp = datetime.now(timezone.utc).isoformat()
        if not entry.entry_id:
            entry.entry_id = f"aud-{uuid.uuid4().hex[:12]}"

        line = entry.to_json()
        daily = self._daily_file()
        with open(daily, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        return entry.entry_id

    def log_simple(
        self,
        action: AuditAction,
        resource: AuditResource,
        actor: str = "system",
        resource_id: str = "",
        result: AuditResult = AuditResult.SUCCESS,
        status_code: int = 200,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
    ) -> str:
        """Quick shorthand to log a simple event."""
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            resource=resource,
            actor=actor,
            resource_id=resource_id,
            result=result,
            status_code=status_code,
            message=message,
            details=details or {},
            duration_ms=duration_ms,
        )
        return self.log(entry)

    # ── Reading ─────────────────────────────────────────────────────

    def read_today(self) -> List[AuditEntry]:
        """Read all entries from today's file."""
        return self.read_file(self._daily_file())

    def read_file(self, path: Path) -> List[AuditEntry]:
        """Read all entries from a specific JSONL file."""
        if not path.exists():
            return []
        entries = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(AuditEntry.from_json(line))
                    except (json.JSONDecodeError, ValueError, KeyError):
                        pass
        return entries

    def read_range(self, start: date_type, end: date_type) -> List[AuditEntry]:
        """Read entries across a date range (inclusive)."""
        entries = []
        current = start
        while current <= end:
            entries.extend(self.read_file(self._daily_file(current)))
            from datetime import timedelta
            current += timedelta(days=1)
        return entries

    def list_files(self) -> List[Path]:
        """List all audit JSONL files sorted by date."""
        return sorted(self.data_dir.glob("*.jsonl"))

    def count(self) -> int:
        """Count total entries across all files."""
        total = 0
        for f in self.list_files():
            total += sum(1 for _ in open(f, "r", encoding="utf-8") if _.strip())
        return total

    # ── Query / Search ──────────────────────────────────────────────

    def search_local(self, query: str) -> List[AuditEntry]:
        """Simple local text search across all audit files."""
        query_lower = query.lower()
        results = []
        for f in self.list_files():
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    if query_lower in line.lower():
                        try:
                            results.append(AuditEntry.from_json(line.strip()))
                        except (json.JSONDecodeError, ValueError, KeyError):
                            pass
        return sorted(results, key=lambda e: e.timestamp, reverse=True)

    def search_gbrain(self, query: str) -> List[Dict[str, Any]]:
        """Semantic search via gbrain."""
        return _gbrain_query(query)

    def keyword_gbrain(self, query: str) -> List[Dict[str, Any]]:
        """Keyword search via gbrain."""
        return _gbrain_search(query)

    # ── Statistics ──────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Aggregate statistics across all entries."""
        total = 0
        action_counts: Counter = Counter()
        resource_counts: Counter = Counter()
        result_counts: Counter = Counter()
        actor_counts: Counter = Counter()
        error_count = 0
        unique_days = set()

        for f in self.list_files():
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    total += 1
                    try:
                        entry = AuditEntry.from_json(line)
                        action_counts[entry.action.value] += 1
                        resource_counts[entry.resource.value] += 1
                        result_counts[entry.result.value] += 1
                        actor_counts[entry.actor] += 1
                        if entry.result in (AuditResult.ERROR, AuditResult.FAILURE):
                            error_count += 1
                        unique_days.add(entry.timestamp[:10])
                    except (json.JSONDecodeError, ValueError, KeyError):
                        pass

        return {
            "total_entries": total,
            "unique_days": len(unique_days),
            "files": len(self.list_files()),
            "actions": dict(action_counts.most_common()),
            "resources": dict(resource_counts.most_common()),
            "results": dict(result_counts.most_common()),
            "top_actors": dict(actor_counts.most_common(10)),
            "errors": error_count,
        }

    # ── gbrain Sync ─────────────────────────────────────────────────

    def sync_to_gbrain(self, date: Optional[str] = None, max_pages: int = 500) -> int:
        """
        Sync audit entries to gbrain PGLite.

        Each entry becomes a gbrain page at audit/<entry_id>.
        Returns number of pages synced.
        """
        if not _gbrain_available():
            console.print("[red]❌ gbrain not found. Install with: bun install -g gbrain[/red]")
            return 0

        if date:
            try:
                dt = date_type.fromisoformat(date)
                entries = self.read_file(self._daily_file(dt))
            except ValueError:
                console.print(f"[red]❌ Invalid date '{date}', use YYYY-MM-DD[/red]")
                return 0
        else:
            # Sync all unsynced files (last 30 days)
            from datetime import timedelta
            entries = []
            for i in range(30):
                dt = date_type.today() - timedelta(days=i)
                entries.extend(self.read_file(self._daily_file(dt)))

        console.print(f"[dim]📤 Syncing {min(len(entries), max_pages)} entries to gbrain...[/dim]")

        synced = 0
        for entry in entries:
            if synced >= max_pages:
                break
            slug = f"audit/{entry.entry_id}"
            markdown = entry.to_gbrain_markdown()
            if _gbrain_put(slug, markdown):
                synced += 1

        if synced:
            console.print(f"[green]✅ Synced {synced} audit entries to gbrain[/green]")
        else:
            console.print("[yellow]⚠️  No entries synced (check gbrain installation)[/yellow]")
        return synced

    # ── Maintenance ─────────────────────────────────────────────────

    def rotate(self, keep_days: int = 90) -> int:
        """Archive/remove audit files older than keep_days. Returns count removed."""
        from datetime import timedelta
        cutoff = date_type.today() - timedelta(days=keep_days)
        removed = 0
        for f in self.list_files():
            try:
                file_date = date_type.fromisoformat(f.stem)
                if file_date < cutoff:
                    f.unlink()
                    removed += 1
            except ValueError:
                pass
        if removed:
            console.print(f"[dim]🗑️ Rotated {removed} old audit file(s)[/dim]")
        return removed
