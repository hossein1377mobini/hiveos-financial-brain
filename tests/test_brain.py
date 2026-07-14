"""Tests for HiveOS Brain — EventStream, DecisionTracer, ApprovalGateEngine."""

import pytest
from datetime import datetime, timezone

from hiveos.brain import EventStream, DecisionTracer, ApprovalGateEngine


# ── B-01: EventStream Tests ───────────────────────────────────────────

class TestEventStream:
    def test_emit_event(self):
        es = EventStream()
        event_id = es.emit("agent.spawn", "test-agent", {"name": "test"})
        assert event_id
        assert len(event_id) > 0

    def test_get_event_by_id(self):
        es = EventStream()
        event_id = es.emit("agent.spawn", "test-agent", {"name": "test"})
        event = es.get_event(event_id)
        assert event is not None
        assert event["event_type"] == "agent.spawn"
        assert event["source"] == "test-agent"
        assert event["payload"]["name"] == "test"

    def test_get_events_default(self):
        es = EventStream()
        for i in range(3):
            es.emit("test.event", "src", {"i": i})
        events = es.get_events()
        assert len(events) == 3

    def test_get_events_filtered(self):
        es = EventStream()
        es.emit("type.a", "src")
        es.emit("type.b", "src")
        es.emit("type.a", "src")
        events = es.get_events(event_type="type.a")
        assert len(events) == 2
        assert all(e["event_type"] == "type.a" for e in events)

    def test_get_events_limit(self):
        es = EventStream()
        for i in range(100):
            es.emit("test.event", "src")
        events = es.get_events(limit=10)
        assert len(events) == 10

    def test_maxlen(self):
        es = EventStream(maxlen=5)
        for i in range(10):
            es.emit("test.event", "src", {"i": i})
        assert es.count == 5
        events = es.get_events()
        assert events[0]["payload"]["i"] == 5  # oldest kept

    def test_clear(self):
        es = EventStream()
        es.emit("test", "src")
        es.clear()
        assert es.count == 0
        assert len(es.get_events()) == 0

    def test_stats(self):
        es = EventStream()
        es.emit("type.a", "src1")
        es.emit("type.b", "src2")
        es.emit("type.a", "src3")
        stats = es.stats()
        assert stats["total_events"] == 3
        assert stats["by_type"]["type.a"] == 2
        assert stats["by_type"]["type.b"] == 1


# ── B-02: DecisionTracer Tests ────────────────────────────────────────

class TestDecisionTracer:
    def test_start_trace(self):
        dt = DecisionTracer()
        trace_id = dt.start_trace(context={"query": "test"})
        assert trace_id
        trace = dt.get_trace(trace_id)
        assert trace["status"] == "in_progress"
        assert trace["context"]["query"] == "test"

    def test_custom_trace_id(self):
        dt = DecisionTracer()
        dt.start_trace(trace_id="my-trace", context={})
        trace = dt.get_trace("my-trace")
        assert trace["trace_id"] == "my-trace"

    def test_add_step(self):
        dt = DecisionTracer()
        trace_id = dt.start_trace(context={})
        step = dt.add_step(trace_id, {
            "action": "classify",
            "reasoning": "keyword match",
            "result": "financial",
        })
        assert step is not None
        assert step["step_number"] == 1
        assert step["action"] == "classify"

    def test_complete_trace(self):
        dt = DecisionTracer()
        trace_id = dt.start_trace(context={})
        ok = dt.complete_trace(trace_id, outcome="success", summary="Done")
        assert ok is True
        trace = dt.get_trace(trace_id)
        assert trace["status"] == "completed"
        assert trace["outcome"] == "success"
        assert trace["summary"] == "Done"
        assert trace["completed_at"]

    def test_fail_trace(self):
        dt = DecisionTracer()
        trace_id = dt.start_trace(context={})
        ok = dt.fail_trace(trace_id, error="Something broke")
        assert ok is True
        trace = dt.get_trace(trace_id)
        assert trace["status"] == "failed"
        assert trace["error"] == "Something broke"

    def test_add_step_nonexistent(self):
        dt = DecisionTracer()
        step = dt.add_step("nonexistent", {"action": "test"})
        assert step is None

    def test_list_traces(self):
        dt = DecisionTracer()
        t1 = dt.start_trace(context={})
        t2 = dt.start_trace(context={})
        dt.complete_trace(t1, "done")
        traces = dt.list_traces()
        assert len(traces) == 2

    def test_list_traces_filtered(self):
        dt = DecisionTracer()
        t1 = dt.start_trace(context={})
        t2 = dt.start_trace(context={})
        dt.complete_trace(t1, "done")
        completed = dt.list_traces(status="completed")
        assert len(completed) == 1
        in_progress = dt.list_traces(status="in_progress")
        assert len(in_progress) == 1

    def test_stats(self):
        dt = DecisionTracer()
        dt.start_trace(context={})
        dt.start_trace(context={})
        dt.start_trace(trace_id="x", context={})
        dt.complete_trace("x", "done")
        stats = dt.stats()
        assert stats["total_traces"] == 3
        assert stats["by_status"]["in_progress"] == 2
        assert stats["by_status"]["completed"] == 1


