"""
Privacy CLI — Command-line interface for privacy management.

Commands:
    hive privacy status          Show privacy status
    hive privacy config          Show privacy configuration
    hive privacy enable <endpoint>  Enable external endpoint
    hive privacy disable <endpoint>  Disable external endpoint
    hive privacy audit           Show recent audit logs
    hive privacy blocked         Show blocked requests
"""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from hiveos.privacy import PrivacyConfig, PrivacyAuditTrail

console = Console()


def _get_config(data_dir: Path) -> PrivacyConfig:
    """Load privacy config from data directory."""
    config_path = data_dir / "privacy.json"
    return PrivacyConfig.load(config_path)


def _get_audit(data_dir: Path) -> PrivacyAuditTrail:
    """Load privacy audit trail."""
    return PrivacyAuditTrail(data_dir / "privacy_audit.db")


@click.group()
@click.option("--data-dir", type=click.Path(), default="~/.hiveos/data", help="Data directory")
@click.pass_context
def privacy(ctx, data_dir):
    """Privacy management commands (ADR-0017: Privacy-First)."""
    ctx.ensure_object(dict)
    ctx.obj["data_dir"] = Path(data_dir).expanduser()


@privacy.command()
@click.pass_context
def status(ctx):
    """Show privacy status."""
    data_dir = ctx.obj["data_dir"]
    config = _get_config(data_dir)
    audit = _get_audit(data_dir)
    
    stats = audit.get_stats()
    
    table = Table(title="Privacy Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Egress Policy", config.egress_policy.value)
    table.add_row("Audit Enabled", str(config.audit_all_egress))
    table.add_row("Total Egress Attempts", str(stats["total_egress_attempts"]))
    table.add_row("Allowed", str(stats["allowed"]))
    table.add_row("Blocked", str(stats["blocked"]))
    
    console.print(table)
    
    # Show endpoints
    endpoint_table = Table(title="External Endpoints")
    endpoint_table.add_column("ID", style="cyan")
    endpoint_table.add_column("Purpose")
    endpoint_table.add_column("Status", style="bold")
    endpoint_table.add_column("URL")
    
    for ep_id, ep in config.allowed_endpoints.items():
        status_style = "green" if ep.enabled else "red"
        status_text = "ENABLED" if ep.enabled else "disabled"
        endpoint_table.add_row(
            ep_id,
            ep.purpose,
            f"[{status_style}]{status_text}[/{status_style}]",
            ep.url,
        )
    
    console.print(endpoint_table)


@privacy.command()
@click.pass_context
def config(ctx):
    """Show privacy configuration."""
    data_dir = ctx.obj["data_dir"]
    config = _get_config(data_dir)
    
    console.print(Panel(
        json.dumps(config.to_dict(), indent=2),
        title="Privacy Configuration",
        border_style="blue",
    ))


@privacy.command()
@click.argument("endpoint_id")
@click.pass_context
def enable(ctx, endpoint_id):
    """Enable an external endpoint."""
    data_dir = ctx.obj["data_dir"]
    config = _get_config(data_dir)
    
    if config.enable_endpoint(endpoint_id):
        config.save(data_dir / "privacy.json")
        console.print(f"[green]✓[/green] Endpoint '{endpoint_id}' enabled")
    else:
        console.print(f"[red]✗[/red] Endpoint '{endpoint_id}' not found")


@privacy.command()
@click.argument("endpoint_id")
@click.pass_context
def disable(ctx, endpoint_id):
    """Disable an external endpoint."""
    data_dir = ctx.obj["data_dir"]
    config = _get_config(data_dir)
    
    if config.disable_endpoint(endpoint_id):
        config.save(data_dir / "privacy.json")
        console.print(f"[green]✓[/green] Endpoint '{endpoint_id}' disabled")
    else:
        console.print(f"[red]✗[/red] Endpoint '{endpoint_id}' not found")


@privacy.command()
@click.option("--limit", default=20, help="Number of entries to show")
@click.pass_context
def audit(ctx, limit):
    """Show recent audit logs."""
    data_dir = ctx.obj["data_dir"]
    audit_trail = _get_audit(data_dir)
    
    entries = audit_trail.get_recent(limit=limit)
    
    table = Table(title="Privacy Audit Log")
    table.add_column("Time", style="cyan")
    table.add_column("Method")
    table.add_column("URL")
    table.add_column("Status", style="bold")
    table.add_column("Reason")
    
    for entry in entries:
        status_style = "green" if entry.allowed else "red"
        status_text = "ALLOWED" if entry.allowed else "BLOCKED"
        table.add_row(
            entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            entry.method,
            entry.url[:60] + "..." if len(entry.url) > 60 else entry.url,
            f"[{status_style}]{status_text}[/{status_style}]",
            entry.reason,
        )
    
    console.print(table)


@privacy.command()
@click.option("--limit", default=20, help="Number of entries to show")
@click.pass_context
def blocked(ctx, limit):
    """Show blocked requests."""
    data_dir = ctx.obj["data_dir"]
    audit_trail = _get_audit(data_dir)
    
    entries = audit_trail.get_blocked(limit=limit)
    
    if not entries:
        console.print("[green]No blocked requests found[/green]")
        return
    
    table = Table(title="Blocked Egress Attempts")
    table.add_column("Time", style="cyan")
    table.add_column("Method")
    table.add_column("URL")
    table.add_column("Reason", style="red")
    
    for entry in entries:
        table.add_row(
            entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            entry.method,
            entry.url[:60] + "..." if len(entry.url) > 60 else entry.url,
            entry.reason,
        )
    
    console.print(table)


if __name__ == "__main__":
    privacy()
