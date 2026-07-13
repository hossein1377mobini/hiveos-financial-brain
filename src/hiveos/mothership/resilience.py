"""
Resilience Engine — health monitoring, failure detection, and task reassignment.

Provides:
- Health check scheduling and execution
- Failure detection with configurable thresholds
- Automatic task reassignment on node failure
- Circuit breaker pattern for degraded nodes
- Recovery detection and node rehabilitation
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import time
import uuid
from collections import defaultdict

from rich.console import Console

from .agent_registry import AgentRegistry, AgentStatus, CapabilityDeclaration
from .task_router import TaskRouter, TaskAssignment, RouteStrategy

console = Console()


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class FailureType(Enum):
    HEARTBEAT_TIMEOUT = "heartbeat_timeout"
    TASK_TIMEOUT = "task_timeout"
    TASK_ERROR = "task_error"
    HEALTH_CHECK_FAILED = "health_check_failed"
    COMMUNICATION_ERROR = "communication_error"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    MANUAL = "manual"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    node_name: str
    status: HealthStatus
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    latency_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY


@dataclass
class FailureEvent:
    """Record of a detected failure."""
    node_name: str
    failure_type: FailureType
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    description: str = ""
    severity: str = "warning"  # warning, critical
    related_task_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[str] = None
    resolution_action: Optional[str] = None

    def resolve(self, action: str):
        self.resolved = True
        self.resolved_at = datetime.utcnow().isoformat()
        self.resolution_action = action


@dataclass
class TaskAssignmentRecord:
    """Track a task assignment for reassignment purposes."""
    task_id: str
    agent_name: str
    node_name: str
    capability: str
    assigned_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "assigned"  # assigned, running, completed, failed, reassigned
    retry_count: int = 0
    max_retries: int = 3
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class HealthChecker:
    """Performs health checks on registered nodes."""

    def __init__(
        self,
        registry: AgentRegistry,
        comm_bus: Optional[Any] = None,
        check_interval: int = 30,
        timeout: float = 10.0,
    ):
        self.registry = registry
        self.comm_bus = comm_bus
        self.check_interval = check_interval
        self.timeout = timeout
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._results: Dict[str, HealthCheckResult] = {}
        self._callbacks: List[Callable[[HealthCheckResult], None]] = []

    def add_callback(self, callback: Callable[[HealthCheckResult], None]):
        """Add a callback for health check results."""
        self._callbacks.append(callback)

    def check_node(self, node_name: str) -> HealthCheckResult:
        """Perform a health check on a specific node."""
        node = self.registry.get(node_name)
        if not node:
            return HealthCheckResult(
                node_name=node_name,
                status=HealthStatus.UNKNOWN,
                errors=[f"Node '{node_name}' not found in registry"],
            )

        start = time.time()
        errors = []
        details = {}

        # 1. Check heartbeat freshness
        if node.last_heartbeat:
            try:
                last = datetime.fromisoformat(node.last_heartbeat)
                elapsed = (datetime.utcnow() - last).total_seconds()
                details["heartbeat_age_seconds"] = elapsed
                if elapsed > self.registry.heartbeat_timeout * 2:
                    errors.append(f"Heartbeat stale: {elapsed:.0f}s > {self.registry.heartbeat_timeout * 2}s")
            except ValueError:
                errors.append("Invalid heartbeat timestamp")
        else:
            errors.append("No heartbeat received yet")

        # 2. Check status field
        details["reported_status"] = node.status

        # 3. Check load
        details["load"] = f"{node.current_load}/{node.max_concurrent}"
        details["load_factor"] = node.current_load / max(1, node.max_concurrent)
        if node.current_load >= node.max_concurrent:
            errors.append("Node at max capacity")

        # 4. Optional: active health check via comm bus
        if self.comm_bus and node.status != "offline":
            try:
                response = self.comm_bus.request_health(node_name)
                if response:
                    details["health_response"] = response.payload
                    if response.payload.get("status") == "healthy":
                        details["active_check"] = "passed"
                    else:
                        errors.append(f"Active health check failed: {response.payload}")
                else:
                    errors.append("Active health check timeout")
            except Exception as e:
                errors.append(f"Active health check error: {e}")

        # 5. Determine overall status
        if errors:
            critical_errors = [e for e in errors if "stale" in e.lower() or "timeout" in e.lower() or "max capacity" in e.lower()]
            if critical_errors:
                status = HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        latency = (time.time() - start) * 1000

        result = HealthCheckResult(
            node_name=node_name,
            status=status,
            latency_ms=latency,
            details=details,
            errors=errors,
        )

        with self._lock:
            self._results[node_name] = result

        # Notify callbacks
        for cb in self._callbacks:
            try:
                cb(result)
            except Exception as e:
                console.print(f"[red]Health check callback error: {e}[/red]")

        return result

    def check_all(self) -> Dict[str, HealthCheckResult]:
        """Check all registered nodes."""
        results = {}
        for agent in self.registry.list():
            results[agent.name] = self.check_node(agent.name)
        return results

    def start(self):
        """Start periodic health checks."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()
        console.print(f"[dim]🏥 Health checker started (interval: {self.check_interval}s)[/dim]")

    def stop(self):
        """Stop periodic health checks."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        console.print("[dim]🏥 Health checker stopped[/dim]")

    def _check_loop(self):
        """Background health check loop."""
        while self._running:
            try:
                self.check_all()
            except Exception as e:
                console.print(f"[red]Health check loop error: {e}[/red]")
            time.sleep(self.check_interval)

    def get_last_result(self, node_name: str) -> Optional[HealthCheckResult]:
        """Get the last health check result for a node."""
        with self._lock:
            return self._results.get(node_name)

    def get_all_results(self) -> Dict[str, HealthCheckResult]:
        """Get all last health check results."""
        with self._lock:
            return dict(self._results)


class FailureDetector:
    """Detects and classifies failures from various signals."""

    def __init__(
        self,
        registry: AgentRegistry,
        health_checker: HealthChecker,
        heartbeat_timeout: int = 30,
        task_timeout: int = 300,
        max_task_errors: int = 3,
    ):
        self.registry = registry
        self.health_checker = health_checker
        self.heartbeat_timeout = heartbeat_timeout
        self.task_timeout = task_timeout
        self.max_task_errors = max_task_errors
        self._lock = threading.RLock()
        self._failures: List[FailureEvent] = []
        self._failure_callbacks: List[Callable[[FailureEvent], None]] = []

    def add_callback(self, callback: Callable[[FailureEvent], None]):
        """Add a callback for detected failures."""
        self._failure_callbacks.append(callback)

    def check_heartbeat_failures(self) -> List[FailureEvent]:
        """Check for nodes that missed heartbeats."""
        failures = []
        now = datetime.utcnow()

        for node in self.registry.list():
            if node.last_heartbeat:
                try:
                    last = datetime.fromisoformat(node.last_heartbeat)
                    elapsed = (now - last).total_seconds()
                    if elapsed > self.heartbeat_timeout:
                        # Count missed heartbeats
                        missed = int(elapsed / self.heartbeat_timeout)
                        failure = FailureEvent(
                            node_name=node.name,
                            failure_type=FailureType.HEARTBEAT_TIMEOUT,
                            description=f"Missed {missed} heartbeat(s) ({elapsed:.0f}s elapsed)",
                            severity="critical" if elapsed > self.heartbeat_timeout * 3 else "warning",
                            metadata={"elapsed_seconds": elapsed, "missed_count": missed},
                        )
                        failures.append(failure)
                        self._record_failure(failure)
                except ValueError:
                    pass

        return failures

    def check_task_timeout(self, task: TaskAssignmentRecord) -> Optional[FailureEvent]:
        """Check if a running task has timed out."""
        if task.status != "running" or not task.started_at:
            return None

        try:
            started = datetime.fromisoformat(task.started_at)
            elapsed = (datetime.utcnow() - started).total_seconds()
            if elapsed > self.task_timeout:
                return FailureEvent(
                    node_name=task.node_name,
                    failure_type=FailureType.TASK_TIMEOUT,
                    description=f"Task {task.task_id} timed out after {elapsed:.0f}s",
                    severity="critical",
                    related_task_id=task.task_id,
                    metadata={"elapsed_seconds": elapsed, "timeout": self.task_timeout},
                )
        except ValueError:
            pass
        return None

    def check_task_error(self, task: TaskAssignmentRecord) -> Optional[FailureEvent]:
        """Check if a task has exceeded max errors."""
        if task.retry_count >= self.max_task_errors and task.status == "failed":
            return FailureEvent(
                node_name=task.node_name,
                failure_type=FailureType.TASK_ERROR,
                description=f"Task {task.task_id} failed {task.retry_count} times",
                severity="critical",
                related_task_id=task.task_id,
                metadata={"retry_count": task.retry_count, "max_retries": self.max_task_errors},
            )
        return None

    def check_health_check_failures(self) -> List[FailureEvent]:
        """Check for nodes with unhealthy health check results."""
        failures = []
        results = self.health_checker.get_all_results()

        for node_name, result in results.items():
            if result.status == HealthStatus.UNHEALTHY:
                failure = FailureEvent(
                    node_name=node_name,
                    failure_type=FailureType.HEALTH_CHECK_FAILED,
                    description=f"Health check unhealthy: {', '.join(result.errors)}",
                    severity="critical",
                    metadata={"errors": result.errors, "details": result.details},
                )
                failures.append(failure)
                self._record_failure(failure)
            elif result.status == HealthStatus.DEGRADED:
                failure = FailureEvent(
                    node_name=node_name,
                    failure_type=FailureType.HEALTH_CHECK_FAILED,
                    description=f"Health check degraded: {', '.join(result.errors)}",
                    severity="warning",
                    metadata={"errors": result.errors, "details": result.details},
                )
                failures.append(failure)
                self._record_failure(failure)

        return failures

    def check_all(self, tasks: List[TaskAssignmentRecord]) -> List[FailureEvent]:
        """Run all failure checks."""
        all_failures = []
        all_failures.extend(self.check_heartbeat_failures())
        all_failures.extend(self.check_health_check_failures())

        for task in tasks:
            timeout_failure = self.check_task_timeout(task)
            if timeout_failure:
                all_failures.append(timeout_failure)
                self._record_failure(timeout_failure)

            error_failure = self.check_task_error(task)
            if error_failure:
                all_failures.append(error_failure)
                self._record_failure(error_failure)

        return all_failures

    def _record_failure(self, failure: FailureEvent):
        """Record a failure and notify callbacks."""
        with self._lock:
            self._failures.append(failure)
            # Keep last 1000 failures
            if len(self._failures) > 1000:
                self._failures = self._failures[-1000:]

        for cb in self._failure_callbacks:
            try:
                cb(failure)
            except Exception as e:
                console.print(f"[red]Failure callback error: {e}[/red]")

    def get_failures(self, node_name: Optional[str] = None, unresolved_only: bool = True) -> List[FailureEvent]:
        """Get recorded failures."""
        with self._lock:
            failures = list(self._failures)

        if node_name:
            failures = [f for f in failures if f.node_name == node_name]
        if unresolved_only:
            failures = [f for f in failures if not f.resolved]
        return failures

    def resolve_failure(self, failure: FailureEvent, action: str):
        """Mark a failure as resolved."""
        failure.resolve(action)
        console.print(f"[green]✅ Failure resolved: {failure.node_name} - {action}[/green]")


class ReassignmentEngine:
    """Handles automatic task reassignment on node failure."""

    def __init__(
        self,
        registry: AgentRegistry,
        task_router: Any,  # TaskRouter
        comm_bus: Any,
        max_reassignments_per_node: int = 10,
        reassignment_cooldown: int = 60,
    ):
        self.registry = registry
        self.task_router = task_router
        self.comm_bus = comm_bus
        self.max_reassignments_per_node = max_reassignments_per_node
        self.reassignment_cooldown = reassignment_cooldown
        self._lock = threading.RLock()
        self._reassignment_counts: Dict[str, int] = defaultdict(int)
        self._last_reassignment: Dict[str, datetime] = {}
        self._reassigned_tasks: Dict[str, TaskAssignmentRecord] = {}

    def handle_node_failure(self, node_name: str, tasks: List[TaskAssignmentRecord]) -> List[TaskAssignmentRecord]:
        """
        Handle a node failure by reassigning its active tasks.

        Returns list of successfully reassigned tasks.
        """
        console.print(f"[red]💥 Handling failure for node '{node_name}' with {len(tasks)} active tasks[/red]")

        # Check cooldown
        now = datetime.utcnow()
        if node_name in self._last_reassignment:
            elapsed = (now - self._last_reassignment[node_name]).total_seconds()
            if elapsed < self.reassignment_cooldown:
                console.print(f"[yellow]⏳ Reassignment cooldown active for {node_name} ({elapsed:.0f}s elapsed)[/yellow]")
                return []

        # Check max reassignments
        if self._reassignment_counts.get(node_name, 0) >= self.max_reassignments_per_node:
            console.print(f"[red]❌ Max reassignments reached for {node_name}[/red]")
            return []

        reassigned = []

        for task in tasks:
            if task.status not in ("assigned", "running"):
                continue

            # Try to reroute
            new_assignment = self.task_router.reroute(
                failed_task_id=task.task_id,
                reason="node_failure",
            )

            if new_assignment:
                # Update task record
                old_node = task.node_name
                task.node_name = new_assignment.node_name
                task.status = "reassigned"
                task.retry_count += 1

                # Notify the new node
                self.comm_bus.assign_task(
                    node=new_assignment.node_name,
                    task_id=task.task_id,
                    agent_id=task.agent_name,
                    capability=task.capability,
                    input_data=task.input_data,
                )

                reassigned.append(task)
                self._reassigned_tasks[task.task_id] = task
                console.print(
                    f"[green]🔄 Reassigned task {task.task_id}: {old_node} → {new_assignment.node_name}[/green]"
                )
            else:
                console.print(f"[red]❌ Could not reassign task {task.task_id}[/red]")

        if reassigned:
            self._reassignment_counts[node_name] += len(reassigned)
            self._last_reassignment[node_name] = now

        return reassigned

    def handle_task_failure(self, task: TaskAssignmentRecord) -> bool:
        """
        Handle a task failure by attempting to reassign.

        Returns True if reassigned, False otherwise.
        """
        if task.retry_count >= task.max_retries:
            console.print(f"[red]❌ Task {task.task_id} exceeded max retries[/red]")
            return False

        # Try to route directly (bypass the router's internal reroute which needs _assignments tracking)
        new_assignment = self.task_router.route(
            agent_id=task.agent_name,
            required_capability=task.capability,
            metadata=task.input_data,
            excluded_nodes=[task.node_name],
        )

        if new_assignment:
            old_node = task.node_name
            task.node_name = new_assignment.node_name
            task.status = "reassigned"
            task.retry_count += 1

            self.comm_bus.assign_task(
                node=new_assignment.node_name,
                task_id=task.task_id,
                agent_id=task.agent_name,
                capability=task.capability,
                input_data=task.input_data,
            )

            self._reassigned_tasks[task.task_id] = task
            console.print(
                f"[green]🔄 Reassigned failed task {task.task_id}: {old_node} → {new_assignment.node_name} "
                f"(retry {task.retry_count}/{task.max_retries})[/green]"
            )
            return True

        return False

    def get_reassignment_stats(self) -> Dict[str, Any]:
        """Get reassignment statistics."""
        with self._lock:
            return {
                "total_reassignments": sum(self._reassignment_counts.values()),
                "by_node": dict(self._reassignment_counts),
                "active_reassigned": len(self._reassigned_tasks),
            }

    def reset_counts(self):
        """Reset reassignment counters (e.g., after node recovery)."""
        with self._lock:
            self._reassignment_counts.clear()
            self._last_reassignment.clear()


class CircuitBreaker:
    """Circuit breaker for degraded nodes."""

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 3,
        timeout: int = 60,
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self._lock = threading.RLock()
        self._states: Dict[str, Dict[str, Any]] = {}  # node_name -> {state, failures, successes, last_change}

    def record_success(self, node_name: str):
        """Record a successful operation."""
        with self._lock:
            if node_name not in self._states:
                self._states[node_name] = {"state": "closed", "failures": 0, "successes": 0, "last_change": datetime.utcnow()}

            state = self._states[node_name]
            state["failures"] = 0
            state["successes"] += 1

            if state["state"] == "half_open" and state["successes"] >= self.success_threshold:
                state["state"] = "closed"
                state["last_change"] = datetime.utcnow()
                console.print(f"[green]🔌 Circuit breaker CLOSED for {node_name}[/green]")

    def record_failure(self, node_name: str):
        """Record a failed operation."""
        with self._lock:
            if node_name not in self._states:
                self._states[node_name] = {"state": "closed", "failures": 0, "successes": 0, "last_change": datetime.utcnow()}

            state = self._states[node_name]
            state["successes"] = 0
            state["failures"] += 1

            if state["state"] == "closed" and state["failures"] >= self.failure_threshold:
                state["state"] = "open"
                state["last_change"] = datetime.utcnow()
                console.print(f"[red]🔌 Circuit breaker OPENED for {node_name}[/red]")
            elif state["state"] == "half_open":
                state["state"] = "open"
                state["last_change"] = datetime.utcnow()
                console.print(f"[red]🔌 Circuit breaker RE-OPENED for {node_name}[/red]")

    def is_open(self, node_name: str) -> bool:
        """Check if circuit is open (blocking requests)."""
        with self._lock:
            if node_name not in self._states:
                return False
            state = self._states[node_name]
            if state["state"] == "open":
                # Check if timeout expired -> transition to half-open
                elapsed = (datetime.utcnow() - state["last_change"]).total_seconds()
                if elapsed >= self.timeout:
                    state["state"] = "half_open"
                    state["last_change"] = datetime.utcnow()
                    console.print(f"[yellow]🔌 Circuit breaker HALF-OPEN for {node_name}[/yellow]")
                    return False  # Allow one request through
                return True
            return False

    def get_state(self, node_name: str) -> str:
        """Get circuit breaker state for a node."""
        with self._lock:
            if node_name not in self._states:
                return "closed"
            return self._states[node_name]["state"]

    def reset(self, node_name: str):
        """Reset circuit breaker for a node."""
        with self._lock:
            if node_name in self._states:
                self._states[node_name] = {"state": "closed", "failures": 0, "successes": 0, "last_change": datetime.utcnow()}


class ResilienceEngine:
    """
    Main resilience engine coordinating health checks, failure detection,
    circuit breaking, and task reassignment.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        task_router: Any,
        comm_bus: Any,
        check_interval: int = 30,
        heartbeat_timeout: int = 30,
        task_timeout: int = 300,
    ):
        self.registry = registry
        self.task_router = task_router
        self.comm_bus = comm_bus

        # Components
        self.health_checker = HealthChecker(
            registry=registry,
            comm_bus=comm_bus,
            check_interval=check_interval,
        )
        self.failure_detector = FailureDetector(
            registry=registry,
            health_checker=self.health_checker,
            heartbeat_timeout=heartbeat_timeout,
            task_timeout=task_timeout,
        )
        self.reassignment_engine = ReassignmentEngine(
            registry=registry,
            task_router=task_router,
            comm_bus=comm_bus,
        )
        self.circuit_breaker = CircuitBreaker()

        # Wire up callbacks
        self.failure_detector.add_callback(self._on_failure)
        self.health_checker.add_callback(self._on_health_check)

        # Task tracking
        self._tasks: Dict[str, TaskAssignmentRecord] = {}
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_interval = 15  # seconds

    def _on_failure(self, failure: FailureEvent):
        """Handle detected failure."""
        console.print(f"[red]🚨 FAILURE: {failure.failure_type.value} on {failure.node_name} - {failure.description}[/red]")

        # Open circuit breaker
        self.circuit_breaker.record_failure(failure.node_name)

        # If node failure, reassign tasks
        if failure.failure_type in (
            FailureType.HEARTBEAT_TIMEOUT,
            FailureType.HEALTH_CHECK_FAILED,
        ) and failure.severity == "critical":
            node_tasks = [t for t in self._tasks.values() if t.node_name == failure.node_name and t.status in ("assigned", "running")]
            if node_tasks:
                self.reassignment_engine.handle_node_failure(failure.node_name, node_tasks)

    def _on_health_check(self, result: HealthCheckResult):
        """Handle health check result."""
        if result.is_healthy:
            self.circuit_breaker.record_success(result.node_name)
        else:
            self.circuit_breaker.record_failure(result.node_name)

    def register_task(self, task: TaskAssignmentRecord):
        """Register a task for monitoring."""
        self._tasks[task.task_id] = task
        # Also register in the router for reroute support
        assignment = TaskAssignment(
            task_id=task.task_id,
            agent_name=task.agent_name,
            node_name=task.node_name,
            node_url=self.registry.get(task.node_name).url if self.registry.get(task.node_name) else "",
            capability=task.capability,
            assigned_at=task.assigned_at,
            strategy=RouteStrategy.BEST_FIT,
        )
        self.task_router._assignments[task.task_id] = assignment

    def unregister_task(self, task_id: str):
        """Unregister a completed task."""
        self._tasks.pop(task_id, None)

    def record_task_start(self, task_id: str):
        """Record task start time."""
        if task_id in self._tasks:
            self._tasks[task_id].started_at = datetime.utcnow().isoformat()
            self._tasks[task_id].status = "running"

    def record_task_completion(self, task_id: str, success: bool, output: Dict[str, Any] = None, error: str = None):
        """Record task completion."""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.completed_at = datetime.utcnow().isoformat()
            task.status = "completed" if success else "failed"
            task.output_data = output or {}
            task.error = error

            if success:
                self.circuit_breaker.record_success(task.node_name)
            else:
                self.circuit_breaker.record_failure(task.node_name)
                # Check if we should reassign
                self.reassignment_engine.handle_task_failure(task)

    def can_assign_to(self, node_name: str) -> bool:
        """Check if a node is available for new assignments."""
        # Check circuit breaker
        if self.circuit_breaker.is_open(node_name):
            return False

        # Check node status
        node = self.registry.get(node_name)
        if not node:
            return False

        if node.status in ("offline", "degraded"):
            return False

        # Check capacity - AgentStatus uses current_load and max_concurrent
        if node.current_load >= node.max_concurrent:
            return False

        return True

    def start(self):
        """Start the resilience engine."""
        if self._running:
            return
        self._running = True
        self.health_checker.start()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        console.print("[green]🛡️ Resilience engine started[/green]")

    def stop(self):
        """Stop the resilience engine."""
        self._running = False
        self.health_checker.stop()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        console.print("[dim]🛡️ Resilience engine stopped[/dim]")

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                # Check all tasks for timeouts/failures
                self.failure_detector.check_all(list(self._tasks.values()))

                # Clean up old completed tasks
                now = datetime.utcnow()
                to_remove = []
                for task_id, task in self._tasks.items():
                    if task.completed_at:
                        try:
                            completed = datetime.fromisoformat(task.completed_at)
                            if (now - completed).total_seconds() > 3600:  # 1 hour
                                to_remove.append(task_id)
                        except ValueError:
                            pass
                for task_id in to_remove:
                    del self._tasks[task_id]

            except Exception as e:
                console.print(f"[red]Resilience monitor error: {e}[/red]")

            time.sleep(self._monitor_interval)

    def get_status(self) -> Dict[str, Any]:
        """Get overall resilience status."""
        health_results = self.health_checker.get_all_results()
        failures = self.failure_detector.get_failures()

        healthy = sum(1 for r in health_results.values() if r.is_healthy)
        degraded = sum(1 for r in health_results.values() if r.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for r in health_results.values() if r.status == HealthStatus.UNHEALTHY)

        return {
            "health": {
                "healthy": healthy,
                "degraded": degraded,
                "unhealthy": unhealthy,
                "total": len(health_results),
            },
            "failures": {
                "total": len(failures),
                "unresolved": len([f for f in failures if not f.resolved]),
                "by_node": {},
            },
            "circuit_breakers": {
                node.name: self.circuit_breaker.get_state(node.name)
                for node in self.registry.list()
            },
            "reassignments": self.reassignment_engine.get_reassignment_stats(),
            "monitored_tasks": len(self._tasks),
        }

    def display_status(self):
        """Display a formatted status report."""
        from rich.table import Table

        status = self.get_status()

        # Health table
        h = status["health"]
        health_table = Table(title="🏥 Node Health")
        health_table.add_column("Status", style="cyan")
        health_table.add_column("Count", style="white")
        health_table.add_row("✅ Healthy", str(h["healthy"]), style="green")
        health_table.add_row("⚠️ Degraded", str(h["degraded"]), style="yellow")
        health_table.add_row("❌ Unhealthy", str(h["unhealthy"]), style="red")
        health_table.add_row("Total", str(h["total"]))
        console.print(health_table)

        # Circuit breakers
        cb_table = Table(title="🔌 Circuit Breakers")
        cb_table.add_column("Node", style="cyan")
        cb_table.add_column("State", style="white")
        for node, state in status["circuit_breakers"].items():
            style = {"closed": "green", "half_open": "yellow", "open": "red"}.get(state, "white")
            cb_table.add_row(node, f"[{style}]{state}[/]")
        console.print(cb_table)

        # Reassignments
        r = status["reassignments"]
        console.print(f"[bold]🔄 Reassignments:[/bold] {r['total_reassignments']} total, {r['active_reassigned']} active")

        # Failures
        if status["failures"]["unresolved"] > 0:
            console.print(f"[red]🚨 Unresolved failures: {status['failures']['unresolved']}[/red]")