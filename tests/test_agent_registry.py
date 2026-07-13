"""Tests for Mothership Agent Registry."""

from pathlib import Path
import time
import pytest
from src.hiveos.mothership.agent_registry import (
    AgentRegistry,
    AgentStatus,
    CapabilityDeclaration,
)


class TestAgentRegistry:
    """AgentRegistry CRUD and capability tests."""

    @pytest.fixture
    def registry(self, tmp_path):
        p = tmp_path / "agents.yaml"
        return AgentRegistry(registry_path=p, heartbeat_timeout=5)

    def test_init_empty(self, registry):
        """Fresh registry has no agents."""
        assert registry.count() == 0
        assert registry.list() == []

    def test_register_single(self, registry):
        """Register an agent and verify it exists."""
        agent = registry.register(
            name="alpha",
            url="http://alpha.local:8080",
            api_key="key123",
            description="Alpha agent",
            capabilities={
                "web-search": CapabilityDeclaration(
                    name="web-search",
                    version="1.0.0",
                    description="Web search capability",
                ),
                "research": CapabilityDeclaration(
                    name="research",
                    version="2.0.0",
                ),
            },
            max_concurrent=10,
        )
        assert agent.name == "alpha"
        assert agent.url == "http://alpha.local:8080"
        assert agent.api_key == "key123"
        assert len(agent.capabilities) == 2
        assert "web-search" in agent.capabilities
        assert agent.capabilities["web-search"].version == "1.0.0"
        assert agent.status == "unknown"
        assert agent.max_concurrent == 10
        assert registry.count() == 1

    def test_register_existing_updates(self, registry):
        """Re-registering same name updates the agent."""
        registry.register(
            name="beta",
            url="http://old.url",
            capabilities={"basic": CapabilityDeclaration(name="basic")},
        )
        r2 = registry.register(
            name="beta",
            url="http://new.url",
            capabilities={"advanced": CapabilityDeclaration(name="advanced")},
        )
        assert r2.url == "http://new.url"
        assert "advanced" in r2.capabilities
        assert registry.count() == 1

    def test_register_persists(self, registry):
        """Registered agents persist to YAML file."""
        registry.register(name="charlie", url="http://charlie.io")
        r2 = AgentRegistry(registry_path=registry.registry_path)
        assert r2.count() == 1
        assert r2.get("charlie") is not None

    def test_get_nonexistent(self, registry):
        """Getting a non-existent agent returns None."""
        assert registry.get("nonexistent") is None

    def test_unregister(self, registry):
        registry.register(name="delta", url="http://delta.io")
        assert registry.count() == 1
        result = registry.unregister("delta")
        assert result is True
        assert registry.count() == 0

    def test_unregister_missing(self, registry):
        result = registry.unregister("missing")
        assert result is False

    def test_heartbeat(self, registry):
        registry.register(name="echo", url="http://echo.io")
        before = registry.get("echo").last_seen
        time.sleep(0.01)
        result = registry.record_heartbeat("echo")
        assert result is True
        after = registry.get("echo").last_seen
        assert after != before
        assert registry.get("echo").status == "online"

    def test_heartbeat_missing(self, registry):
        result = registry.record_heartbeat("missing")
        assert result is False

    def test_heartbeat_with_load(self, registry):
        registry.register(name="foxtrot", url="http://foxtrot.io")
        registry.record_heartbeat("foxtrot", load=3)
        assert registry.get("foxtrot").current_load == 3

    def test_record_completion(self, registry):
        registry.register(name="golf", url="http://golf.io")
        registry.record_completion("golf", success=True)
        assert registry.get("golf").total_tasks_completed == 1
        assert registry.get("golf").total_errors == 0
        registry.record_completion("golf", success=False)
        assert registry.get("golf").total_errors == 1

    def test_record_task_assignment(self, registry):
        registry.register(name="hotel", url="http://hotel.io", max_concurrent=10)
        registry.record_task_assignment("hotel")
        assert registry.get("hotel").current_load == 1
        registry.record_completion("hotel", success=True)
        assert registry.get("hotel").current_load == 0

    def test_find_by_capability(self, registry):
        registry.register(name="india", url="http://india.io", capabilities={
            "web": CapabilityDeclaration(name="web"),
            "research": CapabilityDeclaration(name="research"),
        })
        registry.register(name="juliet", url="http://juliet.io", capabilities={
            "web": CapabilityDeclaration(name="web"),
        })
        results = registry.find_by_capability("web")
        assert len(results) == 2
        results = registry.find_by_capability("research")
        assert len(results) == 1

    def test_find_by_capability_min_version(self, registry):
        registry.register(name="kilo", url="http://kilo.io", capabilities={
            "code": CapabilityDeclaration(name="code", version="2.0.0"),
        })
        registry.register(name="lima", url="http://lima.io", capabilities={
            "code": CapabilityDeclaration(name="code", version="1.0.0"),
        })
        results = registry.find_by_capability("code", min_version="1.5.0")
        assert len(results) == 1
        assert results[0].name == "kilo"

    def test_find_available(self, registry):
        registry.register(name="mike", url="http://mike.io", capabilities={
            "scan": CapabilityDeclaration(name="scan"),
        })
        registry.record_heartbeat("mike")  # sets status to online
        registry.register(name="november", url="http://november.io", capabilities={
            "scan": CapabilityDeclaration(name="scan"),
        })
        # november is still "unknown" — should not appear in available
        available = registry.find_available("scan")
        assert len(available) == 1
        assert available[0].name == "mike"

    def test_list_capabilities(self, registry):
        registry.register(name="oscar", url="http://oscar.io", capabilities={
            "a": CapabilityDeclaration(name="a"),
            "b": CapabilityDeclaration(name="b"),
        })
        registry.register(name="papa", url="http://papa.io", capabilities={
            "a": CapabilityDeclaration(name="a"),
        })
        caps = registry.list_capabilities()
        assert caps["a"] == 2
        assert caps["b"] == 1

    def test_url_trailing_slash_stripped(self, registry):
        agent = registry.register(name="trailing", url="http://example.com/")
        assert agent.url == "http://example.com"

    def test_summary(self, registry):
        registry.register(name="s1", url="http://s1.io")
        registry.register(name="s2", url="http://s2.io")
        registry.record_heartbeat("s1")
        summary = registry.summary()
        assert summary["total_agents"] == 2
        assert summary["online_agents"] == 1
        assert summary["status_counts"]["online"] == 1
        assert summary["status_counts"]["unknown"] == 1

    def test_health_check_timeout_detected(self, registry):
        """Agent with stale heartbeat should be marked degraded/offline."""
        registry.register(name="old", url="http://old.io")
        # Record heartbeat with old timestamp by poking into internals
        from datetime import datetime, timedelta
        old_time = (datetime.utcnow() - timedelta(seconds=20)).isoformat()
        registry._agents["old"].last_heartbeat = old_time
        registry._agents["old"].status = "online"

        changes = registry.check_health()
        assert len(changes) > 0
        assert changes[0]["name"] == "old"
        assert changes[0]["new_status"] in ("degraded", "offline")
