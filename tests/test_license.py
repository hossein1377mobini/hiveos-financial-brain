"""
Tests for HiveOS License Manager — pricing tiers, feature gating, and activation.

Covers:
- License model creation and serialization
- Feature flag checks per tier
- Resource limits per tier
- License activation/deactivation
- Tier upgrades and comparison
- Demo key activation
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def temp_dir():
    """Temporary directory for license storage."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def license_mgr(temp_dir):
    """LicenseManager with temp storage directory."""
    from hiveos.license import LicenseManager
    mgr = LicenseManager(license_path=temp_dir / "license.yaml")
    return mgr


# ── Model Tests ──────────────────────────────────────────────────────


class TestLicenseModels:
    """Test License dataclass and enums."""

    def test_tier_ordering(self):
        """Tiers are ordered by capability."""
        from hiveos.license import LicenseTier
        ordered = LicenseTier.ordered()
        assert ordered == [
            LicenseTier.FREE,
            LicenseTier.PRO,
            LicenseTier.ENTERPRISE,
            LicenseTier.ULTIMATE,
        ]

    def test_tier_comparison(self):
        """Tier comparison operators work."""
        from hiveos.license import LicenseTier
        assert LicenseTier.ULTIMATE >= LicenseTier.PRO
        assert LicenseTier.PRO >= LicenseTier.FREE
        assert LicenseTier.ENTERPRISE > LicenseTier.PRO
        assert not (LicenseTier.FREE >= LicenseTier.PRO)

    def test_free_tier_creation(self):
        """Free tier license creates correctly."""
        from hiveos.license import License
        lic = License.free_tier()
        assert lic.tier.value == "free"
        assert lic.is_active is True
        assert lic.is_expired is False
        assert lic.tier_label == "Free"

    def test_pro_tier(self):
        """Pro tier license."""
        from hiveos.license import License, LicenseTier
        lic = License(tier=LicenseTier.PRO)
        assert lic.tier_label == "Pro"
        assert lic.is_active is True

    def test_enterprise_tier(self):
        """Enterprise tier license."""
        from hiveos.license import License, LicenseTier
        lic = License(tier=LicenseTier.ENTERPRISE, organization="Acme Corp")
        assert lic.tier_label == "Enterprise"
        assert lic.organization == "Acme Corp"

    def test_ultimate_tier(self):
        """Ultimate tier has all features."""
        from hiveos.license import License, LicenseTier, FeatureFlag, ALL_FEATURES
        lic = License(tier=LicenseTier.ULTIMATE)
        for f in ALL_FEATURES:
            assert lic.has_feature(f), f"Ultimate should have feature: {f.value}"

    def test_serialization_roundtrip(self):
        """License serializes and deserializes correctly."""
        from hiveos.license import License, LicenseTier
        from datetime import datetime, timedelta

        original = License(
            tier=LicenseTier.ENTERPRISE,
            license_key="hive-test-key",
            organization="Test Corp",
            contact_email="admin@test.com",
            activated_at=datetime.utcnow().isoformat(),
            expires_at=(datetime.utcnow() + timedelta(days=365)).isoformat(),
            seats=10,
        )
        data = original.to_dict()
        restored = License.from_dict(data)
        assert restored.tier == original.tier
        assert restored.license_key == original.license_key
        assert restored.organization == original.organization
        assert restored.seats == original.seats


class TestFeatureFlags:
    """Test feature gating per tier."""

    def test_free_has_basic_features(self):
        """Free tier has basic features."""
        from hiveos.license import License, FeatureFlag
        lic = License.free_tier()
        assert lic.has_feature(FeatureFlag.FLOW_TEMPLATES)
        assert not lic.has_feature(FeatureFlag.MULTI_WORKSPACE)
        assert not lic.has_feature(FeatureFlag.ADVANCED_RBAC)
        assert not lic.has_feature(FeatureFlag.SSO)

    def test_pro_has_core_features(self):
        """Pro tier has workspace, RBAC, audit export."""
        from hiveos.license import License, LicenseTier, FeatureFlag
        lic = License(tier=LicenseTier.PRO)
        assert lic.has_feature(FeatureFlag.MULTI_WORKSPACE)
        assert lic.has_feature(FeatureFlag.ADVANCED_RBAC)
        assert lic.has_feature(FeatureFlag.DOMAIN_PLUGINS)
        assert not lic.has_feature(FeatureFlag.SSO)
        assert not lic.has_feature(FeatureFlag.UNLIMITED_AGENTS)

    def test_enterprise_has_security_features(self):
        """Enterprise tier has SSO and compliance."""
        from hiveos.license import License, LicenseTier, FeatureFlag
        lic = License(tier=LicenseTier.ENTERPRISE)
        assert lic.has_feature(FeatureFlag.SSO)
        assert lic.has_feature(FeatureFlag.PRIORITY_SUPPORT)
        assert lic.has_feature(FeatureFlag.ANALYTICS)
        assert not lic.has_feature(FeatureFlag.WHITE_LABEL)

    def test_ultimate_has_everything(self):
        """Ultimate includes all features."""
        from hiveos.license import License, LicenseTier, FeatureFlag, ALL_FEATURES
        lic = License(tier=LicenseTier.ULTIMATE)
        for f in ALL_FEATURES:
            assert lic.has_feature(f)

    def test_feature_overrides(self):
        """Feature overrides can enable features on lower tiers."""
        from hiveos.license import License, LicenseTier, FeatureFlag
        lic = License(
            tier=LicenseTier.FREE,
            feature_overrides={"sso": True},
        )
        assert lic.has_feature(FeatureFlag.SSO)

    def test_disabled_features(self):
        """License can explicitly disable features."""
        from hiveos.license import License, LicenseTier, FeatureFlag
        lic = License(
            tier=LicenseTier.ULTIMATE,
            disabled_features={"sso"},
        )
        assert not lic.has_feature(FeatureFlag.SSO)


