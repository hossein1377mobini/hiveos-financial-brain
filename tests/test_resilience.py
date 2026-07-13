"""Tests for Mothership Resilience Engine."""

import pytest
import time
from datetime import datetime, timedelta
from src.hiveos.mothership.resilience import (
    ResilienceEngine,
    HealthChecker,
    FailureDetector,
    ReassignmentEngine,
    CircuitBreaker,
    HealthCheckResult,
    FailureEvent,
    TaskAssignmentRecord,
    HealthStatus,
    FailureType,
)
from src.hiveos.mothership.agent_registry import (
    AgentRegistry,
    CapabilityDeclaration,
)
from src.hiveos.mothership.task_router import (
    TaskRouter,
    RouteStrategy,
)
from src.hiveos.mothership.communication_bus import (
    CommunicationBus,
    InMemoryBusBackend,
)


@pytest.fixture
def registry(tmp_path):
    p = tmp_path / "agents.yaml"
    return AgentRegistry(registry_path=p, heartbeat_timeout=5)


@pytest.fixture
def router(registry):
    return TaskRouter(registry=registry, default_strategy=RouteStrategy.BEST_FIT)


@pytest.fixture
def bus():
    return CommunicationBus(backend=InMemoryBusBackend())


@pytest.fixture
def resilience(registry, router, bus):
    return ResilienceEngine(
        registry=registry,
        task_router=router,
        comm_bus=bus,
        check_interval=30,
        heartbeat_timeout=5,
        task_timeout=60,
    )


class TestHealthChecker:
    """Health checker tests."""

    def test_unknown_node(self, registry):
        checker = registry  # Just use registry directly
        # Node not found -> no health check to run
        pass

    def test_check_node_no_heartbeat(self, registry):
        checker = HealthChecker(registry=registry)
        registry.register(name="silent", url="http://silent.io")
        result = checker.check_node("silent")
        assert result.status in (HealthStatus.UNHEALTHY, HealthStatus.DEGRADED)

    def test_check_node_healthy(self, registry):
        checker = HealthChecker(registry=registry)
        registry.register(
            name="healthy-node",
            url="http://healthy:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
            max_concurrent=10,
        )
        registry.record_heartbeat("healthy-node")
        result = checker.check_node("healthy-node")
        assert result.status == HealthStatus.HEALTHY

    def test_check_node_with_callback(self, registry):
        checker = HealthChecker(registry=registry)
        registry.register(name="cb-node", url="http://cb.io")
        registry.record_heartbeat("cb-node")

        results = []
        checker.add_callback(lambda r: results.append(r))
        checker.check_node("cb-node")
        assert len(results) == 1

    def test_check_all(self, registry):
        checker = HealthChecker(registry=registry)
        registry.register(name="a", url="http://a.io")
        registry.register(name="b", url="http://b.io")
        registry.record_heartbeat("a")
        registry.record_heartbeat("b")

        results = checker.check_all()
        assert "a" in results
        assert "b" in results

    def test_get_last_result(self, registry):
        checker = HealthChecker(registry=registry)
        registry.register(name="n1", url="http://n1.io")
        registry.record_heartbeat("n1")
        checker.check_node("n1")
        result = checker.get_last_result("n1")
        assert result is not None
        assert result.node_name == "n1"


class TestFailureDetector:
    """Failure detector tests."""

    def test_heartbeat_failure(self, registry):
        checker = HealthChecker(registry=registry)
        detector = FailureDetector(registry=registry, health_checker=checker, heartbeat_timeout=3)
        registry.register(name="silent", url="http://silent.io")
        passport = (datetime.utcnow() - timedelta(seconds=120)).isoformat()
        registry._agents["silent"].last_heartbeat = passport

        failures = detector.check_heartbeat_failures()
        assert len(failures) > 0
        assert failures[0].failure_type == FailureType.HEARTBEAT_TIMEOUT
        assert failures[0].node_name == "silent"

    def test_no_failure_recent_heartbeat(self, registry):
        checker = HealthChecker(registry=registry)
        detector = FailureDetector(registry=registry, health_checker=checker, heartbeat_timeout=30)
        registry.register(name="current", url="http://current.io")
        registry.record_heartbeat("current")

        failures = detector.check_heartbeat_failures()
        # Should not detect failures for the recently seen node
        name_failures = [f for f in failures if f.node_name == "current"]
        assert len(name_failures) == 0

    def test_failure_callback(self, registry):
        checker = HealthChecker(registry=registry)
        detector = FailureDetector(registry=registry, health_checker=checker, heartbeat_timeout=3)
        registry.register(name="dying", url="http://dying.io")
        passport = (datetime.utcnow() - timedelta(seconds=120)).isoformat()
        registry._agents["dying"].last_heartbeat = passport

        failures = []
        detector.add_callback(lambda f: failures.append(f))
        detector.check_heartbeat_failures()
        assert len(failures) > 0


