"""
CLI main entry point.
"""

import json
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
from ..engine import FlowEngine
from ..dsl import Flow, Agent, Trigger, TriggerType
from ..utils.validator import FlowValidator
from ..package import PackageBuilder, PackageInstaller, create_manifest_yaml, Manifest
from ..registry import PackageRegistry, RegistryEntry, RemoteRegistryClient
from ..utils.knowledge import KnowledgeManager
from ..utils.config import ConfigManager
from ..sync import NodeRegistry, SyncService, SYNC_DIR
from ..mothership.communication_bus import MessageType, MessagePriority
from ..mothership.task_router import RouteStrategy
from ..rbac import RBACManager, User, Permission, Resource, Action

console = Console()

BANNER = """\
╔══════════════════════════════════════╗
║           HiveOS v0.10.0             ║
║    Multi-Agent Operating System      ║
╚══════════════════════════════════════╝"""

def _load_config():
    config = ConfigManager()
    return config

def _get_engine(config=None):
    if config is None:
        config = _load_config()
    knowledge_dir = Path(config.get("knowledge_dir", "docs"))
    if not knowledge_dir.is_absolute():
        knowledge_dir = Path.cwd() / knowledge_dir
    return FlowEngine(knowledge_dir=knowledge_dir)

def _get_validator():
    return FlowValidator()


@click.group()
@click.option('--version', is_flag=True, help='Show version and exit')
def hive(version):
    """🐝 HiveOS - Multi-Agent Operating System
    
    Orchestrate teams of AI agents with declarative YAML workflows.
    """
    if version:
        rprint(Panel("[bold cyan]HiveOS v0.10.0[/bold cyan]\n"
                     "Multi-Agent Operating System", width=50))
        raise SystemExit(0)


@hive.group()
def flow():
    """Manage and run flows."""
    pass

@flow.command()
@click.argument('flow-file', type=click.Path(exists=True))
@click.option('--validate', is_flag=True, help='Only validate, do not run')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--resume', is_flag=True, help='Resume from last saved state')
def run(flow_file, validate, verbose, resume):
    """Run a flow from a DSL YAML file."""
    rprint("[bold cyan]🐝 HiveOS Flow Engine[/bold cyan]")

    file_path = Path(flow_file).resolve()

    # Validate first
    validator = _get_validator()
    errors = validator.validate_file(file_path)

    if errors:
        console.print("[red]❌ Flow validation failed:[/red]")
        for err in errors:
            console.print(f"  • {err}")
        raise SystemExit(1)

    console.print(f"[green]✅ Flow file is valid:[/green] {file_path}")

    if validate:
        return

    if resume:
        console.print("[yellow]📂 Resume mode enabled — will skip completed agents.[/yellow]")

    # Load and run
    engine = _get_engine(None)

    try:
        flow = engine.load_flow(file_path)
        result = engine.execute_flow(flow, resume=resume)
    except Exception as e:
        console.print(f"[red]❌ Flow execution failed: {e}[/red]")
        raise SystemExit(1)


@flow.command()
@click.argument('directory', type=click.Path(exists=True))
def validate(directory):
    """Validate all flows in a directory."""
    console.print("[bold cyan]🔍 Validating flows...[/bold cyan]")
    
    dir_path = Path(directory)
    validator = _get_validator()
    total_errors = 0
    total_files = 0
    
    for f in dir_path.rglob("*.yml"):
        if f.name.startswith("."):
            continue
        total_files += 1
        errors = validator.validate_file(f)
        if errors:
            total_errors += len(errors)
            console.print(f"[red]✗[/red] {f.relative_to(dir_path)}")
            for err in errors:
                console.print(f"    • {err}")
        else:
            console.print(f"[green]✓[/green] {f.relative_to(dir_path)}")
    
    if total_files == 0:
        console.print("[yellow]No flow files found.[/yellow]")
    else:
        console.print(f"\n[bold]Summary:[/bold] {total_files} files, "
                     f"{'[red]' + str(total_errors) + ' errors[/red]' if total_errors else '[green]all valid[/green]'}")


@flow.command("list")
def list_flows():
    """List available flows."""
    # TODO: scan configured flow directories
    table = Table(title="Available Flows")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="white")
    table.add_column("Agents", style="green")
    
    flow_dir = Path.cwd() / "prototype"
    if flow_dir.exists():
        for f in flow_dir.rglob("*.yml"):
            if f.name.startswith("."):
                continue
            # Quick count of agents
            import yaml
            try:
                data = yaml.safe_load(f.read_text())
                agent_count = len(data.get("agents", []))
                table.add_row(data.get("name", f.stem), 
                            str(f.relative_to(Path.cwd())),
                            str(agent_count))
            except:
                table.add_row(f.stem, str(f.relative_to(Path.cwd())), "?")
    
    console.print(table)


@flow.command()
@click.argument('flow-file', type=click.Path(exists=True), required=False)
def state(flow_file):
    """Show persisted state for a flow (or list all)."""
    engine = _get_engine(None)

    if flow_file:
        file_path = Path(flow_file).resolve()
        flow = engine.load_flow(file_path)
        persisted = engine._load_state(flow.name)
        if persisted is None:
            console.print(f"[yellow]No saved state for '{flow.name}'[/yellow]")
            return
        console.print(f"[bold cyan]📊 State for flow:[/bold cyan] {flow.name}")
        status_colors = {
            "completed": "green",
            "completed_with_errors": "yellow",
            "completed_with_skipped": "yellow",
            "running": "cyan",
            "failed": "red",
        }
        status_color = status_colors.get(persisted["status"], "yellow")
        console.print(f"   Status: [{status_color}]{persisted['status']}[/]")
        console.print(f"   Started: {persisted.get('start_time', '?')}")
        if persisted.get('end_time'):
            console.print(f"   Ended: {persisted['end_time']}")
        agent_count = len(persisted.get('agents', {}))
        status_counts = {}
        for a in persisted['agents'].values():
            s = a.get('status', 'unknown')
            status_counts[s] = status_counts.get(s, 0) + 1
        completed_agents = status_counts.get('completed', 0)
        parts = [f"{completed_agents}/{agent_count} completed"]
        if 'skipped' in status_counts:
            parts.append(f"{status_counts['skipped']} ⏩ skipped")
        if 'failed' in status_counts:
            parts.append(f"{status_counts['failed']} ❌ failed")
        if 'error' in status_counts:
            parts.append(f"{status_counts['error']} ⚠️ error")
        if 'timeout' in status_counts:
            parts.append(f"{status_counts['timeout']} ⏰ timeout")
        console.print(f"   Agents: {', '.join(parts)}")
        # Show raw JSON path
        sfile = engine._state_file(flow.name)
        console.print(f"   File: {sfile}")
    else:
        # List all state directories
        state_root = engine.state_root
        if not state_root.exists():
            console.print("[yellow]No state directories found.[/yellow]")
            return
        from rich.table import Table
        table = Table(title="Persisted Flow States")
        table.add_column("Flow Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Agents", style="white")
        table.add_column("State File", style="dim")
        for d in sorted(state_root.iterdir()):
            if d.is_dir():
                sfile = d / "state.json"
                if sfile.exists():
                    try:
                        data = json.loads(sfile.read_text(encoding="utf-8"))
                        agent_count = len(data.get("agents", {}))
                        completed = sum(1 for a in data["agents"].values() if a.get("status") == "completed")
                        skipped = sum(1 for a in data["agents"].values() if a.get("status") == "skipped")
                        failed = sum(1 for a in data["agents"].values() if a.get("status") in ("failed", "error", "timeout"))
                        status_parts = [f"{completed}/{agent_count}"]
                        if failed:
                            status_parts.append(f"{failed}❌")
                        if skipped:
                            status_parts.append(f"{skipped}⏩")
                        table.add_row(
                            d.name,
                            f"[{'green' if data['status'] == 'completed' else 'yellow'}]{data['status']}[/]",
                            " ".join(status_parts),
                            str(sfile),
                        )
                    except:
                        table.add_row(d.name, "[red]corrupt[/red]", "?", str(sfile))
        console.print(table)


@flow.command()
@click.argument('flow-file', type=click.Path(exists=True))
def clear_state(flow_file):
    """Delete persisted state for a flow."""
    file_path = Path(flow_file).resolve()
    engine = _get_engine(None)
    flow = engine.load_flow(file_path)
    engine.clear_state(flow.name)
    console.print(f"[green]✅ State cleared for '{flow.name}'[/green]")


@hive.group()
def package():
    """Package management commands."""
    pass

