"""
HiveOS Domain Registry — StorageEngine-backed catalog for discovering,
sharing, and learning from pluggable knowledge domains.

Extends DomainManager with:
- Persistent registry of known domains (installed + available)
- Domain search and discovery
- Dependency resolution
- Learning — track usage, suggest relevant domains
- Export/import domain packages
"""

from __future__ import annotations

import json
import shutil
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from hiveos.storage import StorageEngine

# ---------------------------------------------------------------------------
# Registry namespace keys
# ---------------------------------------------------------------------------
_NS_REGISTRY = "domain_registry"
_K_INSTALLED = "installed"       # {name: metadata}
_K_CATALOG = "catalog"           # {name: metadata} — all known (incl remote)
_K_USAGE = "usage_stats"         # {name: {install_count, last_used, ...}}
_K_LEARNED = "learned"           # {name: {insights, patterns, ...}}


class DomainRegistry:
    """StorageEngine-backed domain registry with learning support.

    Usage::

        registry = DomainRegistry(storage=storage, domains_root=Path("domains"))
        registry.scan()               # discover local domains
        registry.install("accounting")  # ensure installed
        registry.learn("accounting")    # analyse and remember
    """

    def __init__(
        self,
        storage: StorageEngine,
        domains_root: Optional[Path] = None,
    ):
        self.storage = storage
        self.domains_root = domains_root or Path.cwd() / "domains"

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def scan(self) -> List[dict]:
        """Scan the domains directory and update the registry catalog.

        Returns a list of domain metadata dicts.
        """
        domains = []
        if not self.domains_root.exists():
            return domains

        catalog = self._get_catalog()

        for child in sorted(self.domains_root.iterdir()):
            if child.is_dir():
                manifest_path = child / "domain.yaml"
                if manifest_path.exists():
                    try:
                        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
                        domain_data = data.get("domain", data)
                        name = domain_data.get("name", child.name)
                        meta = self._extract_meta(name, domain_data, child)
                        catalog[name] = meta
                        domains.append(meta)
                    except Exception as exc:
                        catalog[child.name] = {
                            "name": child.name,
                            "error": str(exc),
                            "status": "corrupted",
                        }

        self._save_catalog(catalog)
        return domains

    def get_domain(self, name: str) -> Optional[dict]:
        """Get domain metadata from registry catalog."""
        catalog = self._get_catalog()
        return catalog.get(name)

    def list_domains(self) -> List[dict]:
        """List all known domains from the registry catalog."""
        catalog = self._get_catalog()
        return list(catalog.values())

    def search(self, query: str) -> List[dict]:
        """Search domains by name, label, description, or tags."""
        q = query.lower()
        catalog = self._get_catalog()
        results = []
        for meta in catalog.values():
            if (q in meta.get("name", "").lower()
                    or q in meta.get("label_en", "").lower()
                    or q in meta.get("label_fa", "").lower()
                    or q in meta.get("description_en", "").lower()
                    or any(q in t.lower() for t in meta.get("tags", []))):
                results.append(meta)
        return results

    # ------------------------------------------------------------------
    # Installation / Removal
    # ------------------------------------------------------------------

    def install(self, name: str) -> dict:
        """Install a domain from the registry by name.

        If the domain directory already exists, just mark it installed.
        Otherwise, look for it in the catalog and try to find its source.
        """
        meta = self.get_domain(name)
        if not meta:
            raise KeyError(f"Domain '{name}' not found in registry")

        target = self.domains_root / name
        if target.exists():
            # Already on disk — just refresh metadata
            pass

        # Mark installed
        installed = self._get_installed()
        installed[name] = {
            **meta,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "status": "installed",
        }
        self._save_installed(installed)

        # Track usage
        self._track_usage(name, "install")

        return installed[name]

    def remove(self, name: str, permanent: bool = False) -> None:
        """Remove a domain from the registry.

        With *permanent=True*, the directory is deleted from disk.
        """
        installed = self._get_installed()
        if name in installed:
            del installed[name]
            self._save_installed(installed)

        if permanent:
            target = self.domains_root / name
            if target.exists():
                shutil.rmtree(target)

            catalog = self._get_catalog()
            if name in catalog:
                del catalog[name]
                self._save_catalog(catalog)

    def list_installed(self) -> List[dict]:
        """List all installed domains."""
        installed = self._get_installed()
        return list(installed.values())

    def is_installed(self, name: str) -> bool:
        """Check if a domain is marked as installed."""
        return name in self._get_installed()

    # ------------------------------------------------------------------
    # Dependencies
    # ------------------------------------------------------------------

    def resolve_dependencies(self, name: str) -> Dict[str, List[str]]:
        """Resolve domain dependencies.

        Returns {domain_name: [dep1, dep2, ...]} for all transitive deps.
        Raises ValueError on circular or missing dependencies.
        """
        catalog = self._get_catalog()
        resolved: Dict[str, List[str]] = {}
        visited = set()

        def _resolve(n: str, path: List[str]):
            if n in resolved:
                return
            if n in visited:
                raise ValueError(f"Circular dependency: {' → '.join(path + [n])}")
            visited.add(n)
            meta = catalog.get(n)
            if not meta:
                raise ValueError(f"Missing dependency: '{n}' required by {path[-1] if path else name}")
            deps = meta.get("depends_on", [])
            resolved[n] = deps
            for dep in deps:
                _resolve(dep, path + [n])

        _resolve(name, [])
        return resolved

    def verify_integrity(self) -> List[dict]:
        """Check all installed domains for completeness.

        Returns a list of issues found.
        """
        issues = []
        catalog = self._get_catalog()
        installed = self._get_installed()

        for name, meta in installed.items():
            domain_dir = self.domains_root / name
            if not domain_dir.exists():
                issues.append({
                    "domain": name,
                    "severity": "error",
                    "message": f"Domain directory missing: {domain_dir}",
                })
                continue

            # Check domain.yaml
            if not (domain_dir / "domain.yaml").exists():
                issues.append({
                    "domain": name,
                    "severity": "error",
                    "message": "Missing domain.yaml manifest",
                })

            # Check agent blueprints
            bp_dir = domain_dir / "agents" / "blueprints"
            agents = meta.get("agents", [])
            for agent in agents:
                agent_id = agent.get("id", "")
                if agent_id and not (bp_dir / f"{agent_id}.yaml").exists():
                    issues.append({
                        "domain": name,
                        "severity": "warning",
                        "message": f"Agent blueprint missing: {agent_id}",
                    })

            # Check flow templates
            flows = meta.get("flows", [])
            for flow in flows:
                flow_file = flow.get("file", "")
                if flow_file and not (domain_dir / flow_file).exists():
                    issues.append({
                        "domain": name,
                        "severity": "warning",
                        "message": f"Flow template missing: {flow_file}",
                    })

            # Check dependencies
            for dep in meta.get("depends_on", []):
                if dep not in installed:
                    issues.append({
                        "domain": name,
                        "severity": "error",
                        "message": f"Unmet dependency: '{dep}' (not installed)",
                    })

        return issues

    # ------------------------------------------------------------------
    # Learning — analysis and suggestions
    # ------------------------------------------------------------------

    def learn(self, name: str) -> dict:
        """Analyse a domain and store insights about it.

        Reads knowledge tree, agents, and flows to build a learning profile.
        """
        meta = self.get_domain(name)
        if not meta:
            raise KeyError(f"Domain '{name}' not found")

        domain_dir = self.domains_root / name
        insights = {
            "domain": name,
            "learned_at": datetime.now(timezone.utc).isoformat(),
            "total_agents": len(meta.get("agents", [])),
            "total_flows": len(meta.get("flows", [])),
            "orchestrator_count": sum(
                1 for a in meta.get("agents", []) if a.get("type") == "orchestrator"
            ),
            "specialist_count": sum(
                1 for a in meta.get("agents", []) if a.get("type") == "specialist"
            ),
            "tags": meta.get("tags", []),
            "coverage_areas": self._extract_coverage(meta),
            "knowledge_tree_nodes": self._count_knowledge_nodes(domain_dir, meta),
            "dependency_count": len(meta.get("depends_on", [])),
        }

        # Store learned insights
        learned = self._get_learned()
        learned[name] = insights
        self._save_learned(learned)

        self._track_usage(name, "learn")
        return insights

    def get_learned(self, name: str) -> Optional[dict]:
        """Get previously stored learning insights for a domain."""
        learned = self._get_learned()
        return learned.get(name)

    def list_learned(self) -> List[dict]:
        """List all learning insights."""
        learned = self._get_learned()
        return list(learned.values())

    def suggest_domains(self, tags: Optional[List[str]] = None) -> List[dict]:
        """Suggest domains based on usage history and tags."""
        installed = self._get_installed()
        installed_names = set(installed.keys())

        usage = self._get_usage()
        catalog = self._get_catalog()

        # Score each uninstalled domain
        scored = []
        for name, meta in catalog.items():
            if name in installed_names:
                continue

            score = 0
            domain_usage = usage.get(name, {})

            # Frequent installs → higher score
            score += domain_usage.get("install_count", 0) * 10
            score += domain_usage.get("learn_count", 0) * 5

            # Tag overlap
            if tags:
                domain_tags = set(meta.get("tags", []))
                score += len(domain_tags & set(tags)) * 3

            # Dependency popularity
            if meta.get("depends_on"):
                score += len([d for d in meta["depends_on"] if d in installed_names]) * 5

            scored.append((score, meta))

        scored.sort(key=lambda x: -x[0])
        return [meta for _, meta in scored if _ > 0]

    # ------------------------------------------------------------------
    # Usage tracking
    # ------------------------------------------------------------------

    def get_usage_stats(self) -> dict:
        """Get aggregated usage statistics for all domains."""
        usage = self._get_usage()
        installed = self._get_installed()
        return {
            "total_installed": len(installed),
            "total_known": len(self._get_catalog()),
            "domains": usage,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_catalog(self) -> dict:
        try:
            data = self.storage.load(_NS_REGISTRY, _K_CATALOG)
            return data if data else {}
        except Exception:
            return {}

    def _save_catalog(self, catalog: dict) -> None:
        self.storage.upsert(_NS_REGISTRY, _K_CATALOG, catalog)

    def _get_installed(self) -> dict:
        try:
            data = self.storage.load(_NS_REGISTRY, _K_INSTALLED)
            return data if data else {}
        except Exception:
            return {}

    def _save_installed(self, installed: dict) -> None:
        self.storage.upsert(_NS_REGISTRY, _K_INSTALLED, installed)

    def _get_usage(self) -> dict:
        try:
            data = self.storage.load(_NS_REGISTRY, _K_USAGE)
            return data if data else {}
        except Exception:
            return {}

    def _save_usage(self, usage: dict) -> None:
        self.storage.upsert(_NS_REGISTRY, _K_USAGE, usage)

    def _get_learned(self) -> dict:
        try:
            data = self.storage.load(_NS_REGISTRY, _K_LEARNED)
            return data if data else {}
        except Exception:
            return {}

    def _save_learned(self, learned: dict) -> None:
        self.storage.upsert(_NS_REGISTRY, _K_LEARNED, learned)

    def _track_usage(self, name: str, action: str) -> None:
        usage = self._get_usage()
        entry = usage.setdefault(name, {
            "install_count": 0,
            "learn_count": 0,
            "last_used": None,
            "last_action": None,
            "history": [],
        })
        if action == "install":
            entry["install_count"] += 1
        elif action == "learn":
            entry["learn_count"] += 1
        entry["last_used"] = datetime.now(timezone.utc).isoformat()
        entry["last_action"] = action
        entry["history"].append({
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Keep last 20 history entries
        entry["history"] = entry["history"][-20:]
        self._save_usage(usage)

    @staticmethod
    def _extract_meta(name: str, domain_data: dict, root: Path) -> dict:
        agents = domain_data.get("agents", [])
        flows = domain_data.get("flows", [])
        label = domain_data.get("label", {})
        description = domain_data.get("description", {})
        metadata = domain_data.get("metadata", {})
        return {
            "name": name,
            "version": domain_data.get("version", "0.0.0"),
            "label_en": label.get("en", name) if isinstance(label, dict) else str(label),
            "label_fa": label.get("fa", ""),
            "description_en": description.get("en", "") if isinstance(description, dict) else "",
            "description_fa": description.get("fa", ""),
            "orchestrator_agent": domain_data.get("orchestrator_agent", ""),
            "depends_on": domain_data.get("depends_on", []),
            "knowledge_tree": domain_data.get("knowledge_tree", ""),
            "tags": metadata.get("tags", []) if isinstance(metadata, dict) else [],
            "total_agents": len(agents),
            "orchestrators": sum(1 for a in agents if a.get("type") == "orchestrator"),
            "specialists": sum(1 for a in agents if a.get("type") == "specialist"),
            "total_flows": len(flows),
            "agents": agents,
            "flows": flows,
            "status": "available",
            "path": str(root),
        }

    @staticmethod
    def _extract_coverage(meta: dict) -> List[str]:
        """Extract unique coverage areas from agent definitions."""
        areas = set()
        for agent in meta.get("agents", []):
            covers = agent.get("covers", [])
            if isinstance(covers, list):
                for c in covers:
                    # Take the top-level area (e.g., "A1" → "A")
                    top = c.split(".")[0][0] if c else ""
                    if top:
                        areas.add(top)
        return sorted(areas)

    @staticmethod
    def _count_knowledge_nodes(domain_dir: Path, meta: dict) -> int:
        tree_rel = meta.get("knowledge_tree", "")
        if not tree_rel:
            return 0
        tree_path = domain_dir / tree_rel
        if not tree_path.exists():
            return 0
        try:
            data = yaml.safe_load(tree_path.read_text(encoding="utf-8"))
            return len(data.get("nodes", []))
        except Exception:
            return 0


# ---------------------------------------------------------------------------
# Convenience: export / import domain as tar.gz
# ---------------------------------------------------------------------------

def export_domain(domain_dir: Path, output: Optional[Path] = None) -> Path:
    """Package a domain directory into a portable ``.tar.gz`` archive.

    Returns the path to the created archive.
    """
    if not domain_dir.exists() or not (domain_dir / "domain.yaml").exists():
        raise ValueError(f"Not a valid domain: {domain_dir}")

    output = output or Path.cwd() / f"{domain_dir.name}.tar.gz"
    with tarfile.open(output, "w:gz") as tar:
        tar.add(domain_dir, arcname=domain_dir.name)
    return output


def import_domain(archive: Path, target_root: Path) -> Path:
    """Extract a domain tar.gz archive into the target directory.

    Returns the path to the extracted domain directory.
    """
    if not archive.exists():
        raise FileNotFoundError(f"Archive not found: {archive}")

    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(path=target_root)

    # The top-level item in the archive should be the domain folder
    extracted = target_root / archive.stem.replace(".tar", "")
    if extracted.exists() and (extracted / "domain.yaml").exists():
        return extracted

    # Try to find it
    for child in target_root.iterdir():
        if child.is_dir() and (child / "domain.yaml").exists():
            return child

    raise ValueError(f"No valid domain found in archive: {archive}")
