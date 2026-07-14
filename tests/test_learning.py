"""Tests for HiveOS Learning — ExecutionLogger."""

import pytest
from hiveos.learning import ExecutionLogger


class TestExecutionLogger:
    def test_log_execution(self):
        el = ExecutionLogger()
        log_id = el.log_execution(
            flow_name="test-flow",
            execution_id="exec-1",
            agent_id="agent-1",
            status="success",
            duration_ms=150,
        )
        assert log_id
        assert len(log_id) > 0

    def test_get_executions_default(self):
        el = ExecutionLogger()
        el.log_execution("f1", "e1", "a1", "success", 100)
        el.log_execution("f1", "e2", "a2", "failed", 200)
        entries = el.get_executions()
        assert len(entries) == 2

    def test_get_executions_by_flow(self):
        el = ExecutionLogger()
        el.log_execution("f1", "e1", "a1", "success", 100)
        el.log_execution("f2", "e2", "a2", "success", 200)
        entries = el.get_executions(flow_name="f1")
        assert len(entries) == 1
        assert entries[0]["flow_name"] == "f1"

    def test_get_executions_by_status(self):
        el = ExecutionLogger()
        el.log_execution("f1", "e1", "a1", "success", 100)
        el.log_execution("f1", "e2", "a2", "failed", 200)
        entries = el.get_executions(status="success")
        assert len(entries) == 1
        assert entries[0]["status"] == "success"

    def test_get_executions_limit(self):
        el = ExecutionLogger()
        for i in range(20):
            el.log_execution("f", f"e{i}", "a", "success", 100)
        entries = el.get_executions(limit=5)
        assert len(entries) == 5

    def test_log_flow_execution(self):
        el = ExecutionLogger()
        agent_results = [
            {"agent_id": "a1", "status": "success", "duration_ms": 100},
            {"agent_id": "a2", "status": "failed", "duration_ms": 200, "error": "timeout"},
        ]
        log_ids = el.log_flow_execution(
            flow_name="close",
            flow_version="1.0",
            execution_id="exec-1",
            trigger="manual",
            agent_results=agent_results,
            status="completed",
            total_duration_ms=300,
        )
        assert len(log_ids) == 2  # one per agent

    def test_get_flow_stats(self):
        el = ExecutionLogger()
        el.log_execution("f1", "e1", "a1", "success", 100)
        el.log_execution("f1", "e2", "a2", "failed", 200)
        stats = el.get_flow_stats("f1")
        assert stats["total_runs"] == 2
        assert stats["avg_duration_ms"] == 150.0
        assert stats["success_rate"] == 50.0
        assert stats["failure_rate"] == 50.0

    def test_get_flow_stats_empty(self):
        el = ExecutionLogger()
        stats = el.get_flow_stats("nonexistent")
        assert stats["total_runs"] == 0

    def test_get_agent_stats(self):
        el = ExecutionLogger()
        el.log_execution("f1", "e1", "agent-a", "success", 100)
        el.log_execution("f1", "e2", "agent-a", "success", 200)
        el.log_execution("f1", "e3", "agent-a", "failed", 50)
        stats = el.get_agent_stats("agent-a")
        assert stats["total_calls"] == 3
        assert stats["success_rate"] == pytest.approx(66.7, 0.1)
        assert stats["avg_duration_ms"] == pytest.approx(116.7, 0.1)
        assert stats["error_count"] == 1

    def test_get_agent_stats_empty(self):
        el = ExecutionLogger()
        stats = el.get_agent_stats("nonexistent")
        assert stats["total_calls"] == 0

    def test_get_trends(self):
        el = ExecutionLogger()
        el.log_execution("f1", "e1", "a1", "success", 100)
        el.log_execution("f1", "e2", "a2", "failed", 200)
        el.log_execution("f2", "e3", "a1", "success", 50)
        trends = el.get_trends()
        assert trends["total_executions"] == 3
        assert trends["unique_flows"] == 2
        assert trends["unique_agents"] == 2
        assert trends["most_active_flow"] == "f1"
        assert trends["most_active_agent"] == "a1"

    def test_clear(self):
        el = ExecutionLogger()
        el.log_execution("f1", "e1", "a1", "success", 100)
        el.clear()
        assert len(el.get_executions()) == 0
        assert el.get_flow_stats("f1")["total_runs"] == 0
        assert el.get_agent_stats("a1")["total_calls"] == 0

    def test_log_flow_creates_flow_summary(self):
        el = ExecutionLogger()
        el.log_flow_execution("f1", "1.0", "e1", "cron", [], "completed", 500)
        # flow_summary entries are included in all_executions
        el.log_execution("f1", "e2", "a1", "success", 100)
        entries = el.get_executions()
        # Should have 1 agent exec + 1 flow summary
        assert len(entries) == 2
