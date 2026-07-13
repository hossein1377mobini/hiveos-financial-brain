"""
CLI flow runner helpers.
"""

from pathlib import Path
from typing import Dict, Any
from rich.console import Console
from ..dsl import FlowDSL
from ..engine import FlowEngine

console = Console()


def run_flow(flow_file: Path) -> Dict[str, Any]:
    """Load and run a flow from a file path."""
    dsl = FlowDSL()
    flow = FlowDSL.load_flow(flow_file)
    engine = FlowEngine()
    return engine.execute_flow(flow)


def list_flows(directory: Path):
    """List all flow files in a directory."""
    return list(directory.rglob("*.yml"))
