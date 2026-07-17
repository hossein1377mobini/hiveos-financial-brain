"""
HiveOS Playground — Component Engine (advanced flow execution).

Processes component-based flows with branching, looping, parallelism,
timers, subflows, transforms, and error handling.

Each method returns a ``ComponentResult`` which the ``PlaygroundRunner``
wraps into its streaming event model.
"""

from __future__ import annotations

import asyncio
import copy
import time
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..dsl import (
    Flow,
    Component,
    ComponentType,
    AgentComponent,
    ConditionComponent,
    SwitchComponent,
    LoopComponent,
    ParallelComponent,
    JoinComponent,
    TimerComponent,
    SubflowComponent,
    TransformComponent,
    ErrorHandlerComponent,
    component_from_dict,
)


# ── Result Types ──────────────────────────────────────────────────────────────


class ComponentResult:
    """Result of executing a single component."""
    def __init__(
        self,
        component_id: str,
        status: str = "pending",  # pending | running | completed | failed | skipped | cancelled
        output: Optional[Any] = None,
        error: Optional[str] = None,
        children: Optional[List["ComponentResult"]] = None,
        duration_ms: float = 0.0,
    ):
        self.component_id = component_id
        self.status = status
        self.output = output
        self.error = error
        self.children = children or []
        self.duration_ms = duration_ms

    def to_dict(self) -> dict:
        return {
            "component_id": self.component_id,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "children": [c.to_dict() for c in self.children],
            "duration_ms": self.duration_ms,
        }


class ExecutionContext:
    """Mutable context passed through component execution.

    Carries data flow — components read from and write to ``scope``.
    Also tracks the global execution state.
    """
    def __init__(self, flow: Flow):
        self.flow = flow
        self.scope: Dict[str, Any] = {}          # component_id → output
        self.errors: Dict[str, str] = {}          # component_id → error msg
        self.status: str = "running"              # running | completed | failed | cancelled
        self.start_time = time.time()
        self.component_map = flow.get_component_map()

    def get_output(self, component_id: str) -> Any:
        """Resolve ``{{outputs.component_id}}`` references to actual values."""
        return self.scope.get(component_id)

    def evaluate_expression(self, expression: str) -> Any:
        """Simple expression evaluator.

        Supports:
        - ``{{outputs.component_id}}`` — variable substitution
        - ``==``, ``!=`` comparisons
        - truthy/falsy evaluation
        """
        # Replace {{outputs.X}} references
        resolved = expression
        for match in re.finditer(r"\{\{outputs\.([\w-]+)\}\}", expression):
            cid = match.group(1)
            val = self.scope.get(cid)
            resolved = resolved.replace(match.group(0), str(val) if val is not None else "")

        # Try boolean evaluation
        if resolved == "true":
            return True
        if resolved == "false":
            return False

        # Comparison: X == Y
        if "==" in resolved:
            parts = [p.strip() for p in resolved.split("==", 1)]
            return parts[0] == parts[1]

        if "!=" in resolved:
            parts = [p.strip() for p in resolved.split("!=", 1)]
            return parts[0] != parts[1]

        # Truthy check — non-empty string
        return bool(resolved) and resolved != ""


# ── Component Engine ──────────────────────────────────────────────────────────


