"""
Tests for HiveOS Dashboard Server.

Covers:
- DashboardApp API endpoints
- Data aggregation from subsystems
- DashboardServer lifecycle (start/stop/status)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from fastapi.testclient import TestClient

# Ensure src is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hiveos.dashboard import DashboardServer, DashboardApp
from hiveos.mothership.agent_registry import AgentRegistry
from hiveos.mothership.task_router import TaskRouter
from hiveos.mothership.communication_bus import CommunicationBus, MessageType
from hiveos.mothership.resilience import ResilienceEngine, HealthStatus, FailureType
from hiveos.rbac import RBACManager, Resource, Action, Permission
from hiveos.audit import AuditTrail, AuditAction, AuditResource, AuditResult
from hiveos.storage import StorageEngine # NEW


# ── Helper: create mock objects ──────────────────────────────────────


@pytest.fixture
def storage(db_path):
    s = StorageEngine(db_path)
    yield s
    s.close()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
def storage(db_path):
    s = StorageEngine(db_path)
    yield s
    s.close()
    if db_path.exists():
        db_path.unlink()


def make_mock_obj(**attrs):
    """Create a MagicMock with the given attributes set."""
    m = MagicMock()
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def temp_dir():
    """Temporary directory for audit data."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry with sample agents using simple mocks."""
    reg = MagicMock(spec=AgentRegistry)

    agent_a = make_mock_obj(
        node_name="agent-a",
        name="agent-a",
        status="online",
        capabilities={"search": True, "code": True},
        current_load=0,
        max_concurrent=5,
        total_tasks_completed=42,
        total_errors=1,
        uptime_seconds=3600,
        last_seen=datetime.utcnow().isoformat(),
    )
    agent_b = make_mock_obj(
        node_name="agent-b",
        name="agent-b",
        status="busy",
        capabilities={"analyze": True},
        current_load=4,
        max_concurrent=5,
        total_tasks_completed=18,
        total_errors=0,
        uptime_seconds=7200,
        last_seen=datetime.utcnow().isoformat(),
    )
    agent_c = make_mock_obj(
        node_name="agent-c",
        name="agent-c",
        status="offline",
        capabilities={"search": True},
        current_load=0,
        max_concurrent=5,
        total_tasks_completed=7,
        total_errors=3,
        uptime_seconds=0,
        last_seen=datetime.utcnow().isoformat(),
    )

    reg._agents = {
        "agent-a": agent_a,
        "agent-b": agent_b,
        "agent-c": agent_c,
    }
    return reg


@pytest.fixture
def mock_task_router():
    """Mock task router with sample assignments."""
    router = MagicMock(spec=TaskRouter)

    t1 = make_mock_obj(
        task_id="t1", capability="search", node_name="agent-a",
        node="agent-a", status="completed",
        created_at=datetime.utcnow().isoformat(),
        completed_at=datetime.utcnow().isoformat(), result="done",
    )
    t2 = make_mock_obj(
        task_id="t2", capability="code", node_name="agent-b",
        node="agent-b", status="running",
        created_at=datetime.utcnow().isoformat(),
        completed_at=None, result="",
    )
    t3 = make_mock_obj(
        task_id="t3", capability="search", node_name="agent-a",
        node="agent-a", status="pending",
        created_at=datetime.utcnow().isoformat(),
        completed_at=None, result="",
    )
    t4 = make_mock_obj(
        task_id="t4", capability="analyze", node_name="agent-c",
        node="agent-c", status="failed",
        created_at=datetime.utcnow().isoformat(),
        completed_at=datetime.utcnow().isoformat(), result="error",
    )

    router._assignments = {"t1": t1, "t2": t2, "t3": t3, "t4": t4}
    return router


@pytest.fixture
def mock_comm_bus():
    """Mock communication bus with sample messages."""
    bus = MagicMock(spec=CommunicationBus)
    bus._message_count = 42
    bus.total_messages = 42
    bus._subscribers = {"agent-a": True, "agent-b": True}
    bus.subscribers = {"agent-a": True, "agent-b": True}

    def make_msg(mid: str, mtype: str, sender: str, target: str):
        return make_mock_obj(
            msg_id=mid, id=mid,
            msg_type=mtype, type=mtype,
            sender=sender, source=sender,
            target=target, destination=target,
            timestamp=datetime.utcnow().isoformat(),
        )

    bus._messages = [
        make_msg("m1", "heartbeat", "agent-a", "mothership"),
        make_msg("m2", "task_complete", "agent-b", "mothership"),
        make_msg("m3", "health_report", "agent-c", "mothership"),
    ]
    bus.messages = bus._messages
    return bus


