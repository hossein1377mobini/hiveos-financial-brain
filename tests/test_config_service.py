"""Tests for HiveOS V2 ConfigService."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from hiveos.dashboard.config_service import ConfigService, DEFAULT_CONFIG


class TestConfigService:
    """ConfigService unit tests."""

    @pytest.fixture
    def config_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def config_path(self, config_dir):
        return config_dir / "config.yaml"

    @pytest.fixture
    def service(self, config_path):
        """Service with auto-created default config."""
        s = ConfigService(config_path)
        assert config_path.exists(), "Config file should be auto-created"
        return s

    def test_default_creation(self, config_path):
        """ConfigService creates default config when file missing."""
        s = ConfigService(config_path)
        assert config_path.exists()
        assert s.get("server.host") == "127.0.0.1"
        assert s.get("server.port") == 8420

    def test_get_default_fallback(self, service):
        """get() returns default for missing keys."""
        assert service.get("nonexistent.key") is None
        assert service.get("nonexistent.key", "fallback") == "fallback"

    def test_get_dot_notation(self, service):
        """get() resolves nested keys with dots."""
        assert service.get("server.port") == 8420
        assert service.get("ai.provider") == "local"
        assert service.get("logging.level") == "INFO"

    def test_set_and_get(self, service, config_path):
        """set() writes a value and persists to disk."""
        service.set("server.port", 9999)
        assert service.get("server.port") == 9999

        # Verify persisted to YAML
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert loaded["server"]["port"] == 9999

    def test_set_creates_nested_keys(self, service):
        """set() auto-creates intermediate dicts."""
        service.set("custom.nested.key", "deep_value")
        assert service.get("custom.nested.key") == "deep_value"

    def test_reload(self, service, config_path):
        """reload() discards in-memory changes and re-reads from disk."""
        service.set("server.port", 5555)

        # Modify file directly
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        data["server"]["port"] = 1111
        config_path.write_text(yaml.dump(data), encoding="utf-8")

        service.reload()
        assert service.get("server.port") == 1111

    def test_to_dict(self, service):
        """to_dict() returns a deep copy of the config."""
        d = service.to_dict()
        assert d["server"]["host"] == "127.0.0.1"
        # Verify it's a copy, not a reference
        d["server"]["host"] = "0.0.0.0"
        assert service.get("server.host") == "127.0.0.1"

    def test_load_existing_file(self, config_path):
        """Service reads an existing config file correctly."""
        data = {"server": {"host": "0.0.0.0", "port": 8080}}
        config_path.write_text(yaml.dump(data), encoding="utf-8")
        s = ConfigService(config_path)
        assert s.get("server.host") == "0.0.0.0"
        assert s.get("server.port") == 8080

    def test_load_corrupted_file(self, config_path):
        """Service raises on invalid YAML."""
        config_path.write_text("{{broken", encoding="utf-8")
        with pytest.raises(Exception):
            ConfigService(config_path)
