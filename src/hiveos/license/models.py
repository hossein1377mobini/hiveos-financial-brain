"""
HiveOS License Models — tier definitions, feature flags, and license state.

Defines the pricing structure:
  FREE       → 1 workspace, 3 agents, 5 flows, basic features
  PRO        → 5 workspaces, 20 agents, 50 flows, all core features
  ENTERPRISE → Unlimited workspaces, unlimited agents, all features + SSO
  ULTIMATE   → Everything + priority support, white-label, dedicated infra
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set


class LicenseTier(str, Enum):
    """Available license tiers."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    ULTIMATE = "ultimate"

    @classmethod
    def ordered(cls) -> List["LicenseTier"]:
        """Tiers in ascending order of capability."""
        return [cls.FREE, cls.PRO, cls.ENTERPRISE, cls.ULTIMATE]

    def __ge__(self, other: "LicenseTier") -> bool:
        """Compare tiers — ENTERPRISE >= PRO etc."""
        order = {t: i for i, t in enumerate(self.ordered())}
        return order[self] >= order[other]

    def __gt__(self, other: "LicenseTier") -> bool:
        order = {t: i for i, t in enumerate(self.ordered())}
        return order[self] > order[other]


class FeatureFlag(str, Enum):
    """Feature flags gated by license tier."""

    # ── Core Platform ──────────────────────────────────────────────
    MULTI_WORKSPACE = "multi_workspace"         # Multiple tenant workspaces
    ADVANCED_RBAC = "advanced_rbac"              # Custom roles & permissions
    AUDIT_TRAIL_EXPORT = "audit_trail_export"    # Export audit logs
    DOMAIN_PLUGINS = "domain_plugins"            # Install domain plugins
    CUSTOM_DOMAIN = "custom_domain"              # White-label / custom domain

    # ── Agents & Flows ─────────────────────────────────────────────
    UNLIMITED_AGENTS = "unlimited_agents"        # No agent count cap
    UNLIMITED_FLOWS = "unlimited_flows"          # No flow count cap
    UNLIMITED_NODES = "unlimited_nodes"          # No satellite node cap
    PARALLEL_EXECUTION = "parallel_execution"    # Concurrent flow runs
    FLOW_SCHEDULING = "flow_scheduling"          # Cron-triggered flows
    FLOW_TEMPLATES = "flow_templates"            # Pre-built flow templates

    # ── Monitoring & Observability ────────────────────────────────
    ADVANCED_DASHBOARD = "advanced_dashboard"    # Real-time + historical
    CUSTOM_DASHBOARD = "custom_dashboard"        # Custom dashboard widgets
    ALERTS = "alerts"                            # Configurable alerts
    ANALYTICS = "analytics"                      # Usage & performance analytics
    LONG_RETENTION = "long_retention"            # >30 day audit retention

    # ── Security & Compliance ──────────────────────────────────────
    SSO = "sso"                                  # Single sign-on
    SAML = "saml"                                # SAML integration
    ENCRYPTION_AT_REST = "encryption_at_rest"    # Data encryption
    COMPLIANCE_REPORTS = "compliance_reports"    # SOC2/ISO reports
    IP_WHITELIST = "ip_whitelist"                # IP-based access control

    # ── Support & Deployment ───────────────────────────────────────
    PRIORITY_SUPPORT = "priority_support"         # SLA-backed support
    DEDICATED_INFRA = "dedicated_infra"           # Dedicated server
    ON_PREMISE = "on_premise"                     # Self-hosted deployment
    WHITE_LABEL = "white_label"                   # Branded interface


# ── Feature set per tier ──────────────────────────────────────────────

ALL_FEATURES: Set[FeatureFlag] = set(FeatureFlag)

# FREE: core essentials for individual users
FREE_FEATURES: Set[FeatureFlag] = {
    FeatureFlag.FLOW_TEMPLATES,
}

# PRO: everything small teams need
PRO_FEATURES: Set[FeatureFlag] = FREE_FEATURES | {
    FeatureFlag.MULTI_WORKSPACE,
    FeatureFlag.ADVANCED_RBAC,
    FeatureFlag.AUDIT_TRAIL_EXPORT,
    FeatureFlag.DOMAIN_PLUGINS,
    FeatureFlag.PARALLEL_EXECUTION,
    FeatureFlag.FLOW_SCHEDULING,
    FeatureFlag.ADVANCED_DASHBOARD,
    FeatureFlag.ALERTS,
}

# ENTERPRISE: full platform for organizations
ENTERPRISE_FEATURES: Set[FeatureFlag] = PRO_FEATURES | {
    FeatureFlag.UNLIMITED_AGENTS,
    FeatureFlag.UNLIMITED_FLOWS,
    FeatureFlag.UNLIMITED_NODES,
    FeatureFlag.CUSTOM_DASHBOARD,
    FeatureFlag.ANALYTICS,
    FeatureFlag.LONG_RETENTION,
    FeatureFlag.SSO,
    FeatureFlag.COMPLIANCE_REPORTS,
    FeatureFlag.PRIORITY_SUPPORT,
    FeatureFlag.IP_WHITELIST,
}

# ULTIMATE: everything
ULTIMATE_FEATURES: Set[FeatureFlag] = ALL_FEATURES