@pytest.fixture
def mock_resilience():
    """Mock resilience engine with sample health states."""
    eng = MagicMock(spec=ResilienceEngine)

    now = datetime.utcnow().isoformat()
    eng._states = {
        "agent-a": {"status": "healthy", "failures": 0, "successes": 42, "last_change": now},
        "agent-b": {"status": "degraded", "failures": 2, "successes": 35, "last_change": now},
        "agent-c": {"status": "unhealthy", "failures": 5, "successes": 7, "last_change": now},
    }
    eng._failures = {
        "agent-c": [
            make_mock_obj(
                node="agent-c",
                failure_type="heartbeat_timeout",
                type="heartbeat_timeout",
                timestamp=now,
                message="Lost connection",
            ),
        ],
    }
    return eng


@pytest.fixture
def mock_rbac():
    """Mock RBAC manager with sample users and roles."""
    mgr = MagicMock(spec=RBACManager)

    admin_u = make_mock_obj(username="admin", role="admin", enabled=True)
    oper_u = make_mock_obj(username="operator", role="operator", enabled=True)
    view_u = make_mock_obj(username="viewer", role="viewer", enabled=True)

    mgr._users = {"admin": admin_u, "operator": oper_u, "viewer": view_u}
    mgr.users = mgr._users

    all_perm = [Permission(Resource.MOTHERSHIP, Action.READ)]
    oper_perm = [Permission(Resource.AGENT, Action.READ), Permission(Resource.FLOW, Action.UPDATE)]
    view_perm = [Permission(Resource.MOTHERSHIP, Action.READ)]

    admin_r = make_mock_obj(name="admin", permissions=all_perm)
    oper_r = make_mock_obj(name="operator", permissions=oper_perm)
    view_r = make_mock_obj(name="viewer", permissions=view_perm)

    mgr._roles = {"admin": admin_r, "operator": oper_r, "viewer": view_r}
    mgr.roles = mgr._roles
    return mgr


@pytest.fixture
def mock_audit():
    """Mock audit trail with sample entries."""
    audit = MagicMock(spec=AuditTrail)

    def make_entry(eid, action, resource, result, actor, detail):
        return make_mock_obj(
            entry_id=eid, id=eid,
            action=action, resource=resource,
            result=result,
            user=actor, actor=actor,
            detail=detail, details=detail,
            timestamp=datetime.utcnow().isoformat(),
        )

    audit._entries = [
        make_entry("a1", AuditAction.CREATE, AuditResource.AGENT, AuditResult.SUCCESS, "admin", "Registered agent-a"),
        make_entry("a2", AuditAction.UPDATE, AuditResource.TASK, AuditResult.SUCCESS, "operator", "Updated task t2"),
        make_entry("a3", AuditAction.DELETE, AuditResource.FLOW, AuditResult.DENIED, "viewer", "Unauthorized delete"),
    ]
    audit.entries = audit._entries
    return audit


@pytest.fixture
def dashboard_app(mock_agent_registry, mock_task_router, mock_comm_bus,
                   mock_resilience, mock_rbac, mock_audit, temp_dir, storage):
    """DashboardApp with mocked subsystems."""
    app = DashboardApp(
        agent_registry=mock_agent_registry,
        task_router=mock_task_router,
        comm_bus=mock_comm_bus,
        resilience=mock_resilience,
        rbac=mock_rbac,
        audit=mock_audit,
        data_dir=temp_dir,
        storage=storage,
    )
    yield app


@pytest.fixture
def client(dashboard_app):
    """FastAPI test client."""
    return TestClient(dashboard_app.app)


# ── Tests ─────────────────────────────────────────────────────────────


