"""Tests for Privacy-First Architecture (ADR-0017)."""

import json
import tempfile
from pathlib import Path
from typing import Tuple

import pytest

from hiveos.privacy import (
    DataClassification,
    EgressPolicy,
    EndpointConfig,
    NetworkGuard,
    PrivacyAuditTrail,
    PrivacyConfig,
    PrivacyViolation,
)


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def privacy_config() -> PrivacyConfig:
    """Default BLOCK_ALL privacy config."""
    return PrivacyConfig()


@pytest.fixture
def audit_db(tmp_path: Path) -> Path:
    return tmp_path / "privacy_audit.db"


@pytest.fixture
def audit_trail(audit_db: Path) -> PrivacyAuditTrail:
    return PrivacyAuditTrail(audit_db)


# ── PrivacyConfig Tests ───────────────────────────────────────────────────


class TestPrivacyConfig:
    def test_default_policy_is_block_all(self):
        config = PrivacyConfig()
        assert config.egress_policy == EgressPolicy.BLOCK_ALL

    def test_default_never_leave_has_customer_data(self):
        config = PrivacyConfig()
        assert DataClassification.CUSTOMER_DATA in config.never_leave
        assert DataClassification.ORG_KNOWLEDGE in config.never_leave

    def test_default_endpoints_are_disabled(self):
        config = PrivacyConfig()
        for ep_id, ep in config.allowed_endpoints.items():
            assert ep.enabled == False, f"{ep_id} should be disabled by default"

    def test_enable_endpoint(self):
        config = PrivacyConfig()
        assert config.enable_endpoint("registry") == True
        assert config.allowed_endpoints["registry"].enabled == True

    def test_enable_unknown_endpoint_returns_false(self):
        config = PrivacyConfig()
        assert config.enable_endpoint("nonexistent") == False

    def test_disable_endpoint(self):
        config = PrivacyConfig()
        config.enable_endpoint("registry")
        assert config.disable_endpoint("registry") == True
        assert config.allowed_endpoints["registry"].enabled == False

    def test_is_egress_allowed_blocked_by_default(self):
        config = PrivacyConfig()
        assert config.is_egress_allowed("registry", [DataClassification.METADATA]) == False

    def test_is_egress_allowed_after_enable_and_policy_change(self):
        config = PrivacyConfig()
        config.enable_endpoint("registry")
        config.set_policy(EgressPolicy.ALLOW_REGISTRY)
        assert config.is_egress_allowed("registry", [DataClassification.METADATA]) == True

    def test_is_egress_rejected_for_never_leave_data(self):
        config = PrivacyConfig()
        config.enable_endpoint("registry")
        config.set_policy(EgressPolicy.ALLOW_ALL)
        # CUSTOMER_DATA always blocked
        assert config.is_egress_allowed("registry", [DataClassification.CUSTOMER_DATA]) == False

    def test_save_and_load_roundtrip(self, tmp_path):
        config = PrivacyConfig()
        config.enable_endpoint("registry")
        config.set_policy(EgressPolicy.ALLOW_REGISTRY)

        path = tmp_path / "privacy.json"
        config.save(path)

        loaded = PrivacyConfig.load(path)
        assert loaded.egress_policy == EgressPolicy.ALLOW_REGISTRY
        assert loaded.allowed_endpoints["registry"].enabled == True

    def test_load_from_nonexistent_returns_defaults(self, tmp_path):
        path = tmp_path / "nonexistent.json"
        config = PrivacyConfig.load(path)
        assert config.egress_policy == EgressPolicy.BLOCK_ALL

    def test_set_policy(self):
        config = PrivacyConfig()
        config.set_policy(EgressPolicy.ALLOW_ALL)
        assert config.egress_policy == EgressPolicy.ALLOW_ALL

    def test_add_endpoint(self):
        config = PrivacyConfig()
        ep = EndpointConfig(
            url="https://example.com",
            purpose="Test",
            data_types=[DataClassification.METADATA],
        )
        config.add_endpoint("test", ep)
        assert "test" in config.allowed_endpoints
        assert config.allowed_endpoints["test"].enabled == False  # Always disabled on add

    def test_can_use_ai_provider_default_false(self):
        config = PrivacyConfig()
        assert config.can_use_ai_provider() == False

    def test_can_access_registry_after_enable(self):
        config = PrivacyConfig()
        config.enable_endpoint("registry")
        config.set_policy(EgressPolicy.ALLOW_REGISTRY)
        assert config.can_access_registry() == True

    def test_can_check_updates_after_enable(self):
        config = PrivacyConfig()
        config.enable_endpoint("updates")
        config.set_policy(EgressPolicy.ALLOW_ALL)
        assert config.can_check_updates() == True