@package.command()
@click.argument('source-dir', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output path')
@click.option('--name', help='Package name')
@click.option('--version', help='Package version')
@click.option('--author', help='Package author')
def build(source_dir, output, name, version, author):
    """Build a package from source directory."""
    source_path = Path(source_dir).resolve()
    
    if not (source_path / "flows").exists():
        # Create the required structure
        (source_path / "flows").mkdir(parents=True, exist_ok=True)
        (source_path / "skills").mkdir(exist_ok=True)
        (source_path / "knowledge").mkdir(exist_ok=True)
        (source_path / "config").mkdir(exist_ok=True)
        
    builder = PackageBuilder(source_path)
    
    # Set output path
    if not output:
        output = source_path.parent / f"{source_path.name}.tar.gz"
    else:
        output = Path(output)
    
    result = builder.build(output)
    console.print(f"[green]✅ Package built: {result}[/green]")


@package.command()
@click.argument('package-file', type=click.Path(exists=True))
def install(package_file):
    """Install a HiveOS package."""
    installer = PackageInstaller()
    manifest = installer.install(Path(package_file))
    console.print(f"[green]✅ Package '{manifest.name}' v{manifest.version} installed![/green]")
    # Sync install count with registry
    reg = PackageRegistry()
    reg.increment_install(manifest.name, manifest.version)


@package.command("list")
def list_packages():
    """List installed packages."""
    installer = PackageInstaller()
    packages = installer.list_packages()
    
    if not packages:
        console.print("[yellow]No packages installed.[/yellow]")
        return
    
    table = Table(title="Installed Packages")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")
    
    for pkg in packages:
        table.add_row(pkg.name, pkg.version, pkg.description)
    
    console.print(table)


@package.command()
@click.argument('source-dir', type=click.Path(exists=True))
@click.option('--name', prompt=True, help='Package name')
@click.option('--version', default='0.5.0', help='Package version')
@click.option('--author', prompt=True, help='Package author')
@click.option('--description', prompt=True, help='Package description')
@click.option('--tags', help='Comma-separated tags')
@click.option('--force', is_flag=True, help='Overwrite existing registry entry')
def publish(source_dir, name, version, author, description, tags, force):
    """Publish a package directory to the local registry."""
    source_path = Path(source_dir).resolve()
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    # Build the tar.gz package first
    builder = PackageBuilder(source_path)
    output = source_path.parent / f"{name}-{version}.tar.gz"
    builder.build(output)

    # Read flows from the source
    flow_dir = source_path / "flows"
    flows = sorted(f.name for f in flow_dir.glob("*.yml")) if flow_dir.exists() else []

    # Publish to registry
    entry = RegistryEntry(
        name=name,
        version=version,
        description=description,
        author=author,
        tags=tag_list,
        flows=flows,
        source_url=str(output.resolve()),
    )
    reg = PackageRegistry()
    success = reg.publish(entry, overwrite=force)
    if success:
        console.print()
        console.print(Panel(
            f"[bold green]📦 {name} v{version}[/bold green]\n\n"
            f"  Author:     {author}\n"
            f"  Tags:       {', '.join(tag_list) or '—'}\n"
            f"  Package:    {output}\n"
            f"  Registry:   ~/.hiveos/registry/catalog.yaml\n\n"
            f"  Install:    [cyan]hive package install {output}[/cyan]\n"
            f"  Discover:   [cyan]hive registry search {name}[/cyan]",
            width=60,
        ))


@hive.group()
def registry():
    """📦 Package registry — discover, search, manage packages."""
    pass


@registry.command("list")
@click.option('--tag', help='Filter by tag')
def registry_list(tag):
    """List published packages in the registry."""
    reg = PackageRegistry()
    entries = reg.list_packages(tag=tag)
    reg.display_table(entries, title="📦 Published Packages")


@registry.command()
@click.argument('query')
def search(query):
    """Search published packages by name, description, tag, or author."""
    reg = PackageRegistry()
    results = reg.search(query)
    if results:
        reg.display_table(results, title=f"🔍 Search: '{query}'")
    else:
        console.print(f"[yellow]No packages found for '{query}'[/yellow]")


@registry.command()
@click.argument('name')
@click.argument('version', required=False)
def info(name, version):
    """Show detailed info about a published package."""
    reg = PackageRegistry()
    entry = reg.get(name, version)
    if entry is None:
        console.print(f"[red]❌ Package '{name}' not found in registry[/red]")
        return

    console.print(Panel(
        f"[bold cyan]📦 {entry.name} v{entry.version}[/bold cyan]\n\n"
        f"  [bold]Description:[/bold]  {entry.description}\n"
        f"  [bold]Author:[/bold]       {entry.author}\n"
        f"  [bold]Tags:[/bold]         {', '.join(entry.tags) or '—'}\n"
        f"  [bold]Flows:[/bold]        {', '.join(entry.flows) or '—'}\n"
        f"  [bold]Dependencies:[/bold] {', '.join(entry.dependencies) or '—'}\n"
        f"  [bold]Published:[/bold]    {entry.published_at}\n"
        f"  [bold]Updated:[/bold]      {entry.updated_at}\n"
        f"  [bold]Installs:[/bold]     {entry.install_count}\n"
        f"  [bold]Source:[/bold]       {entry.source_url or '—'}\n"
        f"  [bold]Requires:[/bold]     HiveOS {entry.requires_hiveos_version}",
        width=64,
    ))


@registry.command()
@click.argument('name')
@click.option('--version', help='Remove a specific version only')
def remove(name, version):
    """Remove a package (or version) from the registry."""
    reg = PackageRegistry()
    reg.remove(name, version)


@registry.command()
def verify():
    """Verify registry integrity — check for missing/corrupt entries."""
    reg = PackageRegistry()
    entries = reg.list_packages()
    errors = 0

    for entry in entries:
        # Check source file exists
        if entry.source_url:
            src = Path(entry.source_url)
            if not src.exists():
                console.print(f"[yellow]⚠️  {entry.name} v{entry.version}: source file missing: {src}[/yellow]")
                errors += 1

        # Check required fields
        if not entry.name or not entry.version:
            console.print(f"[red]❌ Corrupt entry: name='{entry.name}' version='{entry.version}'[/red]")
            errors += 1

    if errors == 0:
        console.print(f"[green]✅ Registry verified — {len(entries)} package(s) OK[/green]")
    else:
        console.print(f"[yellow]⚠️  {errors} issue(s) found in registry[/yellow]")


@hive.group()
def util():
    """Utility commands."""
    pass

@util.command()
def init():
    """Initialize a new HiveOS project in the current directory."""
    cwd = Path.cwd()
    
    dirs = ["flows", "skills", "knowledge", "config", "prototype"]
    for d in dirs:
        (cwd / d).mkdir(exist_ok=True)
    
    # Create .gitkeep files
    for d in dirs:
        gitkeep = cwd / d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")
    
    # Create initial config
    config = ConfigManager(cwd / "config" / "hiveos.yaml")
    
    # Create example flow
    example = cwd / "flows" / "hello-world.yml"
    if not example.exists():
        example.write_text("""# Hello Flow
name: "Hello World"
description: "A simple hello flow"
version: "0.5.0"

trigger:
  type: manual

agents:
  - id: greeter
    name: "Greeter"
    skills:
      - text-generation
    output: greeting.txt

deliver:
  to: origin
  format: markdown
""")
    
    # Initialize global data directory
    from ..storage.engine import StorageEngine
    data_dir = Path.home() / ".hiveos" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    console.print("[green]✅ HiveOS project initialized![/green]")
    console.print(f"\nProject structure created at: {cwd}")
    console.print(f"Global data directory: {data_dir}")
    console.print("\nNext steps:")
    console.print("  1. Edit flows/hello-world.yml")
    console.print("  2. Run: [cyan]hive flow run flows/hello-world.yml[/cyan]")
    console.print("  3. Package: [cyan]hive package build .[/cyan]")


@util.command()
def info():
    """Show HiveOS environment information."""
    config = _load_config()
    
    console.print(Panel("[bold cyan]🐝 HiveOS Information[/bold cyan]", width=60))
    
    info_table = Table.grid(padding=(0, 2))
    info_table.add_column("Key", style="bold yellow")
    info_table.add_column("Value", style="white")
    
    import sys
    info_table.add_row("Version", "0.9.2")
    info_table.add_row("Python", sys.version.split()[0])
    info_table.add_row("Config Path", str(config.config_path))
    info_table.add_row("Working Dir", str(Path.cwd()))
    
    console.print(info_table)
    console.print()


# ── Mothership Commands ──────────────────────────────────────────────

@hive.group()
def mothership():
    """🌍 Mothership orchestration — satellites, sync, registry."""
    pass


@mothership.group()
def node():
    """Manage satellite nodes."""
    pass


@node.command(name="register")
@click.argument("name")
@click.argument("url")
@click.option("--api-key", help="API key for satellite authentication")
@click.option("--description", help="Node description")
@click.option("--capabilities", help="Comma-separated capabilities")
def node_register(name, url, api_key, description, capabilities):
    """Register a satellite node with the Mothership."""
    registry = NodeRegistry()
    cap_list = [c.strip() for c in capabilities.split(",")] if capabilities else None
    registry.register(
        name=name,
        url=url,
        api_key=api_key or "",
        description=description or "",
        capabilities=cap_list,
    )


@node.command(name="list")
def node_list():
    """List all registered satellite nodes."""
    registry = NodeRegistry()
    nodes = registry.list()

    if not nodes:
        console.print("[yellow]No satellites registered.[/yellow]")
        console.print("  Register one: [cyan]hive mothership node register <name> <url>[/cyan]")
        return

    table = Table(title="🌍 Registered Satellites")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="white")
    table.add_column("Status", style="green")
    table.add_column("Last Seen", style="dim")
    table.add_column("Capabilities", style="yellow")

    for n in nodes:
        status_style = {"online": "green", "offline": "red", "unknown": "yellow"}
        s = f"[{status_style.get(n.status, 'yellow')}]{n.status}[/]"
        last_seen = n.last_seen[:19] if n.last_seen else "—"
        caps = ", ".join(n.capabilities[:3]) if n.capabilities else "—"
        if len(n.capabilities) > 3:
            caps += "..."
        table.add_row(n.name, n.url, s, last_seen, caps)

    console.print(table)


