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
from ..package import PackageBuilder, PackageInstaller, create_manifest_yaml
from ..utils.knowledge import KnowledgeManager
from ..utils.config import ConfigManager

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


@flow.command()
def list():
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


@package.command()
def list():
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