class TestResourceLimits:
    """Test resource limits per tier."""

    def test_free_limits(self):
        """Free tier has strict limits."""
        from hiveos.license import License
        lic = License.free_tier()
        assert lic.get_limit("max_workspaces") == 1
        assert lic.get_limit("max_agents") == 3
        assert lic.get_limit("max_flows") == 5
        assert lic.get_limit("max_nodes") == 1
        assert not lic.is_unlimited("max_agents")

    def test_pro_limits(self):
        """Pro tier has moderate limits."""
        from hiveos.license import License, LicenseTier
        lic = License(tier=LicenseTier.PRO)
        assert lic.get_limit("max_workspaces") == 5
        assert lic.get_limit("max_agents") == 20
        assert lic.get_limit("max_flows") == 50
        assert not lic.is_unlimited("max_workspaces")

    def test_enterprise_unlimited_agents(self):
        """Enterprise has unlimited agents and flows."""
        from hiveos.license import License, LicenseTier
        lic = License(tier=LicenseTier.ENTERPRISE)
        assert lic.is_unlimited("max_agents")
        assert lic.is_unlimited("max_flows")
        assert not lic.is_unlimited("max_nodes")  # 25 node cap

    def test_ultimate_unlimited_everything(self):
        """Ultimate has unlimited everything."""
        from hiveos.license import License, LicenseTier
        lic = License(tier=LicenseTier.ULTIMATE)
        assert lic.is_unlimited("max_workspaces")
        assert lic.is_unlimited("max_agents")
        assert lic.is_unlimited("max_flows")
        assert lic.is_unlimited("max_nodes")


class TestLicenseManager:
    """Test LicenseManager CRUD and activation."""

    def test_default_is_free(self, license_mgr):
        """Default license is free tier."""
        assert license_mgr.tier.value == "free"

    def test_activate_demo_pro(self, license_mgr):
        """Activate Pro demo key."""
        assert license_mgr.activate("hive-pro-demo")
        assert license_mgr.tier.value == "pro"

    def test_activate_demo_enterprise(self, license_mgr):
        """Activate Enterprise demo key."""
        assert license_mgr.activate("hive-ent-demo")
        assert license_mgr.tier.value == "enterprise"

    def test_activate_demo_ultimate(self, license_mgr):
        """Activate Ultimate demo key."""
        assert license_mgr.activate("hive-ult-demo")
        assert license_mgr.tier.value == "ultimate"

    def test_activate_invalid_key(self, license_mgr):
        """Invalid license key is rejected."""
        assert not license_mgr.activate("invalid-key")

    def test_activate_real_key(self, license_mgr):
        """Real license key format activates."""
        assert license_mgr.activate("hive-real-license-key-12345")
        assert license_mgr.tier.value in ("pro",)

    def test_activate_enterprise_key(self, license_mgr):
        """Enterprise key detected by prefix."""
        assert license_mgr.activate("hive-ent-custom-abcde")
        assert license_mgr.tier.value == "enterprise"

    def test_deactivate(self, license_mgr):
        """Deactivate returns to free tier."""
        license_mgr.activate("hive-pro-demo")
        assert license_mgr.tier.value == "pro"
        license_mgr.deactivate()
        assert license_mgr.tier.value == "free"

    def test_persistence(self, temp_dir):
        """License persists across manager instances."""
        from hiveos.license import LicenseManager
        mgr1 = LicenseManager(license_path=temp_dir / "license.yaml")
        mgr1.activate("hive-pro-demo")

        mgr2 = LicenseManager(license_path=temp_dir / "license.yaml")
        assert mgr2.tier.value == "pro"

    def test_upgrade_tier(self, license_mgr):
        """Upgrade to a specific tier."""
        from hiveos.license import LicenseTier
        license_mgr.upgrade_tier(LicenseTier.ENTERPRISE)
        assert license_mgr.tier.value == "enterprise"

    def test_feature_check_after_activation(self, license_mgr):
        """Feature availability changes after activation."""
        from hiveos.license import FeatureFlag

        assert not license_mgr.has_feature(FeatureFlag.MULTI_WORKSPACE)
        assert not license_mgr.has_feature(FeatureFlag.SSO)

        license_mgr.activate("hive-ent-demo")

        assert license_mgr.has_feature(FeatureFlag.MULTI_WORKSPACE)
        assert license_mgr.has_feature(FeatureFlag.SSO)

    def test_is_within_limit(self, license_mgr):
        """Check if value is within limit."""
        assert license_mgr.is_within_limit("max_workspaces", 1)  # Free: max 1
        assert not license_mgr.is_within_limit("max_workspaces", 2)  # Exceeded

    def test_upgrade_path(self, license_mgr):
        """Upgrade path from Free lists available upgrades."""
        paths = license_mgr.upgrade_path()
        assert "pro" in paths
        assert "enterprise" in paths
        assert "ultimate" in paths

    def test_list_tiers(self, license_mgr):
        """List all available tiers."""
        tiers = license_mgr.list_tiers()
        assert len(tiers) == 4
        assert tiers[0]["tier"] == "free"
        assert tiers[1]["tier"] == "pro"

    def test_compare_tiers(self, license_mgr):
        """Compare tiers returns current + all tiers."""
        data = license_mgr.compare_tiers()
        assert data["current"] == "free"
        assert len(data["tiers"]) == 4