@node.command(name="remove")
@click.argument("name")
def node_remove(name):
    """Remove a registered satellite node."""
    registry = NodeRegistry()
    registry.remove(name)


@mothership.command()
@click.option("--nodes", help="Comma-separated node names (default: all)")
@click.option("--no-skills", is_flag=True, help="Exclude skills from sync")
@click.option("--no-knowledge", is_flag=True, help="Exclude knowledge docs from sync")
@click.option("--no-flows", is_flag=True, help="Exclude flows from sync")
@click.option("--dry-run", is_flag=True, help="Show what would be synced without sending")
def sync(nodes, no_skills, no_knowledge, no_flows, dry_run):
    """Sync skills, knowledge, and flows to satellite nodes."""
    config = _load_config()
    knowledge_dir = Path(config.get("knowledge_dir", "docs"))
    if not knowledge_dir.is_absolute():
        knowledge_dir = Path.cwd() / knowledge_dir

    registry = NodeRegistry()
    service = SyncService(
        registry=registry,
        knowledge_dir=knowledge_dir,
        flow_dir=Path.cwd() / "prototype",
    )

    node_names = [n.strip() for n in nodes.split(",")] if nodes else None

    if dry_run:
        console.print("[yellow]🏁 Dry-run mode[/yellow]")
        preview = service.preview(
            include_skills=not no_skills,
            include_knowledge=not no_knowledge,
            include_flows=not no_flows,
        )
        for category, items in preview.items():
            console.print(f"  [bold]{category}:[/bold] {len(items)} file(s)")
            for item in items:
                console.print(f"    • {item}")

    service.push_to_all(
        node_names=node_names,
        include_skills=not no_skills,
        include_knowledge=not no_knowledge,
        include_flows=not no_flows,
        dry_run=dry_run,
    )


@mothership.command()
def preview():
    """Preview what would be synced to satellites."""
    config = _load_config()
    knowledge_dir = Path(config.get("knowledge_dir", "docs"))
    if not knowledge_dir.is_absolute():
        knowledge_dir = Path.cwd() / knowledge_dir

    service = SyncService(
        registry=NodeRegistry(),
        knowledge_dir=knowledge_dir,
        flow_dir=Path.cwd() / "prototype",
    )
    preview_data = service.preview()

    console.print("[bold cyan]📋 Sync Preview[/bold cyan]")
    for category, items in preview_data.items():
        console.print(f"\n[bold]{category.upper()}[/bold] ({len(items)})")
        for item in items:
            console.print(f"  • {item}")

    if not any(preview_data.values()):
        console.print("[yellow]Nothing to sync.[/yellow]")


@mothership.command(name="info")
def mothership_info():
    """Show Mothership status summary."""
    registry = NodeRegistry()
    service = SyncService(
        registry=registry,
        knowledge_dir=Path.cwd() / "docs",
        flow_dir=Path.cwd() / "prototype",
    )
    status = service.status()

    config = _load_config()

    panel = Panel(
        f"[bold cyan]🌍 Mothership Status[/bold cyan]\n\n"
        f"  [bold]Satellites:[/bold]     {status['nodes']} registered ({status['online_nodes']} online)\n"
        f"  [bold]Skills:[/bold]         {status['skills']} available\n"
        f"  [bold]Knowledge Docs:[/bold] {status['knowledge_docs']} available\n"
        f"  [bold]Flows:[/bold]          {status['flows']} available\n"
        f"  [bold]Sync Packages:[/bold]  {len(list(SYNC_DIR.glob('*.tar.gz')))} cached",
        width=60,
    )
    console.print(panel)


# ── Enhanced Mothership Commands (Phase 4) ─────────────────────────────

# Import new components lazily to avoid circular imports
def _get_agent_registry():
    from ..mothership.agent_registry import AgentRegistry, CapabilityDeclaration
    return AgentRegistry()

def _get_task_router():
    from ..mothership.task_router import TaskRouter, RouteStrategy
    registry = _get_agent_registry()
    return TaskRouter(registry=registry, default_strategy=RouteStrategy.BEST_FIT)

def _get_comm_bus():
    from ..mothership.communication_bus import CommunicationBus, InMemoryBusBackend
    return CommunicationBus(backend=InMemoryBusBackend())

def _get_resilience():
    from ..mothership.resilience import ResilienceEngine
    registry = _get_agent_registry()
    router = _get_task_router()
    bus = _get_comm_bus()
    return ResilienceEngine(registry=registry, task_router=router, comm_bus=bus)

def _get_server():
    from ..mothership.server import MothershipServer
    from ..sync import NodeRegistry as LegacyNodeRegistry
    registry = _get_agent_registry()
    router = _get_task_router()
    bus = _get_comm_bus()
    resilience = _get_resilience()
    rbac = _get_rbac()
    audit = _get_audit()
    return MothershipServer(
        registry=registry,
        task_router=router,
        bus=bus,
        resilience=resilience,
        health_checker=resilience.health_checker,
        node_registry=LegacyNodeRegistry(),
        rbac=rbac,
        audit_trail=audit,
    )


def _get_rbac():
    """Get RBACManager instance."""
    config = _load_config()
    data_dir = Path(config.get("rbac.data_dir", str(Path.home() / ".hiveos")))
    return RBACManager(data_dir=data_dir)


def _get_audit():
    """Get AuditTrail instance."""
    from ..audit import AuditTrail
    return AuditTrail()


@mothership.group()
def agent():
    """Manage enhanced agent nodes with capabilities."""
    pass


@agent.command(name="register")
@click.argument("name")
@click.argument("url")
@click.option("--api-key", help="API key for agent authentication")
@click.option("--description", help="Agent description")
@click.option("--capability", "capabilities", multiple=True, help="Capability (can repeat: name:version:desc)")
@click.option("--max-concurrent", default=5, help="Max concurrent tasks")
def agent_register(name, url, api_key, description, capabilities, max_concurrent):
    """Register an agent node with structured capabilities."""
    from ..mothership.agent_registry import CapabilityDeclaration
    registry = _get_agent_registry()
    caps = {}
    for c in capabilities:
        parts = c.split(":")
        cap_name = parts[0]
        version = parts[1] if len(parts) > 1 else "1.0.0"
        desc = parts[2] if len(parts) > 2 else ""
        caps[cap_name] = CapabilityDeclaration(name=cap_name, version=version, description=desc)

    registry.register(
        name=name,
        url=url,
        api_key=api_key or "",
        description=description or "",
        capabilities=caps,
        max_concurrent=max_concurrent,
    )


@agent.command(name="list")
@click.option("--status", help="Filter by status (online, offline, degraded, unknown)")
@click.option("--capability", help="Filter by capability name")
def agent_list(status, capability):
    """List all registered agents."""
    registry = _get_agent_registry()
    agents = registry.list()

    if status:
        agents = [a for a in agents if a.status == status]
    if capability:
        agents = [a for a in agents if capability in a.capabilities]

    if not agents:
        console.print("[yellow]No agents found.[/yellow]")
        return

    from rich.table import Table
    table = Table(title="🤖 Registered Agents")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="white")
    table.add_column("Status", style="green")
    table.add_column("Capabilities", style="yellow")
    table.add_column("Load", style="white")
    table.add_column("Tasks", style="dim")

    for a in agents:
        status_style = {"online": "green", "degraded": "yellow", "offline": "red", "unknown": "dim"}
        s = f"[{status_style.get(a.status, 'dim')}]{a.status}[/]"
        caps = ", ".join(a.capabilities.keys()) if a.capabilities else "—"
        if len(caps) > 30:
            caps = caps[:30] + "..."
        table.add_row(
            a.name,
            a.url,
            s,
            caps,
            f"{a.current_load}/{a.max_concurrent}",
            f"✓{a.total_tasks_completed} ✗{a.total_errors}",
        )

    console.print(table)


