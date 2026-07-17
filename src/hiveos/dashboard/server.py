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
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
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
from ..playground import PlaygroundEngine, PlaygroundRunner
from ..brain import EventStream, DecisionTracer, ApprovalGateEngine
from ..learning import ExecutionLogger
from ..learning.analytics import AnalyticsEngine
from ..storage import StorageEngine
from ..domain.registry import DomainRegistry

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
        storage: Optional["StorageEngine"] = None,
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

        self._dashboard_app = DashboardApp(
            agent_registry=agent_registry,
            task_router=task_router,
            comm_bus=comm_bus,
            resilience=resilience,
            rbac=rbac,
            audit=audit,
            data_dir=self.data_dir,
            storage=storage, # Pass the injected storage
        )

    @property
    def app(self):
        return self._dashboard_app.app

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
            if hasattr(self, '_dashboard_app') and self._dashboard_app:
                self._dashboard_app.storage.close()
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
        storage: Optional["StorageEngine"] = None,
    ):
        self.agent_registry = agent_registry
        self.task_router = task_router
        self.comm_bus = comm_bus
        self.resilience = resilience
        self.rbac = rbac
        self.audit = audit
        self.data_dir = data_dir or Path.cwd()

        # ── Shared persistence layer ───────────────────────────────────
        db_path = self.data_dir / "hiveos.db" if self.data_dir else None
        self.storage = storage or StorageEngine(db_path)

        # ── Brain modules ──────────────────────────────────────────────
        self.event_stream = EventStream(storage=self.storage)
        self.decision_tracer = DecisionTracer(storage=self.storage)
        self.approval_gates = ApprovalGateEngine(storage=self.storage)

        # ── Learning modules ───────────────────────────────────────────
        self.execution_logger = ExecutionLogger(storage=self.storage)
        self.analytics = AnalyticsEngine(self.execution_logger)

        # ── Playground ─────────────────────────────────────────────────
        self.playground = PlaygroundEngine()
        self.playground_runner = PlaygroundRunner(
            event_stream=self.event_stream,
            approval_gates=self.approval_gates,
            storage=self.storage,
        )

        # ── Domain Registry ────────────────────────────────────────────
        domains_root = self.data_dir / "domains" if self.data_dir else Path.cwd() / "domains"
        if not domains_root.exists():
            # Fall back to project-level domains (installed package)
            from pathlib import Path as _P
            project_domains = _P(__file__).parent.parent.parent.parent / "domains"
            if project_domains.exists():
                domains_root = project_domains
        self.domain_registry = DomainRegistry(storage=self.storage, domains_root=domains_root)
        self.domain_registry.scan()  # auto-scan on startup

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

        # ── PWA (Progressive Web App) Static Files ────────────────

        @app.get("/manifest.json")
        async def pwa_manifest():
            """Serve Web App Manifest."""
            path = TEMPLATES / "manifest.json"
            if path.exists():
                return FileResponse(path, media_type="application/manifest+json")
            return JSONResponse({"error": "not found"}, status_code=404)

        @app.get("/sw.js")
        async def pwa_service_worker():
            """Serve Service Worker."""
            path = TEMPLATES / "sw.js"
            if path.exists():
                return FileResponse(path, media_type="application/javascript")
            return JSONResponse({"error": "not found"}, status_code=404)

        @app.get("/icons/{filename}")
        async def pwa_icons(filename: str):
            """Serve PWA icon files."""
            path = TEMPLATES / "icons" / filename
            if path.exists():
                ext = path.suffix.lower()
                media_types = {".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon"}
                return FileResponse(path, media_type=media_types.get(ext, "application/octet-stream"))
            return JSONResponse({"error": "not found"}, status_code=404)

        # ── Playground SPA Routes ─────────────────────────────────
        # Serve static assets for the React playground UI
        from fastapi.staticfiles import StaticFiles
        playground_static = TEMPLATES / "playground" / "assets"
        if playground_static.exists():
            app.mount("/playground/assets", StaticFiles(directory=str(playground_static)), name="playground_assets")

        @app.get("/playground", response_class=HTMLResponse)
        @app.get("/playground/{path:path}", response_class=HTMLResponse)
        async def playground_spa(path: str = ""):
            """Serve the React-based Playground SPA (catch-all)."""
            # Don't interfere with API calls
            if path and path.startswith("api/"):
                return JSONResponse({"error": "not found"}, status_code=404)
            html_path = TEMPLATES / "playground" / "index.html"
            if html_path.exists():
                return html_path.read_text(encoding="utf-8")
            return HTMLResponse("<h1>Playground not built yet</h1><p>Run `cd playground-ui && npx vite build`</p>")

        # ── API Routes ────────────────────────────────────────────

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
            """List all known domains from the registry."""
            domains = self.domain_registry.list_domains()
            return {"domains": domains}

        @app.get("/api/domains/installed")
        async def list_installed_domains():
            """List installed domains only."""
            return {"domains": self.domain_registry.list_installed()}

        @app.get("/api/domains/search")
        async def search_domains(q: str = ""):
            """Search domains by name, label, or tags."""
            if not q:
                return {"results": self.domain_registry.list_domains()}
            return {"results": self.domain_registry.search(q)}

        @app.get("/api/domains/{name}")
        async def get_domain(name: str):
            """Get detailed metadata for a domain."""
            meta = self.domain_registry.get_domain(name)
            if not meta:
                return {"error": f"Domain '{name}' not found"}
            # Add installed status and learned insights
            meta["installed"] = self.domain_registry.is_installed(name)
            learned = self.domain_registry.get_learned(name)
            if learned:
                meta["learned"] = learned
            return {"domain": meta}

        @app.post("/api/domains/{name}/install")
        async def install_domain(name: str):
            """Mark a domain as installed."""
            try:
                result = self.domain_registry.install(name)
                return {"status": "ok", "domain": result}
            except KeyError as e:
                return {"error": str(e)}

        @app.delete("/api/domains/{name}")
        async def remove_domain(name: str):
            """Remove a domain from the registry."""
            self.domain_registry.remove(name)
            return {"status": "removed", "domain": name}

        @app.post("/api/domains/{name}/learn")
        async def learn_domain(name: str):
            """Analyse a domain and store insights."""
            try:
                insights = self.domain_registry.learn(name)
                return {"status": "ok", "insights": insights}
            except KeyError as e:
                return {"error": str(e)}

        @app.get("/api/domains/learning/insights")
        async def list_learning_insights():
            """List all learning insights across domains."""
            return {"insights": self.domain_registry.list_learned()}

        @app.get("/api/domains/learning/suggestions")
        async def suggest_domains(tags: str = ""):
            """Get domain suggestions based on usage and tags."""
            tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
            suggestions = self.domain_registry.suggest_domains(tags=tag_list)
            return {"suggestions": suggestions}

        @app.get("/api/domains/usage/stats")
        async def domain_usage_stats():
            """Get aggregated domain usage statistics."""
            return self.domain_registry.get_usage_stats()

        @app.get("/api/domains/{name}/dependencies")
        async def domain_dependencies(name: str):
            """Resolve domain dependencies."""
            try:
                deps = self.domain_registry.resolve_dependencies(name)
                return {"dependencies": deps}
            except ValueError as e:
                return {"error": str(e)}

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

        # ── Component API (Advanced Playground) ──────────────────────

        @app.get("/api/playground/components/types")
        async def component_types():
            """List all supported flow component types with metadata."""
            from ..dsl import FlowDSL
            return {"types": FlowDSL.get_component_types()}

        @app.post("/api/playground/components/validate")
        async def validate_components(data: dict):
            """Validate a component-based flow definition."""
            from ..dsl import FlowDSL
            errors = FlowDSL.validate_structure(data)
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "has_components": "components" in data,
            }

        @app.post("/api/playground/components/execute")
        async def execute_components(data: dict):
            """Execute a component-based flow and return results."""
            from ..dsl import FlowDSL
            from ..playground import ComponentEngine, ExecutionContext

            flow = FlowDSL.parse(data)
            ctx = ExecutionContext(flow)
            engine = ComponentEngine()

            import asyncio
            result = await engine.execute(flow, ctx)
            return {
                "status": ctx.status,
                "result": result.to_dict(),
                "scope": {k: str(v)[:200] for k, v in ctx.scope.items()},
            }

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

        # ── Learning API — Analytics (L-02) ──────────────────────────

        @app.get("/api/learning/analytics/summary")
        async def analytics_summary():
            """Executive analytics summary."""
            return self.analytics.summary()

        @app.get("/api/learning/analytics/timeseries")
        async def analytics_timeseries(
            metric: str = "executions",
            interval: str = "hour",
            hours: int = 24,
        ):
            """Execution time series data."""
            return self.analytics.time_series(metric=metric, interval=interval, hours=hours)

        @app.get("/api/learning/analytics/flows")
        async def analytics_flows(min_runs: int = 1):
            """Flow performance ranking."""
            return {"flows": self.analytics.flow_performance(min_runs=min_runs)}

        @app.get("/api/learning/analytics/agents")
        async def analytics_agents(min_calls: int = 1):
            """Agent performance ranking."""
            return {"agents": self.analytics.agent_performance(min_calls=min_calls)}

        @app.get("/api/learning/analytics/bottlenecks")
        async def analytics_bottlenecks():
            """System bottleneck detection."""
            return self.analytics.bottlenecks()

        @app.get("/api/learning/analytics/anomalies")
        async def analytics_anomalies():
            """Anomaly detection results."""
            return self.analytics.anomalies()

        @app.get("/api/learning/analytics/patterns")
        async def analytics_patterns(min_occurrences: int = 2):
            """Frequent execution patterns."""
            return {"patterns": self.analytics.frequent_sequences(min_occurrences=min_occurrences)}

        @app.get("/api/learning/analytics/templates")
        async def analytics_suggested_templates():
            """Template suggestions from patterns."""
            return {"suggestions": self.analytics.suggested_templates()}

        # ── Playground API — Flow Runner (P-05) ───────────────────

        @app.post("/api/playground/run")
        async def playground_run(request: Request):
            """Execute a flow definition and get run_id for streaming."""
            body = await request.json()
            flow_yaml = body.get("yaml", "")
            if not flow_yaml:
                return {"error": "No flow YAML provided"}
            try:
                run = self.playground_runner.create_run(flow_yaml)
                # Fire-and-forget execution
                asyncio.create_task(self.playground_runner.execute_run_async(run.run_id))
                return {
                    "run_id": run.run_id,
                    "flow_name": run.flow_name,
                    "status": run.status,
                    "created_at": run.created_at,
                }
            except ValueError as e:
                return {"error": str(e)}

        @app.get("/api/playground/runs")
        async def playground_list_runs(limit: int = 20, status: str = None):
            """List recent flow runs."""
            runs = self.playground_runner.list_runs(limit=limit, status=status)
            return {"runs": runs}

        @app.get("/api/playground/runs/{run_id}")
        async def playground_get_run(run_id: str):
            """Get a specific run's status and details."""
            run = self.playground_runner.get_run(run_id)
            if run is None:
                return {"error": "Run not found"}
            return {"run": run.to_dict()}

        @app.post("/api/playground/runs/{run_id}/cancel")
        async def playground_cancel_run(run_id: str):
            """Cancel a queued or running flow."""
            ok = self.playground_runner.cancel_run(run_id)
            return {"cancelled": ok}

        @app.websocket("/api/playground/runs/{run_id}/stream")
        async def playground_run_stream(websocket: WebSocket, run_id: str):
            """WebSocket endpoint for live run streaming events."""
            await websocket.accept()
            queue = self.playground_runner.get_ws_queue(run_id)
            if queue is None:
                await websocket.send_json({"type": "error", "message": "Run not found"})
                await websocket.close()
                return

            try:
                while True:
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=5)
                        await websocket.send_json(event)
                    except asyncio.TimeoutError:
                        # Heartbeat ping
                        try:
                            await websocket.send_json({"type": "ping"})
                        except Exception:
                            break

                    # Stop streaming on terminal events
                    if event.get("type") in ("run.completed", "run.failed", "run.cancelled"):
                        break
            except WebSocketDisconnect:
                pass

        # ── Brain API — 3D Viz Data (B-05) ──────────────────────────

        @app.get("/api/brain/graph")
        async def brain_graph_data():
            """Get graph data for 3D neural visualization.

            Returns nodes (agents) and edges (connections) with
            status/health data for the 3D brain view.
            """
            nodes = []
            edges = []

            # Collect agent nodes
            if self.agent_registry:
                agents = list(getattr(self.agent_registry, '_agents', {}).values())
                for a in agents:
                    status = getattr(a, 'status', 'idle')
                    if hasattr(status, 'value'):
                        status = status.value
                    nodes.append({
                        "id": getattr(a, 'node_name', getattr(a, 'name', 'unknown')),
                        "label": getattr(a, 'node_name', getattr(a, 'name', 'unknown')),
                        "type": "agent",
                        "status": str(status).lower(),
                        "load": getattr(a, 'current_load', 0),
                        "tasks": getattr(a, 'total_tasks_completed', 0),
                        "errors": getattr(a, 'total_errors', 0),
                        "group": "agents",
                    })

            # Also add brain engine nodes
            nodes.append({"id": "brain-event-stream", "label": "Event Stream", "type": "engine", "status": "active", "group": "brain"})
            nodes.append({"id": "brain-decision-tracer", "label": "Decision Tracer", "type": "engine", "status": "active", "group": "brain"})
            nodes.append({"id": "brain-approval-gates", "label": "Approval Gates", "type": "engine", "status": "active", "group": "brain"})

            # Collect hub nodes from brain stats
            es_stats = self.event_stream.stats() if hasattr(self.event_stream, 'stats') else {}
            dt_stats = self.decision_tracer.stats() if hasattr(self.decision_tracer, 'stats') else {}
            ag_stats = self.approval_gates.stats() if hasattr(self.approval_gates, 'stats') else {}

            # Add edges between brain components
            edges.append({"source": "brain-event-stream", "target": "brain-decision-tracer", "label": "triggers", "weight": 1})
            edges.append({"source": "brain-decision-tracer", "target": "brain-approval-gates", "label": "requires", "weight": 1})

            # If we have agents, connect them to brain
            for n in nodes:
                if n["group"] == "agents":
                    edges.append({"source": n["id"], "target": "brain-event-stream", "label": "emits", "weight": 0.5})

            # Stats for the header
            brain_stats = {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "events": es_stats.get("total_events", 0),
                "traces": dt_stats.get("total_traces", 0),
                "pending_gates": ag_stats.get("by_status", {}).get("pending", 0),
                "activity_level": "high" if es_stats.get("total_events", 0) > 10 else "low",
            }

            return {"nodes": nodes, "edges": edges, "stats": brain_stats}

        @app.get("/api/brain/gates/pending-html")
        async def brain_pending_gates_html():
            """Get pending gates in a format suitable for the Gates UI."""
            gates = self.approval_gates.list_gates(status="pending")
            return {"gates": gates}
