"""HiveOS Learning — Execution Logger.

Passively collects execution data from flow runs and agent operations.
No background threads, no persistence — purely in-memory data collection
that can be wired to a persistent store later.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ExecutionLogger:
    """Passive in-memory execution logger, restorable from storage.

    Collects execution events without interfering with running flows.
    """

    def __init__(self, storage: Optional["StorageEngine"] = None):
        self._storage = storage
        self._executions: Dict[str, dict] = {}
        self._by_flow: Dict[str, list] = defaultdict(list)
        self._by_agent: Dict[str, list] = defaultdict(list)
        self._namespace = "learning:executions"

        if self._storage:
            self._restore()

    def _restore(self):
        """Rehydrate execution logs from persistent storage."""
        for entry in self._storage.load_all(self._namespace):
            log_id = entry.get("log_id", "")
            if log_id:
                self._executions[log_id] = entry
                flow = entry.get("flow_name", "unknown")
                agent = entry.get("agent_id", "unknown")
                self._by_flow[flow].append(entry)
                self._by_agent[agent].append(entry)

    def log_execution(
        self,
        flow_name: str,
        execution_id: str,
        agent_id: str,
        status: str,
        duration_ms: int,
        input_summary: str = "",
        output_summary: str = "",
        error: str = "",
    ) -> str:
        """Log a single agent execution event. Returns log_id."""
        log_id = str(uuid.uuid4())
        entry = {
            "log_id": log_id,
            "flow_name": flow_name,
            "execution_id": execution_id,
            "agent_id": agent_id,
            "status": status,
            "duration_ms": duration_ms,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._executions[log_id] = entry
        self._by_flow[flow_name].append(entry)
        self._by_agent[agent_id].append(entry)
        if self._storage:
            self._storage.upsert(self._namespace, log_id, entry)
        return log_id

    def log_flow_execution(
        self,
        flow_name: str,
        flow_version: str,
        execution_id: str,
        trigger: str,
        agent_results: List[Dict[str, Any]],
        status: str,
        total_duration_ms: int,
    ) -> List[str]:
        """Log a full flow execution with all agent results.

        agent_results: list of dicts with keys:
            agent_id, status, duration_ms, error (optional)

        Returns list of log_ids for each agent execution.
        """
        log_ids = []
        for ar in agent_results:
            log_id = self.log_execution(
                flow_name=flow_name,
                execution_id=execution_id,
                agent_id=ar.get("agent_id", "unknown"),
                status=ar.get("status", "unknown"),
                duration_ms=ar.get("duration_ms", 0),
                error=ar.get("error", ""),
            )
            log_ids.append(log_id)

        # Also log a flow-level summary entry
        flow_log_id = str(uuid.uuid4())
        flow_entry = {
            "log_id": flow_log_id,
            "flow_name": flow_name,
            "flow_version": flow_version,
            "execution_id": execution_id,
            "trigger": trigger,
            "status": status,
            "total_duration_ms": total_duration_ms,
            "agent_count": len(agent_results),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "_type": "flow_summary",
        }
        self._executions[flow_log_id] = flow_entry
        if self._storage:
            self._storage.upsert(self._namespace, flow_log_id, flow_entry)
        return log_ids

    def get_executions(
        self,
        limit: int = 50,
        flow_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query recent execution log entries."""
        if flow_name:
            results = list(self._by_flow.get(flow_name, []))
        else:
            results = list(self._executions.values())

        if status:
            results = [e for e in results if e.get("status") == status]

        results.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return results[:limit]

    def get_flow_stats(
        self,
        flow_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get execution statistics for a flow (or all flows)."""
        if flow_name:
            entries = self._by_flow.get(flow_name, [])
            label = flow_name
        else:
            entries = [e for e in self._executions.values() if "_type" not in e]
            label = "*all*"

        total = len(entries)
        if total == 0:
            return {
                "flow_name": label,
                "total_runs": 0,
                "avg_duration_ms": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "by_status": {},
            }

        total_duration = sum(e.get("duration_ms", 0) for e in entries)
        status_counts: Dict[str, int] = defaultdict(int)
        for e in entries:
            status_counts[e.get("status", "unknown")] += 1

        success = status_counts.get("success", 0) + status_counts.get("completed", 0)
        failed = status_counts.get("failed", 0) + status_counts.get("error", 0)

        return {
            "flow_name": label,
            "total_runs": total,
            "avg_duration_ms": round(total_duration / total, 1),
            "success_rate": round(success / total * 100, 1) if total > 0 else 0.0,
            "failure_rate": round(failed / total * 100, 1) if total > 0 else 0.0,
            "by_status": dict(status_counts),
        }

    def get_agent_stats(
        self,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get per-agent performance statistics."""
        if agent_id:
            entries = self._by_agent.get(agent_id, [])
            label = agent_id
        else:
            entries = [e for e in self._executions.values() if "_type" not in e]
            label = "*all*"

        total = len(entries)
        if total == 0:
            return {
                "agent_id": label,
                "total_calls": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0,
                "error_count": 0,
            }

        total_duration = sum(e.get("duration_ms", 0) for e in entries)
        success_count = sum(
            1
            for e in entries
            if e.get("status") in ("success", "completed")
        )
        error_count = sum(
            1
            for e in entries
            if e.get("status") in ("failed", "error")
        )

        return {
            "agent_id": label,
            "total_calls": total,
            "success_rate": round(success_count / total * 100, 1) if total > 0 else 0.0,
            "avg_duration_ms": round(total_duration / total, 1) if total > 0 else 0.0,
            "error_count": error_count,
        }

    def get_trends(self) -> Dict[str, Any]:
        """Get overall execution trends."""
        all_entries = [e for e in self._executions.values() if "_type" not in e]
        total = len(all_entries)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_count = sum(
            1 for e in all_entries if e.get("timestamp", "").startswith(today)
        )

        success_count = sum(
            1
            for e in all_entries
            if e.get("status") in ("success", "completed")
        )

        # Most active flow
        flow_counts: Dict[str, int] = defaultdict(int)
        agent_counts: Dict[str, int] = defaultdict(int)
        for e in all_entries:
            flow_counts[e.get("flow_name", "unknown")] += 1
            agent_counts[e.get("agent_id", "unknown")] += 1

        most_active_flow = max(flow_counts, key=flow_counts.get) if flow_counts else ""
        most_active_agent = max(agent_counts, key=agent_counts.get) if agent_counts else ""

        return {
            "total_executions": total,
            "executions_today": today_count,
            "success_rate_overall": round(success_count / total * 100, 1) if total > 0 else 0.0,
            "most_active_flow": most_active_flow,
            "most_active_agent": most_active_agent,
            "unique_flows": len(flow_counts),
            "unique_agents": len(agent_counts),
        }

    def clear(self) -> None:
        """Clear all execution data."""
        self._executions.clear()
        self._by_flow.clear()
        self._by_agent.clear()
        if self._storage:
            self._storage.clear(self._namespace)
