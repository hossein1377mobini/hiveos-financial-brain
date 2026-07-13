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

console = Console()

BANNER = """
╔══════════════════════════════════════╗
║           HiveOS v0.1.0              ║
║    Multi-Agent Operating System      ║
╚══════════════════════════════════════╝
"""

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
        rprint(Panel("[bold cyan]HiveOS v0.1.0[/bold cyan]\n"
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
@click.option('--version', default='0.1.0', help='Package version')
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
version: "0.1.0"

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
    
    console.print("[green]✅ HiveOS project initialized![/green]")
    console.print(f"\nProject structure created at: {cwd}")
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
    info_table.add_row("Version", "0.1.0")
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
