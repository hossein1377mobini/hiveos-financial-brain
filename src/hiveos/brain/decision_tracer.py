"""HiveOS Brain — Decision Tracer.

Traces every decision path start→finish with full step-by-step visibility.
Each flow execution, agent selection, and routing decision is logged
as a trace that can be replayed and inspected.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class DecisionTracer:
    """Tracks decision paths with step-by-step resolution."""

    def __init__(self):
        self._traces: Dict[str, dict] = {}

    def start_trace(
        self,
        trace_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start a new decision trace. Returns the trace ID."""
        tid = trace_id or str(uuid.uuid4())
        self._traces[tid] = {
            "trace_id": tid,
            "context": context or {},
            "status": "in_progress",
            "steps": [],
            "outcome": "",
            "summary": "",
            "error": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": "",
        }
        return tid

    def add_step(
        self,
        trace_id: str,
        step: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Add a decision step to an existing trace.

        Step dict: {"action": "...", "reasoning": "...", "result": "..."}
        Auto-assigns step_number and timestamp.
        Returns the enriched step or None if trace not found.
        """
        trace = self._traces.get(trace_id)
        if trace is None:
            return None

        enriched = {
            "step_number": len(trace["steps"]) + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": step.get("action", ""),
            "reasoning": step.get("reasoning", ""),
            "result": step.get("result", ""),
        }
        trace["steps"].append(enriched)
        return enriched

    def complete_trace(
        self,
        trace_id: str,
        outcome: str,
        summary: str = "",
    ) -> bool:
        """Mark a trace as completed. Returns True if successful."""
        trace = self._traces.get(trace_id)
        if trace is None:
            return False
        trace["status"] = "completed"
        trace["outcome"] = outcome
        trace["summary"] = summary
        trace["completed_at"] = datetime.now(timezone.utc).isoformat()
        return True

    def fail_trace(self, trace_id: str, error: str) -> bool:
        """Mark a trace as failed. Returns True if successful."""
        trace = self._traces.get(trace_id)
        if trace is None:
            return False
        trace["status"] = "failed"
        trace["error"] = error
        trace["completed_at"] = datetime.now(timezone.utc).isoformat()
        return True

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get full trace with all steps."""
        return self._traces.get(trace_id)

    def list_traces(
        self,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List recent traces, optionally filtered by status."""
        traces = list(self._traces.values())
        if status:
            traces = [t for t in traces if t["status"] == status]
        # Sort by creation time, newest first
        traces.sort(key=lambda t: t["created_at"], reverse=True)
        return traces[:limit]

    def stats(self) -> Dict[str, Any]:
        """Count traces by status."""
        counts: Dict[str, int] = defaultdict(int)
        for t in self._traces.values():
            counts[t["status"]] += 1
        return {
            "total_traces": len(self._traces),
            "by_status": dict(counts),
        }
