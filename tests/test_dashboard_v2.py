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
def config_path(tmp_config_dir):
    return tmp_config_dir / "config.yaml"


@pytest.fixture
def config_service(config_path):
    """ConfigService with temp db path."""
    db_path = config_path.parent / "test.db"
    data = {
        "server": {"host": "127.0.0.1", "port": 8420},
        "storage": {"data_dir": str(config_path.parent), "db_path": str(db_path)},
        "logging": {"level": "DEBUG"},
    }
    config_path.write_text(yaml.dump(data), encoding="utf-8")
    return ConfigService(config_path)


@pytest.fixture
def app(config_service):
    """HiveOSApp wired to temp storage."""
    hive_app = HiveOSApp(config_service.config_path)
    yield hive_app
    hive_app.shutdown()


@pytest.fixture
def client(app):
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
    def test_search_empty(self, client):
        resp = client.get("/api/knowledge/search?q=hello")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["count"] == 0

    def test_stats_empty(self, client):
        resp = client.get("/api/knowledge/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_documents" in data
        assert data["total_chunks"] == 0

    def test_sources_empty(self, client):
        resp = client.get("/api/knowledge/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data

    def test_search_requires_query(self, client):
        resp = client.get("/api/knowledge/search")
        assert resp.status_code == 422  # Missing required query param


# ── Domains ─────────────────────────────────────────────


class TestDomainEndpoints:
    def test_list_domains(self, client):
        resp = client.get("/api/domains")
        assert resp.status_code == 200
        data = resp.json()
        assert "domains" in data
        assert isinstance(data["domains"], list)

    def test_get_domain_not_found(self, client):
        resp = client.get("/api/domains/nonexistent")
        assert resp.status_code == 404

    def test_install_invalid_path(self, client):
        resp = client.post("/api/domains/install", json={"path": "/nonexistent/path"})
        assert resp.status_code == 400

    def test_remove_not_found(self, client):
        resp = client.delete("/api/domains/nonexistent")
        assert resp.status_code == 404


# ── Skills ──────────────────────────────────────────────


class TestSkillEndpoints:
    def test_list_skills(self, client):
        resp = client.get("/api/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert "skills" in data
        assert isinstance(data["skills"], list)

    def test_get_skill_not_found(self, client):
        resp = client.get("/api/skills/nonexistent")
        assert resp.status_code == 404

    def test_run_skill_not_found(self, client):
        resp = client.post("/api/skills/nonexistent/run", json={"input": {}})
        assert resp.status_code == 404


# ── Workflows ───────────────────────────────────────────


class TestWorkflowEndpoints:
    def test_list_workflows(self, client):
        resp = client.get("/api/workflows")
        assert resp.status_code == 200
        data = resp.json()
        assert "workflows" in data
        assert isinstance(data["workflows"], list)

    def test_get_workflow_not_found(self, client):
        resp = client.get("/api/workflows/nonexistent")
        assert resp.status_code == 404

    def test_run_workflow_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/run", json={"input": {}})
        assert resp.status_code == 404


# ── History ─────────────────────────────────────────────


class TestHistoryEndpoints:
    def test_list_history(self, client):
        resp = client.get("/api/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "executions" in data
        assert isinstance(data["executions"], list)

    def test_list_history_with_limit(self, client):
        resp = client.get("/api/history?limit=5")
        assert resp.status_code == 200

    def test_get_execution_not_found(self, client):
        resp = client.get("/api/history/nonexistent-id")
        assert resp.status_code == 200  # Returns 200 with null execution
        data = resp.json()
        assert data.get("execution") is None


# ── Config ──────────────────────────────────────────────


class TestConfigEndpoints:
    def test_get_config(self, client):
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "server" in data
        assert "storage" in data

    def test_update_config(self, client):
        resp = client.put("/api/config", json={"key": "logging.level", "value": "DEBUG"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["value"] == "DEBUG"

    def test_update_and_verify(self, client):
        client.put("/api/config", json={"key": "server.port", "value": 9999})
        resp = client.get("/api/config")
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