# ── B-03: ApprovalGateEngine Tests ────────────────────────────────────

class TestApprovalGateEngine:
    def test_create_gate(self):
        ag = ApprovalGateEngine()
        gate = ag.create_gate(title="Test", description="desc", requestor="user1")
        assert gate["status"] == "pending"
        assert gate["title"] == "Test"
        assert gate["requestor"] == "user1"
        assert gate["gate_id"]

    def test_custom_gate_id(self):
        ag = ApprovalGateEngine()
        gate = ag.create_gate(gate_id="my-gate", title="Test", description="", requestor="user")
        assert gate["gate_id"] == "my-gate"

    def test_approve(self):
        ag = ApprovalGateEngine()
        gate = ag.create_gate(title="Test", description="", requestor="user")
        result = ag.approve(gate["gate_id"], approver="admin", notes="Looks good")
        assert result["status"] == "approved"
        assert result["approver"] == "admin"
        assert result["resolved_at"]

    def test_reject(self):
        ag = ApprovalGateEngine()
        gate = ag.create_gate(title="Test", description="", requestor="user")
        result = ag.reject(gate["gate_id"], approver="admin", reason="Not ready")
        assert result["status"] == "rejected"
        assert result["resolution_reason"] == "Not ready"

    def test_approve_already_resolved(self):
        ag = ApprovalGateEngine()
        gate = ag.create_gate(title="Test", description="", requestor="user")
        ag.approve(gate["gate_id"], "admin")
        result = ag.reject(gate["gate_id"], "admin")  # should remain approved
        assert result["status"] == "approved"

    def test_get_gate(self):
        ag = ApprovalGateEngine()
        gate = ag.create_gate(gate_id="g1", title="Test", description="desc", requestor="user")
        result = ag.get_gate("g1")
        assert result["title"] == "Test"

    def test_get_gate_nonexistent(self):
        ag = ApprovalGateEngine()
        assert ag.get_gate("nonexistent") is None

    def test_list_gates(self):
        ag = ApprovalGateEngine()
        ag.create_gate(title="A", description="", requestor="u")
        ag.create_gate(title="B", description="", requestor="u")
        gates = ag.list_gates()
        assert len(gates) == 2

    def test_list_gates_filtered(self):
        ag = ApprovalGateEngine()
        g1 = ag.create_gate(title="A", description="", requestor="u")
        ag.create_gate(title="B", description="", requestor="u")
        ag.approve(g1["gate_id"], "admin")
        pending = ag.list_gates(status="pending")
        assert len(pending) == 1
        approved = ag.list_gates(status="approved")
        assert len(approved) == 1

    def test_pending_for_user(self):
        ag = ApprovalGateEngine()
        ag.create_gate(title="A", description="", requestor="u")
        g2 = ag.create_gate(title="B", description="", requestor="u")
        ag.approve(g2["gate_id"], "admin")
        pending = ag.pending_for_user()
        assert len(pending) == 1
        assert pending[0]["title"] == "A"

    def test_gate_expiry(self):
        ag = ApprovalGateEngine()
        gate = ag.create_gate(
            title="Expiring", description="", requestor="user",
            timeout_seconds=0,  # expires immediately
        )
        import time
        time.sleep(0.01)
        result = ag.get_gate(gate["gate_id"])
        assert result["status"] == "expired"

    def test_stats(self):
        ag = ApprovalGateEngine()
        g1 = ag.create_gate(title="A", description="", requestor="u")
        g2 = ag.create_gate(title="B", description="", requestor="u")
        ag.approve(g1["gate_id"], "admin")
        stats = ag.stats()
        assert stats["total_gates"] == 2
        assert stats["by_status"]["pending"] == 1
        assert stats["by_status"]["approved"] == 1
        assert stats["resolved_count"] == 1
