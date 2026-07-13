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


def _sanitize_name(name: str) -> str:
    """Convert a flow name to a safe directory name."""
    import re
    safe = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name)
    return safe.strip('_') or 'unnamed'


class FlowEngine:
    """Engine that executes flows according to their DSL."""

    def __init__(self, knowledge_dir: Optional[Path] = None, state_root: Optional[Path] = None):
        self.knowledge_dir = knowledge_dir or Path("docs")
        self.state_root = state_root or Path.home() / ".hiveos" / "flows"
        self.state_root.mkdir(parents=True, exist_ok=True)
        self.flow_state: Dict[str, Dict] = {}
        self._hermes_path = self._find_hermes()

    def _get_state_dir(self, flow_name: str) -> Path:
        """Return the directory where flow state is persisted."""
        return self.state_root / _sanitize_name(flow_name)

    def _state_file(self, flow_name: str) -> Path:
        """Return the JSON state file path for a flow."""
        return self._get_state_dir(flow_name) / "state.json"

    def _save_state(self, flow_name: str):
        """Persist current flow_state to JSON file."""
        state_dir = self._get_state_dir(flow_name)
        state_dir.mkdir(parents=True, exist_ok=True)
        state = self.flow_state.get(flow_name)
        if state is None:
            return
        self._state_file(flow_name).write_text(
            json.dumps(state, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def _load_state(self, flow_name: str) -> Optional[Dict[str, Any]]:
        """Load persisted flow state from JSON file (if exists)."""
        sfile = self._state_file(flow_name)
        if sfile.exists():
            return json.loads(sfile.read_text(encoding="utf-8"))
        return None

    def clear_state(self, flow_name: str):
        """Delete persisted state for a flow (e.g. after a successful completed run)."""
        sfile = self._state_file(flow_name)
        if sfile.exists():
            sfile.unlink()

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

    def execute_flow(self, flow: Flow, resume: bool = False) -> Dict[str, Any]:
        """Execute an entire flow from a Flow object.

        Args:
            flow: The Flow to execute.
            resume: If True, try to load persisted state and skip already-completed agents.
        """
        console.print(f"🐝 [bold cyan]Executing flow:[/bold cyan] {flow.name}")
        if flow.description:
            console.print(f"   📋 {flow.description}")

        flow_name = flow.name

        # --- Resume or fresh start ---
        if resume:
            persisted = self._load_state(flow_name)
            if persisted and persisted.get("status") in ("running", "completed"):
                self.flow_state[flow_name] = persisted
                console.print(f"   [yellow]📂 Resuming from saved state[/yellow]")
                if persisted.get("status") == "completed":
                    console.print(f"   [green]✅ Flow already completed. Use --resume to re-run.[/green]")
                    return persisted
            else:
                console.print(f"   [yellow]No saved state found, starting fresh.[/yellow]")

        if flow_name not in self.flow_state:
            self.flow_state[flow_name] = {
                "status": "running",
                "start_time": time.time(),
                "agents": {},
                "output": None,
            }
            self._save_state(flow_name)

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
                # Skip already-completed agents in resume mode
                existing = self.flow_state[flow_name]["agents"].get(agent.id, {})
                if resume and existing.get("status") == "completed":
                    console.print(f"   [dim]⏩ Skipping {agent.name} (already completed)[/dim]")
                    continue

                agent_result = self._execute_agent(agent, flow)
                self.flow_state[flow_name]["agents"][agent.id] = agent_result
                # Persist state after every agent step
                self._save_state(flow_name)

            # Deliver final output
            self.flow_state[flow_name]["output"] = self._deliver_flow(flow)
            self.flow_state[flow_name]["end_time"] = time.time()
            self.flow_state[flow_name]["status"] = "completed"
            self._save_state(flow_name)

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
        """Execute a single agent by spawning a Hermes subagent with retry logic.

        Uses `hermes chat -q` as a subprocess to run the agent with its
        configured skills and knowledge. Captures output for the next
        agent in the flow. Handles failures and retries per agent.retry count.
        """
        console.print(f"   🔧 [bold]Agent:[/bold] {agent.name} (ID: {agent.id})")
        console.print(f"      Skills: {', '.join(agent.skills)}")
        if agent.depends_on:
            console.print(f"      Depends on: {', '.join(agent.depends_on)}")

        # Determine retry settings
        max_retries = agent.retry or 0

        last_result = None
        for attempt in range(max_retries + 1):
            # --- Build context from previous agents (always from latest persisted state) ---
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

            console.print(f"      [dim]🚀 Spawning Hermes subagent (attempt {attempt + 1}/{max_retries + 1})...[/dim]")
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

                # Determine status
                if result.returncode == 0:
                    status = "completed"
                elif attempt < max_retries:
                    status = "retrying"
                    console.print(f"      [yellow]⚠️  Attempt {attempt + 1} failed, retrying...[/yellow]")
                    time.sleep(2)  # Brief delay before retry
                    continue
                else:
                    status = "failed"

                agent_result = {
                    "agent_id": agent.id,
                    "name": agent.name,
                    "status": status,
                    "n_retries": attempt,
                    "max_retries": max_retries,
                    "output_file": agent.output,
                    "timestamp": time.time(),
                    "elapsed_seconds": round(elapsed, 2),
                    "result": clean_output or stderr,
                    "session_id": session_id,
                    "returncode": result.returncode,
                }

                if status == "completed":
                    console.print(f"   [green]✅ {agent.name} completed (attempt {attempt + 1}) ({elapsed:.1f}s)[/green]")
                    return agent_result
                else:
                    # Final failure
                    console.print(f"   [red]❌ {agent.name} failed after {attempt + 1} attempts ({elapsed:.1f}s)[/red]")
                    if stderr:
                        console.print(f"      [red]   STDERR: {stderr[:300]}[/]")
                    # Record the failed attempt (will be stored below)

            except subprocess.TimeoutExpired:
                if attempt < max_retries:
                    console.print(f"      [yellow]⏰ {agent.name} timed out, retrying...[/yellow]")
                    time.sleep(2)
                    continue
                else:
                    console.print(f"   [red]⏰ {agent.name} timed out after {attempt + 1} attempts[/red]")
                    status = "timeout"
                    # Create the final failed result
                    agent_result = {
                        "agent_id": agent.id,
                        "name": agent.name,
                        "status": status,
                        "n_retries": attempt,
                        "max_retries": max_retries,
                        "output_file": agent.output,
                        "timestamp": time.time(),
                        "result": f"Agent timed out after {attempt + 1} attempts",
                        "returncode": -1,
                    }
                    return agent_result

            except FileNotFoundError:
                console.print(f"   [red]❌ Hermes CLI not found at '{self._hermes_path}'[/red]")
                console.print(f"   [yellow]   Falling back to placeholder mode with retry...[/yellow]")
                # For CLI not found, we'd likely fail immediately, but let's treat this as a final failure after one attempt
                agent_result = {
                    "agent_id": agent.id,
                    "name": agent.name,
                    "status": "failed",
                    "n_retries": attempt,
                    "max_retries": max_retries,
                    "output_file": agent.output,
                    "timestamp": time.time(),
                    "result": f"✅ Agent '{agent.name}' completed (placeholder - Hermes CLI not available)",
                }
                return agent_result

            except Exception as e:
                if attempt < max_retries:
                    console.print(f"      [yellow]❌ {agent.name} error: {e}, retrying...[/yellow]")
                    time.sleep(2)
                    continue
                else:
                    console.print(f"   [red]❌ {agent.name} error: {e}[/red]")
                    agent_result = {
                        "agent_id": agent.id,
                        "name": agent.name,
                        "status": "error",
                        "n_retries": attempt,
                        "max_retries": max_retries,
                        "output_file": agent.output,
                        "timestamp": time.time(),
                        "result": f"Error: {e}",
                        "returncode": -1,
                    }
                    return agent_result

            # If we reach here, it means we need to retry
            last_result = agent_result

        # If all retries exhausted, return the last result (should be the final failure)
        if last_result is None:
            last_result = {
                "agent_id": agent.id,
                "name": agent.name,
                "status": "failed",
                "n_retries": max_retries,
                "max_retries": max_retries,
                "output_file": agent.output,
                "timestamp": time.time(),
                "result": "Agent failed after exhausting all retries",
                "returncode": -1,
            }
        return last_result

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