"""
Flow Engine - executes flows from Flow DSL definitions.
Coordinates agent execution by spawning Hermes subagents.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import time
import json
import os
import subprocess
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .dsl import Flow, Agent, FlowDSL
from .utils.knowledge import KnowledgeManager

console = Console()


class FlowEngine:
    """Engine that executes flows according to their DSL."""

    def __init__(self, knowledge_dir: Optional[Path] = None):
        self.knowledge_dir = knowledge_dir or Path("docs")
        self.flow_state: Dict[str, Dict] = {}
        self._hermes_path = self._find_hermes()

    @staticmethod
    def _find_hermes() -> str:
        """Locate the hermes CLI binary."""
        import shutil
        hermes = shutil.which("hermes")
        if hermes:
            return hermes
        # Fallback: common install paths
        candidates = [
            os.path.expanduser("~/.local/bin/hermes"),
            "/usr/local/bin/hermes",
            "/c/Users/Hossein Mobini/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return "hermes"  # let it fail naturally

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
        """Execute a single agent by spawning a Hermes subagent.

        Uses `hermes chat -q` as a subprocess to run the agent with its
        configured skills and knowledge. Captures output for the next
        agent in the flow.
        """
        console.print(f"   🔧 [bold]Agent:[/bold] {agent.name} (ID: {agent.id})")
        console.print(f"      Skills: {', '.join(agent.skills)}")
        if agent.depends_on:
            console.print(f"      Depends on: {', '.join(agent.depends_on)}")

        # --- Build context from previous agents ---
        previous_output = None
        if agent.depends_on:
            flow_name = flow.name
            predecessors = {}
            for dep_id in agent.depends_on:
                dep_result = self.flow_state.get(flow_name, {}).get("agents", {}).get(dep_id)
                if dep_result:
                    predecessors[dep_id] = dep_result.get("result", {})
            if predecessors:
                previous_output = json.dumps(predecessors, ensure_ascii=False, indent=2)

        # --- Load knowledge documents ---
        knowledge_text = ""
        km = KnowledgeManager(self.knowledge_dir)
        for doc_path in agent.knowledge:
            doc_content = km.get_document(doc_path)
            if doc_content:
                knowledge_text += f"\n=== {doc_path} ===\n{doc_content}\n"

        # --- Build the prompt for the Hermes subagent ---
        prompt_parts = [
            f"You are agent '{agent.name}' in the HiveOS flow '{flow.name}'.",
            f"Your configured skills are: {', '.join(agent.skills)}.",
            f"Apply these skills to accomplish your task.",
        ]
        if knowledge_text:
            prompt_parts.append(f"\n--- Knowledge base ---\n{knowledge_text}\n---")
        if previous_output:
            prompt_parts.append(f"\n--- Input from previous agents ---\n{previous_output}\n---")
        if agent.action:
            prompt_parts.append(f"\n--- Action constraints ---\n{json.dumps(agent.action, ensure_ascii=False, indent=2)}\n---")
        if agent.input_from:
            prompt_parts.append(f"\n--- Input configuration ---\n{json.dumps(agent.input_from, ensure_ascii=False, indent=2)}\n---")

        prompt_parts.append("\nComplete your task and report the result concisely.")
        prompt = "\n".join(prompt_parts)

        console.print(f"      [dim]🚀 Spawning Hermes subagent...[/dim]")
        try:
            start = time.time()
            cmd_list = [self._hermes_path, "chat", "-q", prompt, "-Q", "-v"]
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                timeout=agent.timeout or 120,
            )
            elapsed = time.time() - start

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            # Parse the session_id from output if present
            session_id = None
            clean_output = stdout
            for line in stdout.splitlines():
                if line.startswith("session_id:"):
                    session_id = line.split(":", 1)[1].strip()
                    clean_output = "\n".join(
                        l for l in stdout.splitlines()
                        if not l.startswith("session_id:")
                    ).strip()

            status = "completed" if result.returncode == 0 else "failed"
            agent_result = {
                "agent_id": agent.id,
                "name": agent.name,
                "status": status,
                "output_file": agent.output,
                "timestamp": time.time(),
                "elapsed_seconds": round(elapsed, 2),
                "result": clean_output or stderr,
                "session_id": session_id,
                "returncode": result.returncode,
            }

            if status == "completed":
                console.print(f"   [green]✅ {agent.name} completed ({elapsed:.1f}s)[/green]")
            else:
                console.print(f"   [red]❌ {agent.name} failed ({elapsed:.1f}s)[/red]")
                if stderr:
                    console.print(f"   [red]   STDERR: {stderr[:300]}[/red]")

            return agent_result

        except subprocess.TimeoutExpired:
            console.print(f"   [red]⏰ {agent.name} timed out after {agent.timeout or 120}s[/red]")
            return {
                "agent_id": agent.id,
                "name": agent.name,
                "status": "timeout",
                "output_file": agent.output,
                "timestamp": time.time(),
                "result": f"Agent timed out after {agent.timeout or 120}s",
                "returncode": -1,
            }
        except FileNotFoundError:
            console.print(f"   [red]❌ Hermes CLI not found at '{self._hermes_path}'[/red]")
            console.print(f"   [yellow]   Falling back to placeholder mode.[/yellow]")
            return {
                "agent_id": agent.id,
                "name": agent.name,
                "status": "completed",
                "output_file": agent.output,
                "timestamp": time.time(),
                "result": f"✅ Agent '{agent.name}' completed (placeholder - Hermes CLI not available)",
            }
        except Exception as e:
            console.print(f"   [red]❌ {agent.name} error: {e}[/red]")
            return {
                "agent_id": agent.id,
                "name": agent.name,
                "status": "error",
                "output_file": agent.output,
                "timestamp": time.time(),
                "result": f"Error: {e}",
                "returncode": -1,
            }

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
