"""Tests for HiveOS V2 Dashboard API endpoints."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hiveos.dashboard.app import HiveOSApp
from hiveos.dashboard.config_service import ConfigService
from hiveos.storage import StorageEngine


@pytest.fixture
def tmp_config_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def app(tmp_config_dir):
    """HiveOSApp wired to temp storage."""
    cp = tmp_config_dir / "config.yaml"
    data = {
        "server": {"host": "127.0.0.1", "port": 8420},
        "storage": {"data_dir": str(tmp_config_dir), "db_path": str(tmp_config_dir / "test.db")},
        "logging": {"level": "DEBUG"},
    }
    cp.write_text(yaml.dump(data), encoding="utf-8")
    hive_app = HiveOSApp(cp)
    yield hive_app
    hive_app.shutdown()


@pytest.fixture
def admin_key(app):
    """Get admin API key from the app's RBAC."""
    admin = app.rbac.get_user("admin")
    assert admin is not None, "Admin user not created"
    return admin.api_key


@pytest.fixture
def auth_headers(admin_key):
    return {"Authorization": f"Bearer {admin_key}"}


@pytest.fixture
def client(app, auth_headers):
    return TestClient(app.api)


# ── Health ──────────────────────────────────────────────


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data


# ── Knowledge ───────────────────────────────────────────


class TestKnowledgeEndpoints:
    def test_search_empty(self, client, auth_headers):
        resp = client.get("/api/knowledge/search?q=hello", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["count"] == 0

    def test_stats_empty(self, client, auth_headers):
        resp = client.get("/api/knowledge/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_documents" in data
        assert data["total_chunks"] == 0

    def test_sources_empty(self, client, auth_headers):
        resp = client.get("/api/knowledge/sources", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data

    def test_search_requires_query(self, client, auth_headers):
        resp = client.get("/api/knowledge/search", headers=auth_headers)
        assert resp.status_code == 422  # Missing required query param


# ── Domains ─────────────────────────────────────────────


class TestDomainEndpoints:
    def test_list_domains(self, client, auth_headers):
        resp = client.get("/api/domains", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "domains" in data
        assert isinstance(data["domains"], list)

    def test_get_domain_not_found(self, client, auth_headers):
        resp = client.get("/api/domains/nonexistent", headers=auth_headers)
        assert resp.status_code == 404

    def test_install_invalid_path(self, client, auth_headers):
        resp = client.post("/api/domains/install", json={"path": "/nonexistent/path"}, headers=auth_headers)
        assert resp.status_code == 400

    def test_remove_not_found(self, client, auth_headers):
        resp = client.delete("/api/domains/nonexistent", headers=auth_headers)
        assert resp.status_code == 404


# ── Skills ──────────────────────────────────────────────


class TestSkillEndpoints:
    def test_list_skills(self, client, auth_headers):
        resp = client.get("/api/skills", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "skills" in data
        assert isinstance(data["skills"], list)

    def test_get_skill_not_found(self, client, auth_headers):
        resp = client.get("/api/skills/nonexistent", headers=auth_headers)
        assert resp.status_code == 404

    def test_run_skill_not_found(self, client, auth_headers):
        resp = client.post("/api/skills/nonexistent/run", json={"input": {}}, headers=auth_headers)
        assert resp.status_code == 404


# ── Workflows ───────────────────────────────────────────


class TestWorkflowEndpoints:
    def test_list_workflows(self, client, auth_headers):
        resp = client.get("/api/workflows", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "workflows" in data
        assert isinstance(data["workflows"], list)

    def test_get_workflow_not_found(self, client, auth_headers):
        resp = client.get("/api/workflows/nonexistent", headers=auth_headers)
        assert resp.status_code == 404

    def test_run_workflow_not_found(self, client, auth_headers):
        resp = client.post("/api/workflows/nonexistent/run", json={"input": {}}, headers=auth_headers)
        assert resp.status_code == 404


# ── History ─────────────────────────────────────────────


class TestHistoryEndpoints:
    def test_list_history(self, client, auth_headers):
        resp = client.get("/api/history", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "executions" in data
        assert isinstance(data["executions"], list)

    def test_list_history_with_limit(self, client, auth_headers):
        resp = client.get("/api/history?limit=5", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_execution_not_found(self, client, auth_headers):
        resp = client.get("/api/history/nonexistent-id", headers=auth_headers)
        assert resp.status_code == 200  # Returns 200 with null execution
        data = resp.json()
        assert data.get("execution") is None


# ── Config ──────────────────────────────────────────────


class TestConfigEndpoints:
    def test_get_config(self, client, auth_headers):
        resp = client.get("/api/config", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "server" in data
        assert "storage" in data

    def test_update_config(self, client, auth_headers):
        resp = client.put("/api/config", json={"key": "logging.level", "value": "DEBUG"}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["value"] == "DEBUG"

    def test_update_and_verify(self, client, auth_headers):
        client.put("/api/config", json={"key": "server.port", "value": 9999}, headers=auth_headers)
        resp = client.get("/api/config", headers=auth_headers)
        assert resp.json()["server"]["port"] == 9999


# ── Index / Static ──────────────────────────────────────


class TestStaticServing:
    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "HiveOS" in resp.text


# ── ConfigService unit tests (standalone) ───────────────


class TestConfigServiceUnit:
    def test_default_creation(self, tmp_path):
        cs = ConfigService(tmp_path / "cs_default.yaml")
        assert (tmp_path / "cs_default.yaml").exists()
        assert cs.get("server.port") == 8420

    def test_set_get(self, tmp_path):
        cs = ConfigService(tmp_path / "cs_setget.yaml")
        cs.set("server.port", 5555)
        assert cs.get("server.port") == 5555

    def test_to_dict_returns_copy(self, tmp_path):
        cs = ConfigService(tmp_path / "cs_copy.yaml")
        d = cs.to_dict()
        d["server"]["port"] = 9999
        assert cs.get("server.port") == 8420

    def test_reload(self, tmp_path):
        cp = tmp_path / "cs_reload.yaml"
        cs = ConfigService(cp)
        cs.set("server.port", 5555)
        # Modify directly
        data = yaml.safe_load(cp.read_text(encoding="utf-8"))
        data["server"]["port"] = 1111
        cp.write_text(yaml.dump(data), encoding="utf-8")
        cs.reload()
        assert cs.get("server.port") == 1111