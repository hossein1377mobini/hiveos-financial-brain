"""
HiveOS Domain Manager — discovers, loads, and manages pluggable knowledge domains.

Each domain is a directory under the project's ``domains/`` folder with a
``domain.yaml`` manifest.  The DomainManager provides introspection
(list, info) and lifecycle (install, remove) operations.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

class DomainInfo:
    """Read-only snapshot of a loaded domain."""

    def __init__(self, root: Path, manifest: dict):
        self.root = root
        self._m = manifest

    # -- metadata --
    @property
    def name(self) -> str: return self._m.get("domain", {}).get("name", "?")
    @property
    def version(self) -> str: return self._m.get("domain", {}).get("version", "?")
    @property
    def label_en(self) -> str: return self._m.get("domain", {}).get("label", {}).get("en", self.name)
    @property
    def label_fa(self) -> str: return self._m.get("domain", {}).get("label", {}).get("fa", "")
    @property
    def description_en(self) -> str: return self._m.get("domain", {}).get("description", {}).get("en", "")
    @property
    def description_fa(self) -> str: return self._m.get("domain", {}).get("description", {}).get("fa", "")
    @property
    def orchestrator_agent(self) -> str: return self._m.get("domain", {}).get("orchestrator_agent", "")
    @property
    def tags(self) -> List[str]: return self._m.get("domain", {}).get("metadata", {}).get("tags", [])
    @property
    def depends_on(self) -> List[str]: return self._m.get("domain", {}).get("depends_on", [])

    # -- agents --
    @property
    def agents(self) -> List[dict]:
        return self._m.get("domain", {}).get("agents", [])

    @property
    def orchestrator_count(self) -> int:
        return sum(1 for a in self.agents if a.get("type") == "orchestrator")

    @property
    def specialist_count(self) -> int:
        return sum(1 for a in self.agents if a.get("type") == "specialist")

    @property
    def total_agents(self) -> int:
        return len(self.agents)

    # -- flows --
    @property
    def flows(self) -> List[dict]:
        return self._m.get("domain", {}).get("flows", [])

    @property
    def total_flows(self) -> int:
        return len(self.flows)

    # -- knowledge --
    @property
    def knowledge_tree(self) -> str:
        return self._m.get("domain", {}).get("knowledge_tree", "")

    def knowledge_tree_node_count(self) -> int:
        """Load the knowledge tree YAML and count nodes."""
        tree_path = self.root / self.knowledge_tree
        if not tree_path.exists():
            return 0
        try:
            data = yaml.safe_load(tree_path.read_text(encoding="utf-8"))
            return len(data.get("nodes", []))
        except Exception:
            return 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "label_en": self.label_en,
            "label_fa": self.label_fa,
            "description_en": self.description_en,
            "orchestrator_agent": self.orchestrator_agent,
            "tags": self.tags,
            "depends_on": self.depends_on,
            "total_agents": self.total_agents,
            "orchestrators": self.orchestrator_count,
            "specialists": self.specialist_count,
            "total_flows": self.total_flows,
            "agents": self.agents,
            "flows": self.flows,
        }


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class DomainManager:
    """Scans a domains directory and provides lifecycle operations."""

    def __init__(self, domains_root: Optional[Path] = None):
        self._root = domains_root or Path.cwd() / "domains"
        self._cache: Dict[str, DomainInfo] = {}

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def list_domains(self) -> List[DomainInfo]:
        """Return a DomainInfo for every installed domain."""
        domains = []
        if not self._root.exists():
            return domains
        for child in sorted(self._root.iterdir()):
            if child.is_dir():
                manifest = child / "domain.yaml"
                if manifest.exists():
                    try:
                        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
                        info = DomainInfo(child, data)
                        self._cache[info.name] = info
                        domains.append(info)
                    except Exception:
                        pass
        return domains

    def get_domain(self, name: str) -> Optional[DomainInfo]:
        """Return a specific domain by name (uses cache if possible)."""
        if name in self._cache:
            return self._cache[name]
        for d in self.list_domains():
            if d.name == name:
                self._cache[name] = d
                return d
        return None

    def get_agent_blueprint_path(self, domain_name: str, agent_id: str) -> Optional[Path]:
        """Return the path to an agent blueprint YAML file."""
        domain = self.get_domain(domain_name)
        if not domain:
            return None
        bp_path = domain.root / "agents" / "blueprints" / f"{agent_id}.yaml"
        return bp_path if bp_path.exists() else None

    def get_flow_path(self, domain_name: str, flow_id: str) -> Optional[Path]:
        """Return the path to a flow template file."""
        domain = self.get_domain(domain_name)
        if not domain:
            return None
        for flow in domain.flows:
            if flow.get("id") == flow_id:
                fpath = domain.root / flow.get("file", "")
                return fpath if fpath.exists() else None
        return None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def install(self, source: Path, name: Optional[str] = None) -> DomainInfo:
        """Copy a domain from *source* into the domains directory.

        Returns the installed DomainInfo.
        """
        if not source.exists() or not (source / "domain.yaml").exists():
            raise ValueError(f"Source is not a valid domain: {source}")

        target_name = name or source.name
        target = self._root / target_name
        if target.exists():
            raise FileExistsError(f"Domain '{target_name}' already exists at {target}")

        shutil.copytree(source, target)
        data = yaml.safe_load((target / "domain.yaml").read_text(encoding="utf-8"))
        info = DomainInfo(target, data)
        self._cache[info.name] = info
        return info

    def remove(self, name: str, permanent: bool = False) -> None:
        """Remove a domain from the domains directory.

        With *permanent=True*, the directory is deleted from disk.
        Otherwise it is just evicted from the cache.
        """
        domain = self.get_domain(name)
        if not domain:
            raise KeyError(f"Domain '{name}' not found")

        self._cache.pop(name, None)
        if permanent and domain.root.exists():
            shutil.rmtree(domain.root)

    def refresh(self) -> None:
        """Clear cache and re-scan."""
        self._cache.clear()
        self.list_domains()
