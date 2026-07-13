"""Tests for Mothership-Satellite sync module."""

from pathlib import Path
import json
import tempfile
import time
from datetime import datetime
import pytest
from src.hiveos.sync.node_registry import NodeRegistry, SatelliteNode


class TestNodeRegistry:
    """NodeRegistry CRUD tests."""

    @pytest.fixture
    def registry(self, tmp_path):
        """Create a NodeRegistry backed by a temp file."""
        p = tmp_path / "nodes.yaml"
        return NodeRegistry(registry_path=p)

    def test_init_empty(self, registry):
        """Fresh registry has no nodes."""
        assert registry.count == 0
        assert registry.list() == []

    def test_register_single_node(self, registry):
        """Register a node and verify it exists."""
        node = registry.register(
            name="alpha",
            url="http://alpha.local:8080",
            api_key="secret123",
            description="Alpha test node",
            capabilities=["web", "research"],
        )
        assert node.name == "alpha"
        assert node.url == "http://alpha.local:8080"
        assert node.api_key == "secret123"
        assert node.capabilities == ["web", "research"]
        assert node.status == "unknown"
        assert node.last_seen is not None
        assert node.registered_at != ""
        assert registry.count == 1

    def test_register_existing_updates(self, registry):
        """Re-registering same name updates the node."""
        registry.register(
            name="beta",
            url="http://old.url",
            capabilities=["basic"],
        )
        # Update
        r2 = registry.register(
            name="beta",
            url="http://new.url",
            capabilities=["advanced"],
        )
        assert r2.url == "http://new.url"
        assert r2.capabilities == ["advanced"]
        # last_seen should still be set
        assert r2.last_seen is not None
        assert registry.count == 1

    def test_register_persists_to_file(self, registry):
        """Registered nodes are persisted to the YAML file."""
        registry.register(name="charlie", url="http://charlie.io", description="Persistent")
        # Load a new registry from the same file
        r2 = NodeRegistry(registry_path=registry.registry_path)
        assert r2.count == 1
        assert r2.get("charlie") is not None
        assert r2.get("charlie").description == "Persistent"

    def test_get_returns_none_for_missing(self, registry):
        """Getting a non-existent node returns None."""
        assert registry.get("nonexistent") is None

    def test_remove_existing(self, registry):
        registry.register(name="delta", url="http://delta.io")
        assert registry.count == 1
        result = registry.remove("delta")
        assert result is True
        assert registry.count == 0
        assert registry.get("delta") is None

    def test_remove_missing_returns_false(self, registry):
        result = registry.remove("missing")
        assert result is False
        assert registry.count == 0

    def test_update_heartbeat(self, registry):
        registry.register(name="echo", url="http://echo.io")
        before = registry.get("echo").last_seen
        time.sleep(0.01)
        result = registry.update_heartbeat("echo")
        assert result is True
        after = registry.get("echo").last_seen
        assert after != before
        assert registry.get("echo").status == "online"

    def test_update_heartbeat_missing(self, registry):
        result = registry.update_heartbeat("missing")
        assert result is False

    def test_list_multiple_nodes(self, registry):
        registry.register(name="a", url="http://a.io")
        registry.register(name="b", url="http://b.io")
        registry.register(name="c", url="http://c.io")
        nodes = registry.list()
        assert len(nodes) == 3
        names = sorted(n.name for n in nodes)
        assert names == ["a", "b", "c"]

    def test_remove_persists(self, registry):
        registry.register(name="keep", url="http://keep.io")
        registry.register(name="remove_me", url="http://remove.io")
        registry.remove("remove_me")
        r2 = NodeRegistry(registry_path=registry.registry_path)
        assert r2.count == 1
        assert r2.get("keep") is not None
        assert r2.get("remove_me") is None

    def test_sanitize_name_in_url(self, registry):
        """Node URL gets trailing slash stripped."""
        node = registry.register(name="trailing", url="http://example.com/")
        assert node.url == "http://example.com"