TIER_FEATURES: Dict[LicenseTier, Set[FeatureFlag]] = {
    LicenseTier.FREE: FREE_FEATURES,
    LicenseTier.PRO: PRO_FEATURES,
    LicenseTier.ENTERPRISE: ENTERPRISE_FEATURES,
    LicenseTier.ULTIMATE: ULTIMATE_FEATURES,
}

# Resource limits per tier
TIER_LIMITS: Dict[LicenseTier, Dict[str, int]] = {
    LicenseTier.FREE: {
        "max_workspaces": 1,
        "max_agents": 3,
        "max_flows": 5,
        "max_nodes": 1,
        "max_concurrent_flows": 2,
        "max_agents_per_workspace": 3,
        "audit_retention_days": 7,
    },
    LicenseTier.PRO: {
        "max_workspaces": 5,
        "max_agents": 20,
        "max_flows": 50,
        "max_nodes": 5,
        "max_concurrent_flows": 10,
        "max_agents_per_workspace": 10,
        "audit_retention_days": 90,
    },
    LicenseTier.ENTERPRISE: {
        "max_workspaces": 50,
        "max_agents": -1,       # -1 = unlimited
        "max_flows": -1,
        "max_nodes": 25,
        "max_concurrent_flows": 50,
        "max_agents_per_workspace": -1,
        "audit_retention_days": 365,
    },
    LicenseTier.ULTIMATE: {
        "max_workspaces": -1,
        "max_agents": -1,
        "max_flows": -1,
        "max_nodes": -1,
        "max_concurrent_flows": -1,
        "max_agents_per_workspace": -1,
        "audit_retention_days": -1,  # indefinite
    },
}


# ── License State ─────────────────────────────────────────────────────


@dataclass
class License:
    """
    Represents an activated license for a HiveOS installation.

    Tracks:
    - Current tier
    - License key
    - Activation/expiry dates
    - Feature overrides (admin can enable specific features on lower tiers)
    """

    tier: LicenseTier = LicenseTier.FREE
    license_key: str = ""
    activated_at: str = ""
    expires_at: Optional[str] = None
    seats: int = 1
    organization: str = ""
    contact_email: str = ""
    # Admin overrides to selectively enable features on lower tiers
    feature_overrides: Dict[str, bool] = field(default_factory=dict)
    # Explicitly disabled features (e.g., enterprise wants to disable a feature)
    disabled_features: Set[str] = field(default_factory=set)

    def __post_init__(self):
        now = datetime.utcnow().isoformat()
        if not self.activated_at:
            self.activated_at = now

    @property
    def is_active(self) -> bool:
        """Check if license is currently active (not expired)."""
        if not self.expires_at:
            return True  # never expires
        try:
            expiry = datetime.fromisoformat(self.expires_at)
            return expiry > datetime.utcnow()
        except (ValueError, TypeError):
            return True

    @property
    def is_expired(self) -> bool:
        return not self.is_active

    @property
    def days_remaining(self) -> Optional[int]:
        """Days until expiry, or None if no expiry."""
        if not self.expires_at:
            return None
        try:
            expiry = datetime.fromisoformat(self.expires_at)
            remaining = (expiry - datetime.utcnow()).days
            return max(0, remaining)
        except (ValueError, TypeError):
            return None

    @property
    def tier_label(self) -> str:
        """Human-readable tier label."""
        labels = {
            LicenseTier.FREE: "Free",
            LicenseTier.PRO: "Pro",
            LicenseTier.ENTERPRISE: "Enterprise",
            LicenseTier.ULTIMATE: "Ultimate",
        }
        return labels.get(self.tier, self.tier.value.title())

    def has_feature(self, feature: FeatureFlag) -> bool:
        """Check if this license grants a specific feature."""
        # Check disabled features first
        if feature.value in self.disabled_features:
            return False
        # Check feature overrides
        if feature.value in self.feature_overrides:
            return self.feature_overrides[feature.value]
        # Fall back to tier features
        return feature in TIER_FEATURES.get(self.tier, set())

    def get_limit(self, limit_name: str) -> int:
        """
        Get a resource limit for this license.

        Returns -1 for unlimited.
        """
        limits = TIER_LIMITS.get(self.tier, {})
        return limits.get(limit_name, 0)

    def is_unlimited(self, limit_name: str) -> bool:
        """Check if a resource limit is unlimited (no cap)."""
        return self.get_limit(limit_name) == -1

    def to_dict(self) -> dict:
        return {
            "tier": self.tier.value,
            "license_key": self.license_key,
            "activated_at": self.activated_at,
            "expires_at": self.expires_at,
            "seats": self.seats,
            "organization": self.organization,
            "contact_email": self.contact_email,
            "feature_overrides": self.feature_overrides,
            "disabled_features": list(self.disabled_features),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "License":
        tier_str = data.get("tier", "free")
        try:
            tier = LicenseTier(tier_str)
        except ValueError:
            tier = LicenseTier.FREE

        return cls(
            tier=tier,
            license_key=data.get("license_key", ""),
            activated_at=data.get("activated_at", ""),
            expires_at=data.get("expires_at"),
            seats=data.get("seats", 1),
            organization=data.get("organization", ""),
            contact_email=data.get("contact_email", ""),
            feature_overrides=data.get("feature_overrides", {}),
            disabled_features=set(data.get("disabled_features", [])),
        )

    @classmethod
    def free_tier(cls) -> "License":
        """Create a default free-tier license."""
        return cls(tier=LicenseTier.FREE)