# ── NetworkGuard Tests ───────────────────────────────────────────────────


class TestNetworkGuard:
    def test_block_all_by_default(self, privacy_config):
        guard = NetworkGuard(privacy_config)
        result = guard.check_egress("https://example.com")
        assert result.allowed == False
        assert "BLOCK_ALL" in result.reason

    def test_allow_after_config_change(self, privacy_config):
        privacy_config.set_policy(EgressPolicy.ALLOW_ALL)
        privacy_config.allowed_domains.add("example.com")
        guard = NetworkGuard(privacy_config)
        result = guard.check_egress("https://example.com/path")
        assert result.allowed == True

    def test_block_data_type_in_never_leave(self, privacy_config):
        privacy_config.set_policy(EgressPolicy.ALLOW_ALL)
        guard = NetworkGuard(privacy_config)
        result = guard.check_egress(
            "https://example.com",
            data_types=[DataClassification.CUSTOMER_DATA],
        )
        assert result.allowed == False
        assert "customer_data" in result.reason

    def test_block_unknown_endpoint(self, privacy_config):
        privacy_config.set_policy(EgressPolicy.ALLOW_ALL)
        guard = NetworkGuard(privacy_config)
        result = guard.check_egress(
            "https://example.com",
            endpoint_id="nonexistent",
        )
        assert result.allowed == False
        assert "unknown endpoint" in result.reason.lower()

    def test_block_disabled_endpoint(self, privacy_config):
        privacy_config.set_policy(EgressPolicy.ALLOW_ALL)
        guard = NetworkGuard(privacy_config)
        result = guard.check_egress(
            "https://registry.hiveos.dev",
            endpoint_id="registry",
            data_types=[DataClassification.METADATA],
        )
        assert result.allowed == False
        assert "disabled" in result.reason.lower()

    def test_allow_enabled_endpoint(self, privacy_config):
        privacy_config.set_policy(EgressPolicy.ALLOW_ALL)
        privacy_config.enable_endpoint("registry")
        guard = NetworkGuard(privacy_config)
        result = guard.check_egress(
            "https://registry.hiveos.dev",
            endpoint_id="registry",
            data_types=[DataClassification.METADATA],
        )
        assert result.allowed == True

    def test_block_explicitly_blocked_domain(self, privacy_config):
        privacy_config.blocked_domains.add("evil.example.com")
        guard = NetworkGuard(privacy_config)
        result = guard.check_egress("https://evil.example.com")
        assert result.allowed == False
        assert "blocked" in result.reason.lower()

    def test_block_domain_not_in_allowed_list(self, privacy_config):
        privacy_config.set_policy(EgressPolicy.ALLOW_ALL)
        privacy_config.allowed_domains.add("good.example.com")
        guard = NetworkGuard(privacy_config)
        result = guard.check_egress("https://bad.example.com")
        assert result.allowed == False
        assert "not in allowed" in result.reason.lower()

    def test_stats_count(self, privacy_config):
        guard = NetworkGuard(privacy_config)
        guard.check_egress("https://blocked.com")  # Blocked
        guard.check_egress("https://blocked2.com")  # Blocked
        assert guard.stats["blocked"] == 2
        assert guard.stats["total"] == 2

    def test_reset_stats(self, privacy_config):
        guard = NetworkGuard(privacy_config)
        guard.check_egress("https://blocked.com")  # Blocked
        guard.reset_stats()
        assert guard.stats["blocked"] == 0


# ── PrivacyAuditTrail Tests ──────────────────────────────────────────────


