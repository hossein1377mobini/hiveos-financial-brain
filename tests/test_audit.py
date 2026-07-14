"""Tests for Audit Trail — models, trail, and gbrain integration."""

from pathlib import Path
import json
import pytest
from datetime import datetime, timezone, timedelta, date as date_type
from src.hiveos.audit.models import AuditEntry, AuditAction, AuditResource, AuditResult
from src.hiveos.audit.trail import AuditTrail


class TestAuditEntry:
    """AuditEntry data model tests."""

    def test_entry_creation(self):
        entry = AuditEntry(
            action=AuditAction.CREATE,
            resource=AuditResource.AGENT,
            actor="test-user",
            resource_id="node-1",
            message="Test entry",
        )
        assert entry.action == AuditAction.CREATE
        assert entry.resource == AuditResource.AGENT
        assert entry.actor == "test-user"
        assert entry.resource_id == "node-1"
        assert entry.entry_id.startswith("aud-")
        assert entry.timestamp != ""

    def test_entry_defaults(self):
        entry = AuditEntry(
            action=AuditAction.READ,
            resource=AuditResource.FLOW,
            actor="system",
        )
        assert entry.result == AuditResult.SUCCESS
        assert entry.status_code == 200
        assert entry.details == {}
        assert entry.message == ""
        assert entry.ip == ""
        assert entry.duration_ms == 0.0

    def test_to_dict(self):
        entry = AuditEntry(
            action=AuditAction.EXECUTE,
            resource=AuditResource.TASK,
            actor="operator",
            resource_id="t-1",
            result=AuditResult.FAILURE,
            status_code=500,
            message="Task failed",
            details={"error": "timeout"},
            entry_id="aud-test123",
        )
        d = entry.to_dict()
        assert d["entry_id"] == "aud-test123"
        assert d["action"] == "execute"
        assert d["resource"] == "task"
        assert d["actor"] == "operator"
        assert d["result"] == "failure"
        assert d["details"]["error"] == "timeout"

    def test_from_dict_roundtrip(self):
        original = AuditEntry(
            action=AuditAction.UPDATE,
            resource=AuditResource.USER,
            actor="admin",
            resource_id="jdoe",
            result=AuditResult.SUCCESS,
            status_code=200,
            message="Role updated",
            details={"old_role": "viewer", "new_role": "operator"},
            ip="192.168.1.1",
            duration_ms=12.5,
        )
        d = original.to_dict()
        restored = AuditEntry.from_dict(d)
        assert restored.action == original.action
        assert restored.resource == original.resource
        assert restored.actor == original.actor
        assert restored.message == original.message
        assert restored.details == original.details
        assert restored.duration_ms == 12.5

    def test_to_json_roundtrip(self):
        entry = AuditEntry(
            action=AuditAction.DELETE,
            resource=AuditResource.PACKAGE,
            actor="operator",
        )
        raw = entry.to_json()
        restored = AuditEntry.from_json(raw)
        assert restored.action == entry.action
        assert restored.resource == entry.resource
        assert restored.actor == entry.actor
        assert restored.entry_id == entry.entry_id

    def test_gbrain_markdown(self):
        entry = AuditEntry(
            action=AuditAction.REGISTER,
            resource=AuditResource.AGENT,
            actor="admin",
            resource_id="node-x",
            message="Node registered",
        )
        md = entry.to_gbrain_markdown()
        assert "Audit:" in md
        assert "admin" in md
        assert "register" in md
        assert "agent" in md
        assert "node-x" in md

    def test_all_actions_defined(self):
        """All Permission actions should map to AuditActions."""
        from src.hiveos.rbac.models import Action as RBACAction
        for a in RBACAction:
            assert a.value in [aa.value for aa in AuditAction], \
                f"Missing audit action for RBAC action '{a.value}'"