@agent.command(name="info")
@click.argument("name")
def agent_info(name):
    """Show detailed info about an agent."""
    registry = _get_agent_registry()
    agent = registry.get(name)
    if not agent:
        console.print(f"[red]❌ Agent '{name}' not found[/red]")
        return

    from rich.panel import Panel
    caps_str = ""
    if agent.capabilities:
        for cap_name, cap in agent.capabilities.items():
            caps_str += f"  • {cap_name} (v{cap.version}): {cap.description or '—'}\n"
    else:
        caps_str = "  —"

    panel = Panel(
        f"[bold cyan]🤖 Agent: {agent.name}[/bold cyan]\n\n"
        f"  [bold]URL:[/bold]              {agent.url}\n"
        f"  [bold]Status:[/bold]           {agent.status}\n"
        f"  [bold]Description:[/bold]      {agent.description or '—'}\n"
        f"  [bold]Max Concurrent:[/bold]   {agent.max_concurrent}\n"
        f"  [bold]Current Load:[/bold]     {agent.current_load}\n"
        f"  [bold]Load Factor:[/bold]      {agent.current_load / max(1, agent.max_concurrent) * 100:.0f}%\n"
        f"  [bold]Tasks Completed:[/bold]  {agent.total_tasks_completed}\n"
        f"  [bold]Errors:[/bold]           {agent.total_errors}\n"
        f"  [bold]Reliability:[/bold]       {agent.total_tasks_completed / max(1, agent.total_tasks_completed + agent.total_errors) * 100:.1f}%\n"
        f"  [bold]Last Heartbeat:[/bold]   {agent.last_heartbeat or '—'}\n"
        f"  [bold]Registered:[/bold]        {agent.registered_at}\n\n"
        f"  [bold]Capabilities:[/bold]\n{caps_str}",
        width=70,
    )
    console.print(panel)


@agent.command(name="remove")
@click.argument("name")
def agent_remove(name):
    """Remove an agent from the registry."""
    registry = _get_agent_registry()
    registry.unregister(name)


@agent.command(name="capabilities")
def agent_capabilities():
    """List all capability types and how many agents provide each."""
    registry = _get_agent_registry()
    caps = registry.list_capabilities()

    if not caps:
        console.print("[yellow]No capabilities registered.[/yellow]")
        return

    from rich.table import Table
    table = Table(title="📋 Capability Inventory")
    table.add_column("Capability", style="cyan")
    table.add_column("Providers", style="green")
    table.add_column("Online", style="white")

    for cap, count in sorted(caps.items(), key=lambda x: -x[1]):
        online = sum(1 for a in registry.find_available(cap))
        table.add_row(cap, str(count), str(online))

    console.print(table)


@agent.command(name="heartbeat")
@click.argument("name")
@click.option("--load", type=int, help="Current load")
def agent_heartbeat(name, load):
    """Record a heartbeat from an agent (for testing)."""
    registry = _get_agent_registry()
    success = registry.record_heartbeat(name, load=load)
    if success:
        console.print(f"[green]✅ Heartbeat recorded for '{name}'[/green]")
    else:
        console.print(f"[red]❌ Agent '{name}' not found[/red]")


# ── Task Router Commands ────────────────────────────────────────────────

@mothership.group()
def route():
    """Task routing commands."""
    pass


@route.command(name="assign")
@click.argument("agent_id")
@click.argument("capability")
@click.option("--metadata", help="JSON metadata")
@click.option("--preferred", help="Comma-separated preferred nodes")
@click.option("--excluded", help="Comma-separated excluded nodes")
@click.option("--strategy", type=click.Choice([s.value for s in RouteStrategy]), help="Routing strategy")
def route_assign(agent_id, capability, metadata, preferred, excluded, strategy):
    """Route a task to the best available node."""
    router = _get_task_router()
    from ..mothership.task_router import RouteStrategy as RTS
    strat = RTS(strategy) if strategy else None
    pref = [n.strip() for n in preferred.split(",")] if preferred else None
    excl = [n.strip() for n in excluded.split(",")] if excluded else None
    meta = json.loads(metadata) if metadata else {}

    assignment = router.route(
        agent_id=agent_id,
        required_capability=capability,
        metadata=meta,
        preferred_nodes=pref,
        excluded_nodes=excl,
        strategy=strat,
    )

    if assignment:
        console.print(f"[green]✅ Routed to '{assignment.node_name}' ({assignment.node_url})[/green]")
        console.print(f"   Task ID: {assignment.task_id}")
        console.print(f"   Strategy: {assignment.strategy.value}")
    else:
        console.print(f"[red]❌ No available node for capability '{capability}'[/red]")


@route.command(name="reroute")
@click.argument("task_id")
@click.option("--reason", default="manual", help="Reroute reason")
def route_reroute(task_id, reason):
    """Re-route a failed task."""
    router = _get_task_router()
    assignment = router.reroute(task_id, reason=reason)
    if assignment:
        console.print(f"[green]✅ Re-routed to '{assignment.node_name}'[/green]")
    else:
        console.print("[red]❌ Could not reroute[/red]")


@route.command(name="metrics")
def route_metrics():
    """Show routing metrics."""
    router = _get_task_router()
    router.display_metrics()


@route.command(name="rules")
@click.option("--add", nargs=3, metavar="CAPABILITY STRATEGY MAX_LOAD", help="Add rule: capability strategy max_load")
@click.option("--remove", help="Remove rule by capability")
def route_rules(add, remove):
    """Manage routing rules."""
    router = _get_task_router()
    from ..mothership.task_router import RoutingRule, RouteStrategy as RTS

    if add:
        cap, strat, max_load = add
        rule = RoutingRule(
            capability=cap,
            strategy=RTS(strat),
            max_load_factor=float(max_load),
        )
        router.add_rule(rule)
        console.print(f"[green]✅ Added rule for '{cap}'[/green]")

    if remove:
        if router.remove_rule(remove):
            console.print(f"[green]🗑️ Removed rule for '{remove}'[/green]")
        else:
            console.print(f"[red]❌ No rule found for '{remove}'[/red]")


# ── Communication Bus Commands ────────────────────────────────────────

@mothership.group()
def bus():
    """Communication bus commands."""
    pass


@bus.command(name="publish")
@click.argument("msg_type", type=click.Choice([t.value for t in MessageType]))
@click.argument("payload", required=False)
@click.option("--recipient", help="Target node (default: broadcast)")
@click.option("--priority", type=click.Choice([p.name for p in MessagePriority]), default="NORMAL")
def bus_publish(msg_type, payload, recipient, priority):
    """Publish a message to the bus."""
    bus = _get_comm_bus()
    from ..mothership.communication_bus import MessageType, MessagePriority
    msg = MessageType(msg_type)
    pri = MessagePriority[priority]
    data = json.loads(payload) if payload else {}

    message = bus.publish(msg_type=msg, payload=data, recipient=recipient, priority=pri)
    console.print(f"[green]📤 Published {msg_type} (id: {message.message_id})[/green]")


@bus.command(name="subscribe")
@click.argument("msg_types", nargs=-1)
@click.option("--count", default=5, help="Number of messages to wait for")
def bus_subscribe(msg_types, count):
    """Subscribe to message types and print received messages."""
    bus = _get_comm_bus()
    from ..mothership.communication_bus import MessageType
    types = [MessageType(t) for t in msg_types] if msg_types else list(MessageType)

    received = []
    def callback(msg):
        received.append(msg)
        console.print(f"[cyan]📨 {msg.type.value} from {msg.sender}: {msg.payload}[/cyan]")

    sub_id = bus.subscribe(types, callback)
    console.print(f"[dim]Subscribed (id: {sub_id}). Waiting for {count} messages...[/dim]")

    # Wait for messages
    import time
    start = time.time()
    while len(received) < count and time.time() - start < 30:
        time.sleep(0.5)

    bus.unsubscribe(sub_id)
    console.print(f"[dim]Received {len(received)} messages.[/dim]")


@bus.command(name="stats")
def bus_stats():
    """Show bus statistics."""
    # Placeholder - would need to track in bus
    console.print("[dim]Bus stats not yet implemented[/dim]")


# ── Resilience Commands ────────────────────────────────────────────────

@mothership.group()
def health():
    """Health and resilience commands."""
    pass


