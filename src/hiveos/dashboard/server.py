"""
Dashboard Server — FastAPI-based web UI for HiveOS monitoring.

Aggregates data from all subsystems (Agent Registry, Task Router,
Communication Bus, Resilience, RBAC, Audit Trail) and exposes
REST endpoints + an embedded single-page HTML dashboard.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from rich.console import Console

from ..mothership.agent_registry import AgentRegistry, AgentStatus
from ..mothership.task_router import TaskRouter, TaskAssignment
from ..mothership.communication_bus import CommunicationBus
from ..mothership.resilience import (
    ResilienceEngine,
    HealthStatus,
    HealthCheckResult,
)
from ..rbac import RBACManager, Resource, Action
from ..audit import AuditTrail, AuditAction, AuditResource
from ..license import FeatureFlag
from ..playground import PlaygroundEngine
from ..brain import EventStream, DecisionTracer, ApprovalGateEngine
from ..learning import ExecutionLogger

console = Console()

HERE = Path(__file__).parent
TEMPLATES = HERE / "templates"


class DashboardServer:
    """Manages the FastAPI dashboard lifecycle."""

    def __init__(
        self,
        agent_registry: Optional[AgentRegistry] = None,
        task_router: Optional[TaskRouter] = None,
        comm_bus: Optional[CommunicationBus] = None,
        resilience: Optional[ResilienceEngine] = None,
        rbac: Optional[RBACManager] = None,
        audit: Optional[AuditTrail] = None,
        host: str = "127.0.0.1",
        port: int = 8080,
        data_dir: Optional[Path] = None,
    ):
        self.host = host
        self.port = port
        self.data_dir = data_dir or Path.cwd()
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

        # Subsystem references (lazy inits)
        self._agent_registry = agent_registry
        self._task_router = task_router
        self._comm_bus = comm_bus
        self._resilience = resilience
        self._rbac = rbac
        self._audit = audit

        self.app = DashboardApp(
            agent_registry=agent_registry,
            task_router=task_router,
            comm_bus=comm_bus,
            resilience=resilience,
            rbac=rbac,
            audit=audit,
            data_dir=self.data_dir,
        ).app

    # ── Lifecycle ────────────────────────────────────────────────────

    def start(self) -> str:
        """Start the dashboard server in a background thread."""
        if self._server:
            return f"Dashboard already running at http://{self.host}:{self.port}"

        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            loop="asyncio",
        )
        self._server = uvicorn.Server(config)

        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._server.serve())

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        time.sleep(0.5)  # brief wait for socket bind
        return f"Dashboard started at http://{self.host}:{self.port}"

    def stop(self) -> str:
        """Stop the dashboard server."""
        if self._server:
            self._server.should_exit = True
            self._server = None
            self._thread = None
            return "Dashboard stopped."
        return "Dashboard is not running."

    def status(self) -> Dict[str, Any]:
        """Return current server status."""
        return {
            "running": self._server is not None,
            "host": self.host,
            "port": self.port,
            "url": f"http://{self.host}:{self.port}",
        }


class DashboardApp:
    """FastAPI application with HiveOS dashboard endpoints."""

    def __init__(
        self,
        agent_registry: Optional[AgentRegistry] = None,
        task_router: Optional[TaskRouter] = None,
        comm_bus: Optional[CommunicationBus] = None,
        resilience: Optional[ResilienceEngine] = None,
        rbac: Optional[RBACManager] = None,
        audit: Optional[AuditTrail] = None,
        data_dir: Optional[Path] = None,
        ):
        self.agent_registry = agent_registry
        self.task_router = task_router
        self.comm_bus = comm_bus
        self.resilience = resilience
        self.rbac = rbac
        self.audit = audit
        self.data_dir = data_dir or Path.cwd()
        self.playground = PlaygroundEngine()
        self.event_stream = EventStream()
        self.decision_tracer = DecisionTracer()
        self.approval_gates = ApprovalGateEngine()
        self.execution_logger = ExecutionLogger()

        self.app = FastAPI(title="HiveOS Dashboard", version="0.5.0")
        self._register_routes()

    # ── Routes ───────────────────────────────────────────────────────

    def _register_routes(self):
        app = self.app

        @app.get("/", response_class=HTMLResponse)
        async def index():
            """Serve the single-page dashboard HTML."""
            html_path = TEMPLATES / "index.html"
            if html_path.exists():
                return html_path.read_text(encoding="utf-8")
            return HTMLResponse("<h1>HiveOS Dashboard</h1><p>Template not found.</p>")

        @app.get("/api/overview")
        async def overview():
            """Aggregated system overview."""
            data: Dict[str, Any] = {
                "timestamp": datetime.utcnow().isoformat(),
                "agents": {"total": 0, "online": 0, "offline": 0, "degraded": 0, "busy": 0},
                "tasks": {"total": 0, "pending": 0, "running": 0, "completed": 0, "failed": 0},
                "health": {"healthy": 0, "degraded": 0, "unhealthy": 0, "unknown": 0},
                "bus": {"messages_total": 0, "subscribers": 0},
                "rbac": {"users": 0, "roles": 0},
                "audit": {"entries_today": 0},
            }

            if self.agent_registry:
                agents = self.agent_registry.list_agents() if hasattr(self.agent_registry, 'list_agents') else []
                if not agents:
                    agents = list(getattr(self.agent_registry, '_agents', {}).values())
                data["agents"]["total"] = len(agents)
                for a in agents:
                    status = getattr(a, 'status', 'unknown')
                    if hasattr(status, 'value'):
                        status = status.value
                    s = str(status).lower()
                    if s in ("online", "healthy"):
                        data["agents"]["online"] += 1
                    elif s in ("offline", "unhealthy"):
                        data["agents"]["offline"] += 1
                    elif s == "degraded":
                        data["agents"]["degraded"] += 1
                    elif s == "busy":
                        data["agents"]["busy"] += 1

            if self.task_router:
                assignments = list(getattr(self.task_router, '_assignments', {}).values())
                data["tasks"]["total"] = len(assignments)
                for t in assignments:
                    status = getattr(t, 'status', None)
                    if hasattr(status, 'value'):
                        status = status.value
                    s = str(status).lower()
                    if s in ("pending", "queued"):
                        data["tasks"]["pending"] += 1
                    elif s in ("running", "in_progress", "assigned"):
                        data["tasks"]["running"] += 1
                    elif s in ("completed", "success"):
                        data["tasks"]["completed"] += 1
                    elif s in ("failed", "error"):
                        data["tasks"]["failed"] += 1

            if self.resilience:
                states = getattr(self.resilience, '_states', {})
                for node_name, state in states.items():
                    if isinstance(state, dict):
                        hs = state.get('status', state.get('health', 'unknown'))
                    else:
                        hs = getattr(state, 'status', 'unknown')
                    if hasattr(hs, 'value'):
                        hs = hs.value
                    hs = str(hs).lower()
                    if hs == "healthy":
                        data["health"]["healthy"] += 1
                    elif hs == "degraded":
                        data["health"]["degraded"] += 1
                    elif hs == "unhealthy":
                        data["health"]["unhealthy"] += 1
                    else:
                        data["health"]["unknown"] += 1

            if self.comm_bus:
                bus = self.comm_bus
                data["bus"]["messages_total"] = getattr(bus, '_message_count', getattr(bus, 'total_messages', 0))
                data["bus"]["subscribers"] = len(getattr(bus, '_subscribers', getattr(bus, 'subscribers', {})))

            if self.rbac:
                data["rbac"]["users"] = len(getattr(self.rbac, '_users', getattr(self.rbac, 'users', {})))
                data["rbac"]["roles"] = len(getattr(self.rbac, '_roles', getattr(self.rbac, 'roles', {})))

            if self.audit:
                today = datetime.utcnow().strftime("%Y-%m-%d")
                entries = getattr(self.audit, '_entries', getattr(self.audit, 'entries', []))
                if entries and hasattr(entries[0], 'timestamp'):
                    data["audit"]["entries_today"] = sum(
                        1 for e in entries
                        if e.timestamp.startswith(today)
                    )
                else:
                    data["audit"]["entries_today"] = len(entries)

            return data

        @app.get("/api/agents")
        async def list_agents():
            """List all registered agents with details."""
            agents_data = []
            if self.agent_registry:
                agents = getattr(self.agent_registry, '_agents', {}).values()
                for a in agents:
                    status = getattr(a, 'status', 'unknown')
                    if hasattr(status, 'value'):
                        status = status.value
                    agents_data.append({
                        "name": getattr(a, 'node_name', getattr(a, 'name', 'unknown')),
                        "status": str(status),
                        "capabilities": list(getattr(a, 'capabilities', {}).keys()) if hasattr(a, 'capabilities') else [],
                        "load": getattr(a, 'current_load', 0),
                        "max_concurrent": getattr(a, 'max_concurrent', 5),
                        "tasks_completed": getattr(a, 'total_tasks_completed', 0),
                        "errors": getattr(a, 'total_errors', 0),
                        "uptime": getattr(a, 'uptime_seconds', 0),
                        "last_seen": str(getattr(a, 'last_seen', '')),
                    })
            return {"agents": agents_data}

        @app.get("/api/tasks")
        async def list_tasks():
            """List all task assignments."""
            tasks_data = []
            if self.task_router:
                assignments = list(getattr(self.task_router, '_assignments', {}).values())
                for t in assignments:
                    status = getattr(t, 'status', None)
                    if hasattr(status, 'value'):
                        status = status.value
                    tasks_data.append({
                        "id": getattr(t, 'task_id', getattr(t, 'id', '')),
                        "agent": getattr(t, 'capability', getattr(t, 'agent', '')),
                        "node": getattr(t, 'node_name', getattr(t, 'node', '')),
                        "status": str(status) if status else 'unknown',
                        "created": str(getattr(t, 'created_at', '')),
                        "completed": str(getattr(t, 'completed_at', '')),
                        "result": str(getattr(t, 'result', '')),
                    })
            return {"tasks": tasks_data}

        @app.get("/api/health")
        async def system_health():
            """Detailed health information per node."""
            health_data = []
            if self.resilience:
                states = getattr(self.resilience, '_states', {})
                for node_name, state in states.items():
                    if isinstance(state, dict):
                        hs = state.get('status', state.get('health', 'unknown'))
                        failures = state.get('failures', 0)
                        successes = state.get('successes', 0)
                        last_change = state.get('last_change', '')
                    else:
                        hs = getattr(state, 'status', 'unknown')
                        failures = getattr(state, 'failures', 0)
                        successes = getattr(state, 'successes', 0)
                        last_change = getattr(state, 'last_change', '')
                    if hasattr(hs, 'value'):
                        hs = hs.value
                    health_data.append({
                        "node": node_name,
                        "status": str(hs),
                        "failures": failures,
                        "successes": successes,
                        "last_change": str(last_change),
                    })

                # Also get failure history
                failures_history = getattr(self.resilience, '_failures', {})
                recent_failures = []
                for node_name, flist in failures_history.items():
                    for f in (flist or [])[-20:]:
                        if isinstance(f, dict):
                            recent_failures.append({
                                "node": node_name,
                                "type": f.get('type', 'unknown'),
                                "timestamp": str(f.get('timestamp', '')),
                                "message": str(f.get('message', '')),
                            })
                        else:
                            recent_failures.append({
                                "node": node_name,
                                "type": getattr(f, 'failure_type', str(type(f).__name__)),
                                "timestamp": str(getattr(f, 'timestamp', '')),
                                "message": str(getattr(f, 'message', '')),
                            })

            return {"nodes": health_data, "recent_failures": recent_failures if health_data else []}

        @app.get("/api/bus")
        async def bus_status():
            """Communication bus stats."""
            if not self.comm_bus:
                return {"messages": [], "stats": {"total": 0, "by_type": {}}}
            bus = self.comm_bus
            messages = list(getattr(bus, '_messages', getattr(bus, 'messages', [])))[-50:]
            msg_list = []
            for m in messages:
                mtype = getattr(m, 'msg_type', getattr(m, 'type', 'unknown'))
                if hasattr(mtype, 'value'):
                    mtype = mtype.value
                msg_list.append({
                    "id": getattr(m, 'msg_id', getattr(m, 'id', '')),
                    "type": str(mtype),
                    "sender": getattr(m, 'sender', getattr(m, 'source', '')),
                    "target": getattr(m, 'target', getattr(m, 'destination', '')),
                    "timestamp": str(getattr(m, 'timestamp', '')),
                })
            return {
                "messages": msg_list,
                "stats": {
                    "total": getattr(bus, '_message_count', getattr(bus, 'total_messages', 0)),
                    "subscribers": len(getattr(bus, '_subscribers', getattr(bus, 'subscribers', {}))),
                },
            }

        @app.get("/api/audit")
        async def audit_log(limit: int = 50):
            """Recent audit trail entries."""
            entries_data = []
            if self.audit:
                entries = getattr(self.audit, '_entries', getattr(self.audit, 'entries', []))[-limit:]
                for e in entries:
                    action = getattr(e, 'action', '')
                    resource = getattr(e, 'resource', '')
                    result = getattr(e, 'result', '')
                    if hasattr(action, 'value'):
                        action = action.value
                    if hasattr(resource, 'value'):
                        resource = resource.value
                    if hasattr(result, 'value'):
                        result = result.value
                    entries_data.append({
                        "id": getattr(e, 'entry_id', getattr(e, 'id', '')),
                        "action": str(action),
                        "resource": str(resource),
                        "result": str(result),
                        "user": getattr(e, 'user', getattr(e, 'actor', '')),
                        "detail": getattr(e, 'detail', getattr(e, 'details', '')),
                        "timestamp": str(getattr(e, 'timestamp', '')),
                    })
            return {"entries": entries_data}

        @app.get("/api/rbac")
        async def rbac_status():
            """RBAC users and roles."""
            if not self.rbac:
                return {"users": [], "roles": []}
            users = []
            for u in getattr(self.rbac, '_users', getattr(self.rbac, 'users', {})).values():
                users.append({
                    "username": getattr(u, 'username', ''),
                    "role": getattr(u, 'role', ''),
                    "enabled": getattr(u, 'enabled', True),
                    "workspace": getattr(u, 'workspace', 'default'),
                })
            roles = []
            for r in getattr(self.rbac, '_roles', getattr(self.rbac, 'roles', {})).values():
                perms = getattr(r, 'permissions', [])
                roles.append({
                    "name": getattr(r, 'name', ''),
                    "permissions": [str(p) for p in perms] if perms else [],
                })
            return {"users": users, "roles": roles}

        @app.get("/api/nodes")
        async def list_nodes():
            """List satellite nodes from NodeRegistry."""
            nodes_data = []
            # Try to access NodeRegistry through AgentRegistry's _node_registry
            node_reg = None
            if self.agent_registry:
                node_reg = getattr(self.agent_registry, '_node_registry', None)
            if node_reg:
                nodes = getattr(node_reg, '_nodes', {}).values()
                for n in nodes:
                    nodes_data.append({
                        "name": getattr(n, 'name', ''),
                        "endpoint": getattr(n, 'endpoint', ''),
                        "last_seen": str(getattr(n, 'last_seen', '')),
                        "version": getattr(n, 'version', ''),
                    })
            return {"nodes": nodes_data}

        @app.get("/api/domains")
        async def list_domains():
            """List installed domain plugins."""
            domains = []
            domains_path = self.data_dir / "domains"
            if domains_path.exists():
                for d in sorted(domains_path.iterdir()):
                    if d.is_dir() and (d / "domain.yaml").exists():
                        try:
                            import yaml
                            manifest = yaml.safe_load((d / "domain.yaml").read_text(encoding="utf-8"))
                            domains.append({
                                "name": manifest.get("name", d.name),
                                "label": manifest.get("label", d.name),
                                "version": manifest.get("version", "0.0.0"),
                                "agents": len(manifest.get("agents", [])),
                                "flows": len(manifest.get("flows", [])),
                            })
                        except Exception:
                            domains.append({"name": d.name, "label": d.name, "error": "parse failed"})
            return {"domains": domains}

        @app.get("/api/workspaces")
        async def list_workspaces():
            """List workspaces from the WorkspaceManager."""
            from ..workspace import WorkspaceManager
            mgr = WorkspaceManager()
            workspaces = mgr.list_workspaces()
            return {
                "workspaces": [
                    {
                        "id": ws.workspace_id,
                        "name": ws.name,
                        "description": ws.description,
                        "owner": ws.owner,
                        "members": ws.member_count,
                        "active": ws.active,
                        "created_at": ws.created_at[:10] if ws.created_at else "",
                    }
                    for ws in workspaces
                ]
            }

        @app.get("/api/license")
        async def license_status():
            """Current license information."""
            from ..license import LicenseManager
            mgr = LicenseManager()
            lic = mgr.current
            return {
                "tier": lic.tier.value,
                "label": lic.tier_label,
                "active": lic.is_active,
                "expires_at": lic.expires_at or "",
                "days_remaining": lic.days_remaining,
                "organization": lic.organization,
                "seats": lic.seats,
                "limits": {
                    "max_workspaces": lic.get_limit("max_workspaces"),
                    "max_agents": lic.get_limit("max_agents"),
                    "max_flows": lic.get_limit("max_flows"),
                    "max_nodes": lic.get_limit("max_nodes"),
                    "max_concurrent_flows": lic.get_limit("max_concurrent_flows"),
                    "audit_retention_days": lic.get_limit("audit_retention_days"),
                },
                "enabled_features": sorted(
                    f.value for f in FeatureFlag if lic.has_feature(f)
                ),
            }

        # ── Playground API ──────────────────────────────────────────

        @app.post("/api/playground/validate")
        async def playground_validate(request: Request):
            """Validate a flow YAML."""
            body = await request.json()
            yaml_content = body.get("yaml", "")
            result = self.playground.validate_flow(yaml_content)
            return result

        @app.post("/api/playground/auto-agents")
        async def playground_auto_agents(request: Request):
            """Auto-generate agent team from task description."""
            body = await request.json()
            task = body.get("task", "")
            domain = body.get("domain", "accounting")
            result = self.playground.auto_agents(task, domain)
            return result

        @app.get("/api/playground/templates")
        async def playground_templates(domain: str = "accounting"):
            """List domain flow templates."""
            result = self.playground.list_templates(domain)
            return result

        # ── Brain API — Event Stream ────────────────────────────────

        @app.get("/api/brain/events")
        async def brain_events(limit: int = 50, event_type: str = None):
            """Get recent events from the event stream."""
            events = self.event_stream.get_events(limit=limit, event_type=event_type)
            return {"events": events}

        @app.get("/api/brain/events/{event_id}")
        async def brain_event(event_id: str):
            """Get a specific event by ID."""
            event = self.event_stream.get_event(event_id)
            if event is None:
                return {"error": "Event not found"}
            return {"event": event}

        @app.get("/api/brain/events/stats")
        async def brain_event_stats():
            """Event stream statistics."""
            return self.event_stream.stats()

        # ── Brain API — Decision Tracer ─────────────────────────────

        @app.post("/api/brain/traces")
        async def brain_start_trace(request: Request):
            """Start a new decision trace."""
            body = await request.json()
            trace_id = self.decision_tracer.start_trace(
                trace_id=body.get("trace_id"),
                context=body.get("context"),
            )
            return {"trace_id": trace_id}

        @app.post("/api/brain/traces/{trace_id}/steps")
        async def brain_add_step(trace_id: str, request: Request):
            """Add a decision step to a trace."""
            body = await request.json()
            step = self.decision_tracer.add_step(trace_id, body)
            if step is None:
                return {"error": "Trace not found"}
            return {"step": step}

        @app.get("/api/brain/traces/{trace_id}")
        async def brain_get_trace(trace_id: str):
            """Get a full trace with all steps."""
            trace = self.decision_tracer.get_trace(trace_id)
            if trace is None:
                return {"error": "Trace not found"}
            return {"trace": trace}

        @app.get("/api/brain/traces")
        async def brain_list_traces(limit: int = 20, status: str = None):
            """List recent decision traces."""
            traces = self.decision_tracer.list_traces(limit=limit, status=status)
            return {"traces": traces}

        @app.post("/api/brain/traces/{trace_id}/complete")
        async def brain_complete_trace(trace_id: str, request: Request):
            """Mark a trace as completed."""
            body = await request.json()
            ok = self.decision_tracer.complete_trace(
                trace_id,
                outcome=body.get("outcome", ""),
                summary=body.get("summary", ""),
            )
            if not ok:
                return {"error": "Trace not found"}
            return {"status": "completed"}

        @app.post("/api/brain/traces/{trace_id}/fail")
        async def brain_fail_trace(trace_id: str, request: Request):
            """Mark a trace as failed."""
            body = await request.json()
            ok = self.decision_tracer.fail_trace(
                trace_id,
                error=body.get("error", ""),
            )
            if not ok:
                return {"error": "Trace not found"}
            return {"status": "failed"}

        @app.get("/api/brain/traces/stats")
        async def brain_trace_stats():
            """Decision tracer statistics."""
            return self.decision_tracer.stats()

        # ── Brain API — Approval Gates ──────────────────────────────

        @app.get("/api/brain/gates")
        async def brain_list_gates(status: str = None, limit: int = 50):
            """List approval gates."""
            gates = self.approval_gates.list_gates(status=status, limit=limit)
            return {"gates": gates}

        @app.get("/api/brain/gates/pending")
        async def brain_pending_gates():
            """Get all pending approval gates."""
            gates = self.approval_gates.pending_for_user()
            return {"gates": gates}

        @app.post("/api/brain/gates")
        async def brain_create_gate(request: Request):
            """Create a new approval gate."""
            body = await request.json()
            gate = self.approval_gates.create_gate(
                gate_id=body.get("gate_id"),
                title=body.get("title", ""),
                description=body.get("description", ""),
                requestor=body.get("requestor", ""),
                context=body.get("context"),
                timeout_seconds=body.get("timeout_seconds", 86400),
            )
            return {"gate": gate}

        @app.post("/api/brain/gates/{gate_id}/approve")
        async def brain_approve_gate(gate_id: str, request: Request):
            """Approve a gate."""
            body = await request.json()
            gate = self.approval_gates.approve(
                gate_id,
                approver=body.get("approver", ""),
                notes=body.get("notes", ""),
            )
            if gate is None:
                return {"error": "Gate not found"}
            return {"gate": gate}

        @app.post("/api/brain/gates/{gate_id}/reject")
        async def brain_reject_gate(gate_id: str, request: Request):
            """Reject a gate."""
            body = await request.json()
            gate = self.approval_gates.reject(
                gate_id,
                approver=body.get("approver", ""),
                reason=body.get("reason", ""),
            )
            if gate is None:
                return {"error": "Gate not found"}
            return {"gate": gate}

        @app.get("/api/brain/gates/stats")
        async def brain_gate_stats():
            """Approval gate statistics."""
            return self.approval_gates.stats()

        # ── Learning API ────────────────────────────────────────────

        @app.post("/api/learning/log")
        async def learning_log(request: Request):
            """Log a single agent execution."""
            body = await request.json()
            log_id = self.execution_logger.log_execution(
                flow_name=body.get("flow_name", ""),
                execution_id=body.get("execution_id", ""),
                agent_id=body.get("agent_id", ""),
                status=body.get("status", "unknown"),
                duration_ms=body.get("duration_ms", 0),
                input_summary=body.get("input_summary", ""),
                output_summary=body.get("output_summary", ""),
                error=body.get("error", ""),
            )
            return {"log_id": log_id}

        @app.post("/api/learning/log-flow")
        async def learning_log_flow(request: Request):
            """Log a full flow execution."""
            body = await request.json()
            log_ids = self.execution_logger.log_flow_execution(
                flow_name=body.get("flow_name", ""),
                flow_version=body.get("flow_version", ""),
                execution_id=body.get("execution_id", ""),
                trigger=body.get("trigger", ""),
                agent_results=body.get("agent_results", []),
                status=body.get("status", "unknown"),
                total_duration_ms=body.get("total_duration_ms", 0),
            )
            return {"log_ids": log_ids}

        @app.get("/api/learning/executions")
        async def learning_executions(
            limit: int = 50,
            flow_name: str = None,
            status: str = None,
        ):
            """Query execution logs."""
            entries = self.execution_logger.get_executions(
                limit=limit,
                flow_name=flow_name,
                status=status,
            )
            return {"executions": entries}

        @app.get("/api/learning/stats/flow")
        async def learning_flow_stats(flow_name: str = None):
            """Get flow execution statistics."""
            return self.execution_logger.get_flow_stats(flow_name=flow_name)

        @app.get("/api/learning/stats/agent")
        async def learning_agent_stats(agent_id: str = None):
            """Get per-agent statistics."""
            return self.execution_logger.get_agent_stats(agent_id=agent_id)

        @app.get("/api/learning/trends")
        async def learning_trends():
            """Get overall execution trends."""
            return self.execution_logger.get_trends()
