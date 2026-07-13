"""
Node Registry — manages satellite node registration for Mothership.

A node is a remote Hermes instance that can receive and execute flows.
The registry is stored as a YAML file at ~/.hiveos/nodes.yaml.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml
from rich.console import Console

console = Console()


@dataclass
class SatelliteNode:
    """A registered satellite node."""
    name: str
    url: str
    api_key: str = ""
    description: str = ""
    capabilities: List[str] = None
    status: str = "unknown"  # online, offline, unknown
    last_seen: Optional[str] = None
    registered_at: str = ""

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if not self.registered_at:
            self.registered_at = datetime.utcnow().isoformat()


class NodeRegistry:
    """Manages satellite node registration in a YAML file."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or Path.home() / ".hiveos" / "nodes.yaml"
        self._nodes: Dict[str, SatelliteNode] = {}
        self.load()

    def load(self) -> Dict[str, SatelliteNode]:
        """Load nodes from YAML file."""
        if self.registry_path.exists():
            raw = yaml.safe_load(self.registry_path.read_text(encoding="utf-8"))
            if raw and "nodes" in raw:
                for name, data in raw["nodes"].items():
                    self._nodes[name] = SatelliteNode(**data)
            console.print(f"   📡 Loaded {len(self._nodes)} satellite(s) from registry")
        return self._nodes

    def save(self):
        """Persist nodes to YAML file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "0.1.0",
            "nodes": {
                name: {k: v for k, v in asdict(node).items() if v}
                for name, node in self._nodes.items()
            }
        }
        self.registry_path.write_text(
            yaml.dump(data, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )

    def register(self, name: str, url: str, api_key: str = "",
                 description: str = "", capabilities: List[str] = None) -> SatelliteNode:
        """Register a new satellite node (or update existing)."""
        node = SatelliteNode(
            name=name,
            url=url.rstrip("/"),
            api_key=api_key,
            description=description,
            capabilities=capabilities or [],
            status="unknown",
            last_seen=datetime.utcnow().isoformat(),
            registered_at=self._nodes[name].registered_at if self._nodes.get(name) else "",
        )
        self._nodes[name] = node
        self.save()
        action = "Updated" if name in self._nodes else "Registered"
        console.print(f"   [green]✅ {action} satellite '{name}' at {url}[/green]")
        return node

    def remove(self, name: str) -> bool:
        """Unregister a satellite node."""
        if name in self._nodes:
            del self._nodes[name]
            self.save()
            console.print(f"   [green]🗑️  Removed satellite '{name}'[/green]")
            return True
        console.print(f"   [red]❌ Satellite '{name}' not found[/red]")
        return False

    def get(self, name: str) -> Optional[SatelliteNode]:
        """Get a node by name."""
        return self._nodes.get(name)

    def list(self) -> List[SatelliteNode]:
        """Return all registered nodes."""
        return list(self._nodes.values())

    def update_heartbeat(self, name: str) -> bool:
        """Update last_seen for a node (e.g. from a heartbeat webhook)."""
        if name in self._nodes:
            self._nodes[name].last_seen = datetime.utcnow().isoformat()
            self._nodes[name].status = "online"
            self.save()
            return True
        return False

    @property
    def count(self) -> int:
        return len(self._nodes)