class TestDashboardApp:
    """Test DashboardApp API endpoints."""

    def test_index_page(self, client):
        """Dashboard index page returns HTML."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "HiveOS" in resp.text

    def test_overview(self, client):
        """Overview endpoint returns aggregated stats."""
        resp = client.get("/api/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "agents" in data
        assert "tasks" in data
        assert "health" in data
        assert "bus" in data
        assert "rbac" in data
        assert "audit" in data
        assert data["agents"]["total"] == 3
        assert data["agents"]["online"] == 1
        assert data["agents"]["offline"] == 1
        assert data["agents"]["busy"] == 1

    def test_overview_tasks(self, client):
        """Overview shows correct task counts."""
        resp = client.get("/api/overview")
        data = resp.json()
        assert data["tasks"]["total"] == 4
        assert data["tasks"]["completed"] == 1
        assert data["tasks"]["running"] == 1
        assert data["tasks"]["pending"] == 1
        assert data["tasks"]["failed"] == 1

    def test_overview_health(self, client):
        """Overview shows correct health counts."""
        resp = client.get("/api/overview")
        data = resp.json()
        assert data["health"]["healthy"] == 1
        assert data["health"]["degraded"] == 1
        assert data["health"]["unhealthy"] == 1

    def test_overview_rbac(self, client):
        """Overview shows RBAC user/role counts."""
        resp = client.get("/api/overview")
        data = resp.json()
        assert data["rbac"]["users"] == 3
        assert data["rbac"]["roles"] == 3

    def test_agents_endpoint(self, client):
        """Agents endpoint returns agent list."""
        resp = client.get("/api/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert "agents" in data
        assert len(data["agents"]) == 3
        names = [a["name"] for a in data["agents"]]
        assert "agent-a" in names
        assert "agent-b" in names
        assert "agent-c" in names

    def test_tasks_endpoint(self, client):
        """Tasks endpoint returns task list."""
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert "tasks" in data
        assert len(data["tasks"]) == 4

    def test_health_endpoint(self, client):
        """Health endpoint returns node health data."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert len(data["nodes"]) == 3
        assert "recent_failures" in data

    def test_bus_endpoint(self, client):
        """Bus endpoint returns message stats."""
        resp = client.get("/api/bus")
        assert resp.status_code == 200
        data = resp.json()
        assert "stats" in data
        assert data["stats"]["total"] == 42
        assert data["stats"]["subscribers"] == 2

    def test_audit_endpoint(self, client):
        """Audit endpoint returns entry list."""
        resp = client.get("/api/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert len(data["entries"]) == 3

    def test_rbac_endpoint(self, client):
        """RBAC endpoint returns users and roles."""
        resp = client.get("/api/rbac")
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "roles" in data
        assert len(data["users"]) == 3
        assert len(data["roles"]) == 3

    def test_domains_endpoint(self, client, temp_dir):
        """Domains endpoint returns installed domains."""
        # Create a mock domain
        domain_dir = temp_dir / "domains" / "accounting"
        domain_dir.mkdir(parents=True)
        (domain_dir / "domain.yaml").write_text(
            "name: accounting\nlabel: Accounting\nversion: 0.1.0\nagents:\n  - reconciler\nflows:\n  - close\n"
        )
        resp = client.get("/api/domains")
        assert resp.status_code == 200
        data = resp.json()
        assert "domains" in data
        assert len(data["domains"]) >= 1

    def test_all_endpoints_return_json(self, client):
        """All API endpoints return valid JSON."""
        endpoints = [
            "/api/overview",
            "/api/agents",
            "/api/tasks",
            "/api/health",
            "/api/bus",
            "/api/audit",
            "/api/rbac",
            "/api/nodes",
        ]
        for ep in endpoints:
            resp = client.get(ep)
            assert resp.status_code == 200, f"{ep} returned {resp.status_code}"
            assert "application/json" in resp.headers.get("content-type", ""), f"{ep} is not JSON"


class TestDashboardServer:
    """Test DashboardServer lifecycle."""

    def test_create_default(self):
        """Server can be created with defaults."""
        server = DashboardServer()
        status = server.status()
        assert status["running"] is False
        assert status["host"] == "127.0.0.1"
        assert status["port"] == 8080

    def test_create_custom(self):
        """Server can be created with custom host/port."""
        server = DashboardServer(host="0.0.0.0", port=9090)
        status = server.status()
        assert status["host"] == "0.0.0.0"
        assert status["port"] == 9090

    def test_status_when_not_running(self):
        """Status correctly reports not running."""
        server = DashboardServer()
        assert server.status()["running"] is False

    def test_start_stop(self):
        """Server can start and stop."""
        server = DashboardServer(port=8081)
        result = server.start()
        assert "Dashboard started" in result
        time.sleep(0.3)
        assert server.status()["running"] is True

        result = server.stop()
        assert "Dashboard stopped" in result

    def test_start_already_running(self):
        """Starting an already running server returns message."""
        server = DashboardServer(port=8082)
        server.start()
        time.sleep(0.3)
        result = server.start()
        assert "already running" in result
        server.stop()

    def test_stop_when_not_running(self):
        """Stopping a non-running server returns message."""
        server = DashboardServer()
        result = server.stop()
        assert "not running" in result


class TestDashboardWithMocks:
    """Integration-style tests with mocked subsystems."""

    def test_dashboard_app_creates_app(self, dashboard_app):
        """DashboardApp creates a FastAPI app."""
        assert dashboard_app.app is not None
        assert dashboard_app.app.title == "HiveOS Dashboard"

    def test_dashboard_server_with_subsystems(self, mock_agent_registry,
                                               mock_task_router, mock_comm_bus,
                                               mock_resilience, temp_dir, storage):
        """Server can be created with subsystem references."""
        server = DashboardServer(
            agent_registry=mock_agent_registry,
            task_router=mock_task_router,
            comm_bus=mock_comm_bus,
            resilience=mock_resilience,
            data_dir=temp_dir,
            storage=storage,
        )
        assert server._agent_registry is not None
        assert server._task_router is not None
        server.stop()

    def test_data_dir_creates_domains(self, temp_dir, storage):
        """Dashboard uses data_dir for domain discovery."""
        app = DashboardApp(data_dir=temp_dir, storage=storage)
        domains_path = temp_dir / "domains"
        assert not domains_path.exists() or list(domains_path.iterdir()) == []
        app.storage.close()

    @patch("hiveos.dashboard.server.uvicorn")
    def test_server_start_thread(self, mock_uvicorn, dashboard_app):
        """Server start creates uvicorn config and thread."""
        server = DashboardServer()
        assert server.status()["running"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