@health.command(name="check")
@click.argument("node", required=False)
def health_check(node):
    """Run health check on a node or all nodes."""
    resilience = _get_resilience()
    if node:
        result = resilience.health_checker.check_node(node)
        status_style = {"healthy": "green", "degraded": "yellow", "unhealthy": "red", "unknown": "dim"}
        s = f"[{status_style.get(result.status.value, 'dim')}]{result.status.value}[/]"
        console.print(f"Health check for {node}: {s}")
        console.print(f"  Latency: {result.latency_ms:.1f}ms")
        if result.errors:
            console.print(f"  Errors: {', '.join(result.errors)}")
        console.print(f"  Details: {result.details}")
    else:
        results = resilience.health_checker.check_all()
        from rich.table import Table
        table = Table(title="🏥 Health Check Results")
        table.add_column("Node", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Latency (ms)", style="white")
        table.add_column("Errors", style="red")
        for name, result in results.items():
            status_style = {"healthy": "green", "degraded": "yellow", "unhealthy": "red", "unknown": "dim"}
            s = f"[{status_style.get(result.status.value, 'dim')}]{result.status.value}[/]"
            err_str = ", ".join(result.errors) if result.errors else "—"
            table.add_row(name, s, f"{result.latency_ms:.1f}", err_str)
        console.print(table)


@health.command(name="monitor")
@click.option("--interval", default=30, help="Check interval (seconds)")
def health_monitor(interval):
    """Start continuous health monitoring."""
    resilience = _get_resilience()
    resilience.start()
    console.print(f"[green]🏥 Health monitoring started (interval: {interval}s)[/green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    try:
        import time
        while True:
            time.sleep(interval)
            resilience.display_status()
    except KeyboardInterrupt:
        resilience.stop()
        console.print("[dim]Health monitoring stopped[/dim]")


@health.command(name="status")
def health_status():
    """Show overall resilience status."""
    resilience = _get_resilience()
    resilience.display_status()


@health.command(name="failures")
@click.option("--resolved", is_flag=True, help="Show resolved failures too")
def health_failures(resolved):
    """List detected failures."""
    resilience = _get_resilience()
    failures = resilience.failure_detector.get_failures(unresolved_only=not resolved)

    if not failures:
        console.print("[green]No failures detected.[/green]")
        return

    from rich.table import Table
    table = Table(title="🚨 Detected Failures")
    table.add_column("Node", style="cyan")
    table.add_column("Type", style="red")
    table.add_column("Severity", style="white")
    table.add_column("Description", style="white")
    table.add_column("Time", style="dim")
    table.add_column("Resolved", style="green")

    for f in failures:
        table.add_row(
            f.node_name,
            f.failure_type.value,
            f.severity,
            f.description,
            f.timestamp[:19],
            "✅" if f.resolved else "❌",
        )
    console.print(table)


@health.command(name="circuits")
def health_circuits():
    """Show circuit breaker states."""
    resilience = _get_resilience()
    status = resilience.get_status()

    from rich.table import Table
    table = Table(title="🔌 Circuit Breakers")
    table.add_column("Node", style="cyan")
    table.add_column("State", style="white")

    for node, state in status["circuit_breakers"].items():
        style = {"closed": "green", "half_open": "yellow", "open": "red"}.get(state, "white")
        table.add_row(node, f"[{style}]{state}[/]")
    console.print(table)


@health.command(name="reassignments")
def health_reassignments():
    """Show reassignment statistics."""
    resilience = _get_resilience()
    stats = resilience.reassignment_engine.get_reassignment_stats()

    console.print(f"[bold]🔄 Total Reassignments:[/bold] {stats['total_reassignments']}")
    console.print(f"[bold]Active Reassigned Tasks:[/bold] {stats['active_reassigned']}")

    if stats["by_node"]:
        from rich.table import Table
        table = Table(title="Reassignments by Node")
        table.add_column("Node", style="cyan")
        table.add_column("Count", style="white")
        for node, count in stats["by_node"].items():
            table.add_row(node, str(count))
        console.print(table)


# ── Server Commands ────────────────────────────────────────────────────

@mothership.group()
def server():
    """Mothership HTTP server commands."""
    pass


@server.command(name="start")
@click.option("--host", default="0.0.0.0", help="Bind host")
@click.option("--port", default=8080, help="Bind port")
@click.option("--foreground", is_flag=True, help="Run in foreground")
def server_start(host, port, foreground):
    """Start the Mothership HTTP server."""
    server = _get_server()
    server.host = host
    server.port = port
    server.start(background=not foreground)
    if not foreground:
        console.print("[dim]Server running in background. Use 'hive mothership server stop' to stop.[/dim]")


@server.command(name="stop")
def server_stop():
    """Stop the Mothership HTTP server."""
    # Note: This would need a way to get the running server instance
    # For now, just a placeholder
    console.print("[yellow]Server stop not yet implemented (run in foreground with Ctrl+C)[/yellow]")


@server.command(name="status")
def server_status():
    """Show server status."""
    server = _get_server()
    status = {
        "uptime": server._uptime(),
        "agents": server.registry.count(),
        "tasks_assigned": server.metrics.get("tasks_assigned", 0),
        "tasks_completed": server.metrics.get("tasks_completed", 0),
        "tasks_failed": server.metrics.get("tasks_failed", 0),
        "bus_messages": server.metrics.get("bus_messages", 0),
    }
    from rich.table import Table
    table = Table(title="🌍 Mothership Server Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    for k, v in status.items():
        table.add_row(k, str(v))
    console.print(table)


def main():
    try:
        rprint(BANNER)
        hive()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


if __name__ == "__main__":
    main()


# ── RBAC Commands ──────────────────────────────────────────────────────

@hive.group()
def rbac():
    """🔐 Role-Based Access Control."""
    pass


# ── RBAC Users ─────────────────────────────────────────────────────────

@rbac.group()
def user():
    """Manage RBAC users."""
    pass


@user.command(name="list")
def rbac_user_list():
    """List all users."""
    mgr = _get_rbac()
    users = mgr.list_users()
    if not users:
        console.print("[yellow]No users found[/yellow]")
        return
    from rich.table import Table
    table = Table(title="🔐 RBAC Users")
    table.add_column("Username", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Enabled", style="white")
    table.add_column("Email", style="dim")
    for u in users.values():
        table.add_row(u.username, u.role, "✅" if u.enabled else "❌", u.email or "-")
    console.print(table)


@user.command(name="add")
@click.argument("username")
@click.option("--role", default="viewer", help="Role name (default: viewer)")
@click.option("--api-key", help="API key (auto-generated if omitted)")
@click.option("--email", help="Email address")
def rbac_user_add(username, role, api_key, email):
    """Add a new RBAC user."""
    mgr = _get_rbac()
    existing = mgr.get_user(username)
    if existing:
        console.print(f"[red]❌ User '{username}' already exists[/red]")
        raise SystemExit(1)
    if not mgr.get_role(role):
        console.print(f"[red]❌ Role '{role}' does not exist[/red]")
        raise SystemExit(1)
    import uuid
    key = api_key or f"hive-{uuid.uuid4().hex[:16]}"
    user_obj = User(
        username=username,
        role=role,
        api_key=key,
        email=email or "",
    )
    mgr.add_user(user_obj)
    console.print(f"[green]✅ User '{username}' created (role: {role})[/green]")
    console.print(f"[dim]   API Key: {key}[/dim]")


@user.command(name="remove")
@click.argument("username")
def rbac_user_remove(username):
    """Remove an RBAC user."""
    mgr = _get_rbac()
    if mgr.remove_user(username):
        console.print(f"[green]🗑️ User '{username}' removed[/green]")
    else:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        raise SystemExit(1)


@user.command(name="set-role")
@click.argument("username")
@click.argument("role")
def rbac_user_set_role(username, role):
    """Change a user's role."""
    mgr = _get_rbac()
    if not mgr.get_role(role):
        console.print(f"[red]❌ Role '{role}' does not exist[/red]")
        raise SystemExit(1)
    if mgr.update_user_role(username, role):
        console.print(f"[green]✅ User '{username}' role set to '{role}'[/green]")
    else:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        raise SystemExit(1)


@user.command(name="set-api-key")
@click.argument("username")
@click.argument("api_key")
def rbac_user_set_api_key(username, api_key):
    """Update a user's API key."""
    mgr = _get_rbac()
    if mgr.update_user_api_key(username, api_key):
        console.print(f"[green]✅ API key updated for '{username}'[/green]")
    else:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        raise SystemExit(1)


@user.command(name="enable")
@click.argument("username")
def rbac_user_enable(username):
    """Enable a user."""
    mgr = _get_rbac()
    if mgr.enable_user(username, True):
        console.print(f"[green]✅ User '{username}' enabled[/green]")
    else:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        raise SystemExit(1)


@user.command(name="disable")
@click.argument("username")
def rbac_user_disable(username):
    """Disable a user."""
    mgr = _get_rbac()
    if mgr.enable_user(username, False):
        console.print(f"[yellow]🔒 User '{username}' disabled[/yellow]")
    else:
        console.print(f"[red]❌ User '{username}' not found[/red]")
        raise SystemExit(1)


# ── RBAC Roles ─────────────────────────────────────────────────────────

@rbac.group()
def role():
    """Manage RBAC roles."""
    pass


@role.command(name="list")
def rbac_role_list():
    """List all roles."""
    mgr = _get_rbac()
    roles = mgr.list_roles()
    if not roles:
        console.print("[yellow]No roles found[/yellow]")
        return
    from rich.table import Table
    table = Table(title="🔐 RBAC Roles")
    table.add_column("Role", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Permissions", style="dim")
    table.add_column("Built-in", style="yellow")
    for r in roles.values():
        perms = sorted(p.to_str() for p in r.permissions)
        perms_str = ", ".join(perms[:5])
        if len(perms) > 5:
            perms_str += f" ... (+{len(perms)-5})"
        table.add_row(r.name, r.description, perms_str, "✅" if r.is_builtin else "❌")
    console.print(table)


@role.command(name="show")
@click.argument("role_name")
def rbac_role_show(role_name):
    """Show role details."""
    mgr = _get_rbac()
    r = mgr.get_role(role_name)
    if not r:
        console.print(f"[red]❌ Role '{role_name}' not found[/red]")
        raise SystemExit(1)
    console.print(f"[bold]🔐 Role:[/bold] {r.name}")
    console.print(f"[bold]Description:[/bold] {r.description or '-'}")
    console.print(f"[bold]Built-in:[/bold] {'✅' if r.is_builtin else '❌'}")
    console.print("")
    perms = sorted(p.to_str() for p in r.permissions)
    console.print(f"[bold]Permissions ({len(perms)}):[/bold]")
    for p in perms:
        console.print(f"  • {p}")


@role.command(name="add")
@click.argument("name")
@click.option("--description", default="", help="Role description")
@click.option("--permission", "permissions", multiple=True, help="Permission in 'resource:action' format (can repeat)")
def rbac_role_add(name, description, permissions):
    """Add a custom role."""
    mgr = _get_rbac()
    from ..rbac.models import Permission as RBACPermission
    perms = set()
    for p in permissions:
        try:
            perms.add(RBACPermission.from_str(p))
        except ValueError as e:
            console.print(f"[red]❌ Invalid permission '{p}': {e}[/red]")
            raise SystemExit(1)
    role_obj = Role(
        name=name,
        description=description,
        permissions=perms,
    )
    if mgr.add_role(role_obj):
        console.print(f"[green]✅ Role '{name}' created[/green]")
        console.print(f"[dim]   Permissions: {len(perms)}[/dim]")
    else:
        console.print(f"[red]❌ Could not create role '{name}' (built-in conflict)[/red]")
        raise SystemExit(1)


@role.command(name="remove")
@click.argument("name")
def rbac_role_remove(name):
    """Remove a custom role (not built-in)."""
    mgr = _get_rbac()
    if mgr.remove_role(name):
        console.print(f"[green]🗑️ Role '{name}' removed[/green]")
    else:
        console.print(f"[red]❌ Could not remove role '{name}' (built-in or in-use)[/red]")
        raise SystemExit(1)


# ── Audit Commands ─────────────────────────────────────────────────────

@hive.group()
def audit():
    """📜 Audit trail — log, search, and manage audit entries."""
    pass


@audit.command(name="list")
@click.option("--days", default=1, help="Number of days back to show")
@click.option("--limit", default=20, help="Max entries to show")
@click.option("--action", help="Filter by action (create, read, update, delete, etc.)")
@click.option("--resource", help="Filter by resource (agent, flow, task, etc.)")
@click.option("--actor", help="Filter by actor username")
def audit_list(days, limit, action, resource, actor):
    """List recent audit entries."""
    from ..audit import AuditTrail, AuditEntry
    trail = _get_audit()
    from datetime import timedelta, date as date_type
    today = date_type.today()
    start = today - timedelta(days=days - 1)
    entries = trail.read_range(start, today)

    # Apply filters
    if action:
        entries = [e for e in entries if e.action.value == action]
    if resource:
        entries = [e for e in entries if e.resource.value == resource]
    if actor:
        entries = [e for e in entries if e.actor == actor]

    entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]

    if not entries:
        console.print("[yellow]No audit entries found[/yellow]")
        return

    from rich.table import Table
    table = Table(title=f"📜 Audit Trail (last {days}d, showing {len(entries)})")
    table.add_column("Time", style="dim", width=20)
    table.add_column("Actor", style="cyan")
    table.add_column("Action", style="green")
    table.add_column("Resource", style="white")
    table.add_column("Resource ID", style="dim")
    table.add_column("Result", style="yellow")
    table.add_column("Message", style="white")

    for e in entries:
        ts = e.timestamp[11:23] if len(e.timestamp) > 23 else e.timestamp
        result_style = {"success": "green", "failure": "red", "denied": "yellow", "error": "red"}
        rst = result_style.get(e.result.value, "white")
        msg = e.message[:60] + "..." if len(e.message) > 60 else e.message
        table.add_row(ts, e.actor, e.action.value, e.resource.value,
                      e.resource_id or "-", f"[{rst}]{e.result.value}[/]", msg)
    console.print(table)


@audit.command(name="stats")
def audit_stats():
    """Show audit statistics."""
    trail = _get_audit()
    stats = trail.stats()
    from rich.table import Table

    console.print(f"[bold]📜 Audit Statistics[/bold]")
    console.print(f"   Total entries: {stats['total_entries']}")
    console.print(f"   Unique days: {stats['unique_days']}")
    console.print(f"   Files on disk: {stats['files']}")
    console.print(f"   Errors/Failures: {stats['errors']}")

    if stats["actions"]:
        table = Table(title="Actions Breakdown")
        table.add_column("Action", style="cyan")
        table.add_column("Count", style="white")
        for k, v in stats["actions"].items():
            table.add_row(k, str(v))
        console.print(table)

    if stats["resources"]:
        table = Table(title="Resources Breakdown")
        table.add_column("Resource", style="cyan")
        table.add_column("Count", style="white")
        for k, v in stats["resources"].items():
            table.add_row(k, str(v))
        console.print(table)


@audit.command(name="search")
@click.argument("query")
def audit_search(query):
    """Search audit entries locally by keyword."""
    trail = _get_audit()
    entries = trail.search_local(query)

    if not entries:
        console.print(f"[yellow]No entries matching '{query}'[/yellow]")
        return

    from rich.table import Table
    table = Table(title=f"📜 Audit Search: '{query}' ({len(entries)} results)")
    table.add_column("Time", style="dim")
    table.add_column("Actor", style="cyan")
    table.add_column("Action", style="green")
    table.add_column("Resource", style="white")
    table.add_column("Result", style="yellow")
    table.add_column("Message", style="white")

    for e in entries[:20]:
        ts = e.timestamp[11:23] if len(e.timestamp) > 23 else e.timestamp
        msg = e.message[:60]
        table.add_row(ts, e.actor, e.action.value, e.resource.value,
                      e.result.value, msg)
    console.print(table)
    if len(entries) > 20:
        console.print(f"[dim]... and {len(entries) - 20} more[/dim]")


@audit.command(name="search-gbrain")
@click.argument("query")
def audit_search_gbrain(query):
    """Semantic search via gbrain."""
    trail = _get_audit()
    results = trail.search_gbrain(query)
    if not results:
        console.print("[yellow]No gbrain results (try 'hive audit sync-gbrain' first)[/yellow]")
        return
    from rich.table import Table
    table = Table(title=f"🔍 gbrain Semantic Search: '{query}'")
    table.add_column("Slug", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Snippet", style="white")
    for r in results[:10]:
        table.add_row(r.get("slug", ""), str(r.get("score", "")),
                      r.get("snippet", "")[:80])
    console.print(table)


@audit.command(name="sync-gbrain")
@click.option("--date", help="Sync specific date (YYYY-MM-DD), default: last 30 days")
@click.option("--max", default=500, help="Max pages to sync")
def audit_sync_gbrain(date, max):
    """Sync audit entries to gbrain PGLite for semantic search."""
    trail = _get_audit()
    synced = trail.sync_to_gbrain(date=date, max_pages=max)
    if synced:
        console.print(f"[green]✅ Synced {synced} entries to gbrain[/green]")
        console.print("[dim]   Now search with: hive audit search-gbrain <query>[/dim]")


@audit.command(name="rotate")
@click.option("--keep-days", default=90, help="Days of audit to keep (default: 90)")
def audit_rotate(keep_days):
    """Rotate old audit files."""
    trail = _get_audit()
    removed = trail.rotate(keep_days=keep_days)
    console.print(f"[green]✅ Rotated {removed} old files (keeping {keep_days}d)[/green]")


# ── Dashboard Commands ────────────────────────────────────────────────

@hive.group()
def dashboard():
    """📊 Dashboard — Web UI for monitoring agents, flows, and nodes."""
    pass


@dashboard.command(name="start")
@click.option("--host", default="127.0.0.1", help="Bind address")
@click.option("--port", default=8080, help="Port number")
@click.option("--data-dir", default=None, help="HiveOS data directory")
def dashboard_start(host, port, data_dir):
    """Start the dashboard web server."""
    from ..dashboard import DashboardServer

    data_path = Path(data_dir) if data_dir else None
    server = DashboardServer(
        host=host,
        port=port,
        data_dir=data_path,
    )
    result = server.start()
    console.print(f"[green]✅ {result}[/green]")
    console.print(f"[dim]   Open: http://{host}:{port}[/dim]")
    console.print(f"[dim]   Stop: hive dashboard stop[/dim]")


@dashboard.command(name="stop")
def dashboard_stop():
    """Stop the dashboard web server."""
    from ..dashboard import DashboardServer

    server = DashboardServer()
    result = server.stop()
    console.print(f"[yellow]{result}[/yellow]")


@dashboard.command(name="status")
def dashboard_status():
    """Show dashboard server status."""
    from ..dashboard import DashboardServer

    server = DashboardServer()
    status = server.status()
    if status["running"]:
        console.print(f"[green]✅ Dashboard is running[/green]")
        console.print(f"   URL: {status['url']}")
    else:
        console.print("[yellow]⏸️  Dashboard is not running[/yellow]")


# ── Workspace Commands ───────────────────────────────────────────────

@hive.group()
def workspace():
    """🏢 Workspaces — multi-tenant isolation per team/org."""
    pass


@workspace.command(name="create")
@click.argument("name")
@click.option("--description", default="", help="Workspace description")
@click.option("--owner", default="admin", help="Owner username")
@click.option("--id", "ws_id", default=None, help="Custom workspace ID")
def workspace_create(name, description, owner, ws_id):
    """Create a new workspace with isolated data directories."""
    from ..workspace import WorkspaceManager
    mgr = WorkspaceManager()
    ws = mgr.create_workspace(
        name=name,
        description=description,
        owner=owner,
        workspace_id=ws_id,
    )
    mgr.display_info(ws)


@workspace.command(name="list")
@click.option("--all", "show_all", is_flag=True, help="Include inactive workspaces")
def workspace_list(show_all):
    """List all workspaces."""
    from ..workspace import WorkspaceManager
    mgr = WorkspaceManager()
    workspaces = mgr.list_workspaces(include_inactive=show_all)
    mgr.display_table(workspaces)


@workspace.command(name="info")
@click.argument("workspace_id")
def workspace_info(workspace_id):
    """Show detailed workspace information."""
    from ..workspace import WorkspaceManager
    mgr = WorkspaceManager()
    ws = mgr.get_workspace(workspace_id)
    if not ws:
        console.print(f"[red]❌ Workspace '{workspace_id}' not found[/red]")
        raise SystemExit(1)
    mgr.display_info(ws)


@workspace.command(name="update")
@click.argument("workspace_id")
@click.option("--name", help="New workspace name")
@click.option("--description", help="New description")
def workspace_update(workspace_id, name, description):
    """Update workspace metadata."""
    from ..workspace import WorkspaceManager
    mgr = WorkspaceManager()
    ws = mgr.update_workspace(workspace_id, name=name, description=description)
    if ws:
        mgr.display_info(ws)


@workspace.command(name="remove")
@click.argument("workspace_id")
@click.option("--permanent", is_flag=True, help="Permanently delete all data")
def workspace_remove(workspace_id, permanent):
    """Remove/deactivate a workspace."""
    from ..workspace import WorkspaceManager
    mgr = WorkspaceManager()
    mgr.remove_workspace(workspace_id, permanent=permanent)


@workspace.command(name="activate")
@click.argument("workspace_id")
def workspace_activate(workspace_id):
    """Reactivate a deactivated workspace."""
    from ..workspace import WorkspaceManager
    mgr = WorkspaceManager()
    mgr.activate_workspace(workspace_id)


@workspace.group()
def member():
    """Manage workspace members."""
    pass


@member.command(name="add")
@click.argument("workspace_id")
@click.argument("username")
@click.option("--role", default="viewer", help="Workspace role: owner, admin, operator, contributor, viewer")
def workspace_member_add(workspace_id, username, role):
    """Add a member to a workspace."""
    from ..workspace import WorkspaceManager, WorkspaceRole
    mgr = WorkspaceManager()
    try:
        ws_role = WorkspaceRole(role)
    except ValueError:
        console.print(f"[red]❌ Invalid role '{role}'. Valid: owner, admin, operator, contributor, viewer[/red]")
        raise SystemExit(1)
    mgr.add_member(workspace_id, username, ws_role)


@member.command(name="remove")
@click.argument("workspace_id")
@click.argument("username")
def workspace_member_remove(workspace_id, username):
    """Remove a member from a workspace."""
    from ..workspace import WorkspaceManager
    mgr = WorkspaceManager()
    mgr.remove_member(workspace_id, username)


@member.command(name="set-role")
@click.argument("workspace_id")
@click.argument("username")
@click.argument("role")
def workspace_member_set_role(workspace_id, username, role):
    """Change a member's workspace role."""
    from ..workspace import WorkspaceManager, WorkspaceRole
    mgr = WorkspaceManager()
    try:
        ws_role = WorkspaceRole(role)
    except ValueError:
        console.print(f"[red]❌ Invalid role '{role}'. Valid: owner, admin, operator, contributor, viewer[/red]")
        raise SystemExit(1)
    mgr.set_member_role(workspace_id, username, ws_role)


# ── License Commands ────────────────────────────────────────────────────

@hive.group()
def license():
    """💰 License management — tiers, activation, feature gating."""
    pass


def _get_license():
    from ..license import LicenseManager
    return LicenseManager()


@license.command(name="info")
def license_info():
    """Show current license information."""
    mgr = _get_license()
    mgr.display_license()


@license.command(name="activate")
@click.argument("license_key")
@click.option("--org", default="", help="Organization name")
@click.option("--email", default="", help="Contact email")
def license_activate(license_key, org, email):
    """Activate a license key (or use demo keys: hive-pro-demo, hive-ent-demo, hive-ult-demo)."""
    mgr = _get_license()
    if mgr.activate(license_key, organization=org, email=email):
        mgr.display_license()


@license.command(name="deactivate")
def license_deactivate():
    """Deactivate current license and revert to Free tier."""
    mgr = _get_license()
    mgr.deactivate()


@license.command(name="upgrade")
@click.argument("tier", type=click.Choice(["pro", "enterprise", "ultimate"]))
@click.option("--key", default="", help="License key (optional)")
def license_upgrade(tier, key):
    """Upgrade/downgrade to a specific tier."""
    mgr = _get_license()
    from ..license import LicenseTier
    new_tier = LicenseTier(tier)
    mgr.upgrade_tier(new_tier, license_key=key)
    mgr.display_license()


@license.command(name="tiers")
def license_tiers():
    """Show all available license tiers and features."""
    mgr = _get_license()
    mgr.display_tier_table()


@license.command(name="check")
@click.argument("feature_name")
def license_check(feature_name):
    """Check if a specific feature is available on current license."""
    mgr = _get_license()
    from ..license import FeatureFlag

    try:
        feature = FeatureFlag(feature_name)
    except ValueError:
        console.print(f"[red]❌ Unknown feature '{feature_name}'[/red]")
        available = sorted(f.value for f in FeatureFlag)
        console.print(f"[dim]Available features: {', '.join(available)}[/dim]")
        raise SystemExit(1)

    if mgr.has_feature(feature):
        console.print(f"[green]✅ Feature '[bold]{feature_name}[/bold]' is available on your [bold]{mgr.tier.value.upper()}[/bold] license[/green]")
    else:
        tier_needed = mgr._tier_for_feature(feature)
        tier_label = tier_needed.value.upper() if tier_needed else "a higher"
        console.print(f"[yellow]⚠️  Feature '[bold]{feature_name}[/bold]' requires {tier_label} tier (current: {mgr.tier.value.upper()})[/yellow]")


# ── Domain Commands ─────────────────────────────────────────────────

@hive.group()
def domain():
    """🧩 Domain plugins — manage knowledge domains for agent teams."""
    pass


@domain.command("list")
def domain_list():
    """List all installed domain plugins."""
    from ..domain.manager import DomainManager
    mgr = DomainManager()

    domains = mgr.list_domains()
    if not domains:
        console.print("[yellow]No domain plugins installed.[/yellow]")
        console.print("  Install one: [cyan]hive domain install <path>[/cyan]")
        return

    table = Table(title="🧩 Installed Domain Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Label (EN)", style="white")
    table.add_column("Agents", style="yellow")
    table.add_column("Flows", style="blue")
    table.add_column("Tags", style="dim")

    for d in domains:
        info = d.to_dict()
        agent_str = f"{info['total_agents']} ({info['orchestrators']}O + {info['specialists']}S)"
        tags_str = ", ".join(info['tags'][:3])
        if len(info['tags']) > 3:
            tags_str += "..."
        table.add_row(
            info['name'],
            info['version'],
            info['label_en'],
            agent_str,
            str(info['total_flows']),
            tags_str,
        )
    console.print(table)


@domain.command()
@click.argument("name")
def info(name):
    """Show detailed information about a domain plugin."""
    from ..domain.manager import DomainManager
    mgr = DomainManager()

    d = mgr.get_domain(name)
    if d is None:
        console.print(f"[red]❌ Domain '{name}' not found[/red]")
        console.print("  Available: [cyan]hive domain list[/cyan]")
        return

    info_dict = d.to_dict()
    node_count = d.knowledge_tree_node_count()

    from rich.panel import Panel
    lines = [
        f"[bold cyan]🧩 {info_dict['label_en']}[/bold cyan] [dim]v{info_dict['version']}[/dim]",
        "",
    ]
    if info_dict.get('label_fa'):
        lines.append(f"  [bold]نام:[/bold] {info_dict['label_fa']}")
    lines.append(f"  [bold]Name:[/bold] {info_dict['name']}")
    lines.append(f"  [bold]Description:[/bold] {info_dict['description_en']}")
    lines.append(f"  [bold]Orchestrator:[/bold] {info_dict.get('orchestrator_agent', '—')}")
    lines.append(f"  [bold]Dependencies:[/bold] {', '.join(info_dict.get('depends_on', [])) or 'None'}")
    lines.append("")
    lines.append(f"  [bold]Agents:[/bold] {info_dict['total_agents']} total ({info_dict['orchestrators']} orchestrators, {info_dict['specialists']} specialists)")
    lines.append(f"  [bold]Flow Templates:[/bold] {info_dict['total_flows']}")
    lines.append(f"  [bold]Knowledge Nodes:[/bold] {node_count}")
    lines.append(f"  [bold]Tags:[/bold] {', '.join(info_dict.get('tags', []))}")
    lines.append("")
    lines.append(f"  [bold]Path:[/bold] {d.root}")
    lines.append(f"  [bold]Domain YAML:[/bold] {d.root / 'domain.yaml'}")

    console.print(Panel("\n".join(lines), width=72))

    # List agents
    from rich.table import Table
    agent_table = Table(title="Agent Blueprints", box=None, padding=(0, 2))
    agent_table.add_column("ID", style="cyan")
    agent_table.add_column("Type", style="yellow")
    agent_table.add_column("Label (EN)", style="white")
    agent_table.add_column("Skills", style="dim")

    for agent in info_dict['agents']:
        skills = agent.get("skills", [])
        skills_str = ", ".join(skills[:3]) if isinstance(skills, list) else ""
        if isinstance(skills, list) and len(skills) > 3:
            skills_str += "..."
        agent_table.add_row(
            agent.get("id", "?"),
            agent.get("type", "?"),
            agent.get("label", {}).get("en", "?"),
            skills_str,
        )
    console.print(agent_table)


@domain.command()
@click.argument("source", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--name", help="Override domain name (default: source directory name)")
def install(source, name):
    """Install a domain plugin from a directory path."""
    from ..domain.manager import DomainManager
    mgr = DomainManager()

    src = Path(source).resolve()
    try:
        d = mgr.install(src, name=name)
        console.print(f"[green]✅ Domain [bold]{d.name}[/bold] v{d.version} installed![/green]")
        console.print(f"   Path: {d.root}")
        console.print(f"   Agents: {d.total_agents}  |  Flows: {d.total_flows}")
    except FileExistsError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)


@domain.command()
@click.argument("name")
@click.option("--permanent", is_flag=True, help="Delete domain directory from disk")
def remove(name, permanent):
    """Remove a domain plugin from the project."""
    from ..domain.manager import DomainManager
    mgr = DomainManager()

    try:
        mgr.remove(name, permanent=permanent)
        if permanent:
            console.print(f"[green]✅ Domain '{name}' permanently removed![/green]")
        else:
            console.print(f"[green]✅ Domain '{name}' removed from registry (files preserved).[/green]")
    except KeyError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise SystemExit(1)


@domain.command()
@click.option("--name", prompt=True, help="Domain name (e.g. accounting)")
@click.option("--label", prompt=True, help="English label (e.g. Accounting)")
@click.option("--label-fa", prompt=True, help="Persian label (e.g. حسابداری)")
@click.option("--description", prompt=True, help="English description")
def init(name, label, label_fa, description):
    """Scaffold a new domain plugin in the project."""
    from pathlib import Path

    root = Path.cwd() / "domains" / name
    if root.exists():
        console.print(f"[red]❌ Domain directory already exists: {root}[/red]")
        raise SystemExit(1)

    # Create directory structure
    (root / "agents" / "blueprints").mkdir(parents=True)
    (root / "flows").mkdir(parents=True)
    (root / "knowledge").mkdir(parents=True)

    # domain.yaml
    domain_yaml = f"""# ============================================================
# {label} Domain — HiveOS Domain Plugin
# ============================================================

domain:
  name: "{name}"
  version: "1.0.0-dev"
  label:
    fa: "{label_fa}"
    en: "{label}"
  description:
    fa: ""
    en: "{description}"
  depends_on: []
  orchestrator_agent: ""
  metadata:
    authors: []
    tags: []
  agents: []
  flows: []
  knowledge_tree: "knowledge/tree.yaml"
"""
    (root / "domain.yaml").write_text(domain_yaml, encoding="utf-8")

    # knowledge/tree.yaml
    (root / "knowledge" / "tree.yaml").write_text(
        "version: \"1.0.0\"\ndomain: \"" + name + "\"\nlabel:\n  fa: \"\"\n  en: \"Knowledge Tree\"\nnodes: {}\n",
        encoding="utf-8",
    )

    # .gitkeep in blueprints
    (root / "agents" / "blueprints" / ".gitkeep").write_text("")

    # example flow
    example = root / "flows" / "example.yaml"
    if not example.exists():
        example.write_text(f"""# Example Flow for {label}
name: "Example Flow"
version: "1.0.0"
domain: "{name}"
trigger:
  type: manual
agents:
  - id: example-agent
    name: "Example Agent"
    role: domain agent
    skills: []
    depends_on: []
    output: "output.md"
    deliver:
      format: markdown
""", encoding="utf-8")

    console.print(f"[green]✅ Domain scaffolded: {root}[/green]")
    console.print(f"   Agents: {root / 'agents' / 'blueprints'}")
    console.print(f"   Flows:  {root / 'flows'}")
    console.print(f"   Knowledge: {root / 'knowledge'}")
    console.print(f"\nNext: edit [cyan]{root / 'domain.yaml'}[/cyan] and add agents")


# ── Update Commands ────────────────────────────────────────────────────

@hive.group()
def update():
    """🔄 Check for HiveOS updates — auto-update skeleton."""
    pass


@update.command()
def check():
    """Check the latest HiveOS release on GitHub."""
    from ..update import UpdateChecker
    UpdateChecker().check_and_notify()


@update.command()
def info():
    """Show update-related information (current version, latest available)."""
    from ..update import UpdateChecker
    from rich.table import Table
    from hiveos import __version__

    checker = UpdateChecker()
    result = checker.check()

    table = Table(title="🔄 Update Info", width=60)
    table.add_column("Property", style="bold yellow")
    table.add_column("Value", style="white")

    table.add_row("Current Version", __version__)
    table.add_row("Latest Version", result.latest_version or "—")
    table.add_row("Update Available",
                  "[green]✔ Yes[/green]" if result.update_available else "[dim]No[/dim]")
    table.add_row("Download URL", result.download_url or "—")

    if result.error:
        table.add_row("Error", f"[red]{result.error}[/red]")

    console.print(table)

    if result.update_available:
        console.print(f"\n[bold cyan]🚀 Upgrade:[/bold cyan] {__version__} → [bold]{result.latest_version}[/bold]")
        console.print(f"   [dim]{result.download_url}[/dim]")


# ── Desktop Commands ──────────────────────────────────────────────────

@hive.group()
def desktop():
    """🖥️ Open HiveOS in a native Windows desktop window."""
    pass


@desktop.command()
@click.option('--port', default=9876, help='Dashboard port (default 9876)')
@click.option('--width', default=1280, help='Window width (default 1280)')
@click.option('--height', default=800, help='Window height (default 800)')
@click.option('--fullscreen', is_flag=True, help='Start in fullscreen mode')
def start(port, width, height, fullscreen):
    """Start HiveOS desktop application — native Windows window."""
    from ..desktop import DesktopApp

    console.print("[bold cyan]🐝 HiveOS Desktop[/bold cyan]")
    console.print(f"   Window: {width}×{height} on port {port}")

    app = DesktopApp(
        port=port,
        width=width,
        height=height,
        fullscreen=fullscreen,
        debug=False,
    )
    app.run()


@desktop.command()
def connect():
    """Open a connection to an already-running dashboard server."""
    import webbrowser

    from ..utils.config import ConfigManager

    config = ConfigManager()
    host = config.get("dashboard_host", "127.0.0.1")
    port = config.get("dashboard_port", 9876)
    url = f"http://{host}:{port}"

    console.print(f"[cyan]🔗 Opening dashboard at {url}[/cyan]")
    webbrowser.open(url)


# ── Main entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    hive()