class TestPrivacyAuditTrail:
    def test_log_and_retrieve(self, audit_trail):
        from hiveos.privacy import EgressAuditEntry

        entry = EgressAuditEntry(
            url="https://example.com",
            method="GET",
            allowed=True,
            reason="Test entry",
            data_types=[DataClassification.METADATA],
        )
        entry_id = audit_trail.log_egress(entry)
        assert entry_id > 0

        recent = audit_trail.get_recent(limit=10)
        assert len(recent) == 1
        assert recent[0].url == "https://example.com"
        assert recent[0].allowed == True

    def test_get_blocked_only(self, audit_trail):
        from hiveos.privacy import EgressAuditEntry

        audit_trail.log_egress(EgressAuditEntry(url="https://ok.com", allowed=True, reason="OK"))
        audit_trail.log_egress(EgressAuditEntry(url="https://blocked.com", allowed=False, reason="NO"))
        audit_trail.log_egress(EgressAuditEntry(url="https://ok2.com", allowed=True, reason="OK"))

        blocked = audit_trail.get_blocked()
        assert len(blocked) == 1
        assert blocked[0].url == "https://blocked.com"

    def test_stats(self, audit_trail):
        from hiveos.privacy import EgressAuditEntry

        audit_trail.log_egress(EgressAuditEntry(url="https://ok.com", allowed=True, reason="OK", endpoint_id="registry"))
        audit_trail.log_egress(EgressAuditEntry(url="https://blocked.com", allowed=False, reason="NO", endpoint_id="registry"))

        stats = audit_trail.get_stats()
        assert stats["total_egress_attempts"] == 2
        assert stats["allowed"] == 1
        assert stats["blocked"] == 1

    def test_cleanup_old(self, audit_trail):
        from hiveos.privacy import EgressAuditEntry
        from datetime import datetime, timezone, timedelta

        # Old entry
        old = EgressAuditEntry(
            url="https://old.com",
            allowed=True,
            reason="Old",
            timestamp=datetime.now(timezone.utc) - timedelta(days=200),
        )
        audit_trail.log_egress(old)

        # Recent entry
        recent = EgressAuditEntry(
            url="https://recent.com",
            allowed=True,
            reason="Recent",
        )
        audit_trail.log_egress(recent)

        deleted = audit_trail.cleanup_old(retention_days=90)
        assert deleted == 1  # Old entry deleted

    def test_log_rejects_customer_data(self, audit_trail, privacy_config):
        """Verify privacy enforcement at the NetworkGuard level."""
        guard = NetworkGuard(privacy_config)
        result = guard.check_egress(
            "https://example.com",
            data_types=[DataClassification.CUSTOMER_DATA],
        )
        assert result.allowed == False


# ── PrivacyGuard (monkey-patch) Tests ────────────────────────────────────


class TestPrivacyGuard:
    def test_privacy_guard_install_and_uninstall(self, privacy_config):
        import urllib.request
        from hiveos.privacy import PrivacyGuard

        guard = PrivacyGuard(privacy_config)
        original_urlopen = urllib.request.urlopen

        guard.install()
        assert urllib.request.urlopen != original_urlopen

        guard.uninstall()
        assert urllib.request.urlopen == original_urlopen

    def test_privacy_guard_blocks_with_block_all(self, privacy_config):
        """PrivacyGuard blocks external calls when BLOCK_ALL."""
        import urllib.request
        from urllib.error import URLError
        from hiveos.privacy import PrivacyGuard, PrivacyViolation

        guard = PrivacyGuard(privacy_config)
        guard.install()

        with pytest.raises(PrivacyViolation):
            urllib.request.urlopen("http://example.com")

        guard.uninstall()


# ── End-to-end: Config Save/Load → Guard → Audit ────────────────────────


class TestPrivacyIntegration:
    def test_config_guard_audit_integration(self, tmp_path):
        """End-to-end: configure policy → guard request → audit trail."""
        # Setup
        config_path = tmp_path / "privacy.json"
        audit_path = tmp_path / "privacy_audit.db"

        config = PrivacyConfig()
        config.enable_endpoint("registry")
        config.set_policy(EgressPolicy.ALLOW_REGISTRY)
        config.save(config_path)

        # Reload
        loaded = PrivacyConfig.load(config_path)
        guard = NetworkGuard(loaded)
        audit = PrivacyAuditTrail(audit_path)

        # Guard allows registry
        result = guard.check_egress(
            "https://registry.hiveos.dev/packs",
            endpoint_id="registry",
            data_types=[DataClassification.METADATA],
        )
        assert result.allowed == True

        # Log to audit
        from hiveos.privacy import EgressAuditEntry
        audit.log_egress(EgressAuditEntry(
            url="https://registry.hiveos.dev/packs",
            method="GET",
            allowed=True,
            reason=result.reason,
            data_types=[DataClassification.METADATA],
        ))

        # Verify audit
        entries = audit.get_recent(limit=10)
        assert len(entries) == 1
        assert entries[0].allowed == True

        # Guard blocks request with customer data (always blocked)
        blocked = guard.check_egress(
            "https://registry.hiveos.dev/packs",
            endpoint_id="registry",
            data_types=[DataClassification.CUSTOMER_DATA],
        )
        assert blocked.allowed == False

        audit.log_egress(EgressAuditEntry(
            url="https://registry.hiveos.dev/packs",
            method="POST",
            allowed=False,
            reason=blocked.reason,
        ))

        # Verify both in audit
        all_entries = audit.get_recent(limit=10)
        assert len(all_entries) == 2
        assert sum(1 for e in all_entries if e.allowed) == 1
        assert sum(1 for e in all_entries if not e.allowed) == 1
