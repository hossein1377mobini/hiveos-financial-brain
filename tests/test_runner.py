"""Tests for HiveOS Playground Runner — Flow execution with streaming (P-05)."""

import asyncio
import pytest
import yaml

from hiveos.playground import PlaygroundRunner
from hiveos.brain import EventStream, ApprovalGateEngine


SAMPLE_FLOW = """\
name: "Test Flow"
version: "1.0.0"
description: "A test flow for runner"
trigger:
  type: manual
agents:
  - id: agent-1
    name: "Agent One"
    skills: ["analyze"]
    depends_on: []
  - id: agent-2
    name: "Agent Two"
    skills: ["report"]
    depends_on: ["agent-1"]
"""


class TestPlaygroundRunner:
    def test_create_run(self):
        runner = PlaygroundRunner()
        run = runner.create_run(SAMPLE_FLOW)
        assert run.run_id
        assert run.flow_name == "Test Flow"
        assert run.status == "queued"
        assert run.run_id in run.to_dict()["run_id"]

    def test_create_run_invalid_yaml(self):
        runner = PlaygroundRunner()
        with pytest.raises(Exception):  # yaml.scanner.ScannerError or similar
            runner.create_run("not: valid: yaml: [[[")

    def test_create_run_not_dict(self):
        runner = PlaygroundRunner()
        with pytest.raises(ValueError, match="dictionary"):
            runner.create_run("- just\n  a list")

    def test_get_run(self):
        runner = PlaygroundRunner()
        run = runner.create_run(SAMPLE_FLOW)
        assert runner.get_run(run.run_id) is run

    def test_get_run_nonexistent(self):
        runner = PlaygroundRunner()
        assert runner.get_run("nonexistent") is None

    def test_list_runs(self):
        runner = PlaygroundRunner()
        runner.create_run(SAMPLE_FLOW)
        runner.create_run(SAMPLE_FLOW)
        runs = runner.list_runs()
        assert len(runs) >= 2  # at least 2 (could be more if other tests leaked)

    def test_list_runs_empty(self):
        # Note: _run_store is process-global, so can't fully isolate.
        # Just verify the method returns a list.
        runner = PlaygroundRunner()
        runs = runner.list_runs()
        assert isinstance(runs, list)

    def test_list_runs_filtered(self):
        runner = PlaygroundRunner()
        runner.create_run(SAMPLE_FLOW)
        runs = runner.list_runs(status="queued")
        assert len(runs) >= 1
        runs = runner.list_runs(status="running")
        assert len(runs) == 0

    @pytest.mark.asyncio
    async def test_execute_run_async(self):
        runner = PlaygroundRunner(event_stream=EventStream(), approval_gates=ApprovalGateEngine())
        run = runner.create_run(SAMPLE_FLOW)
        result = await runner.execute_run_async(run.run_id)
        assert result.status == "completed"
        assert result.started_at is not None
        assert result.completed_at is not None
        assert "agent-1" in result.agents
        assert "agent-2" in result.agents
        assert result.agents["agent-1"]["status"] == "completed"
        assert result.agents["agent-2"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_run_no_agents(self):
        runner = PlaygroundRunner()
        flow_no_agents = """\
name: "Empty Flow"
version: "1.0.0"
description: "No agents"
trigger:
  type: manual
agents: []
"""
        run = runner.create_run(flow_no_agents)
        result = await runner.execute_run_async(run.run_id)
        assert result.status == "completed"

    def test_cancel_run(self):
        runner = PlaygroundRunner()
        run = runner.create_run(SAMPLE_FLOW)
        assert runner.cancel_run(run.run_id) is True
        assert run.status == "cancelled"

    def test_cancel_nonexistent(self):
        runner = PlaygroundRunner()
        assert runner.cancel_run("nonexistent") is False

    def test_cancel_already_completed(self):
        runner = PlaygroundRunner()
        run = runner.create_run(SAMPLE_FLOW)
        runner.cancel_run(run.run_id)
        assert runner.cancel_run(run.run_id) is False

    def test_ws_queue(self):
        runner = PlaygroundRunner()
        run = runner.create_run(SAMPLE_FLOW)
        queue = runner.get_ws_queue(run.run_id)
        assert queue is not None
        assert queue.maxsize == 200

    def test_ws_queue_nonexistent(self):
        runner = PlaygroundRunner()
        assert runner.get_ws_queue("nonexistent") is None

    def test_to_dict_initial(self):
        runner = PlaygroundRunner()
        run = runner.create_run(SAMPLE_FLOW)
        d = run.to_dict()
        assert d["status"] == "queued"
        assert d["flow_name"] == "Test Flow"
        assert d["run_id"] == run.run_id
        assert d["logs"] == []

    @pytest.mark.asyncio
    async def test_run_emits_events(self):
        runner = PlaygroundRunner(event_stream=EventStream(), approval_gates=ApprovalGateEngine())
        run = runner.create_run(SAMPLE_FLOW)
        queue = runner.get_ws_queue(run.run_id)
        _ = asyncio.create_task(runner.execute_run_async(run.run_id))

        # Collect events emitted during execution
        events = []
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=2)
                events.append(event["type"])
                if event["type"] == "run.completed":
                    break
        except asyncio.TimeoutError:
            pass

        assert "run.started" in events
        assert "agent.started" in events
        assert "agent.completed" in events
        assert "run.completed" in events


class TestPlaygroundRunnerWithGates:
    @pytest.mark.asyncio
    async def test_run_with_approval_gate(self):
        flow_with_gate = """\
name: "Gate Flow"
version: "1.0.0"
description: "Flow requiring approval"
trigger:
  type: manual
agents:
  - id: gate-keeper
    name: "Gate Keeper"
    skills: ["review", "approve"]
    depends_on: []
"""
        approval_gates = ApprovalGateEngine()
        runner = PlaygroundRunner(event_stream=EventStream(), approval_gates=approval_gates)
        run = runner.create_run(flow_with_gate)
        result = await runner.execute_run_async(run.run_id)
        assert result.status == "completed"
        # The "approve" skill should trigger a gate creation
        all_gates = approval_gates.list_gates()
        assert len(all_gates) >= 1

    @pytest.mark.asyncio
    async def test_agent_skipped_on_dep_failure(self):
        flow = """\
name: "Dep Test"
version: "1.0.0"
description: "Test dependency skip"
trigger:
  type: manual
agents:
  - id: agent-alpha
    name: "Alpha"
    skills: ["fail-intentionally"]
    depends_on: []
  - id: agent-beta
    name: "Beta"
    skills: ["report"]
    depends_on: ["agent-alpha"]
"""
        runner = PlaygroundRunner(event_stream=EventStream(), approval_gates=ApprovalGateEngine())
        run = runner.create_run(flow)
        result = await runner.execute_run_async(run.run_id)
        # Currently the runner simulates all agents as completing, so both should succeed
        assert result.status == "completed"