class ComponentEngine:
    """Executes component-based flows.

    Usage::

        engine = ComponentEngine()
        result = await engine.execute(flow, context)
    """

    def __init__(self):
        pass

    # ── Main Entry ───────────────────────────────────────────────────────

    async def execute(
        self,
        flow: Flow,
        context: Optional[ExecutionContext] = None,
    ) -> ComponentResult:
        """Execute a component-based flow, returning the root result."""
        ctx = context or ExecutionContext(flow)
        root = ComponentResult(component_id="__root__", status="running")

        if flow.uses_components():
            result = await self._execute_components(flow.components, ctx)
            root.children = [result]
        else:
            # Fallback: simple agents → chain execution
            result = await self._execute_simple_agents(flow.agents, ctx)
            root.children = [result]

        root.status = ctx.status
        root.duration_ms = (time.time() - ctx.start_time) * 1000
        return root

    # ── Component Dispatcher ─────────────────────────────────────────────

    async def _execute_components(
        self,
        components: List[Component],
        ctx: ExecutionContext,
    ) -> ComponentResult:
        """Execute a list of Component objects in sequence."""
        results: List[ComponentResult] = []
        for comp in components:
            result = await self._execute_single(comp, ctx)
            results.append(result)

            # If a component failed and no error_handler, stop
            if result.status == "failed" and ctx.status == "failed":
                break

        # Mark completed if we got through all components without failure
        if ctx.status == "running":
            ctx.status = "completed"

        # Return the last meaningful result or a container
        if len(results) == 1:
            return results[0]
        container = ComponentResult(component_id="__sequence__", status="completed")
        container.children = results
        return container

    async def _execute_single(
        self,
        comp: Component,
        ctx: ExecutionContext,
    ) -> ComponentResult:
        """Dispatch a single component to the right handler."""
        start = time.time()

        if isinstance(comp, AgentComponent):
            result = await self._execute_agent(comp, ctx)
        elif isinstance(comp, ConditionComponent):
            result = await self._execute_condition(comp, ctx)
        elif isinstance(comp, SwitchComponent):
            result = await self._execute_switch(comp, ctx)
        elif isinstance(comp, LoopComponent):
            result = await self._execute_loop(comp, ctx)
        elif isinstance(comp, ParallelComponent):
            result = await self._execute_parallel(comp, ctx)
        elif isinstance(comp, JoinComponent):
            result = await self._execute_join(comp, ctx)
        elif isinstance(comp, TimerComponent):
            result = await self._execute_timer(comp, ctx)
        elif isinstance(comp, SubflowComponent):
            result = await self._execute_subflow(comp, ctx)
        elif isinstance(comp, TransformComponent):
            result = await self._execute_transform(comp, ctx)
        elif isinstance(comp, ErrorHandlerComponent):
            result = await self._execute_error_handler(comp, ctx)
        else:
            result = ComponentResult(
                component_id=comp.id,
                status="failed",
                error=f"Unknown component type: {type(comp).__name__}",
            )

        result.duration_ms = (time.time() - start) * 1000

        # Store output in context scope
        if result.status == "completed" and result.output is not None:
            ctx.scope[comp.id] = result.output
        elif result.status == "failed":
            ctx.errors[comp.id] = result.error or "Unknown error"
            # Check if any error_handler covers this component
            if not self._has_error_handler_for(comp.id, ctx):
                ctx.status = "failed"

        return result

    # ── Component Handlers ───────────────────────────────────────────────

    async def _execute_agent(self, comp: AgentComponent, ctx: ExecutionContext) -> ComponentResult:
        """Execute a domain agent component (placeholder — delegates to runner)."""
        # In real execution this delegates to PlaygroundRunner which spawns Hermes.
        # For now returns a placeholder result with the component info.
        output = {
            "component_id": comp.id,
            "ref": comp.ref,
            "status": "completed",
            "message": f"Agent component '{comp.label or comp.id}' completed (ready for execution)",
        }
        return ComponentResult(
            component_id=comp.id,
            status="completed",
            output=output,
        )

    async def _execute_condition(self, comp: ConditionComponent, ctx: ExecutionContext) -> ComponentResult:
        """If/else branch."""
        result = ctx.evaluate_expression(comp.expression)
        branch_key = "true" if result else "false"
        branch = comp.branches.get(branch_key, comp.branches.get("default", []))

        children = []
        if branch:
            child_result = await self._execute_components(branch, ctx)
            children = [child_result]

        return ComponentResult(
            component_id=comp.id,
            status="completed",
            output={"branch": branch_key, "expression_result": result},
            children=children,
        )

    async def _execute_switch(self, comp: SwitchComponent, ctx: ExecutionContext) -> ComponentResult:
        """Multi-branch routing."""
        value = ctx.evaluate_expression(comp.expression)
        str_val = str(value) if value is not None else ""
        branch = comp.cases.get(str_val, comp.default)

        children = []
        if branch:
            child_result = await self._execute_components(branch, ctx)
            children = [child_result]

        return ComponentResult(
            component_id=comp.id,
            status="completed",
            output={"matched_case": str_val},
            children=children,
        )

    async def _execute_loop(self, comp: LoopComponent, ctx: ExecutionContext) -> ComponentResult:
        """Repeat body until condition or max iterations."""
        iteration = 0
        all_results: List[ComponentResult] = []

        while iteration < comp.max_iterations:
            if ctx.status == "cancelled":
                break

            iteration += 1
            try:
                iter_result = await self._execute_components(comp.body, ctx)
                all_results.append(iter_result)
            except Exception as exc:
                if not comp.continue_on_error:
                    return ComponentResult(
                        component_id=comp.id,
                        status="failed",
                        error=f"Loop iteration {iteration} failed: {exc}",
                        children=all_results,
                    )
                all_results.append(ComponentResult(
                    component_id=comp.id,
                    status="failed",
                    error=str(exc),
                ))

            # Check termination condition
            if comp.until:
                try:
                    should_stop = ctx.evaluate_expression(comp.until)
                    if should_stop:
                        break
                except Exception:
                    pass

        return ComponentResult(
            component_id=comp.id,
            status="completed",
            output={"iterations": iteration},
            children=all_results,
        )

    async def _execute_parallel(self, comp: ParallelComponent, ctx: ExecutionContext) -> ComponentResult:
        """Execute branches concurrently."""
        tasks = []
        branch_names = list(comp.branches.keys())
        for name in branch_names:
            branch = comp.branches[name]
            tasks.append(self._execute_components(branch, ctx))

        # Run all branches concurrently
        branch_results = await asyncio.gather(*tasks, return_exceptions=True)

        children = []
        for name, result in zip(branch_names, branch_results):
            if isinstance(result, Exception):
                children.append(ComponentResult(
                    component_id=f"{comp.id}/{name}",
                    status="failed",
                    error=str(result),
                ))
            else:
                children.append(result)

        return ComponentResult(
            component_id=comp.id,
            status="completed",
            output={"branches": {n: (c.status if hasattr(c, 'status') else 'failed') for n, c in zip(branch_names, children)}},
            children=children,
        )

    async def _execute_join(self, comp: JoinComponent, ctx: ExecutionContext) -> ComponentResult:
        """Sync point — just collects upstream outputs."""
        collected = {}
        for upstream_id in comp.from_ids:
            collected[upstream_id] = ctx.scope.get(upstream_id)
        return ComponentResult(
            component_id=comp.id,
            status="completed",
            output={"joined": collected},
        )

    async def _execute_timer(self, comp: TimerComponent, ctx: ExecutionContext) -> ComponentResult:
        """Wait for a duration."""
        await asyncio.sleep(comp.duration)
        return ComponentResult(
            component_id=comp.id,
            status="completed",
            output={"duration_seconds": comp.duration},
        )

    async def _execute_subflow(self, comp: SubflowComponent, ctx: ExecutionContext) -> ComponentResult:
        """Execute a nested flow."""
        try:
            from pathlib import Path
            # Resolve subflow path: domains/{ref}.yaml or {ref}.yaml
            subflow_path = Path(comp.ref)
            if not subflow_path.is_file():
                # Try under domains/
                subflow_path = Path(__file__).resolve().parent.parent.parent / "domains" / f"{comp.ref}.yaml"
                if not subflow_path.is_file():
                    # Try domains/{domain}/flows/{name}.yaml
                    parts = comp.ref.split("/", 1)
                    if len(parts) == 2:
                        subflow_path = Path(__file__).resolve().parent.parent.parent / "domains" / parts[0] / "flows" / f"{parts[1]}.yaml"

            if not subflow_path.is_file():
                return ComponentResult(
                    component_id=comp.id,
                    status="failed",
                    error=f"Subflow not found: {comp.ref}",
                )

            from ..dsl import FlowDSL
            subflow = FlowDSL.load_flow(subflow_path)
            subflow_ctx = ExecutionContext(subflow)

            # Pass inputs
            if comp.input:
                subflow_ctx.scope["__input__"] = comp.input

            result = await self.execute(subflow, subflow_ctx)
            result.component_id = comp.id
            return result
        except Exception as exc:
            return ComponentResult(
                component_id=comp.id,
                status="failed",
                error=str(exc),
            )

    async def _execute_transform(self, comp: TransformComponent, ctx: ExecutionContext) -> ComponentResult:
        """Data transformation step."""
        try:
            # Resolve input
            input_data = None
            if comp.input:
                input_data = ctx.evaluate_expression(comp.input)
                if input_data is None:
                    input_data = ctx.scope.get(comp.input)

            # Apply mapping
            output = {}
            if input_data and isinstance(input_data, dict):
                for target_key, source_expr in comp.mapping.items():
                    # Simple dot-path resolution
                    if source_expr.startswith("{{") and source_expr.endswith("}}"):
                        path = source_expr[2:-2].strip()
                        output[target_key] = self._resolve_path(input_data, path)
                    else:
                        output[target_key] = source_expr
            elif comp.template:
                # Simple string template
                output["result"] = comp.template
                if input_data:
                    for key, val in (input_data.items() if isinstance(input_data, dict) else {}):
                        output["result"] = output["result"].replace(f"{{{{{key}}}}}", str(val))

            return ComponentResult(
                component_id=comp.id,
                status="completed",
                output=output or input_data,
            )
        except Exception as exc:
            return ComponentResult(
                component_id=comp.id,
                status="failed",
                error=str(exc),
            )

    async def _execute_error_handler(self, comp: ErrorHandlerComponent, ctx: ExecutionContext) -> ComponentResult:
        """Error handling — runs when a watched component fails."""
        handled = []
        for watched_id in comp.on_ids:
            if watched_id in ctx.errors:
                error_msg = ctx.errors[watched_id]
                if comp.action == "skip":
                    # Clear the error and continue
                    del ctx.errors[watched_id]
                    handled.append({"component": watched_id, "action": "skip"})
                elif comp.action == "retry" and comp.max_retries > 0:
                    # Retry logic would go here
                    handled.append({"component": watched_id, "action": "retry", "retries_left": comp.max_retries})
                elif comp.action == "notify":
                    handled.append({"component": watched_id, "action": "notify", "error": error_msg})
                else:
                    # abort — already the default
                    handled.append({"component": watched_id, "action": "abort"})

        # If we skipped errors, restore overall status
        if any(h["action"] == "skip" for h in handled):
            remaining_errors = {k: v for k, v in ctx.errors.items() if k not in {h["component"] for h in handled if h["action"] == "skip"}}
            if not remaining_errors:
                ctx.status = "completed"

        return ComponentResult(
            component_id=comp.id,
            status="completed" if not any(h["action"] == "abort" for h in handled) else "failed",
            output={"handled": handled},
        )

    # ── Simple Agent Fallback ────────────────────────────────────────────

    async def _execute_simple_agents(
        self,
        agents: List,
        ctx: ExecutionContext,
    ) -> ComponentResult:
        """Execute simple linear agents (backward compat)."""
        results = []
        for agent in agents:
            comp = AgentComponent(
                id=agent.id,
                ref=agent.id,
                skills=agent.skills,
                input_from=agent.input_from.get("agent") if isinstance(agent.input_from, dict) else agent.input_from,
                output=agent.output,
                action=agent.action,
                timeout=agent.timeout,
                retry=agent.retry,
                deliver=agent.deliver,
            )
            result = await self._execute_agent(comp, ctx)
            results.append(result)
            if result.status == "failed":
                break

        if len(results) == 1:
            return results[0]
        container = ComponentResult(component_id="__agents__", status="completed")
        container.children = results
        return container

    # ── Internal helpers ─────────────────────────────────────────────────

    @staticmethod
    def _has_error_handler_for(component_id: str, ctx: ExecutionContext) -> bool:
        """Check if any error_handler component covers this id."""
        for comp in ctx.flow.components:
            if isinstance(comp, ErrorHandlerComponent):
                if component_id in comp.on_ids:
                    return True
        return False

    @staticmethod
    def _resolve_path(data: Any, path: str) -> Any:
        """Walk a dot-separated path into a dict/list structure."""
        current = data
        for part in path.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
            if current is None:
                return None
        return current
