"""
Flow DSL definitions and schema validation.

Defines the data models for Flow DSL YAML files.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path
import yaml


class TriggerType(Enum):
    CRON = "cron"
    EVENT = "event"
    MANUAL = "manual"
    WEBHOOK = "webhook"


@dataclass
class Trigger:
    """Flow trigger definition."""
    type: TriggerType
    pattern: str
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Agent:
    """Single agent definition within a flow."""
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


@dataclass
class Flow:
    """Complete flow definition parsed from DSL YAML."""
    name: str
    description: str
    version: str
    trigger: Trigger
    agents: List[Agent]
    memory: Dict[str, Any] = field(default_factory=dict)
    deliver: Dict[str, Any] = field(default_factory=dict)


class FlowDSL:
    """Parser and builder for Flow DSL YAML files."""

    @staticmethod
    def load_flow(path: Path) -> Flow:
        """Load a Flow DSL YAML file and return a Flow object."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))

        # Build trigger
        trigger_data = data.get("trigger", {"type": "manual", "pattern": ""})
        if isinstance(trigger_data, dict):
            trigger_type_str = trigger_data.get("type", "manual")
            try:
                trigger_type = TriggerType(trigger_type_str)
            except ValueError:
                trigger_type = TriggerType.MANUAL
            trigger = Trigger(
                type=trigger_type,
                pattern=trigger_data.get("pattern", trigger_data.get("cron", "")),
                config={k: v for k, v in trigger_data.items()
                        if k not in ("type", "pattern", "cron")},
            )
        else:
            trigger = Trigger(type=TriggerType.MANUAL, pattern="")

        # Build agents
        agents = []
        for agent_data in data.get("agents", []):
            agent = Agent(
                id=agent_data.get("id", ""),
                name=agent_data.get("name", agent_data.get("id", "")),
                skills=agent_data.get("skills", []),
                knowledge=agent_data.get("knowledge", []),
                depends_on=agent_data.get("depends_on", []),
                input_from=agent_data.get("input_from"),
                output=agent_data.get("output"),
                action=agent_data.get("action"),
                timeout=agent_data.get("timeout"),
                retry=agent_data.get("retry"),
                deliver=agent_data.get("deliver"),
            )
            agents.append(agent)

        return Flow(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            version=data.get("version", "0.0.0"),
            trigger=trigger,
            agents=agents,
            memory=data.get("memory", {}),
            deliver=data.get("deliver", {}),
        )

    @staticmethod
    def validate_structure(data: Dict[str, Any]) -> List[str]:
        """Validate parsed YAML structure, return list of errors."""
        errors = []
        required = ["name", "version", "agents"]
        for r in required:
            if r not in data:
                errors.append(f"Missing required field: '{r}'")
        if "agents" in data and not isinstance(data["agents"], list):
            errors.append("'agents' must be a list")
        return errors
