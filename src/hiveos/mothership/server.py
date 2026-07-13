"""
Mothership HTTP Server — REST API for satellite communication.

Exposes endpoints for:
- Satellite node registration and heartbeat
- Task assignment and result collection
- Health monitoring
- Communication bus message exchange
- Package sync triggers
"""

import json
import threading
from pathlib import Path
from typing import Optional, Any, Dict, Callable
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

from rich.console import Console

console = Console()

# ── Request/Response Helpers ─────────────────────────────────────────

def _json_response(handler: BaseHTTPRequestHandler, data: Dict[str, Any], status: int = 200):
    """Send a JSON response."""
    body = json.dumps(data, indent=2, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", len(body))
    handler.end_headers()
    handler.wfile.write(body)


def _json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    """Read JSON body from request."""
    content_length = int(handler.headers.get("Content-Length", 0))
    if content_length == 0:
        return {}
    raw = handler.rfile.read(content_length)
    return json.loads(raw)


# ── Handler ──────────────────────────────────────────────────────────

class MothershipHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Mothership API."""

    # Set by MothershipServer before starting
    mothership: "MothershipServer" = None

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        # Routing
        if path == "/api/v1/status":
            return self._handle_status()
        elif path == "/api/v1/agents":
            return self._handle_agents_list()
        elif path.startswith("/api/v1/agents/") and path.count("/") == 4:
            name = path.split("/")[-1]
            return self._handle_agent_get(name)
        elif path == "/api/v1/health":
            return self._handle_health()
        elif path.startswith("/api/v1/health/"):
            name = path.split("/")[-1]
            return self._handle_agent_health(name)
        elif path == "/api/v1/capabilities":
            return self._handle_capabilities()
        elif path == "/api/v1/tasks":
            return self._handle_tasks_list()
        elif path == "/api/v1/circuits":
            return self._handle_circuits()
        elif path == "/api/v1/messages":
            return self._handle_messages_list(params)
        elif path == "/api/v1/metrics":
            return self._handle_metrics()

        _json_response(self, {"error": "Not found"}, 404)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/v1/agents/register":
            return self._handle_agent_register()
        elif path.startswith("/api/v1/agents/") and path.endswith("/heartbeat"):
            name = path.split("/")[-2]
            return self._handle_heartbeat(name)
        elif path == "/api/v1/agents/unregister":
            return self._handle_agent_unregister()
        elif path == "/api/v1/tasks/assign":
            return self._handle_task_assign()
        elif path.startswith("/api/v1/tasks/") and path.endswith("/complete"):
            task_id = path.split("/")[-2]
            return self._handle_task_complete(task_id)
        elif path.startswith("/api/v1/tasks/") and path.endswith("/failed"):
            task_id = path.split("/")[-2]
            return self._handle_task_failed(task_id)
        elif path.startswith("/api/v1/tasks/") and path.endswith("/progress"):
            task_id = path.split("/")[-2]
            return self._handle_task_progress(task_id)
        elif path == "/api/v1/sync":
            return self._handle_sync()
        elif path == "/api/v1/messages/publish":
            return self._handle_message_publish()

        _json_response(self, {"error": "Not found"}, 404)

    def do_PUT(self):
        """Handle PUT requests."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/v1/config":
            return self._handle_config_update()

        _json_response(self, {"error": "Not found"}, 404)

    # ── Status ──────────────────────────────────────────────────────

    def _handle_status(self):
        server = self.mothership
        status = {
            "version": "0.5.0",
            "uptime": server._uptime(),
            "agents_registered": server.registry.count(),
            "agents_online": sum(1 for a in server.registry.list() if a.status == "online"),
            "tasks_assigned": server.metrics.get("tasks_assigned", 0),
            "tasks_completed": server.metrics.get("tasks_completed", 0),
            "tasks_failed": server.metrics.get("tasks_failed", 0),
            "bus_messages": server.metrics.get("bus_messages", 0),
        }
        _json_response(self, status)

    # ── Agent Registration ──────────────────────────────────────────

    def _handle_agent_register(self):
        try:
            body = _json_body(self)
            name = body.get("name")
            url = body.get("url")
            if not name or not url:
                _json_response(self, {"error": "Missing 'name' or 'url'"}, 400)
                return

            from .agent_registry import CapabilityDeclaration
            caps = {}
            for c in body.get("capabilities", []):
                if isinstance(c, str):
                    caps[c] = CapabilityDeclaration(name=c)
                elif isinstance(c, dict):
                    caps[c["name"]] = CapabilityDeclaration(**c)

            agent = self.mothership.registry.register(
                name=name,
                url=url,
                api_key=body.get("api_key", ""),
                description=body.get("description", ""),
                capabilities=caps,
                max_concurrent=body.get("max_concurrent", 5),
            )
            _json_response(self, {"name": agent.name, "status": "registered"}, 201)
        except Exception as e:
            _json_response(self, {"error": str(e)}, 500)

    def _handle_agent_unregister(self):
        try:
            body = _json_body(self)
            name = body.get("name")
            if not name:
                _json_response(self, {"error": "Missing 'name'"}, 400)
                return
            success = self.mothership.registry.unregister(name)
            _json_response(self, {"removed": success})
        except Exception as e:
            _json_response(self, {"error": str(e)}, 500)

    def _handle_agents_list(self):
        agents = self.mothership.registry.list()
        data = []
        for a in agents:
            data.append({
                "name": a.name,
                "url": a.url,
                "status": a.status,
                "capabilities": list(a.capabilities.keys()),
                "load": f"{a.current_load}/{a.max_concurrent}",
                "tasks_completed": a.total_tasks_completed,
                "last_seen": a.last_seen,
            })
        _json_response(self, {"agents": data, "total": len(data)})

    def _handle_agent_get(self, name):
        agent = self.mothership.registry.get(name)
        if not agent:
            _json_response(self, {"error": f"Agent '{name}' not found"}, 404)
            return
        _json_response(self, {
            "name": agent.name,
            "url": agent.url,
            "status": agent.status,
            "description": agent.description,
            "capabilities": {k: {"name": v.name, "version": v.version, "description": v.description}
                             for k, v in agent.capabilities.items()},
            "load": agent.current_load,
            "max_concurrent": agent.max_concurrent,
            "tasks_completed": agent.total_tasks_completed,
            "errors": agent.total_errors,
            "last_heartbeat": agent.last_heartbeat,
            "registered_at": agent.registered_at,
        })

    # ── Heartbeat ──────────────────────────────────────────────────

    def _handle_heartbeat(self, name):
        try:
            body = _json_body(self)
            load = body.get("load")
            success = self.mothership.registry.record_heartbeat(name, load=load)
            if success:
                _json_response(self, {"acknowledged": True})
            else:
                _json_response(self, {"error": f"Unknown agent '{name}'"}, 404)
        except Exception as e:
            _json_response(self, {"error": str(e)}, 500)

    # ── Health ──────────────────────────────────────────────────────

    def _handle_health(self):
        if self.mothership.resilience:
            results = self.mothership.health_checker.check_all()
            data = {
                name: {"status": r.status.value, "latency_ms": r.latency_ms, "errors": r.errors}
                for name, r in results.items()
            }
            _json_response(self, {"nodes": data})
        else:
            _json_response(self, {"error": "Resilience engine not configured"}, 503)

    def _handle_agent_health(self, name):
        if self.mothership.health_checker:
            result = self.mothership.health_checker.check_node(name)
            _json_response(self, {
                "node": result.node_name,
                "status": result.status.value,
                "latency_ms": result.latency_ms,
                "errors": result.errors,
                "details": result.details,
            })
        else:
            _json_response(self, {"error": "Health checker not available"}, 503)

    # ── Capabilities ────────────────────────────────────────────────

    def _handle_capabilities(self):
        caps = self.mothership.registry.list_capabilities()
        _json_response(self, {"capabilities": caps})

    # ── Tasks ───────────────────────────────────────────────────────

    def _handle_tasks_list(self):
        tasks = []
        for task in self.mothership._tasks.values():
            tasks.append({
                "task_id": task.task_id,
                "agent_name": task.agent_name,
                "node_name": task.node_name,
                "capability": task.capability,
                "status": task.status,
                "assigned_at": task.assigned_at,
                "retry_count": task.retry_count,
            })
        _json_response(self, {"tasks": tasks, "total": len(tasks)})

    def _handle_task_assign(self):
        try:
            body = _json_body(self)
            agent_id = body.get("agent_id")
            capability = body.get("capability")
            if not agent_id or not capability:
                _json_response(self, {"error": "Missing 'agent_id' or 'capability'"}, 400)
                return

            assignment = self.mothership.task_router.route(
                agent_id=agent_id,
                required_capability=capability,
                metadata=body.get("metadata", {}),
                preferred_nodes=body.get("preferred_nodes"),
                excluded_nodes=body.get("excluded_nodes"),
            )

            if assignment:
                from .resilience import TaskAssignmentRecord
                task_record = TaskAssignmentRecord(
                    task_id=assignment.task_id,
                    agent_name=assignment.agent_name,
                    node_name=assignment.node_name,
                    capability=assignment.capability,
                    input_data=body.get("input_data", {}),
                )
                self.mothership.resilience_engine.register_task(task_record)
                self.mothership._tasks[assignment.task_id] = task_record
                self.mothership.metrics["tasks_assigned"] = self.mothership.metrics.get("tasks_assigned", 0) + 1

                _json_response(self, {
                    "task_id": assignment.task_id,
                    "node": assignment.node_name,
                    "node_url": assignment.node_url,
                    "capability": assignment.capability,
                    "strategy": assignment.strategy.value,
                }, 201)
            else:
                _json_response(self, {"error": f"No available node for capability '{capability}'"}, 503)
        except Exception as e:
            _json_response(self, {"error": str(e)}, 500)

    def _handle_task_complete(self, task_id):
        try:
            body = _json_body(self)
            task = self.mothership._tasks.get(task_id)
            if not task:
                _json_response(self, {"error": f"Task '{task_id}' not found"}, 404)
                return

            task.status = "completed"
            task.completed_at = datetime.utcnow().isoformat()
            task.output_data = body.get("output", {})

            self.mothership.registry.record_completion(task.node_name, True)
            self.mothership.metrics["tasks_completed"] = self.mothership.metrics.get("tasks_completed", 0) + 1

            if self.mothership.resilience:
                self.mothership.resilience_engine.record_task_completion(task_id, True, task.output_data)

            _json_response(self, {"acknowledged": True, "task_id": task_id})
        except Exception as e:
            _json_response(self, {"error": str(e)}, 500)

    def _handle_task_failed(self, task_id):
        try:
            body = _json_body(self)
            task = self.mothership._tasks.get(task_id)
            if not task:
                _json_response(self, {"error": f"Task '{task_id}' not found"}, 404)
                return

            task.status = "failed"
            task.completed_at = datetime.utcnow().isoformat()
            task.error = body.get("error", "Unknown error")

            self.mothership.registry.record_completion(task.node_name, False)
            self.mothership.metrics["tasks_failed"] = self.mothership.metrics.get("tasks_failed", 0) + 1

            if self.mothership.resilience:
                self.mothership.resilience_engine.record_task_completion(
                    task_id, False, error=task.error
                )

            _json_response(self, {"acknowledged": True, "task_id": task_id})
        except Exception as e:
            _json_response(self, {"error": str(e)}, 500)

    def _handle_task_progress(self, task_id):
        try:
            body = _json_body(self)
            task = self.mothership._tasks.get(task_id)
            if not task:
                _json_response(self, {"error": f"Task '{task_id}' not found"}, 404)
                return

            _json_response(self, {"acknowledged": True, "task_id": task_id})
        except Exception as e:
            _json_response(self, {"error": str(e)}, 500)

    # ── Circuits ────────────────────────────────────────────────────

    def _handle_circuits(self):
        if not self.mothership.resilience:
            _json_response(self, {"error": "Resilience not configured"}, 503)
            return
        circuits = {}
        for agent in self.mothership.registry.list():
            circuits[agent.name] = self.mothership.resilience.circuit_breaker.get_state(agent.name)
        _json_response(self, {"circuits": circuits})

    # ── Messages ────────────────────────────────────────────────────

    def _handle_messages_list(self, params):
        # Placeholder for message log
        _json_response(self, {"messages": [], "total": 0})

    def _handle_message_publish(self):
        try:
            body = _json_body(self)
            msg_type = body.get("type")
            if not msg_type:
                _json_response(self, {"error": "Missing 'type'"}, 400)
                return

            from .communication_bus import MessageType
            try:
                message_type = MessageType(msg_type)
            except ValueError:
                _json_response(self, {"error": f"Invalid message type: {msg_type}"}, 400)
                return

            message = self.mothership.bus.publish(
                msg_type=message_type,
                payload=body.get("payload", {}),
                recipient=body.get("recipient"),
                node_id="mothership",
            )
            self.mothership.metrics["bus_messages"] = self.mothership.metrics.get("bus_messages", 0) + 1

            _json_response(self, {"message_id": message.message_id, "type": msg_type}, 201)
        except Exception as e:
            _json_response(self, {"error": str(e)}, 500)

    # ── Sync ────────────────────────────────────────────────────────

    def _handle_sync(self):
        try:
            from ..sync import SyncService, NodeRegistry
            service = SyncService(
                registry=self.mothership.node_registry,
                knowledge_dir=self.mothership.knowledge_dir,
                flow_dir=self.mothership.flow_dir,
            )
            package = service.build_sync_package()
            if package:
                _json_response(self, {"package": str(package), "status": "built"})
            else:
                _json_response(self, {"status": "nothing_to_sync"})
        except Exception as e:
            _json_response(self, {"error": str(e)}, 500)

    # ── Config ──────────────────────────────────────────────────────

    def _handle_config_update(self):
        try:
            body = _json_body(self)
            # Update metrics or config
            if "heartbeat_timeout" in body:
                self.mothership.registry.heartbeat_timeout = body["heartbeat_timeout"]
            _json_response(self, {"updated": True})
        except Exception as e:
            _json_response(self, {"error": str(e)}, 500)

    # ── Metrics ─────────────────────────────────────────────────────

    def _handle_metrics(self):
        metrics = dict(self.mothership.metrics)
        if self.mothership.resilience:
            metrics["resilience"] = self.mothership.resilience.get_status()
        _json_response(self, metrics)


# ── Server ───────────────────────────────────────────────────────────

class MothershipServer:
    """
    HTTP server for the Mothership API.

    Provides a REST API for satellite nodes to:
    - Register and send heartbeats
    - Receive task assignments
    - Report task completions/failures
    - Trigger sync operations
    - Publish messages to the bus
    """

    def __init__(
        self,
        registry: Any,
        task_router: Any,
        bus: Any,
        resilience: Any = None,
        health_checker: Any = None,
        host: str = "0.0.0.0",
        port: int = 8080,
        knowledge_dir: Optional[Path] = None,
        flow_dir: Optional[Path] = None,
        node_registry: Any = None,
    ):
        self.registry = registry
        self.task_router = task_router
        self.bus = bus
        self.resilience = resilience
        self.health_checker = health_checker or (resilience.health_checker if resilience else None)
        self.resilience_engine = resilience
        self.host = host
        self.port = port
        self.knowledge_dir = knowledge_dir or Path("docs")
        self.flow_dir = flow_dir or Path("prototype")
        self.node_registry = node_registry  # Legacy NodeRegistry for sync

        self._httpd: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._start_time = datetime.utcnow()
        self._tasks: Dict[str, Any] = {}
        self._metrics: Dict[str, int] = {"tasks_assigned": 0, "tasks_completed": 0, "tasks_failed": 0, "bus_messages": 0}

    @property
    def metrics(self) -> Dict[str, int]:
        return self._metrics

    def _uptime(self) -> float:
        """Return uptime in seconds."""
        return (datetime.utcnow() - self._start_time).total_seconds()

    def start(self, background: bool = True):
        """Start the Mothership HTTP server."""
        # Inject server reference into handler
        MothershipHandler.mothership = self

        self._httpd = HTTPServer((self.host, self.port), MothershipHandler)

        if background:
            self._thread = threading.Thread(target=self._serve, daemon=True)
            self._thread.start()
            console.print(f"[green]🌍 Mothership server started on http://{self.host}:{self.port}[/green]")
        else:
            self._serve()

    def _serve(self):
        """Run the server."""
        try:
            self._httpd.serve_forever()
        except Exception as e:
            console.print(f"[red]Server error: {e}[/red]")

    def stop(self):
        """Stop the Mothership HTTP server."""
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        console.print("[dim]🌍 Mothership server stopped[/dim]")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()