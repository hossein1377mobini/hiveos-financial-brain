"""
Workspace Manager — CRUD, persistence, and data isolation.

Manages multiple workspaces with:
- YAML-backed persistence per workspace
- Data isolation (separate directories per workspace)
- Member management
- Workspace-scoped resource paths
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .models import Workspace, WorkspaceMember, WorkspaceRole, WorkspaceSettings, generate_workspace_id

console = Console()

WORKSPACES_DIR = Path.home() / ".hiveos" / "workspaces"


class WorkspaceManager:
    """
    Manages workspace lifecycle and data isolation.

    Each workspace is stored as:
      ~/.hiveos/workspaces/
        <workspace-id>/
          workspace.yaml      # workspace metadata + members
          agents/             # isolated agent registry
          flows/              # isolated flow storage
          audit/              # isolated audit trail
          config/             # isolated configuration
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or WORKSPACES_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._workspaces: Dict[str, Workspace] = {}
        self._load_all()

    # ── Persistence ──────────────────────────────────────────────────

    def _workspace_path(self, workspace_id: str) -> Path:
        return self.base_dir / workspace_id

    def _metadata_path(self, workspace_id: str) -> Path:
        return self._workspace_path(workspace_id) / "workspace.yaml"

    def _load_all(self):
        """Load all workspaces from disk."""
        self._workspaces = {}
        if not self.base_dir.exists():
            return
        for d in self.base_dir.iterdir():
            if d.is_dir():
                meta = d / "workspace.yaml"
                if meta.exists():
                    try:
                        data = yaml.safe_load(meta.read_text(encoding="utf-8"))
                        if data and "workspace_id" in data:
                            ws = Workspace.from_dict(data)
                            self._workspaces[ws.workspace_id] = ws
                    except Exception as e:
                        console.print(f"[yellow]⚠️  Error loading workspace {d.name}: {e}[/yellow]")

    def _save_workspace(self, workspace: Workspace):
        """Save a single workspace metadata to disk."""
        path = self._metadata_path(workspace.workspace_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(workspace.to_dict(), f, default_flow_style=False, allow_unicode=True)

    # ── CRUD ─────────────────────────────────────────────────────────

    def create_workspace(
        self,
        name: str,
        description: str = "",
        owner: str = "",
        workspace_id: Optional[str] = None,
        settings: Optional[WorkspaceSettings] = None,
    ) -> Workspace:
        """
        Create a new workspace with isolated directories.
        
        Args:
            name: Display name for the workspace
            description: Optional description
            owner: Owner username
            workspace_id: Optional custom ID (auto-generated if not provided)
            settings: Optional custom settings
            
        Returns:
            The created Workspace
        """
        if not workspace_id:
            workspace_id = generate_workspace_id(name)
            # Ensure uniqueness
            base_id = workspace_id
            counter = 1
            while workspace_id in self._workspaces or self._workspace_path(workspace_id).exists():
                workspace_id = f"{base_id}-{counter}"
                counter += 1

        if settings is None:
            settings = WorkspaceSettings()

        workspace = Workspace(
            workspace_id=workspace_id,
            name=name,
            description=description,
            owner=owner,
            settings=settings,
            members=[],
        )

        # Add owner as member with OWNER role
        if owner:
            workspace.add_member(owner, WorkspaceRole.OWNER)
            # Auto-join the owner
            owner_member = workspace.get_member(owner)
            if owner_member:
                owner_member.joined_at = datetime.utcnow().isoformat()

        # Create isolated directories
        self._init_workspace_dirs(workspace_id)

        # Persist
        self._save_workspace(workspace)
        self._workspaces[workspace_id] = workspace

        console.print(f"[green]✅ Workspace '{name}' created (id: {workspace_id})[/green]")
        return workspace

    def _init_workspace_dirs(self, workspace_id: str):
        """Create isolated directory structure for a workspace."""
        base = self._workspace_path(workspace_id)
        dirs = ["agents", "flows", "audit", "config"]
        for d in dirs:
            (base / d).mkdir(parents=True, exist_ok=True)

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID."""
        return self._workspaces.get(workspace_id)

    def list_workspaces(self, include_inactive: bool = False) -> List[Workspace]:
        """List all workspaces."""
        if include_inactive:
            return list(self._workspaces.values())
        return [ws for ws in self._workspaces.values() if ws.active]

    def update_workspace(
        self,
        workspace_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[WorkspaceSettings] = None,
    ) -> Optional[Workspace]:
        """Update workspace metadata."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            console.print(f"[red]❌ Workspace '{workspace_id}' not found[/red]")
            return None

        if name is not None:
            ws.name = name
        if description is not None:
            ws.description = description
        if settings is not None:
            ws.settings = settings

        ws.updated_at = datetime.utcnow().isoformat()
        self._save_workspace(ws)
        console.print(f"[green]✅ Workspace '{ws.name}' updated[/green]")
        return ws

    def remove_workspace(self, workspace_id: str, permanent: bool = False) -> bool:
        """
        Remove a workspace.
        
        Args:
            workspace_id: The workspace to remove
            permanent: If True, delete all data. If False, just deactivate.
            
        Returns:
            True if successful
        """
        ws = self._workspaces.get(workspace_id)
        if not ws:
            console.print(f"[red]❌ Workspace '{workspace_id}' not found[/red]")
            return False

        if permanent:
            # Delete all data
            path = self._workspace_path(workspace_id)
            if path.exists():
                shutil.rmtree(path)
            console.print(f"[red]🗑️  Workspace '{ws.name}' permanently deleted[/red]")
        else:
            # Just deactivate
            ws.active = False
            ws.updated_at = datetime.utcnow().isoformat()
            self._save_workspace(ws)
            console.print(f"[yellow]⏸️  Workspace '{ws.name}' deactivated[/yellow]")

        if permanent:
            del self._workspaces[workspace_id]
        return True

    def activate_workspace(self, workspace_id: str) -> bool:
        """Reactivate a deactivated workspace."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            console.print(f"[red]❌ Workspace '{workspace_id}' not found[/red]")
            return False
        ws.active = True
        ws.updated_at = datetime.utcnow().isoformat()
        self._save_workspace(ws)
        console.print(f"[green]✅ Workspace '{ws.name}' reactivated[/green]")
        return True

    # ── Member Management ────────────────────────────────────────────

    def add_member(self, workspace_id: str, username: str, role: "WorkspaceRole | str" = WorkspaceRole.VIEWER) -> bool:
        """Add a member to a workspace."""
        if isinstance(role, str):
            try:
                role = WorkspaceRole(role)
            except ValueError:
                console.print(f"[red]❌ Invalid workspace role: '{role}'[/red]")
                return False
        ws = self._workspaces.get(workspace_id)
        if not ws:
            console.print(f"[red]❌ Workspace '{workspace_id}' not found[/red]")
            return False
        if ws.has_member(username):
            console.print(f"[yellow]⚠️  '{username}' is already a member of '{ws.name}'[/yellow]")
            return False
        ws.add_member(username, role)
        self._save_workspace(ws)
        console.print(f"[green]✅ Added '{username}' as '{role.value}' to '{ws.name}'[/green]")
        return True

    def remove_member(self, workspace_id: str, username: str) -> bool:
        """Remove a member from a workspace."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            console.print(f"[red]❌ Workspace '{workspace_id}' not found[/red]")
            return False
        if username == ws.owner:
            console.print(f"[red]❌ Cannot remove the owner from workspace[/red]")
            return False
        if ws.remove_member(username):
            self._save_workspace(ws)
            console.print(f"[yellow]🗑️  Removed '{username}' from '{ws.name}'[/yellow]")
            return True
        console.print(f"[yellow]⚠️  '{username}' is not a member of '{ws.name}'[/yellow]")
        return False

    def set_member_role(self, workspace_id: str, username: str, role: WorkspaceRole) -> bool:
        """Change a member's role within a workspace."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            console.print(f"[red]❌ Workspace '{workspace_id}' not found[/red]")
            return False
        member = ws.get_member(username)
        if not member:
            console.print(f"[yellow]⚠️  '{username}' is not a member of '{ws.name}'[/yellow]")
            return False
        member.workspace_role = role
        ws.updated_at = datetime.utcnow().isoformat()
        self._save_workspace(ws)
        console.print(f"[green]✅ '{username}' role changed to '{role.value}' in '{ws.name}'[/green]")
        return True

    # ── Data Isolation ───────────────────────────────────────────────

    def workspace_dir(self, workspace_id: str, subdir: str = "") -> Optional[Path]:
        """Get the isolated data directory for a workspace resource."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return None
        base = self._workspace_path(workspace_id)
        if subdir:
            return base / subdir
        return base

    def workspace_exists(self, workspace_id: str) -> bool:
        """Check if a workspace exists."""
        return workspace_id in self._workspaces

    def get_workspaces_for_user(self, username: str) -> List[Workspace]:
        """Get all workspaces a user is a member of."""
        return [
            ws for ws in self._workspaces.values()
            if ws.active and ws.has_member(username)
        ]

    # ── Display ──────────────────────────────────────────────────────

    def display_table(self, workspaces: Optional[List[Workspace]] = None, title: str = "🏢 Workspaces"):
        """Display workspaces in a rich table."""
        if workspaces is None:
            workspaces = self.list_workspaces()

        if not workspaces:
            console.print(f"[yellow]No workspaces found[/yellow]")
            return

        table = Table(title=title)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Owner", style="yellow")
        table.add_column("Members", style="green")
        table.add_column("Active", style="dim")
        table.add_column("Created", style="dim")

        for ws in workspaces:
            active_status = "✅" if ws.active else "⏸️"
            created = ws.created_at[:10] if ws.created_at else ""
            table.add_row(
                ws.workspace_id,
                ws.name,
                ws.owner,
                str(ws.member_count),
                active_status,
                created,
            )
        console.print(table)

    def display_info(self, workspace: Workspace):
        """Show detailed workspace info."""
        console.print(Panel(
            f"[bold cyan]🏢 Workspace: {workspace.name}[/bold cyan]\n\n"
            f"  [bold]ID:[/bold]          {workspace.workspace_id}\n"
            f"  [bold]Description:[/bold] {workspace.description or '—'}\n"
            f"  [bold]Owner:[/bold]       {workspace.owner or '—'}\n"
            f"  [bold]Status:[/bold]      {'✅ Active' if workspace.active else '⏸️ Inactive'}\n"
            f"  [bold]Members:[/bold]     {workspace.member_count}\n"
            f"  [bold]Created:[/bold]     {workspace.created_at[:19] if workspace.created_at else '—'}\n"
            f"  [bold]Updated:[/bold]     {workspace.updated_at[:19] if workspace.updated_at else '—'}\n\n"
            f"  [bold]Settings:[/bold]\n"
            f"    Max agents:        {workspace.settings.max_agents}\n"
            f"    Max flows:         {workspace.settings.max_flows}\n"
            f"    Max concurrent:    {workspace.settings.max_concurrent_flows}\n"
            f"    Audit retention:   {workspace.settings.retention_days}d\n"
            f"    Default delivery:  {workspace.settings.default_delivery}\n\n"
            f"  [bold]Members:[/bold]\n"
            + "\n".join(
                f"    • {m.username} — [{'🟢' if m.joined_at else '🟡'}] {m.workspace_role.value}"
                for m in workspace.members
            ) if workspace.members else "    (none)",
            width=64,
        ))
