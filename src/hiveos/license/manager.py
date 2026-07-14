"""
HiveOS License Manager — YAML-backed license persistence and validation.

Handles:
- License activation/deactivation
- Feature gating checks
- Resource limit enforcement
- License key validation
- Dashboard integration data
"""

from __future__ import annotations

import uuid
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta

import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .models import (
    License, LicenseTier, FeatureFlag,
    TIER_FEATURES, TIER_LIMITS,
)

console = Console()

LICENSE_DIR = Path.home() / ".hiveos"
LICENSE_FILE = LICENSE_DIR / "license.yaml"
DEMO_KEYS = {
    "hive-pro-demo": LicenseTier.PRO,
    "hive-ent-demo": LicenseTier.ENTERPRISE,
    "hive-ult-demo": LicenseTier.ULTIMATE,
}


class LicenseManager:
    """
    Manages HiveOS license state.

    Features:
    - YAML-backed persistence
    - License key activation (with demo keys for testing)
    - Feature availability checks
    - Resource limit queries
    - Upgrade path suggestions
    """

    def __init__(self, license_path: Optional[Path] = None):
        self.license_path = license_path or LICENSE_FILE
        self.license_path.parent.mkdir(parents=True, exist_ok=True)
        self._license: Optional[License] = None
        self._load()

    # ── Persistence ─────────────────────────────────────────────────

    def _load(self):
        """Load license from disk."""
        if self.license_path.exists():
            try:
                data = yaml.safe_load(self.license_path.read_text(encoding="utf-8"))
                if data:
                    self._license = License.from_dict(data)
                    return
            except Exception:
                pass
        # Default to free tier
        self._license = License.free_tier()
        self._save()

    def _save(self):
        """Persist license to disk."""
        if self._license:
            with open(self.license_path, "w", encoding="utf-8") as f:
                yaml.dump(self._license.to_dict(), f, default_flow_style=False, allow_unicode=True)

    # ── License Info ────────────────────────────────────────────────

    @property
    def current(self) -> License:
        """Get the current license."""
        if self._license is None:
            self._load()
        return self._license  # type: ignore

    @property
    def tier(self) -> LicenseTier:
        """Current tier shortcut."""
        return self.current.tier

    @property
    def is_active(self) -> bool:
        """Check if license is active and not expired."""
        return self.current.is_active

    # ── Activation ──────────────────────────────────────────────────

    def activate(self, license_key: str, organization: str = "", email: str = "") -> bool:
        """
        Activate a license key.

        Supports:
        - Demo keys for testing (hive-pro-demo, hive-ent-demo, hive-ult-demo)
        - Real license key format (hive-xxxxxxxxxxxxxxxx)

        Returns True if activation succeeded.
        """
        key = license_key.strip()

        # Check demo keys
        if key in DEMO_KEYS:
            tier = DEMO_KEYS[key]
            self._license = License(
                tier=tier,
                license_key=key,
                organization=organization or "Demo Organization",
                contact_email=email or "demo@example.com",
                activated_at=datetime.utcnow().isoformat(),
                expires_at=(datetime.utcnow() + timedelta(days=30)).isoformat(),
            )
            self._save()
            console.print(f"[green]✅ License activated: [bold]{tier.value.upper()}[/bold] (demo, 30 days)[/green]")
            return True

        # Real license key format: hive-<hex>
        if key.startswith("hive-") and len(key) >= 20:
            # Determine tier from key prefix
            tier = LicenseTier.PRO  # default for real keys
            if "enterprise" in key.lower() or "-ent-" in key.lower():
                tier = LicenseTier.ENTERPRISE
            elif "ultimate" in key.lower() or "-ult-" in key.lower():
                tier = LicenseTier.ULTIMATE

            self._license = License(
                tier=tier,
                license_key=key,
                organization=organization or "",
                contact_email=email or "",
                activated_at=datetime.utcnow().isoformat(),
                expires_at=(datetime.utcnow() + timedelta(days=365)).isoformat(),
            )
            self._save()
            console.print(f"[green]✅ License activated: [bold]{tier.value.upper()}[/bold] (1 year)[/green]")
            return True

        console.print(f"[red]❌ Invalid license key: '{license_key}'[/red]")
        return False

    def deactivate(self) -> bool:
        """Deactivate current license and reset to free tier."""
        self._license = License.free_tier()
        self._save()
        console.print("[yellow]🔓 License deactivated — reverted to Free tier[/yellow]")
        return True

    def upgrade_tier(self, new_tier: LicenseTier, license_key: str = "") -> bool:
        """Upgrade (or downgrade) to a specific tier."""
        current = self.current
        self._license = License(
            tier=new_tier,
            license_key=license_key or current.license_key,
            organization=current.organization,
            contact_email=current.contact_email,
            activated_at=current.activated_at,
            expires_at=current.expires_at,
            feature_overrides=current.feature_overrides,
            disabled_features=current.disabled_features,
        )
        self._save()
        console.print(f"[green]✅ License changed to [bold]{new_tier.value.upper()}[/bold][/green]")
        return True

    # ── Feature Checks ──────────────────────────────────────────────

    def has_feature(self, feature: FeatureFlag) -> bool:
        """Check if the current license grants a feature."""
        return self.current.has_feature(feature)

    def require_feature(self, feature: FeatureFlag) -> bool:
        """Check feature and print warning if not available."""
        if not self.has_feature(feature):
            tier_needed = self._tier_for_feature(feature)
            if tier_needed:
                console.print(
                    f"[yellow]⚠️  Feature '{feature.value}' requires "
                    f"[bold]{tier_needed.value.upper()}[/bold] tier "
                    f"(current: {self.current.tier.value.upper()})[/yellow]"
                )
            else:
                console.print(
                    f"[yellow]⚠️  Feature '{feature.value}' is not available "
                    f"on your current tier[/yellow]"
                )
            return False
        return True

    def _tier_for_feature(self, feature: FeatureFlag) -> Optional[LicenseTier]:
        """Find the minimum tier that includes a feature."""
        for tier in LicenseTier.ordered():
            if feature in TIER_FEATURES.get(tier, set()):
                return tier
        return None

    # ── Resource Limits ─────────────────────────────────────────────

    def get_limit(self, limit_name: str) -> int:
        """Get a numeric limit (-1 = unlimited)."""
        return self.current.get_limit(limit_name)

    def is_within_limit(self, limit_name: str, current_value: int) -> bool:
        """Check if a value is within the license limit."""
        limit = self.get_limit(limit_name)
        if limit == -1:
            return True  # unlimited
        return current_value <= limit

    def enforce_limit(self, limit_name: str, current_value: int, resource_label: str = "") -> bool:
        """Enforce a resource limit, printing warning if exceeded."""
        if not self.is_within_limit(limit_name, current_value):
            limit = self.get_limit(limit_name)
            label = resource_label or limit_name
            console.print(
                f"[red]❌ {label} limit exceeded: {current_value}/{limit}. "
                f"Upgrade to [bold]{self._next_tier().value.upper()}[/bold] for more.[/red]"
            )
            return False
        return True

    def _next_tier(self) -> LicenseTier:
        """Suggest the next tier up from current."""
        ordered = LicenseTier.ordered()
        idx = ordered.index(self.current.tier)
        if idx < len(ordered) - 1:
            return ordered[idx + 1]
        return self.current.tier

    # ── Tier Info ───────────────────────────────────────────────────

    def list_tiers(self) -> List[Dict[str, Any]]:
        """Get info about all available tiers."""
        result = []
        for tier in LicenseTier.ordered():
            limits = TIER_LIMITS.get(tier, {})
            features = TIER_FEATURES.get(tier, set())
            result.append({
                "tier": tier.value,
                "label": tier.value.title(),
                "features": sorted(f.value for f in features),
                "limits": limits,
            })
        return result

    def compare_tiers(self) -> Dict[str, Any]:
        """Get comparison data for all tiers."""
        return {
            "current": self.current.tier.value,
            "tiers": self.list_tiers(),
        }

    def upgrade_path(self) -> List[str]:
        """Suggest available upgrade paths."""
        current_idx = LicenseTier.ordered().index(self.current.tier)
        return [
            t.value
            for t in LicenseTier.ordered()[current_idx + 1:]
        ]

    # ── Display ─────────────────────────────────────────────────────

    def display_license(self):
        """Show current license info in a rich panel."""
        lic = self.current
        tier_color = {
            LicenseTier.FREE: "cyan",
            LicenseTier.PRO: "green",
            LicenseTier.ENTERPRISE: "yellow",
            LicenseTier.ULTIMATE: "magenta",
        }.get(lic.tier, "white")

        status = "✅ Active" if lic.is_active else "❌ Expired"
        expiry = lic.expires_at[:10] if lic.expires_at else "Never"
        remaining = lic.days_remaining
        remaining_str = f" ({remaining} days)" if remaining is not None else ""

        # Limits summary
        limits_info = ""
        for key, label in [
            ("max_workspaces", "Workspaces"),
            ("max_agents", "Agents"),
            ("max_flows", "Flows"),
            ("max_nodes", "Nodes"),
            ("audit_retention_days", "Audit Retention"),
        ]:
            val = lic.get_limit(key)
            val_str = "∞" if val == -1 else str(val)
            if key == "audit_retention_days":
                val_str = "∞" if val == -1 else f"{val}d"
            limits_info += f"    {label}:       {val_str}\n"

        # Feature highlights
        enabled_features = [f.value for f in FeatureFlag if lic.has_feature(f)]
        total = len(FeatureFlag)
        enabled_count = len(enabled_features)

        console.print(Panel(
            f"[bold {tier_color}]🐝 HiveOS License — {lic.tier_label}[/bold {tier_color}]\n\n"
            f"  [bold]Status:[/bold]     {status}{remaining_str}\n"
            f"  [bold]License Key:[/bold] {lic.license_key or '—'}\n"
            f"  [bold]Expires:[/bold]    {expiry}\n"
            f"  [bold]Organization:[/bold] {lic.organization or '—'}\n"
            f"  [bold]Contact:[/bold]    {lic.contact_email or '—'}\n\n"
            f"  [bold]Limits:[/bold]\n{limits_info}\n"
            f"  [bold]Features:[/bold]   {enabled_count}/{total} enabled\n",
            width=60,
        ))
        return lic

    def display_tier_table(self):
        """Show all tiers in a comparison table."""
        table = Table(title="📊 HiveOS License Tiers")
        table.add_column("Feature", style="bold cyan")
        for tier in LicenseTier.ordered():
            table.add_column(tier.value.title(), style="bold")

        # Feature rows
        feature_labels = {
            FeatureFlag.MULTI_WORKSPACE: "Multi-Workspace",
            FeatureFlag.DOMAIN_PLUGINS: "Domain Plugins",
            FeatureFlag.ADVANCED_RBAC: "Advanced RBAC",
            FeatureFlag.FLOW_SCHEDULING: "Flow Scheduling",
            FeatureFlag.ADVANCED_DASHBOARD: "Advanced Dashboard",
            FeatureFlag.ANALYTICS: "Analytics",
            FeatureFlag.SSO: "SSO / SAML",
            FeatureFlag.PRIORITY_SUPPORT: "Priority Support",
            FeatureFlag.ON_PREMISE: "On-Premise",
            FeatureFlag.WHITE_LABEL: "White-Label",
        }

        for feature, label in feature_labels.items():
            row = [label]
            for tier in LicenseTier.ordered():
                has = feature in TIER_FEATURES.get(tier, set())
                is_current = tier == self.current.tier
                marker = "[green]✅[/]" if has else "[dim]—[/]"
                if is_current:
                    marker = f"{marker} [bold]*[/]"
                row.append(marker)
            table.add_row(*row)

        # Limit rows
        limit_labels = [
            ("max_workspaces", "Max Workspaces"),
            ("max_agents", "Max Agents"),
            ("max_flows", "Max Flows"),
            ("max_nodes", "Max Nodes"),
        ]
        for key, label in limit_labels:
            row = [label]
            for tier in LicenseTier.ordered():
                val = TIER_LIMITS.get(tier, {}).get(key, 0)
                val_str = "∞" if val == -1 else str(val)
                is_current = tier == self.current.tier
                if is_current:
                    val_str = f"[bold]{val_str}[/] [dim]*[/]"
                row.append(val_str)
            table.add_row(*row)

        console.print(table)
        console.print("[dim]* Current tier[/dim]")
