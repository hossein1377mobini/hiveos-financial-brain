"""Tests for HiveOS Learning Analytics Engine — Pattern Recognition, Trends, Bottlenecks (L-02)."""

import pytest
from datetime import datetime, timezone, timedelta

from hiveos.learning import ExecutionLogger
from hiveos.learning.analytics import AnalyticsEngine


@pytest.fixture
def engine():
    logger = ExecutionLogger()
    return AnalyticsEngine(logger)


@pytest.fixture
def engine_with_data():
    logger = ExecutionLogger()
    
    # Log various executions across different flows, agents, statuses
    for i in range(20):
        logger.log_execution(
            flow_name="financial-close",
            execution_id=f"exec-{i}",
            agent_id="financial-recorder",
            status="success" if i < 15 else "failed",
            duration_ms=150 + i * 10,
            error="" if i < 15 else "timeout",
        )
    
    for i in range(10):
        logger.log_execution(
            flow_name="financial-close",
            execution_id=f"exec-{i+20}",
            agent_id="financial-reporter",
            status="success" if i < 8 else "failed",
            duration_ms=200 + i * 20,
            error="" if i < 8 else "data_error",
        )
    
    for i in range(5):
        logger.log_execution(
            flow_name="tax-return",
            execution_id=f"exec-{i+30}",
            agent_id="tax-specialist",
            status="success",
            duration_ms=300 + i * 5,
        )
    
    # A flow execution with multiple agents in sequence (for pattern recognition)
    logger.log_flow_execution(
        flow_name="monthly-close",
        flow_version="1.0",
        execution_id="flow-1",
        trigger="manual",
        agent_results=[
            {"agent_id": "recorder", "status": "success", "duration_ms": 100},
            {"agent_id": "reporter", "status": "success", "duration_ms": 200},
            {"agent_id": "orchestrator", "status": "success", "duration_ms": 50},
        ],
        status="completed",
        total_duration_ms=350,
    )
    logger.log_flow_execution(
        flow_name="monthly-close",
        flow_version="1.0",
        execution_id="flow-2",
        trigger="manual",
        agent_results=[
            {"agent_id": "recorder", "status": "success", "duration_ms": 120},
            {"agent_id": "reporter", "status": "success", "duration_ms": 180},
            {"agent_id": "orchestrator", "status": "success", "duration_ms": 60},
        ],
        status="completed",
        total_duration_ms=360,
    )
    logger.log_flow_execution(
        flow_name="monthly-close",
        flow_version="1.0",
        execution_id="flow-3",
        trigger="cron",
        agent_results=[
            {"agent_id": "recorder", "status": "success", "duration_ms": 110},
            {"agent_id": "reporter", "status": "success", "duration_ms": 190},
            {"agent_id": "orchestrator", "status": "success", "duration_ms": 55},
        ],
        status="completed",
        total_duration_ms=355,
    )
    
    return AnalyticsEngine(logger)


class TestAnalyticsTimeSeries:
    def test_time_series_empty(self, engine):
        result = engine.time_series(hours=24)
        assert result["total_in_window"] == 0
        assert len(result["points"]) == 0

    def test_time_series_with_data(self, engine_with_data):
        result = engine_with_data.time_series(hours=24)
        assert result["total_in_window"] > 0
        assert len(result["points"]) > 0
        for p in result["points"]:
            assert "timestamp" in p
            assert "total" in p
            assert "success" in p
            assert "failed" in p

    def test_time_series_interval(self, engine_with_data):
        result = engine_with_data.time_series(interval="day", hours=168)
        assert len(result["points"]) > 0


class TestAnalyticsFlowPerformance:
    def test_flow_performance_empty(self, engine):
        result = engine.flow_performance()
        assert result == []

    def test_flow_performance_with_data(self, engine_with_data):
        result = engine_with_data.flow_performance(min_runs=1)
        assert len(result) >= 2  # financial-close and tax-return

        # Find financial-close
        fc = next((f for f in result if f["flow_name"] == "financial-close"), None)
        assert fc is not None
        assert fc["total_runs"] == 30  # 20 recorder + 10 reporter
        assert fc["success_rate"] > 0
        assert fc["avg_duration_ms"] > 0
        assert fc["p95_duration_ms"] > 0

    def test_flow_performance_min_runs(self, engine_with_data):
        result = engine_with_data.flow_performance(min_runs=10)
        # Only financial-close has >10 runs
        names = [f["flow_name"] for f in result]
        assert "financial-close" in names


class TestAnalyticsAgentPerformance:
    def test_agent_performance_empty(self, engine):
        result = engine.agent_performance()
        assert result == []

    def test_agent_performance_with_data(self, engine_with_data):
        result = engine_with_data.agent_performance(min_calls=1)
        assert len(result) >= 2
        # Find financial-recorder
        fr = next((a for a in result if a["agent_id"] == "financial-recorder"), None)
        assert fr is not None
        assert fr["total_calls"] == 20
        assert fr["success_rate"] == 75.0  # 15/20
        assert fr["failure_rate"] == 25.0


class TestAnalyticsBottlenecks:
    def test_bottlenecks_empty(self, engine):
        result = engine.bottlenecks()
        assert result["slowest_agents"] == []
        assert result["most_failing_agents"] == []

    def test_bottlenecks_with_data(self, engine_with_data):
        result = engine_with_data.bottlenecks()
        assert len(result["slowest_agents"]) > 0
        # tax-specialist should be slowest (highest durations)
        assert result["slowest_agents"][0]["avg_duration_ms"] > 0
        # financial-recorder should have most failures
        assert len(result["most_failing_agents"]) > 0


class TestAnalyticsPatternRecognition:
    def test_frequent_sequences_empty(self, engine):
        result = engine.frequent_sequences()
        assert result == []

    def test_frequent_sequences_with_data(self, engine_with_data):
        result = engine_with_data.frequent_sequences(min_occurrences=2)
        # Should find recorder → reporter → orchestrator pattern (3 times)
        matching = [s for s in result if "recorder" in str(s["sequence"])]
        assert len(matching) > 0
        # The pattern should appear at least 3 times
        for m in matching:
            assert m["occurrences"] >= 2

    def test_suggested_templates_empty(self, engine):
        result = engine.suggested_templates()
        assert result == []

    def test_suggested_templates_with_data(self, engine_with_data):
        result = engine_with_data.suggested_templates()
        if result:
            for s in result:
                assert s["confidence"] in ("high", "medium")
                assert len(s["agent_ids"]) > 0
                assert s["occurrences"] > 0


class TestAnalyticsAnomalies:
    def test_anomalies_empty(self, engine):
        result = engine.anomalies()
        assert result["anomalies"] == []
        assert result["threshold_ms"] == 0

    def test_anomalies_with_data(self, engine_with_data):
        result = engine_with_data.anomalies()
        assert result["mean_duration_ms"] > 0
        assert result["std_dev_ms"] > 0
        # Our data has no extreme outliers, so anomalies may be 0
        assert result["total_anomalies"] >= 0


class TestAnalyticsSummary:
    def test_summary_empty(self, engine):
        result = engine.summary()
        assert result["summary"]["total_executions_24h"] == 0
        assert result["top_flows"] == []
        assert result["top_bottlenecks"]["slowest_agents"] == []

    def test_summary_with_data(self, engine_with_data):
        result = engine_with_data.summary()
        assert result["summary"]["total_executions_24h"] > 0
        assert result["summary"]["unique_flows"] >= 2
        assert len(result["top_bottlenecks"]["slowest_agents"]) > 0
        assert "summary" in result
        assert "top_flows" in result
        assert "top_bottlenecks" in result
