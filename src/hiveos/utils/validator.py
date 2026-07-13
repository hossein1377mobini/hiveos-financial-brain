"""
Flow validator for Flow DSL files.
"""

from pathlib import Path
import yaml
from typing import Dict, List, Optional, Any
from rich.console import Console

console = Console()

class ValidationError(Exception):
    """Raised when flow validation fails."""
    pass

class FlowValidator:
    """Validates Flow DSL YAML files against the schema."""
    
    REQUIRED_TOP_LEVEL = ["name", "version", "agents"]
    
    REQUIRED_AGENT_FIELDS = ["id", "skills"]
    
    OPTIONAL_AGENT_FIELDS = [
        "name", "knowledge", "depends_on", "input_from",
        "output", "action", "timeout", "retry", "deliver"
    ]
    
    def validate_file(self, path: Path) -> List[str]:
        """Validate a flow YAML file, returning a list of errors."""
        errors = []
        
        if not path.exists():
            errors.append(f"File not found: {path}")
            return errors
        
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {e}")
            return errors
        
        if not isinstance(data, dict):
            errors.append("Flow file must contain a YAML mapping (dictionary)")
            return errors
        
        # Validate top-level required fields
        for field in self.REQUIRED_TOP_LEVEL:
            if field not in data:
                errors.append(f"Missing required top-level field: {field}")
        
        # Validate agents
        if "agents" in data:
            if not isinstance(data["agents"], list):
                errors.append("'agents' must be a list")
            else:
                agent_ids = []
                for i, agent in enumerate(data["agents"]):
                    agent_errors = self._validate_agent(agent, i)
                    errors.extend(agent_errors)
                    
                    if "id" in agent:
                        if agent["id"] in agent_ids:
                            errors.append(f"Duplicate agent ID: {agent['id']}")
                        agent_ids.append(agent["id"])
                
                # Validate dependencies
                for agent in data["agents"]:
                    if "depends_on" in agent:
                        for dep_id in agent["depends_on"]:
                            if dep_id not in agent_ids:
                                errors.append(
                                    f"Agent '{agent.get('id', '?')}' depends on "
                                    f"unknown agent: {dep_id}"
                                )
        
        # Validate trigger (optional but structured)
        if "trigger" in data:
            trigger = data["trigger"]
            # Trigger can be minimal (just type) or more complex
            if isinstance(trigger, dict):
                valid_types = {"cron", "event", "manual", "webhook"}
                trigger_type = trigger.get("type", trigger.get("cron"))
                if "type" in trigger and trigger["type"] not in valid_types:
                    errors.append(
                        f"Invalid trigger type '{trigger['type']}'. "
                        f"Valid: {', '.join(sorted(valid_types))}"
                    )
        
        return errors
    
    def _validate_agent(self, agent: Any, index: int) -> List[str]:
        """Validate a single agent definition."""
        errors = []
        agent_label = f"agents[{index}]"
        
        if not isinstance(agent, dict):
            errors.append(f"{agent_label}: must be a mapping (dictionary)")
            return errors
        
        for field in self.REQUIRED_AGENT_FIELDS:
            if field not in agent:
                errors.append(f"{agent_label}: missing required field: {field}")
        
        if "id" in agent and not isinstance(agent["id"], str):
            errors.append(f"{agent_label}: 'id' must be a string")
        
        if "skills" in agent:
            if not isinstance(agent["skills"], list):
                errors.append(f"{agent_label}: 'skills' must be a list")
        
        if "depends_on" in agent:
            if not isinstance(agent["depends_on"], list):
                errors.append(f"{agent_label}: 'depends_on' must be a list")
            elif len(agent["depends_on"]) == 0:
                errors.append(f"{agent_label}: 'depends_on' is empty")
        
        if "timeout" in agent and not isinstance(agent["timeout"], (int, float)):
            errors.append(f"{agent_label}: 'timeout' must be a number")
        
        if "retry" in agent and not isinstance(agent["retry"], int):
            errors.append(f"{agent_label}: 'retry' must be an integer")
        
        return errors
    
    def validate_flow(self, data: Dict[str, Any]) -> List[str]:
        """Validate a parsed flow dict (from YAML), returning errors list."""
        errors = []
        
        for field in self.REQUIRED_TOP_LEVEL:
            if field not in data:
                errors.append(f"Missing required top-level field: {field}")
        
        if "agents" in data:
            agent_ids = []
            for i, agent in enumerate(data["agents"]):
                agent_errors = self._validate_agent(agent, i)
                errors.extend(agent_errors)
                if "id" in agent:
                    agent_ids.append(agent["id"])
        
        return errors