class TestAuditTrail:
    """AuditTrail JSONL persistence tests."""

    @pytest.fixture
    def trail(self, tmp_path):
        """AuditTrail with temp storage."""
        return AuditTrail(data_dir=tmp_path)

    def test_log_and_count(self, trail):
        entry = AuditEntry(action=AuditAction.CREATE, resource=AuditResource.AGENT, actor="admin")
        eid = trail.log(entry)
        assert eid == entry.entry_id
        assert trail.count() == 1

    def test_log_simple(self, trail):
        eid = trail.log_simple(AuditAction.READ, AuditResource.FLOW, "user1")
        assert eid.startswith("aud-")
        assert trail.count() == 1

    def test_read_today(self, trail):
        trail.log_simple(AuditAction.CREATE, AuditResource.AGENT, "admin")
        trail.log_simple(AuditAction.READ, AuditResource.FLOW, "user1")
        entries = trail.read_today()
        assert len(entries) == 2
        assert entries[0].action == AuditAction.CREATE
        assert entries[1].action == AuditAction.READ

    def test_read_range(self, trail):
        trail.log_simple(AuditAction.CREATE, AuditResource.AGENT, "admin")
        today = date_type.today()
        entries = trail.read_range(today, today)
        assert len(entries) == 1

    def test_multiple_days(self, trail, tmp_path):
        trail.log_simple(AuditAction.CREATE, AuditResource.AGENT, "admin")
        # Create another trail instance pointing to same dir
        trail2 = AuditTrail(data_dir=tmp_path)
        trail2.log_simple(AuditAction.READ, AuditResource.FLOW, "user2")
        assert trail.count() == 2

    def test_list_files(self, trail):
        assert len(trail.list_files()) == 0
        trail.log_simple(AuditAction.CREATE, AuditResource.AGENT, "admin")
        files = trail.list_files()
        assert len(files) == 1
        assert files[0].suffix == ".jsonl"

    def test_search_local(self, trail):
        trail.log_simple(AuditAction.CREATE, AuditResource.AGENT, "admin",
                         resource_id="node-alpha", message="Alpha node created")
        trail.log_simple(AuditAction.DELETE, AuditResource.AGENT, "admin",
                         resource_id="node-beta", message="Beta node removed")
        results = trail.search_local("Alpha")
        assert len(results) == 1
        assert results[0].resource_id == "node-alpha"
        results = trail.search_local("node")
        assert len(results) == 2

    def test_stats(self, trail):
        assert trail.stats()["total_entries"] == 0
        trail.log_simple(AuditAction.CREATE, AuditResource.AGENT, "admin")
        trail.log_simple(AuditAction.EXECUTE, AuditResource.TASK, "operator")
        trail.log_simple(AuditAction.EXECUTE, AuditResource.TASK, "operator",
                         result=AuditResult.FAILURE)
        stats = trail.stats()
        assert stats["total_entries"] == 3
        assert stats["actions"]["execute"] == 2
        assert stats["actions"]["create"] == 1
        assert stats["resources"]["task"] == 2
        assert stats["resources"]["agent"] == 1
        assert stats["errors"] == 1

    def test_rotate(self, trail):
        trail.log_simple(AuditAction.CREATE, AuditResource.AGENT, "admin")
        # Rotate with keep_days=0 should remove today's file... but rotate
        # removes files with date < cutoff, not <= cutoff
        # So keep_days=0 should keep today
        removed = trail.rotate(keep_days=0)
        assert removed == 0  # today's file is kept
        assert trail.count() == 1

    def test_rotate_removes_old(self, trail, tmp_path):
        # Create an old file manually
        old_date = date_type.today() - timedelta(days=100)
        old_file = tmp_path / f"{old_date.isoformat()}.jsonl"
        old_file.write_text('{"entry_id":"old"}\n', encoding="utf-8")
        # Today's file
        trail.log_simple(AuditAction.CREATE, AuditResource.AGENT, "admin")
        removed = trail.rotate(keep_days=30)
        assert removed == 1
        assert trail.count() == 1

    def test_invalid_json_skipped(self, trail):
        daily = trail._daily_file()
        with open(daily, "w") as f:
            f.write("invalid json\n")
        entries = trail.read_today()
        assert len(entries) == 0

    def test_large_entry(self, trail):
        details = {"data": "x" * 10000}
        trail.log_simple(AuditAction.CREATE, AuditResource.AGENT, "admin",
                         details=details)
        assert trail.count() == 1

    def test_concurrent_logging(self, trail):
        """Multiple logs should all be readable back."""
        for i in range(10):
            trail.log_simple(AuditAction.CREATE, AuditResource.AGENT,
                             f"user-{i}", resource_id=f"node-{i}")
        entries = trail.read_today()
        assert len(entries) == 10
        assert entries[0].actor == "user-0"
        assert entries[9].actor == "user-9"