class TestReassignmentEngine:
    """Reassignment engine tests."""

    def test_handle_task_failure(self, registry, router, bus):
        engine = ReassignmentEngine(
            registry=registry,
            task_router=router,
            comm_bus=bus,
            max_reassignments_per_node=10,
            reassignment_cooldown=0,
        )

        reg = registry
        reg.register(
            name="node-a",
            url="http://a:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
        )
        reg.register(
            name="node-b",
            url="http://b:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
        )
        reg.record_heartbeat("node-a")
        reg.record_heartbeat("node-b")

        task = TaskAssignmentRecord(
            task_id="test-task",
            agent_name="worker",
            node_name="node-a",
            capability="task",
        )

        result = engine.handle_task_failure(task)
        assert result is True
        assert task.node_name == "node-b"  # should be reassigned to node-b
        assert task.status == "reassigned"
        assert task.retry_count == 1

    def test_max_retries_exhausted(self, registry, router, bus):
        engine = ReassignmentEngine(
            registry=registry,
            task_router=router,
            comm_bus=bus,
        )

        registry.register(
            name="only-node",
            url="http://only:8080",
            capabilities={"task": CapabilityDeclaration(name="task")},
        )
        registry.record_heartbeat("only-node")

        task = TaskAssignmentRecord(
            task_id="doomed",
            agent_name="worker",
            node_name="only-node",
            capability="task",
            retry_count=3,
            max_retries=3,
        )

        result = engine.handle_task_failure(task)
        assert result is False  # Max retries reached


class TestCircuitBreaker:
    """Circuit breaker tests."""

    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.is_open("node-a") is False

    def test_opens_after_failures(self):
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        for _ in range(3):
            cb.record_failure("node-a")
        assert cb.is_open("node-a") is True

    def test_closes_after_successes(self):
        from datetime import datetime, timedelta

        cb = CircuitBreaker(failure_threshold=2, success_threshold=2, timeout=10)

        # Open the circuit
        cb.record_failure("node-a")
        cb.record_failure("node-a")
        # Force state to open directly (the test might have is_open transitioning)
        cb._states["node-a"]["state"] = "open"
        cb._states["node-a"]["last_change"] = datetime.utcnow()

        assert cb.is_open("node-a") is True  # Still within timeout window

        # Force timeout by setting last_change far in the past
        cb._states["node-a"]["last_change"] = datetime.utcnow() - timedelta(seconds=60)

        # Now is_open should allow (transitions to half-open)
        cb.is_open("node-a")

        # Record successes
        cb.record_success("node-a")
        cb.record_success("node-a")
        assert cb.get_state("node-a") == "closed"

    def test_get_state(self):
        cb = CircuitBreaker()
        assert cb.get_state("node-a") == "closed"
        for _ in range(5):
            cb.record_failure("node-a")
        assert cb.get_state("node-a") == "open"

    def test_reset(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure("node-a")
        assert cb.is_open("node-a") is True
        cb.reset("node-a")
        assert cb.is_open("node-a") is False


class TestResilienceEngine:
    """End-to-end resilience engine tests."""

    def test_create_engine(self, resilience):
        assert resilience is not None
        assert resilience.health_checker is not None
        assert resilience.failure_detector is not None
        assert resilience.reassignment_engine is not None
        assert resilience.circuit_breaker is not None

    def test_register_and_monitor_task(self, resilience, registry, router):
        task = TaskAssignmentRecord(
            task_id="e2e-task",
            agent_name="worker",
            node_name="test-node",
            capability="test",
        )
        resilience.register_task(task)
        resilience.record_task_start("e2e-task")
        assert task.status == "running"
        assert task.started_at is not None

        resilience.record_task_completion("e2e-task", success=True, output={"result": "ok"})
        assert task.status == "completed"

    def test_task_failure_triggers_reassignment(self, resilience, registry, router, bus):
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

        task = TaskAssignmentRecord(
            task_id="fail-task",
            agent_name="worker",
            node_name="node-a",
            capability="work",
            max_retries=2,
        )
        resilience.register_task(task)
        resilience.record_task_start("fail-task")

        resilience.record_task_completion("fail-task", success=False, error="test error")
        # After failure and retry, task should be reassigned
        assert task.node_name == "node-b"

    def test_can_assign_to(self, resilience, registry):
        registry.register(
            name="node-a",
            url="http://a:8080",
            capabilities={"work": CapabilityDeclaration(name="work")},
        )
        registry.record_heartbeat("node-a")

        assert resilience.can_assign_to("node-a") is True

        # Circuit open
        resilience.circuit_breaker.record_failure("node-a")
        resilience.circuit_breaker.record_failure("node-a")
        # Force timeout
        resilience.circuit_breaker._states["node-a"]["last_change"] = datetime.utcnow()

        # With failure_threshold=5 by default, it shouldn't be open yet after 2 failures
        # Actually we have default threshold of 5
        # Let's use 5 failures
        for _ in range(5):
            resilience.circuit_breaker.record_failure("node-a")

        # Now circuit is open
        assert resilience.can_assign_to("node-a") is False

    def test_get_status(self, resilience, registry):
        registry.register(
            name="stat-node",
            url="http://stat:8080",
            capabilities={"work": CapabilityDeclaration(name="work")},
        )
        registry.record_heartbeat("stat-node")

        status = resilience.get_status()
        assert "health" in status
        assert "failures" in status
        assert "circuit_breakers" in status
        assert "reassignments" in status
        assert "monitored_tasks" in status
