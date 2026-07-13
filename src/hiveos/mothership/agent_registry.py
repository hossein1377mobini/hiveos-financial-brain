"""
Agent Registry — Enhanced capability-based node registry.

Extends the basic NodeRegistry with structured capability declarations,
heartbeat monitoring with timeout detection, and capability-based search.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import time
import yaml
import threading
from rich.console import Console

from ..sync.node_registry import NodeRegistry, SatelliteNode

console = Console()


@dataclass
class CapabilityDeclaration:
    """Structured declaration of an agent's capability."""
    name: str                      # e.g. "web-search", "code-generation"
    version: str = "1.0.0"        # capability version
    description: str = ""          # what this capability does
    parameters: Dict[str, Any] = field(default_factory=dict)  # configuration params
    required_skills: List[str] = field(default_factory=list)   # Hermes skill names
    estimated_load: float = 1.0   # relative resource cost (1.0 = baseline)
    tags: List[str] = field(default_factory=list)  # for categorization


@dataclass
class AgentCapability:
    """An agent node's complete capability profile."""
    node_name: str
    capabilities: Dict[str, CapabilityDeclaration] = field(default_factory=dict)
    current_load: int = 0          # number of active tasks
    max_concurrent: int = 5        # max parallel tasks this node can handle
    total_tasks_completed: int = 0
    total_errors: int = 0
    uptime_seconds: int = 0

    @property
    def load_factor(self) -> float:
        """Load as a fraction of capacity (0.0 = idle, 1.0 = full)."""
        return self.current_load / self.max_concurrent if self.max_concurrent > 0 else 1.0

    @property
    def has_capacity(self) -> bool:
        """Whether the node can accept more tasks."""
        return self.current_load < self.max_concurrent

    @property
    def reliability_score(self) -> float:
        """Simple reliability metric (0.0–1.0)."""
        total = self.total_tasks_completed + self.total_errors
        if total == 0:
            return 1.0
        return self.total_tasks_completed / total


@dataclass
class AgentStatus:
    """Full status of a registered agent node."""
    name: str
    url: str
    api_key: str = ""
    description: str = ""
    capabilities: Dict[str, CapabilityDeclaration] = field(default_factory=dict)
    status: str = "unknown"       # online, offline, degraded, unknown
    last_seen: Optional[str] = None
    last_heartbeat: Optional[str] = None
    registered_at: str = ""
    heartbeat_count: int = 0
    missed_heartbeats: int = 0
    current_load: int = 0
    max_concurrent: int = 5
    total_tasks_completed: int = 0
    total_errors: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_satellite_node(self) -> SatelliteNode:
        """Convert to the simpler SatelliteNode for backward compatibility."""
        cap_names = list(self.capabilities.keys()) if self.capabilities else []
        return SatelliteNode(
            name=self.name,
            url=self.url,
            api_key=self.api_key,
            description=self.description,
            capabilities=cap_names,
            status=self.status,
            last_seen=self.last_seen,
            registered_at=self.registered_at,
        )

    @classmethod
    def from_satellite_node(cls, node: SatelliteNode) -> "AgentStatus":
        """Create from a SatelliteNode (capabilities become simple declarations)."""
        caps = {}
        for cap_name in (node.capabilities or []):
            caps[cap_name] = CapabilityDeclaration(name=cap_name, description=cap_name)
        return cls(
            name=node.name,
            url=node.url,
            api_key=node.api_key,
            description=node.description,
            capabilities=caps,
            status=node.status,
            last_seen=node.last_seen,
            registered_at=node.registered_at or datetime.utcnow().isoformat(),
        )


