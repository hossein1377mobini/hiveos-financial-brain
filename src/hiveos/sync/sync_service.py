"""
Sync Service — mothership-to-satellite knowledge & skill synchronization.

Builds sync packages and pushes them to registered satellite nodes.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import tarfile
import json
import io
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table

from .node_registry import NodeRegistry, SatelliteNode
from ..utils.knowledge import KnowledgeManager
from ..utils.config import ConfigManager

console = Console()

SYNC_DIR = Path.home() / ".hiveos" / "sync"


class SyncService:
    """Coordinates Mothership → Satellite knowledge/skill sync."""

    def __init__(self, registry: Optional[NodeRegistry] = None,
                 knowledge_dir: Optional[Path] = None,
                 skill_dir: Optional[Path] = None,
                 flow_dir: Optional[Path] = None):
        self.registry = registry or NodeRegistry()
        km = KnowledgeManager(knowledge_dir or Path("docs"))
        self.knowledge_dir = km.knowledge_dir
        self.skill_dir = skill_dir or Path(".")
        self.flow_dir = flow_dir or Path("prototype")
        self._sync_dir = SYNC_DIR
        self._sync_dir.mkdir(parents=True, exist_ok=True)

    def _find_skills(self) -> List[Path]:
        """Discover skill .md files in the project."""
        skills = []
        for pattern in ["*.md", "hiveos-skill.md"]:
            skills.extend(self.skill_dir.glob(pattern))
        # Filter to actual skill files (contain frontmatter)
        return [s for s in skills if s.read_text(encoding="utf-8").startswith("---")]

    def _find_flows(self) -> List[Path]:
        """Discover flow YAML files."""
        if self.flow_dir.exists():
            return list(self.flow_dir.rglob("*.yml"))
        return []

    def _find_knowledge(self) -> List[Path]:
        """Discover knowledge documents."""
        if self.knowledge_dir.exists():
            return list(self.knowledge_dir.rglob("*.md"))
        return []

    def build_sync_package(self, include_skills: bool = True,
                           include_knowledge: bool = True,
                           include_flows: bool = True) -> Optional[Path]:
        """Build a sync package (.tar.gz) with selected assets.

        Returns path to the generated package, or None if nothing to package.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        package_path = self._sync_dir / f"hiveos-sync-{timestamp}.tar.gz"

        files_to_package = {}

        if include_skills:
            skills = self._find_skills()
            if skills:
                files_to_package["skills"] = skills
                console.print(f"   📚 Found {len(skills)} skill(s)")

        if include_knowledge:
            knowledge = self._find_knowledge()
            if knowledge:
                files_to_package["knowledge"] = knowledge
                console.print(f"   📖 Found {len(knowledge)} knowledge doc(s)")

        if include_flows:
            flows = self._find_flows()
            if flows:
                files_to_package["flows"] = flows
                console.print(f"   🔄 Found {len(flows)} flow(s)")

        if not files_to_package:
            console.print("[yellow]   ⚠️  Nothing to sync[/yellow]")
            return None

        # Create the manifest
        manifest = {
            "type": "hiveos-sync",
            "version": "0.1.0",
            "created_at": datetime.utcnow().isoformat(),
            "contents": {k: len(v) for k, v in files_to_package.items()},
        }

        with tarfile.open(package_path, "w:gz") as tar:
            # Write manifest
            manifest_info = tarfile.TarInfo(name="manifest.json")
            manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
            manifest_info.size = len(manifest_bytes)
            tar.addfile(manifest_info, io.BytesIO(manifest_bytes))

            # Write each asset
            for category, files in files_to_package.items():
                for fpath in files:
                    arcname = f"{category}/{fpath.name}"
                    tar.add(str(fpath), arcname=arcname)

        console.print(f"   [green]📦 Sync package built: {package_path}[/green]")
        return package_path

    def _push_to_node(self, node: SatelliteNode, package_path: Path) -> Dict[str, Any]:
        """Push a sync package to a satellite node via HTTP POST.

        Uses multipart/form-data to send the tar.gz file.
        Falls back gracefully if the node is unreachable.
        """
        import urllib.request
        import uuid

        boundary = uuid.uuid4().hex
        endpoint = f"{node.url}/api/v1/hiveos/sync"

        # Build multipart body
        package_data = package_path.read_bytes()
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="package"; filename="{package_path.name}"\r\n'
            f"Content-Type: application/gzip\r\n\r\n"
        ).encode("utf-8") + package_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {node.api_key}",
        }

        try:
            req = urllib.request.Request(
                endpoint, data=body, headers=headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                response_data = resp.read().decode("utf-8")
                return {
                    "node": node.name,
                    "status": "success",
                    "http_status": resp.status,
                    "response": response_data[:500],
                }
        except Exception as e:
            return {
                "node": node.name,
                "status": "failed",
                "error": str(e),
            }

    def pull_from_node(self, node_name: str) -> bool:
        """Pull updates from a satellite node (placeholder for future)."""
        console.print(f"   [yellow]⏳ Pull from '{node_name}' not yet implemented[/yellow]")
        return False

    def push_to_all(self, node_names: Optional[List[str]] = None,
                    include_skills: bool = True,
                    include_knowledge: bool = True,
                    include_flows: bool = True,
                    dry_run: bool = False) -> List[Dict[str, Any]]:
        """Build and push sync package to one or all registered nodes.

        Args:
            node_names: Specific nodes to push to (None = all nodes).
            include_skills: Include skill files in sync.
            include_knowledge: Include knowledge docs in sync.
            include_flows: Include flow YAML files in sync.
            dry_run: If True, only show what would be pushed without sending.

        Returns:
            List of results per node.
        """
        # Build the package
        package_path = self.build_sync_package(
            include_skills=include_skills,
            include_knowledge=include_knowledge,
            include_flows=include_flows,
        )
        if package_path is None:
            return []

        # Determine target nodes
        if node_names:
            nodes = []
            for n in node_names:
                node = self.registry.get(n)
                if node:
                    nodes.append(node)
                else:
                    console.print(f"   [red]❌ Unknown node '{n}'[/red]")
            if not nodes:
                console.print("[red]❌ No valid nodes specified[/red]")
                return []
        else:
            nodes = self.registry.list()
            if not nodes:
                console.print("[yellow]⚠️  No satellites registered. Register one with:\n"
                              "   hive mothership node register <name> <url>[/yellow]")
                return []

        console.print(f"\n[bold cyan]📡 Pushing to {len(nodes)} satellite(s)...[/bold cyan]")

        if dry_run:
            console.print("[yellow]   🏁 Dry-run mode — no packages sent[/yellow]")
            results = []
            for node in nodes:
                console.print(f"   [dim]📤 Would push to '{node.name}' at {node.url}[/dim]")
                results.append({"node": node.name, "status": "dry_run"})
            console.print(f"\n[green]✅ Dry-run complete. {len(nodes)} node(s) would receive sync[/green]")
            return results

        # Push sequentially (parallel in future)
        results = []
        for node in nodes:
            console.print(f"   📤 Pushing to '{node.name}' at {node.url}...")
            result = self._push_to_node(node, package_path)
            results.append(result)
            if result["status"] == "success":
                console.print(f"   [green]✅ Synced to '{node.name}'[/green]")
                self.registry.update_heartbeat(node.name)
            else:
                console.print(f"   [red]❌ Failed to sync to '{node.name}': {result.get('error', 'unknown')}[/red]")

        # Summary
        success_count = sum(1 for r in results if r["status"] == "success")
        console.print(f"\n[bold]📡 Sync summary:[/bold] {success_count}/{len(results)} nodes successful")
        return results

    def status(self) -> Dict[str, Any]:
        """Show sync status summary."""
        nodes = self.registry.list()
        skills = self._find_skills()
        knowledge = self._find_knowledge()
        flows = self._find_flows()

        return {
            "nodes": len(nodes),
            "skills": len(skills),
            "knowledge_docs": len(knowledge),
            "flows": len(flows),
            "online_nodes": sum(1 for n in nodes if n.status == "online"),
        }

    def preview(self, include_skills: bool = True,
                include_knowledge: bool = True,
                include_flows: bool = True) -> Dict[str, List[str]]:
        """Preview what would be synced without building a package."""
        result = {}
        if include_skills:
            result["skills"] = [s.name for s in self._find_skills()]
        if include_knowledge:
            result["knowledge"] = [str(k.relative_to(self.knowledge_dir))
                                   for k in self._find_knowledge()]
        if include_flows:
            result["flows"] = [str(f.name) for f in self._find_flows()]
        return result
