"""Tests for Mothership Task Router."""

import pytest
from src.hiveos.mothership.task_router import (
    TaskRouter,
    TaskAssignment,
    RouteStrategy,
    RoutingRule,
)
from src.hiveos.mothership.agent_registry import (
    AgentRegistry,
    CapabilityDeclaration,
)


@pytest.fixture
def registry(tmp_path):
    p = tmp_path / "agents.yaml"
    return AgentRegistry(registry_path=p, heartbeat_timeout=5)


@pytest.fixture
def router(registry):
    return TaskRouter(registry=registry, default_strategy=RouteStrategy.BEST_FIT)


class TestTaskRouter:
    """Task routing tests."""

    def test_no_candidates_returns_none(self, router):
        """Routing with no registered agents returns None."""
        assignment = router.route(
            agent_id="researcher",
            required_capability="web-search",
        )
        assert assignment is None

    def test_route_to_exact_capability(self, router, registry):
        """Route to the only agent with matching capability."""
        registry.register(
            name="node1",
            url="http://node1:8080",
            capabilities={
                "web-search": CapabilityDeclaration(name="web-search"),
            },
        )
        registry.record_heartbeat("node1")

        assignment = router.route(
            agent_id="researcher",
            required_capability="web-search",
        )
        assert assignment is not None
        assert assignment.node_name == "node1"
        assert assignment.agent_name == "researcher"
        assert assignment.capability == "web-search"

    def test_route_prefers_online_over_unknown(self, router, registry):
        """Route should prefer online nodes."""
        registry.register(
            name="offline-node",
            url="http://offline:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
        )
        registry.register(
            name="online-node",
            url="http://online:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
        )
        registry.record_heartbeat("online-node")

        assignment = router.route(agent_id="worker", required_capability="task")
        assert assignment.node_name == "online-node"

    def test_least_loaded_strategy(self, router, registry):
        """LEAST_LOADED should pick the least loaded node."""
        registry.register(
            name="busy",
            url="http://busy:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
            max_concurrent=10,
        )
        registry.register(
            name="idle",
            url="http://idle:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
            max_concurrent=10,
        )
        registry.record_heartbeat("busy", load=8)
        registry.record_heartbeat("idle", load=0)

        assignment = router.route(
            agent_id="worker",
            required_capability="task",
            strategy=RouteStrategy.LEAST_LOADED,
        )
        assert assignment.node_name == "idle"

    def test_capacity_full_skipped(self, router, registry):
        """Node at max capacity should not receive assignments."""
        registry.register(
            name="full",
            url="http://full:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
            max_concurrent=2,
        )
        registry.record_heartbeat("full")
        registry.record_task_assignment("full")
        registry.record_task_assignment("full")

        registry.register(
            name="available",
            url="http://available:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
            max_concurrent=5,
        )
        registry.record_heartbeat("available")

        assignment = router.route(
            agent_id="worker",
            required_capability="task",
        )
        assert assignment.node_name == "available"

    def test_preferred_nodes(self, router, registry):
        """Preferred nodes should be prioritized."""
        registry.register(
            name="node-a",
            url="http://a:8080",
            capabilities={"scan": CapabilityDeclaration(name="scan")},
        )
        registry.register(
            name="node-b",
            url="http://b:8080",
            capabilities={"scan": CapabilityDeclaration(name="scan")},
        )
        registry.record_heartbeat("node-a")
        registry.record_heartbeat("node-b")

        assignment = router.route(
            agent_id="scanner",
            required_capability="scan",
            preferred_nodes=["node-b"],
        )
        assert assignment.node_name == "node-b"

    def test_excluded_nodes(self, router, registry):
        """Excluded nodes should be skipped."""
        registry.register(
            name="node-a",
            url="http://a:8080",
            capabilities={"work": CapabilityDeclaration(name="work")},
        )
        registry.register(
            name="node-b",
            url="http://b:8080",
            capabilities={"work": CapabilityDeclaration(name="work")},
        )
        registry.record_heartbeat("node-a")
        registry.record_heartbeat("node-b")

        assignment = router.route(
            agent_id="worker",
            required_capability="work",
            excluded_nodes=["node-a"],
        )
        assert assignment.node_name == "node-b"

    def test_routing_rule_applied(self, router, registry):
        """Custom routing rules should override defaults."""
        registry.register(
            name="heavy",
            url="http://heavy:8080",
            capabilities={"compute": CapabilityDeclaration(name="compute")},
            max_concurrent=5,
        )
        registry.register(
            name="light",
            url="http://light:8080",
            capabilities={"compute": CapabilityDeclaration(name="compute")},
            max_concurrent=5,
        )
        registry.record_heartbeat("heavy")
        registry.record_heartbeat("light")

        rule = RoutingRule(
            capability="compute",
            strategy=RouteStrategy.ROUND_ROBIN,
            max_load_factor=1.0,
        )
        router.add_rule(rule)

        assignment = router.route(agent_id="worker", required_capability="compute")
        assert assignment is not None
        # ROUND_ROBIN should work

    def test_capability_first_strategy(self, router, registry):
        registry.register(
            name="node-a",
            url="http://a:8080",
            capabilities={"web": CapabilityDeclaration(name="web")},
        )
        registry.record_heartbeat("node-a")

        assignment = router.route(
            agent_id="scraper",
            required_capability="web",
            strategy=RouteStrategy.CAPABILITY_FIRST,
        )
        assert assignment is not None

    def test_round_robin_distributes(self, router, registry):
        """Round robin should distribute across available nodes."""
        registry.register(
            name="worker-a",
            url="http://a:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
            max_concurrent=10,
        )
        registry.register(
            name="worker-b",
            url="http://b:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
            max_concurrent=10,
        )
        registry.record_heartbeat("worker-a")
        registry.record_heartbeat("worker-b")

        results = set()
        for i in range(4):
            a = router.route(
                agent_id=f"task-{i}",
                required_capability="task",
                strategy=RouteStrategy.ROUND_ROBIN,
            )
            if a:
                results.add(a.node_name)

        assert len(results) == 2  # Both nodes used

    def test_affinity_strategy(self, router, registry):
        """AFFINITY strategy should prefer nodes with history."""
        registry.register(
            name="veteran",
            url="http://vet:8080",
            capabilities={"code": CapabilityDeclaration(name="code")},
        )
        registry.register(
            name="rookie",
            url="http://rook:8080",
            capabilities={"code": CapabilityDeclaration(name="code")},
        )
        registry.record_heartbeat("veteran")
        registry.record_heartbeat("rookie")
        registry.record_completion("veteran", success=True)
        registry.record_completion("veteran", success=True)

        assignment = router.route(
            agent_id="coder",
            required_capability="code",
            strategy=RouteStrategy.AFFINITY,
        )
        assert assignment.node_name == "veteran"

    def test_reroute_failed_task(self, router, registry):
        """Failed task should be rerouted to a different node."""
        registry.register(
            name="node-a",
            url="http://a:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
        )
        registry.register(
            name="node-b",
            url="http://b:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
        )
        registry.record_heartbeat("node-a")
        registry.record_heartbeat("node-b")

        orig = router.route(agent_id="worker", required_capability="task")
        assert orig is not None

        rerouted = router.reroute(orig.task_id, reason="test_failure")
        assert rerouted is not None
        assert rerouted.node_name != orig.node_name  # Should be different node

    def test_reroute_no_alternative(self, router, registry):
        """Reroute should return None if no alternative available."""
        registry.register(
            name="lonely",
            url="http://lonely:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
        )
        registry.record_heartbeat("lonely")

        orig = router.route(agent_id="worker", required_capability="task")
        assert orig is not None

        rerouted = router.reroute(orig.task_id, reason="test")
        assert rerouted is None  # No other nodes

    def test_metrics_tracking(self, router, registry):
        """Router should track assignment metrics."""
        registry.register(
            name="metric-node",
            url="http://metric:8080",
            capabilities={"test": CapabilityDeclaration(name="test")},
        )
        registry.record_heartbeat("metric-node")

        router.route(agent_id="t1", required_capability="test")
        router.route(agent_id="t2", required_capability="test")

        # Record completions
        tasks = router.list_active_assignments()
        for t in tasks:
            router.record_completion(t.task_id, success=True)

        m = router.metrics.summary()
        assert m["total"] == 2
        assert "test" in m["by_capability"]

    def test_rule_management(self, router):
        """Add and remove rules."""
        rule = RoutingRule(capability="test", strategy=RouteStrategy.LEAST_LOADED)
        router.add_rule(rule)
        assert len(router.rules) == 1

        result = router.remove_rule("test")
        assert result is True
        assert len(router.rules) == 0

        result = router.remove_rule("nonexistent")
        assert result is False

    def test_clear_rules(self, router):
        router.add_rule(RoutingRule(capability="a"))
        router.add_rule(RoutingRule(capability="b"))
        router.clear_rules()
        assert len(router.rules) == 0