class AgentRegistry:
    """
    Enhanced registry for agent nodes with capability-based declarations.

    Extends the basic NodeRegistry by adding structured capability profiles,
    heartbeat monitoring with configurable timeout, and rich search/filter.
    """

    def __init__(
        self,
        registry_path: Optional[Path] = None,
        heartbeat_timeout: int = 30,       # seconds before marking offline
        heartbeat_check_interval: int = 15, # seconds between health checks
    ):
        self.registry_path = registry_path or Path.home() / ".hiveos" / "agents.yaml"
        self.heartbeat_timeout = heartbeat_timeout
        self._agents: Dict[str, AgentStatus] = {}
        self._lock = threading.Lock()
        self._running = False
        self._health_thread: Optional[threading.Thread] = None
        self._on_status_change: Optional[Callable[[str, str, str], None]] = None
        self._migrate_from_legacy()
        self.load()

    # ── Persistence ─────────────────────────────────────────────────

    def _migrate_from_legacy(self):
        """Migrate nodes from legacy ~/.hiveos/nodes.yaml if it exists and agents.yaml doesn't."""
        legacy = Path.home() / ".hiveos" / "nodes.yaml"
        if legacy.exists() and not self.registry_path.exists():
            try:
                raw = yaml.safe_load(legacy.read_text(encoding="utf-8"))
                if raw and "nodes" in raw:
                    agents = {"version": "0.2.0", "agents": {}}
                    for name, data in raw["nodes"].items():
                        agents["agents"][name] = {
                            "name": name,
                            "url": data.get("url", ""),
                            "api_key": data.get("api_key", ""),
                            "description": data.get("description", ""),
                            "status": data.get("status", "unknown"),
                            "last_seen": data.get("last_seen"),
                            "registered_at": data.get("registered_at", datetime.utcnow().isoformat()),
                        }
                    self.registry_path.parent.mkdir(parents=True, exist_ok=True)
                    self.registry_path.write_text(
                        yaml.dump(agents, default_flow_style=False, allow_unicode=True),
                        encoding="utf-8",
                    )
                    console.print(f"   [dim]Migrated {len(raw['nodes'])} node(s) from legacy registry[/dim]")
            except Exception:
                pass  # If migration fails, start fresh

    def load(self):
        """Load agents from YAML file."""
        if self.registry_path.exists():
            try:
                raw = yaml.safe_load(self.registry_path.read_text(encoding="utf-8"))
                if raw and "agents" in raw:
                    for name, data in raw["agents"].items():
                        caps = {}
                        for c in data.get("capabilities", []):
                            if isinstance(c, dict):
                                caps[c["name"]] = CapabilityDeclaration(**c)
                            elif isinstance(c, str):
                                caps[c] = CapabilityDeclaration(name=c)
                        data["capabilities"] = caps
                        self._agents[name] = AgentStatus(**data)
            except Exception as e:
                console.print(f"[yellow]⚠️  Failed to load agent registry: {e}[/yellow]")

    def save(self):
        """Persist agents to YAML file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "0.2.0",
            "agents": {},
        }
        for name, agent in self._agents.items():
            entry = asdict(agent)
            # Convert CapabilityDeclaration dicts back to list-of-dicts for clean YAML
            caps_list = []
            for cap_name, cap in agent.capabilities.items():
                cap_dict = asdict(cap)
                caps_list.append(cap_dict)
            entry["capabilities"] = caps_list
            # Remove empty fields for cleaner YAML
            entry = {k: v for k, v in entry.items() if v is not None and v != "" and v != [] and v != {}}
            data["agents"][name] = entry

        self.registry_path.write_text(
            yaml.dump(data, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )

    # ── Agent Registration ───────────────────────────────────────────

    def register(
        self,
        name: str,
        url: str,
        api_key: str = "",
        description: str = "",
        capabilities: Optional[Dict[str, CapabilityDeclaration]] = None,
        max_concurrent: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentStatus:
        """Register a new agent node (or update existing)."""
        with self._lock:
            existing = self._agents.get(name)
            now = datetime.utcnow().isoformat()

            agent = AgentStatus(
                name=name,
                url=url.rstrip("/"),
                api_key=api_key,
                description=description,
                capabilities=capabilities or {},
                status="unknown",
                last_seen=now,
                registered_at=existing.registered_at if existing else now,
                max_concurrent=max_concurrent,
                current_load=existing.current_load if existing else 0,
                total_tasks_completed=existing.total_tasks_completed if existing else 0,
                total_errors=existing.total_errors if existing else 0,
                metadata=metadata or {},
            )
            self._agents[name] = agent
            self.save()
            action = "Updated" if existing else "Registered"
            console.print(f"   [green]✅ {action} agent '{name}' at {url}[/green]")
            if agent.capabilities:
                console.print(f"      Capabilities: {', '.join(agent.capabilities.keys())}")
            return agent

    def unregister(self, name: str) -> bool:
        """Remove an agent node from the registry."""
        with self._lock:
            if name in self._agents:
                del self._agents[name]
                self.save()
                console.print(f"   [green]🗑️  Unregistered agent '{name}'[/green]")
                return True
            console.print(f"   [red]❌ Agent '{name}' not found[/red]")
            return False

    def get(self, name: str) -> Optional[AgentStatus]:
        """Get an agent by name."""
        return self._agents.get(name)

    def list(self) -> List[AgentStatus]:
        """Return all registered agents."""
        return list(self._agents.values())

    def count(self) -> int:
        """Number of registered agents."""
        return len(self._agents)

    # ── Capability Search ────────────────────────────────────────────

    def find_by_capability(self, capability_name: str, min_version: str = "") -> List[AgentStatus]:
        """Find agents that declare a specific capability."""
        results = []
        for agent in self._agents.values():
            if capability_name in agent.capabilities:
                cap = agent.capabilities[capability_name]
                if min_version and cap.version < min_version:
                    continue
                results.append(agent)
        return results

    def find_available(self, capability_name: str, min_version: str = "") -> List[AgentStatus]:
        """Find agents that have a capability AND have capacity."""
        results = []
        for agent in self.find_by_capability(capability_name, min_version):
            if agent.status == "online" and agent.current_load < agent.max_concurrent:
                results.append(agent)
        return results

    def list_capabilities(self) -> Dict[str, int]:
        """List all distinct capabilities and how many agents provide each."""
        cap_map: Dict[str, int] = {}
        for agent in self._agents.values():
            for cap_name in agent.capabilities:
                cap_map[cap_name] = cap_map.get(cap_name, 0) + 1
        return cap_map

    # ── Heartbeat ────────────────────────────────────────────────────

    def record_heartbeat(self, name: str, load: Optional[int] = None) -> bool:
        """Record a heartbeat from an agent node."""
        with self._lock:
            agent = self._agents.get(name)
            if not agent:
                return False

            now = datetime.utcnow().isoformat()
            agent.last_heartbeat = now
            agent.last_seen = now
            agent.heartbeat_count += 1
            agent.missed_heartbeats = 0

            old_status = agent.status
            agent.status = "online"

            if load is not None:
                agent.current_load = load

            self.save()

            if old_status != "online" and self._on_status_change:
                self._on_status_change(name, old_status, "online")

            return True

    def record_completion(self, name: str, success: bool):
        """Record a task completion or error for an agent."""
        with self._lock:
            agent = self._agents.get(name)
            if not agent:
                return
            if success:
                agent.total_tasks_completed += 1
            else:
                agent.total_errors += 1
            agent.current_load = max(0, agent.current_load - 1)
            self.save()

    def record_task_assignment(self, name: str):
        """Increment the load counter for a node receiving a task."""
        with self._lock:
            agent = self._agents.get(name)
            if agent:
                agent.current_load += 1
                self.save()

    # ── Health Monitoring ────────────────────────────────────────────

    def check_health(self) -> List[Dict[str, Any]]:
        """Check all agents for heartbeat timeout. Returns list of status changes."""
        changes = []
        now = datetime.utcnow()
        with self._lock:
            for name, agent in self._agents.items():
                if agent.last_heartbeat:
                    try:
                        last = datetime.fromisoformat(agent.last_heartbeat)
                        elapsed = (now - last).total_seconds()
                    except (ValueError, TypeError):
                        elapsed = self.heartbeat_timeout + 1  # force offline

                    old_status = agent.status

                    if elapsed > self.heartbeat_timeout * 3:
                        new_status = "offline"
                    elif elapsed > self.heartbeat_timeout:
                        agent.missed_heartbeats += 1
                        new_status = "degraded" if agent.missed_heartbeats < 3 else "offline"
                    else:
                        new_status = "online"

                    if new_status != old_status:
                        agent.status = new_status
                        changes.append({
                            "name": name,
                            "old_status": old_status,
                            "new_status": new_status,
                            "elapsed": elapsed,
                        })
                        if self._on_status_change:
                            self._on_status_change(name, old_status, new_status)

            if changes:
                self.save()

        return changes

    def start_health_monitor(self):
        """Start background health check thread."""
        if self._running:
            return
        self._running = True
        self._health_thread = threading.Thread(target=self._health_loop, daemon=True)
        self._health_thread.start()
        console.print("[dim]🧪 Agent health monitor started[/dim]")

    def stop_health_monitor(self):
        """Stop background health check thread."""
        self._running = False
        if self._health_thread:
            self._health_thread.join(timeout=5)
            self._health_thread = None
        console.print("[dim]🧪 Agent health monitor stopped[/dim]")

    def _health_loop(self):
        """Background loop that periodically checks agent health."""
        while self._running:
            try:
                changes = self.check_health()
                for c in changes:
                    status_icon = "🟢" if c["new_status"] == "online" else "🟡" if c["new_status"] == "degraded" else "🔴"
                    console.print(
                        f"   {status_icon} Agent '{c['name']}': "
                        f"{c['old_status']} → {c['new_status']} "
                        f"(no heartbeat for {c['elapsed']:.0f}s)"
                    )
            except Exception as e:
                console.print(f"[red]Health check error: {e}[/red]")
            time.sleep(self.heartbeat_check_interval)

    def on_status_change(self, callback: Callable[[str, str, str], None]):
        """Register a callback for status changes: callback(name, old_status, new_status)."""
        self._on_status_change = callback

    # ── Summary ──────────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        """Return a summary of the agent registry state."""
        agents = self.list()
        status_counts = {}
        for a in agents:
            status_counts[a.status] = status_counts.get(a.status, 0) + 1

        return {
            "total_agents": len(agents),
            "status_counts": status_counts,
            "online_agents": status_counts.get("online", 0),
            "capabilities": self.list_capabilities(),
            "total_capability_types": len(self.list_capabilities()),
            "total_tasks_completed": sum(a.total_tasks_completed for a in agents),
            "total_errors": sum(a.total_errors for a in agents),
        }

    def display_summary(self):
        """Print a summary table to the console."""
        from rich.table import Table
        summary = self.summary()

        table = Table(title="🌍 Mothership Agent Registry")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Total Agents", str(summary["total_agents"]))
        table.add_row("Online", str(summary["online_agents"]))
        table.add_row("Capability Types", str(summary["total_capability_types"]))

        for status, count in summary["status_counts"].items():
            icon = "🟢" if status == "online" else "🟡" if status == "degraded" else "🔴"
            table.add_row(f"{icon} {status.title()}", str(count))

        table.add_row("Tasks Completed", str(summary["total_tasks_completed"]))
        table.add_row("Total Errors", str(summary["total_errors"]))

        console.print(table)
