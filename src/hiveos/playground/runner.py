"""HiveOS Playground — Flow Runner with WebSocket streaming.

Executes flows via the FlowEngine and streams real-time progress
events (agent status, logs, approval gates, completion) to WebSocket
or polling clients.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
import threading
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from ..engine import FlowEngine
from ..dsl import FlowDSL
from ..brain import EventStream, ApprovalGateEngine
from ..storage import StorageEngine

# ── In-memory/Persistent run store ──────────────────────────────────────────
_run_store: Dict[str, "FlowRun"] = {}
_storage: Optional["StorageEngine"] = None
_namespace = "playground:runs"


class FlowRun:
    """Represents a single flow execution with streaming state."""

    def __init__(
        self,
        run_id: str,
        flow_yaml: str,
        flow_name: str,
        flow_definition: dict,
        event_stream: Optional[EventStream] = None,
        approval_gates: Optional[ApprovalGateEngine] = None,
    ):
        self.run_id = run_id
        self.flow_yaml = flow_yaml
        self.flow_name = flow_name
        self.flow_definition = flow_definition
        self.event_stream = event_stream
        self.approval_gates = approval_gates

        self.status: str = "queued"  # queued → running → completed / failed / cancelled
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.agents: Dict[str, dict] = {}
        self.current_agent: Optional[str] = None
        self.logs: List[dict] = []
        self.error: Optional[str] = None
        self.output: Optional[dict] = None

        # WebSocket subscribers (set of asyncio.Queue)
        self._subscribers: List[asyncio.Queue] = []

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "flow_name": self.flow_name,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "agents": list(self.agents.values()),
            "current_agent": self.current_agent,
            "logs": self.logs[-50:],
            "error": self.error,
            "output": self.output,
        }

    def _emit(self, event_type: str, data: dict) -> None:
        """Broadcast an event to all subscribers."""
        payload = {
            "type": event_type,
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        self.logs.append(payload)
        dead: List[asyncio.Queue] = []
        for q in self._subscribers:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self._subscribers.remove(q)


class PlaygroundRunner:
    """Orchestrates flow execution with streaming output."""

    def __init__(
        self,
        domains_root: Optional[Path] = None,
        event_stream: Optional[EventStream] = None,
        approval_gates: Optional[ApprovalGateEngine] = None,
        storage: Optional["StorageEngine"] = None,
    ):
        self.domains_root = (
            domains_root
            or Path(__file__).resolve().parent.parent.parent.parent / "domains"
        )
        self.event_stream = event_stream or EventStream()
        self.approval_gates = approval_gates or ApprovalGateEngine()
        self._engine = FlowEngine()

        PlaygroundRunner._storage = storage  # None means no persistence
        self._restore_runs()

    def _restore_runs(self):
        """Rehydrate FlowRun objects from storage into _run_store."""
        if PlaygroundRunner._storage:
            for run_data in PlaygroundRunner._storage.load_all(_namespace):
                run_id = run_data.get("run_id")
                if run_id:
                    flow_yaml = run_data.get("flow_yaml", "")
                    flow_def = run_data.get("flow_definition", {})
                    flow_name = run_data.get("flow_name", "unknown")
                    run = FlowRun(
                        run_id=run_id,
                        flow_yaml=flow_yaml,
                        flow_name=flow_name,
                        flow_definition=flow_def,
                        event_stream=self.event_stream,
                        approval_gates=self.approval_gates,
                    )
                    # Restore state
                    run.status = run_data.get("status", "queued")
                    run.created_at = run_data.get("created_at", datetime.now(timezone.utc).isoformat())
                    run.started_at = run_data.get("started_at")
                    run.completed_at = run_data.get("completed_at")
                    run.agents = {a["agent_id"]: a for a in run_data.get("agents_list", [])}
                    run.current_agent = run_data.get("current_agent")
                    run.logs = run_data.get("logs", [])
                    run.error = run_data.get("error")
                    run.output = run_data.get("output")
                    _run_store[run_id] = run

    def _persist_run(self, run: FlowRun):
        if PlaygroundRunner._storage:
            # Convert agents dict to list for easier storage
            run_data = run.to_dict()
            run_data["agents_list"] = list(run.agents.values())
            PlaygroundRunner._storage.upsert(_namespace, run.run_id, run_data)

    def create_run(self, flow_yaml: str) -> FlowRun:
        """Parse YAML and create a run in 'queued' status."""
        import yaml

        data = yaml.safe_load(flow_yaml)
        if not isinstance(data, dict):
            raise ValueError("Flow YAML must parse to a dictionary")

        flow_name = data.get("name", f"flow-{uuid.uuid4().hex[:8]}")
        run_id = f"run-{uuid.uuid4().hex[:12]}"

        run = FlowRun(
            run_id=run_id,
            flow_yaml=flow_yaml,
            flow_name=flow_name,
            flow_definition=data,
            event_stream=self.event_stream,
            approval_gates=self.approval_gates,
        )
        _run_store[run_id] = run
        self._persist_run(run)
        return run

    def get_run(self, run_id: str) -> Optional[FlowRun]:
        return _run_store.get(run_id)

    def list_runs(
        self, limit: int = 20, status: Optional[str] = None
    ) -> List[dict]:
        results = [r.to_dict() for r in _run_store.values()]
        if status:
            results = [r for r in results if r["status"] == status]
        results.sort(key=lambda r: r["created_at"], reverse=True)
        return results[:limit]

    async def execute_run_async(self, run_id: str) -> FlowRun:
        """Execute a flow asynchronously, emitting streaming events."""
        run = _run_store.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        run.status = "running"
        run.started_at = datetime.now(timezone.utc).isoformat()
        run._emit("run.started", {"flow_name": run.flow_name})
        self._persist_run(run)

        if self.event_stream:
            self.event_stream.emit(
                "flow.started", "playground", {"run_id": run_id, "flow_name": run.flow_name}
            )

        try:
            flow_def = run.flow_definition
            agents_def = flow_def.get("agents", [])

            if not agents_def:
                run.status = "completed"
                run.completed_at = datetime.now(timezone.utc).isoformat()
                run._emit("run.completed", {"status": "no_agents"})
                self._persist_run(run)
                return run

            # Execute agents in order with dependency tracking
            executed_ids: set = set()
            for agent_def in agents_def:
                agent_id = agent_def.get("id", "unknown")
                agent_name = agent_def.get("name", agent_id)
                depends_on = agent_def.get("depends_on", [])

                run.current_agent = agent_id

                # Check dependencies
                dep_statuses = {}
                for dep_id in depends_on:
                    dep = run.agents.get(dep_id, {})
                    dep_statuses[dep_id] = dep.get("status", "pending")

                failed_deps = [d for d, s in dep_statuses.items() if s in ("failed", "error")]
                if failed_deps:
                    agent_result = {
                        "agent_id": agent_id,
                        "name": agent_name,
                        "status": "skipped",
                        "reason": f"Dependency failed: {', '.join(failed_deps)}",
                        "started_at": datetime.now(timezone.utc).isoformat(),
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    }
                    run.agents[agent_id] = agent_result
                    run._emit("agent.skipped", agent_result)
                    continue

                # Start agent
                agent_entry = {
                    "agent_id": agent_id,
                    "name": agent_name,
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "skills": agent_def.get("skills", []),
                }
                run.agents[agent_id] = agent_entry
                run._emit("agent.started", agent_entry)

                # Simulate agent execution (in production, this spawns Hermes subagents)
                agent_start = time.time()
                await asyncio.sleep(0.5)  # simulate work

                # Check for approval gates
                skills = agent_def.get("skills", [])
                has_gate = any("approve" in (s or "").lower() or "gate" in (s or "").lower() for s in skills)

                if has_gate:
                    gate = self.approval_gates.create_gate(
                        title=f"Approve {agent_name}",
                        description=f"Agent '{agent_name}' requires approval to proceed",
                        requestor=run_id,
                        context={
                            "run_id": run_id,
                            "agent_id": agent_id,
                            "agent_name": agent_name,
                            "flow_name": run.flow_name,
                        },
                        timeout_seconds=3600,
                    )
                    run._emit("agent.waiting_approval", {
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "gate_id": gate["gate_id"],
                        "gate": gate,
                    })
                    if self.event_stream:
                        self.event_stream.emit(
                            "agent.awaiting_approval", run_id,
                            {"agent_id": agent_id, "gate_id": gate["gate_id"]},
                        )

                elapsed = time.time() - agent_start
                agent_entry["status"] = "completed"
                agent_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
                agent_entry["elapsed_seconds"] = round(elapsed, 2)
                run._emit("agent.completed", {
                    "agent_id": agent_id,
                    "name": agent_name,
                    "elapsed_seconds": round(elapsed, 2),
                })

                if self.event_stream:
                    self.event_stream.emit(
                        "agent.completed", run_id,
                        {"agent_id": agent_id, "elapsed": round(elapsed, 2)},
                    )

                executed_ids.add(agent_id)

            # Flow completed
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc).isoformat()
            run.current_agent = None
            run.output = {
                "flow_name": run.flow_name,
                "agent_count": len(run.agents),
                "completed_agents": [a["agent_id"] for a in run.agents.values() if a.get("status") == "completed"],
                "skipped_agents": [a["agent_id"] for a in run.agents.values() if a.get("status") == "skipped"],
                "status": "completed",
                "timestamp": run.completed_at,
            }
            run._emit("run.completed", {"status": "success", "output": run.output})
            self._persist_run(run)

            if self.event_stream:
                self.event_stream.emit(
                    "flow.completed", "playground",
                    {"run_id": run_id, "flow_name": run.flow_name, "status": "completed"},
                )

        except Exception as e:
            run.status = "failed"
            run.error = str(e)
            run.completed_at = datetime.now(timezone.utc).isoformat()
            run._emit("run.failed", {"error": str(e)})
            self._persist_run(run)
            if self.event_stream:
                self.event_stream.emit(
                    "flow.failed", "playground",
                    {"run_id": run_id, "error": str(e)},
                )

        return run

    def cancel_run(self, run_id: str) -> bool:
        """Cancel a queued or running flow."""
        run = _run_store.get(run_id)
        if not run or run.status not in ("queued", "running"):
            return False
        run.status = "cancelled"
        run.completed_at = datetime.now(timezone.utc).isoformat()
        run._emit("run.cancelled", {})
        self._persist_run(run)
        return True

    def get_ws_queue(self, run_id: str) -> Optional[asyncio.Queue]:
        """Get or create a subscriber queue for a run's WebSocket events."""
        run = _run_store.get(run_id)
        if not run:
            return None
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        run._subscribers.append(q)
        return q


# ── Cleanup old runs periodically ──
def _cleanup_old_runs(max_age_hours: int = 24):
    now = time.time()
    cutoff = now - max_age_hours * 3600
    to_delete = []
    for run_id, run in _run_store.items():
        if run.completed_at:
            try:
                t = datetime.fromisoformat(run.completed_at).timestamp()
                if t < cutoff:
                    to_delete.append(run_id)
            except (ValueError, TypeError):
                pass
    for rid in to_delete:
        del _run_store[rid]
