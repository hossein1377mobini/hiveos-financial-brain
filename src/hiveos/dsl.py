"""
Flow DSL definitions and schema validation.

Supports two flow models:
  1. **Simple** — linear list of ``agents`` (backward compatible)
  2. **Component-based** — directed graph of ``components`` (advanced flows)

Component types: agent, condition, switch, loop, parallel, join, timer,
subflow, transform, error_handler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


# ── Enums ────────────────────────────────────────────────────────────────────


class TriggerType(Enum):
    CRON = "cron"
    EVENT = "event"
    MANUAL = "manual"
    WEBHOOK = "webhook"


class ComponentType(Enum):
    AGENT = "agent"
    CONDITION = "condition"
    SWITCH = "switch"
    LOOP = "loop"
    PARALLEL = "parallel"
    JOIN = "join"
    TIMER = "timer"
    SUBFLOW = "subflow"
    TRANSFORM = "transform"
    ERROR_HANDLER = "error_handler"


# ── Trigger ───────────────────────────────────────────────────────────────────


@dataclass
class Trigger:
    type: TriggerType
    pattern: str = ""
    config: Dict[str, Any] = field(default_factory=dict)


# ── Simple Agent (backward compat) ────────────────────────────────────────────


@dataclass
class SimpleAgent:
    id: str
    name: str
    skills: List[str]
    knowledge: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    input_from: Optional[Dict] = None
    output: Optional[str] = None
    action: Optional[Dict] = None
    timeout: Optional[int] = None
    retry: Optional[int] = None
    deliver: Optional[Dict] = None


# ── Components ────────────────────────────────────────────────────────────────


@dataclass
class Component:
    """Base fields shared by every component type."""
    id: str
    type: ComponentType
    label: str = ""                     # Display label on canvas
    position: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0})


@dataclass
class AgentComponent(Component):
    """Runs a domain agent (blueprint or inline)."""
    ref: str = ""                       # Domain agent blueprint id, e.g. "financial-orchestrator"
    skills: List[str] = field(default_factory=list)
    input_from: Optional[str] = None    # Component id whose output to use
    output: Optional[str] = None
    action: Optional[Dict] = None
    timeout: Optional[int] = None
    retry: Optional[int] = None
    deliver: Optional[Dict] = None


@dataclass
class ConditionComponent(Component):
    """If/else branch based on an expression."""
    expression: str = ""
    branches: Dict[str, List["_ComponentDef"]] = field(default_factory=dict)
    # default branch key is "true" / "false"


@dataclass
class SwitchComponent(Component):
    """Multi-branch routing based on a value expression."""
    expression: str = ""                # e.g. "{{outputs.previous.status}}"
    cases: Dict[str, List["_ComponentDef"]] = field(default_factory=dict)
    default: List["_ComponentDef"] = field(default_factory=list)  # fallback


@dataclass
class LoopComponent(Component):
    """Repeat a sequence of components."""
    until: str = ""                     # condition expression
    max_iterations: int = 10
    body: List["_ComponentDef"] = field(default_factory=list)
    continue_on_error: bool = False


@dataclass
class ParallelComponent(Component):
    """Execute multiple branches concurrently."""
    branches: Dict[str, List["_ComponentDef"]] = field(default_factory=dict)
    timeout: Optional[int] = None       # Overall timeout in seconds


@dataclass
class JoinComponent(Component):
    """Sync point after parallel branches. Waits for all upstream."""
    from_ids: List[str] = field(default_factory=list)


@dataclass
class TimerComponent(Component):
    """Wait/delay before continuing."""
    duration: float = 1.0               # seconds


@dataclass
class SubflowComponent(Component):
    """Nested flow execution."""
    ref: str = ""                       # e.g. "accounting/reconcile"
    input: Optional[Dict] = None
    await_completion: bool = True


@dataclass
class TransformComponent(Component):
    """Data mapping / transformation step."""
    input: str = ""                     # expression or component ref
    mapping: Dict[str, str] = field(default_factory=dict)
    template: Optional[str] = None      # Jinja2-like string template


@dataclass
class ErrorHandlerComponent(Component):
    """Error handling strategy for a component or group."""
    on_ids: List[str] = field(default_factory=list)
    action: str = "abort"               # abort | skip | retry | notify
    max_retries: int = 1


# Union type for component definitions (helps type checking)
# Backward-compatible alias: SimpleAgent → Agent
Agent = SimpleAgent

_ComponentDef = Union[
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
]


# ── Flow ──────────────────────────────────────────────────────────────────────


@dataclass
class Flow:
    """Complete flow definition.

    Supports two mutually exclusive shapes:
    - **Simple**: ``agents`` is a list of ``SimpleAgent`` (v0.x compat)
    - **Component**: ``components`` is a list of ``Component`` instances
    - **Hybrid**: if both are present, ``components`` takes precedence.
    """
    name: str
    description: str = ""
    version: str = "0.0.0"
    trigger: Trigger = field(default_factory=lambda: Trigger(TriggerType.MANUAL))
    agents: List[SimpleAgent] = field(default_factory=list)
    components: List[_ComponentDef] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    deliver: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def uses_components(self) -> bool:
        """True if this flow uses the component-based model."""
        return len(self.components) > 0

    def get_component_map(self) -> Dict[str, _ComponentDef]:
        """Build id → component lookup."""
        return {c.id: c for c in self.components}


# ── Component Factory ────────────────────────────────────────────────────────


def _parse_comp_list(lst: list) -> list:
    """Parse a list of raw component dicts into Component objects."""
    return [component_from_dict(c) if isinstance(c, dict) else c for c in lst]


def component_from_dict(data: dict) -> _ComponentDef:
    """Parse a raw dict into the correct Component dataclass (recursive)."""
    ctype_str = data.get("type", "agent")
    try:
        ctype = ComponentType(ctype_str)
    except ValueError:
        ctype = ComponentType.AGENT

    base = {
        "id": data.get("id", ""),
        "type": ctype,
        "label": data.get("label", data.get("name", "")),
        "position": data.get("position", {"x": 0, "y": 0}),
    }

    if ctype == ComponentType.AGENT:
        return AgentComponent(
            **base,
            ref=data.get("ref", ""),
            skills=data.get("skills", []),
            input_from=data.get("input_from"),
            output=data.get("output"),
            action=data.get("action"),
            timeout=data.get("timeout"),
            retry=data.get("retry"),
            deliver=data.get("deliver"),
        )
    elif ctype == ComponentType.CONDITION:
        branches_raw = data.get("branches", {})
        branches = {k: _parse_comp_list(v) for k, v in branches_raw.items()}
        return ConditionComponent(**base, expression=data.get("expression", ""), branches=branches)
    elif ctype == ComponentType.SWITCH:
        cases_raw = data.get("cases", {})
        cases = {k: _parse_comp_list(v) for k, v in cases_raw.items()}
        return SwitchComponent(
            **base,
            expression=data.get("expression", ""),
            cases=cases,
            default=_parse_comp_list(data.get("default", [])),
        )
    elif ctype == ComponentType.LOOP:
        return LoopComponent(
            **base,
            until=data.get("until", ""),
            max_iterations=data.get("max_iterations", 10),
            body=_parse_comp_list(data.get("body", [])),
            continue_on_error=data.get("continue_on_error", False),
        )
    elif ctype == ComponentType.PARALLEL:
        branches_raw = data.get("branches", {})
        branches = {k: _parse_comp_list(v) for k, v in branches_raw.items()}
        return ParallelComponent(**base, branches=branches, timeout=data.get("timeout"))
    elif ctype == ComponentType.JOIN:
        return JoinComponent(**base, from_ids=data.get("from_ids", data.get("from", [])))
    elif ctype == ComponentType.TIMER:
        return TimerComponent(**base, duration=float(data.get("duration", 1.0)))
    elif ctype == ComponentType.SUBFLOW:
        return SubflowComponent(**base, ref=data.get("ref", ""), input=data.get("input"), await_completion=data.get("await_completion", True))
    elif ctype == ComponentType.TRANSFORM:
        return TransformComponent(**base, input=data.get("input", ""), mapping=data.get("mapping", {}), template=data.get("template"))
    elif ctype == ComponentType.ERROR_HANDLER:
        return ErrorHandlerComponent(**base, on_ids=data.get("on_ids", data.get("on", [])), action=data.get("action", "abort"), max_retries=data.get("max_retries", 1))
    else:
        return AgentComponent(**base, ref="")


# ── FlowDSL: Parser & Validator ──────────────────────────────────────────────


_COMPONENT_TYPES = {t.value for t in ComponentType}


class FlowDSL:
    """Parser and builder for Flow DSL YAML files (agent + component model)."""

    @staticmethod
    def load_flow(path: Path) -> Flow:
        """Load a Flow DSL YAML file and return a Flow object."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return FlowDSL.parse(data)

    @staticmethod
    def parse(data: dict) -> Flow:
        """Parse a raw dict into a Flow object (no validation)."""
        # Trigger
        trigger = FlowDSL._parse_trigger(data.get("trigger", {}))

        # Backward compat: simple agents
        agents = FlowDSL._parse_simple_agents(data.get("agents", []))

        # Components (new model)
        raw_components = data.get("components", [])
        components = [component_from_dict(c) for c in raw_components] if raw_components else []

        return Flow(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            version=data.get("version", "0.0.0"),
            trigger=trigger,
            agents=agents,
            components=components,
            memory=data.get("memory", {}),
            deliver=data.get("deliver", {}),
            tags=data.get("tags", []),
        )

    @staticmethod
    def validate_structure(data: Dict[str, Any]) -> List[str]:
        """Validate parsed YAML structure, return list of errors.

        Supports both simple (agents) and component-based flows.
        """
        errors: List[str] = []
        has_agents = "agents" in data and isinstance(data["agents"], list)
        has_components = "components" in data and isinstance(data["components"], list) and len(data["components"]) > 0

        if "agents" in data and not isinstance(data["agents"], list):
            errors.append("'agents' must be a list of agent definitions")

        if not has_agents and not has_components:
            errors.append("Flow must have either 'agents' (simple) or 'components' (advanced)")

        # Basic required fields
        if "name" not in data or not data.get("name"):
            errors.append("Missing or empty required field: 'name'")

        if "version" not in data or not data.get("version"):
            errors.append("Missing or empty required field: 'version'")

        # Validate simple agents
        if has_agents:
            for idx, agent in enumerate(data["agents"]):
                if not isinstance(agent, dict):
                    errors.append(f"Agent at index {idx} must be a dict")
                    continue
                if "id" not in agent or not agent.get("id"):
                    errors.append(f"Agent at index {idx} missing 'id'")

        # Validate components
        if has_components:
            seen_ids: set = set()
            for idx, comp in enumerate(data["components"]):
                if not isinstance(comp, dict):
                    errors.append(f"Component at index {idx} must be a dict")
                    continue
                cid = comp.get("id", "")
                if not cid:
                    errors.append(f"Component at index {idx} missing 'id'")
                elif cid in seen_ids:
                    errors.append(f"Duplicate component id '{cid}' at index {idx}")
                seen_ids.add(cid)

                ctype = comp.get("type", "")
                if ctype not in _COMPONENT_TYPES:
                    errors.append(f"Component '{cid}': unknown type '{ctype}'")
                    continue

                # Type-specific validation
                if ctype == "condition":
                    if not comp.get("expression"):
                        errors.append(f"Component '{cid}': condition needs 'expression'")
                elif ctype == "switch":
                    if not comp.get("expression"):
                        errors.append(f"Component '{cid}': switch needs 'expression'")
                elif ctype == "loop":
                    if not comp.get("body"):
                        errors.append(f"Component '{cid}': loop needs 'body'")
                elif ctype == "parallel":
                    if not comp.get("branches"):
                        errors.append(f"Component '{cid}': parallel needs 'branches'")
                elif ctype == "agent":
                    pass  # agent is always valid
                elif ctype == "timer":
                    if "duration" not in comp:
                        errors.append(f"Component '{cid}': timer needs 'duration'")

        return errors

    @staticmethod
    def get_component_types() -> List[Dict[str, Any]]:
        """Return metadata about all supported component types (for UI)."""
        return [
            {"type": "agent", "label": "Agent", "icon": "🤖", "category": "execution",
             "description": "Run a domain agent with skills"},
            {"type": "condition", "label": "Condition", "icon": "🔀", "category": "flow-control",
             "description": "If/else branch based on an expression"},
            {"type": "switch", "label": "Switch", "icon": "🔀", "category": "flow-control",
             "description": "Multi-branch routing"},
            {"type": "loop", "label": "Loop", "icon": "🔄", "category": "flow-control",
             "description": "Repeat a sequence until a condition is met"},
            {"type": "parallel", "label": "Parallel", "icon": "⚡", "category": "flow-control",
             "description": "Execute branches concurrently"},
            {"type": "join", "label": "Join", "icon": "🔗", "category": "flow-control",
             "description": "Sync point after parallel execution"},
            {"type": "timer", "label": "Timer", "icon": "⏱", "category": "utility",
             "description": "Wait for a duration before continuing"},
            {"type": "subflow", "label": "Subflow", "icon": "🔽", "category": "composition",
             "description": "Run another flow as a nested step"},
            {"type": "transform", "label": "Transform", "icon": "🔧", "category": "data",
             "description": "Map or transform data between components"},
            {"type": "error_handler", "label": "Error Handler", "icon": "🛡", "category": "error",
             "description": "Define error handling strategy (abort/skip/retry/notify)"},
        ]

    # ── Internal Parsers ──────────────────────────────────────────────────

    @staticmethod
    def _parse_trigger(data: Any) -> Trigger:
        if not isinstance(data, dict):
            return Trigger(type=TriggerType.MANUAL, pattern="")
        type_str = data.get("type", "manual")
        try:
            trig_type = TriggerType(type_str)
        except ValueError:
            trig_type = TriggerType.MANUAL
        return Trigger(
            type=trig_type,
            pattern=data.get("pattern", data.get("cron", "")),
            config={k: v for k, v in data.items() if k not in ("type", "pattern", "cron")},
        )

    @staticmethod
    def _parse_simple_agents(data: list) -> List[SimpleAgent]:
        agents = []
        for d in data:
            if not isinstance(d, dict):
                continue
            agents.append(SimpleAgent(
                id=d.get("id", ""),
                name=d.get("name", d.get("id", "")),
                skills=d.get("skills", []),
                knowledge=d.get("knowledge", []),
                depends_on=d.get("depends_on", []),
                input_from=d.get("input_from"),
                output=d.get("output"),
                action=d.get("action"),
                timeout=d.get("timeout"),
                retry=d.get("retry"),
                deliver=d.get("deliver"),
            ))
        return agents
