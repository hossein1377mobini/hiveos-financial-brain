"""
Task Router — capability-aware task routing with load balancing.

Routes flow agents to satellite nodes based on:
- Capability matching (required skills, knowledge, tools)
- Current load (prefer less-loaded nodes)
- Health status (prefer online nodes)
- Affinity/anti-affinity rules
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
import uuid
from collections import defaultdict

from rich.console import Console

from .agent_registry import AgentRegistry, AgentStatus

console = Console()


class RouteStrategy(Enum):
    """Task routing strategies."""
    CAPABILITY_FIRST = "capability_first"      # Prefer exact capability match
    LEAST_LOADED = "least_loaded"              # Prefer nodes with lowest load
    ROUND_ROBIN = "round_robin"                # Distribute evenly across capable nodes
    AFFINITY = "affinity"                       # Prefer nodes with task affinity
    BEST_FIT = "best_fit"                       # Combine capability + load + health


@dataclass
class RoutingRule:
    """A rule for routing tasks to specific nodes."""
    capability: str                           # Required capability
    min_version: str = ""                     # Minimum capability version
    preferred_nodes: List[str] = field(default_factory=list)  # Node affinity
    excluded_nodes: List[str] = field(default_factory=list)   # Node anti-affinity
    strategy: RouteStrategy = RouteStrategy.BEST_FIT
    max_load_factor: float = 0.8              # Max load ratio (0-1)
    health_threshold: str = "online"           # Minimum health: online, degraded


@dataclass
class TaskAssignment:
    """Result of a routing decision."""
    task_id: str
    agent_name: str                           # Flow agent ID (e.g., "researcher")
    node_name: str                            # Satellite node name
    node_url: str
    capability: str
    assigned_at: str
    strategy: RouteStrategy
    rule: Optional[RoutingRule] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingMetrics:
    """Metrics for routing decisions."""
    total_assignments: int = 0
    successful: int = 0
    failed: int = 0
    fallback_used: int = 0
    by_strategy: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_node: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_capability: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record(self, assignment: TaskAssignment, success: bool):
        self.total_assignments += 1
        if success:
            self.successful += 1
        else:
            self.failed += 1
        self.by_strategy[assignment.strategy.value] += 1
        self.by_node[assignment.node_name] += 1
        self.by_capability[assignment.capability] += 1

    def summary(self) -> Dict[str, Any]:
        return {
            "total": self.total_assignments,
            "success_rate": f"{self.successful / max(1, self.total_assignments) * 100:.1f}%",
            "by_strategy": dict(self.by_strategy),
            "by_node": dict(self.by_node),
            "by_capability": dict(self.by_capability),
        }


class TaskRouter:
    """
    Capability-aware task router for Mothership.

    Given a flow agent's requirements (skills, knowledge, tools), finds the
    best satellite node to execute that agent.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        default_strategy: RouteStrategy = RouteStrategy.BEST_FIT,
        rules: Optional[List[RoutingRule]] = None,
    ):
        self.registry = registry
        self.default_strategy = default_strategy
        self.rules = rules or []
        self._assignments: Dict[str, TaskAssignment] = {}
        self._lock = threading.RLock()
        self.metrics = RoutingMetrics()

        # Hook for when registry health changes
        registry.on_status_change(self._on_agent_status_change)

    def _on_agent_status_change(self, name: str, old: str, new: str):
        """Callback when agent health changes."""
        console.print(f"[dim]🔄 Router notified: {name} {old} → {new}[/dim]")

    # ── Rule Management ────────────────────────────────────────────

    def add_rule(self, rule: RoutingRule):
        """Add a routing rule (higher priority rules checked first)."""
        self.rules.insert(0, rule)
        console.print(f"[dim]📐 Added routing rule for capability: {rule.capability}[/dim]")

    def remove_rule(self, capability: str) -> bool:
        """Remove a routing rule by capability name."""
        for i, rule in enumerate(self.rules):
            if rule.capability == capability:
                self.rules.pop(i)
                return True
        return False

    def clear_rules(self):
        """Remove all routing rules."""
        self.rules.clear()

    # ── Core Routing ────────────────────────────────────────────────

    def route(
        self,
        agent_id: str,
        required_capability: str,
        min_version: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        strategy: Optional[RouteStrategy] = None,
        preferred_nodes: Optional[List[str]] = None,
        excluded_nodes: Optional[List[str]] = None,
    ) -> Optional[TaskAssignment]:
        """
        Route a task to the best available node.

        Args:
            agent_id: Flow agent identifier (e.g., "researcher")
            required_capability: Capability name the node must provide
            min_version: Minimum version of the capability
            metadata: Additional context for routing
            strategy: Override the default routing strategy
            preferred_nodes: Node names to prefer (affinity)
            excluded_nodes: Node names to avoid (anti-affinity)

        Returns:
            TaskAssignment if a suitable node found, None otherwise.
        """
        with self._lock:
            # Build candidate list
            candidates = self._find_candidates(
                capability=required_capability,
                min_version=min_version,
                preferred=preferred_nodes,
                excluded=excluded_nodes,
            )

            if not candidates:
                console.print(f"[yellow]⚠️  No eligible nodes for capability '{required_capability}'[/yellow]")
                return None

            # Apply routing strategy
            strat = strategy or self.default_strategy
            selected = self._select_node(candidates, strat, required_capability)

            if not selected:
                console.print(f"[red]❌ No node selected after strategy '{strat.value}'[/red]")
                return None

            # Record assignment
            task_id = f"{agent_id}-{uuid.uuid4().hex[:8]}"
            assignment = TaskAssignment(
                task_id=task_id,
                agent_name=agent_id,
                node_name=selected.name,
                node_url=selected.url,
                capability=required_capability,
                assigned_at=datetime.utcnow().isoformat(),
                strategy=strat,
                metadata=metadata or {},
            )

            self._assignments[task_id] = assignment
            self.registry.record_task_assignment(selected.name)

            console.print(
                f"[green]🎯 Routed '{agent_id}' → '{selected.name}' "
                f"(cap: {required_capability}, load: {selected.current_load}/{selected.max_concurrent}, "
                f"strategy: {strat.value})[/green]"
            )
            return assignment

    def _find_candidates(
        self,
        capability: str,
        min_version: str = "",
        preferred: Optional[List[str]] = None,
        excluded: Optional[List[str]] = None,
    ) -> List[AgentStatus]:
        """Find nodes that match the capability requirements."""
        # First, check for explicit routing rules
        for rule in self.rules:
            if rule.capability == capability:
                candidates = self._apply_rule(rule, min_version, preferred, excluded)
                if candidates:
                    return candidates

        # Fall back to registry query
        candidates = self.registry.find_available(capability, min_version)

        # Apply preferred/excluded even without rules
        if preferred:
            pref_set = set(preferred)
            candidates.sort(key=lambda c: 0 if c.name in pref_set else 1)

        if excluded:
            excl_set = set(excluded)
            candidates = [c for c in candidates if c.name not in excl_set]

        return candidates

    def _apply_rule(
        self,
        rule: RoutingRule,
        min_version: str,
        preferred: Optional[List[str]],
        excluded: Optional[List[str]],
    ) -> List[AgentStatus]:
        """Apply a routing rule to filter candidates."""
        candidates = self.registry.find_by_capability(
            rule.capability,
            min_version or rule.min_version,
        )

        # Filter by health threshold
        health_order = {"online": 3, "degraded": 2, "offline": 1, "unknown": 0}
        min_health = health_order.get(rule.health_threshold, 3)
        candidates = [c for c in candidates if health_order.get(c.status, 0) >= min_health]

        # Apply load factor
        candidates = [
            c for c in candidates
            if c.current_load / max(1, c.max_concurrent) <= rule.max_load_factor
        ]

        # Apply preferred nodes (sort to top)
        if preferred:
            pref_set = set(preferred)
            candidates.sort(key=lambda c: 0 if c.name in pref_set else 1)

        # Apply excluded nodes
        if excluded:
            excl_set = set(excluded)
            candidates = [c for c in candidates if c.name not in excl_set]

        # Apply rule's own preferences
        if rule.preferred_nodes:
            pref_set = set(rule.preferred_nodes)
            candidates.sort(key=lambda c: 0 if c.name in pref_set else 1)

        if rule.excluded_nodes:
            excl_set = set(rule.excluded_nodes)
            candidates = [c for c in candidates if c.name not in excl_set]

        return candidates

    def _select_node(
        self,
        candidates: List[AgentStatus],
        strategy: RouteStrategy,
        capability: str,
    ) -> Optional[AgentStatus]:
        """Select the best node from candidates using the given strategy."""
        if not candidates:
            return None

        if strategy == RouteStrategy.CAPABILITY_FIRST:
            # Already filtered by capability; just pick first healthy
            return next((c for c in candidates if c.status == "online"), candidates[0])

        elif strategy == RouteStrategy.LEAST_LOADED:
            return min(candidates, key=lambda c: c.current_load / max(1, c.max_concurrent))

        elif strategy == RouteStrategy.ROUND_ROBIN:
            # Round robin per capability
            cap_key = capability
            # Track rotation index per capability
            if not hasattr(self, "_rr_index"):
                self._rr_index = {}
            idx = self._rr_index.get(cap_key, 0)
            selected = candidates[idx % len(candidates)]
            self._rr_index[cap_key] = (idx + 1) % len(candidates)
            return selected

        elif strategy == RouteStrategy.AFFINITY:
            # Prefer nodes with previous successful completions for this capability
            best = None
            best_score = -1
            for c in candidates:
                score = c.total_tasks_completed
                if c.status == "online":
                    score += 10
                if score > best_score:
                    best_score = score
                    best = c
            return best or candidates[0]

        elif strategy == RouteStrategy.BEST_FIT:
            # Score: health + capacity + performance
            best = None
            best_score = -1
            for c in candidates:
                if c.status == "offline":
                    continue
                health_score = {"online": 30, "degraded": 15, "unknown": 10}.get(c.status, 0)
                load_score = (1 - c.current_load / max(1, c.max_concurrent)) * 30
                perf_score = min(20, c.total_tasks_completed * 2)
                reliability = 100 * (1 - c.total_errors / max(1, c.total_tasks_completed + c.total_errors))
                reliability_score = min(20, reliability / 5)
                score = health_score + load_score + perf_score + reliability_score
                if score > best_score:
                    best_score = score
                    best = c
            return best or candidates[0]

        return candidates[0]

    # ── Assignment Tracking ────────────────────────────────────────

    def record_completion(self, task_id: str, success: bool):
        """Record the completion of a routed task."""
        with self._lock:
            assignment = self._assignments.get(task_id)
            if not assignment:
                return
            self.metrics.record(assignment, success)
            self.registry.record_completion(assignment.node_name, success)
            # Keep assignment for a bit for debugging
            # Could add TTL cleanup later

    def get_assignment(self, task_id: str) -> Optional[TaskAssignment]:
        """Get assignment details by task ID."""
        return self._assignments.get(task_id)

    def list_active_assignments(self) -> List[TaskAssignment]:
        """List all active (not completed) assignments."""
        return list(self._assignments.values())

    # ── Re-routing (for resilience) ────────────────────────────────

    def reroute(
        self,
        failed_task_id: str,
        reason: str = "node_failure",
    ) -> Optional[TaskAssignment]:
        """
        Re-route a failed task to a different node.

        Args:
            failed_task_id: The task that failed
            reason: Why it failed (node_failure, timeout, error, etc.)

        Returns:
            New TaskAssignment or None if no alternative found.
        """
        with self._lock:
            failed = self._assignments.get(failed_task_id)
            if not failed:
                console.print(f"[red]❌ Cannot reroute: task {failed_task_id} not found[/red]")
                return None

            console.print(f"[yellow]🔄 Re-routing task {failed_task_id} (reason: {reason})[/yellow]")

            # Exclude the failed node and any other node currently assigned
            excluded = {failed.node_name}

            # Also exclude any node currently offline/degraded
            all_nodes = self.registry.list()
            for n in all_nodes:
                if n.status in ("offline", "degraded"):
                    excluded.add(n.name)

            # Re-route with same requirements
            new_assignment = self.route(
                agent_id=failed.agent_name,
                required_capability=failed.capability,
                metadata={**failed.metadata, "rerouted_from": failed.node_name, "reason": reason},
                excluded_nodes=list(excluded),
            )

            if new_assignment:
                self.metrics.fallback_used += 1
                console.print(
                    f"[green]✅ Re-routed: {failed.node_name} → {new_assignment.node_name}[/green]"
                )
            else:
                console.print(f"[red]❌ No alternative node available for reroute[/red]")

            return new_assignment

    # ── Metrics & Summary ──────────────────────────────────────────

    def display_metrics(self):
        """Print routing metrics summary."""
        from rich.table import Table

        table = Table(title="🎯 Task Router Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        m = self.metrics.summary()
        table.add_row("Total Assignments", str(m["total"]))
        table.add_row("Success Rate", m["success_rate"])
        table.add_row("Fallback Used", str(self.metrics.fallback_used))

        console.print(table)

        if m["by_node"]:
            node_table = Table(title="Assignments by Node")
            node_table.add_column("Node", style="cyan")
            node_table.add_column("Tasks", style="white")
            for node, count in sorted(m["by_node"].items(), key=lambda x: -x[1]):
                node_table.add_row(node, str(count))
            console.print(node_table)

    def status(self) -> Dict[str, Any]:
        """Get router status summary."""
        return {
            "total_assignments": self.metrics.total_assignments,
            "active_assignments": len(self._assignments),
            "rules_count": len(self.rules),
            "default_strategy": self.default_strategy.value,
            "metrics": self.metrics.summary(),
        }