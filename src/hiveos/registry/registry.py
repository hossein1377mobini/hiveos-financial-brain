"""
Package Registry — local YAML-based catalog for discovering and publishing HiveOS packages.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import yaml
import json
from rich.console import Console
from rich.table import Table

console = Console()

REGISTRY_DIR = Path.home() / ".hiveos" / "registry"
REGISTRY_FILE = REGISTRY_DIR / "catalog.yaml"


@dataclass
class RegistryEntry:
    """A single entry in the package registry."""

    name: str
    version: str
    description: str
    author: str
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    flows: List[str] = field(default_factory=list)
    requires_hiveos_version: str = ">=0.1.0"
    published_at: str = ""
    updated_at: str = ""
    source_url: str = ""  # Remote registry URL or local path
    install_count: int = 0
    homepage: str = ""
    license: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegistryEntry":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class RegistryConfig:
    """Configuration for the package registry."""

    registry_dir: Path = REGISTRY_DIR
    remote_registries: List[str] = field(default_factory=list)
    auto_sync: bool = False


class PackageRegistry:
    """Local YAML-based package registry.

    Manages a catalog.yaml file at ~/.hiveos/registry/catalog.yaml.
    Supports publishing, searching, and listing local packages.
    """

    def __init__(self, config: Optional[RegistryConfig] = None):
        self.config = config or RegistryConfig()
        self._catalog_path = self.config.registry_dir / "catalog.yaml"
        self._catalog: Dict[str, Dict[str, RegistryEntry]] = {}  # name -> version -> entry
        self._load()

    # ── Persistence ──────────────────────────────────────────────

    def _load(self) -> None:
        """Load the catalog from disk."""
        if self._catalog_path.exists():
            try:
                raw = yaml.safe_load(self._catalog_path.read_text(encoding="utf-8"))
                if raw and isinstance(raw, dict):
                    for name, versions in raw.items():
                        self._catalog[name] = {}
                        if isinstance(versions, dict):
                            for ver, entry_data in versions.items():
                                entry_data["name"] = name
                                entry_data["version"] = ver
                                self._catalog[name][ver] = RegistryEntry.from_dict(entry_data)
            except yaml.YAMLError as e:
                console.print(f"[yellow]⚠️  Registry file corrupt, starting fresh: {e}[/yellow]")
                self._catalog = {}
        else:
            self._catalog = {}

    def _save(self) -> None:
        """Persist the catalog to disk."""
        self.config.registry_dir.mkdir(parents=True, exist_ok=True)
        raw: Dict[str, Dict[str, dict]] = {}
        for name, versions in self._catalog.items():
            raw[name] = {}
            for ver, entry in versions.items():
                d = entry.to_dict()
                # Remove redundant keys stored in the key already
                d.pop("name", None)
                d.pop("version", None)
                raw[name][ver] = d
        self._catalog_path.write_text(
            yaml.dump(raw, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    # ── CRUD ─────────────────────────────────────────────────────

    def publish(self, entry: RegistryEntry, overwrite: bool = False) -> bool:
        """Publish a package entry to the registry.

        Args:
            entry: The package entry to publish.
            overwrite: If True, overwrite an existing version.

        Returns:
            True if published, False if version already exists and overwrite=False.
        """
        if entry.name not in self._catalog:
            self._catalog[entry.name] = {}

        if entry.version in self._catalog[entry.name] and not overwrite:
            console.print(
                f"[yellow]⚠️  {entry.name} v{entry.version} already exists in registry. "
                f"Use --force to overwrite.[/yellow]"
            )
            return False

        now = datetime.utcnow().isoformat(timespec="seconds")
        entry.published_at = self._catalog[entry.name].get(entry.version, entry).published_at or now
        entry.updated_at = now

        self._catalog[entry.name][entry.version] = entry
        self._save()
        console.print(f"[green]✅ Published {entry.name} v{entry.version} to registry[/green]")
        return True

    def get(self, name: str, version: Optional[str] = None) -> Optional[RegistryEntry]:
        """Get a package entry by name and optionally version.

        If version is None, returns the latest version.
        """
        versions = self._catalog.get(name)
        if not versions:
            return None
        if version:
            return versions.get(version)
        # Return latest by version string (assuming semver)
        return versions.get(max(versions.keys(), key=lambda v: [int(x) for x in v.split(".")]))

    def list_packages(self, tag: Optional[str] = None) -> List[RegistryEntry]:
        """List all registered packages, optionally filtered by tag.

        Returns the latest version of each package.
        """
        results = []
        for name, versions in self._catalog.items():
            # Latest version
            latest_ver = max(versions.keys(), key=lambda v: [int(x) for x in v.split(".")])
            entry = versions[latest_ver]
            if tag:
                if tag not in entry.tags:
                    continue
            results.append(entry)
        results.sort(key=lambda e: e.name.lower())
        return results

    def search(self, query: str) -> List[RegistryEntry]:
        """Search packages by name, description, tags, or author (case-insensitive)."""
        q = query.lower()
        results = []
        for name, versions in self._catalog.items():
            latest_ver = max(versions.keys(), key=lambda v: [int(x) for x in v.split(".")])
            entry = versions[latest_ver]
            if (
                q in entry.name.lower()
                or q in entry.description.lower()
                or q in [t.lower() for t in entry.tags]
                or q in entry.author.lower()
            ):
                results.append(entry)
        return results

    def remove(self, name: str, version: Optional[str] = None) -> bool:
        """Remove a package (or a specific version) from the registry."""
        if name not in self._catalog:
            console.print(f"[red]❌ Package '{name}' not found in registry[/red]")
            return False

        if version:
            if version not in self._catalog[name]:
                console.print(f"[red]❌ {name} v{version} not found in registry[/red]")
                return False
            del self._catalog[name][version]
            console.print(f"[green]🗑️  Removed {name} v{version}[/green]")
            if not self._catalog[name]:
                del self._catalog[name]
        else:
            del self._catalog[name]
            console.print(f"[green]🗑️  Removed '{name}' and all versions[/green]")

        self._save()
        return True

    def increment_install(self, name: str, version: str) -> None:
        """Increment the install counter for a package."""
        versions = self._catalog.get(name)
        if versions and version in versions:
            versions[version].install_count += 1
            self._save()

    def get_latest_version(self, name: str) -> Optional[str]:
        """Get the latest version string for a package."""
        versions = self._catalog.get(name)
        if not versions:
            return None
        return max(versions.keys(), key=lambda v: [int(x) for x in v.split(".")])

    def display_table(self, entries: List[RegistryEntry], title: str = "Package Registry") -> None:
        """Display package entries in a rich table."""
        if not entries:
            console.print("[yellow]No packages found.[/yellow]")
            return

        table = Table(title=title)
        table.add_column("Package", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Description", style="white", max_width=40)
        table.add_column("Author", style="yellow")
        table.add_column("Tags", style="dim")
        table.add_column("Installs", style="blue", justify="right")

        for entry in entries:
            tags = ", ".join(entry.tags[:3])
            if len(entry.tags) > 3:
                tags += "..."
            table.add_row(
                entry.name,
                entry.version,
                entry.description[:40] + ("..." if len(entry.description) > 40 else ""),
                entry.author,
                tags or "—",
                str(entry.install_count),
            )

        console.print(table)
