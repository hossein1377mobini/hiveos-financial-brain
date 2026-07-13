"""
Flow Engine - executes flows from Flow DSL definitions.
Coordinates agent execution through Hermes delegate_task.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import time
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .dsl import Flow, Agent, FlowDSL

console = Console()


class FlowEngine:
    """Engine that executes flows according to their DSL."""

    def __init__(self, knowledge_dir: Optional[Path] = None):
        self.knowledge_dir = knowledge_dir or Path("docs")
        self.flow_state: Dict[str, Dict] = {}

    def load_flow(self, flow_path: Path) -> Flow:
        """Load a flow from a YAML file using FlowDSL."""
        return FlowDSL.load_flow(flow_path)

    def execute_flow(self, flow: Flow) -> Dict[str, Any]:
        """Execute an entire flow from a Flow object."""
        console.print(f"🐝 [bold cyan]Executing flow:[/bold cyan] {flow.name}")
        if flow.description:
            console.print(f"   📋 {flow.description}")

        flow_name = flow.name
        self.flow_state[flow_name] = {
            "status": "running",
            "start_time": time.time(),
            "agents": {},
            "output": None,
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Processing flow...", total=None)

            # Determine agent execution order
            execution_order = self._determine_execution_order(flow.agents)

            # Execute agents sequentially (parallel support planned)
            for agent in execution_order:
                agent_result = self._execute_agent(agent, flow)
                self.flow_state[flow_name]["agents"][agent.id] = agent_result

            # Deliver final output
            self.flow_state[flow_name]["output"] = self._deliver_flow(flow)
            self.flow_state[flow_name]["end_time"] = time.time()
            self.flow_state[flow_name]["status"] = "completed"

        return self.flow_state[flow_name]

    def _determine_execution_order(self, agents: List[Agent]) -> List[Agent]:
        """Topological sort based on depends_on."""
        executed = []
        remaining = list(agents)
        executed_ids = set()

        while remaining:
            # Find agents whose dependencies are satisfied
            ready = [
                a for a in remaining
                if not a.depends_on or all(dep in executed_ids for dep in a.depends_on)
            ]

            if not ready:
                # Break circular dependency by taking the first remaining
                console.print("[yellow]⚠️  Circular dependency detected, breaking...[/yellow]")
                ready = [remaining[0]]

            for agent in ready:
                executed.append(agent)
                executed_ids.add(agent.id)
                remaining.remove(agent)

        return executed

    def _execute_agent(self, agent: Agent, flow: Flow) -> Dict[str, Any]:
        """Execute a single agent.

        In production, this delegates to Hermes via delegate_task.
        Currently returns a placeholder result.
        """
        console.print(f"   🔧 [bold]Agent:[/bold] {agent.name} (ID: {agent.id})")
        console.print(f"      Skills: {', '.join(agent.skills)}")
        if agent.depends_on:
            console.print(f"      Depends on: {', '.join(agent.depends_on)}")

        # Placeholder: In real implementation, this would call delegate_task
        # via Hermes to spawn a subagent with the specified skills
        result = {
            "agent_id": agent.id,
            "name": agent.name,
            "status": "completed",
            "output_file": agent.output,
            "timestamp": time.time(),
            "result": f"✅ Agent '{agent.name}' completed successfully",
        }

        console.print(f"   [green]✅ {agent.name} completed[/green]")
        return result

    def _deliver_flow(self, flow: Flow) -> Dict[str, Any]:
        """Deliver flow output to the configured destination."""
        destination = flow.deliver.get("to", "origin")
        console.print(f"   📤 Delivering to: {destination}")

        return {
            "delivered": True,
            "destination": destination,
            "format": flow.deliver.get("format", "markdown"),
            "timestamp": time.time(),
        }

    def get_flow_status(self, flow_name: str) -> Optional[Dict[str, Any]]:
        """Get the status of a running or completed flow."""
        return self.flow_state.get(flow_name)
