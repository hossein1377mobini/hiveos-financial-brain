"""Tests for Dashboard Auth Middleware (CRIT-1 fix).

Covers:
- AuthChecker: 401 on missing header, 401 on invalid key, 403 on insufficient perms
- Audit logging of denied requests
- V2 app endpoints require Bearer token
- CORS middleware headers
- Admin-only vs user-level permission checks
"""

from __future__ import annotations

import tempfile
import secrets
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hiveos.rbac import RBACManager, Resource, Action
from hiveos.audit import AuditTrail, AuditAction, AuditResource, AuditResult
from hiveos.audit.models import AuditEntry
from hiveos.dashboard.auth import AuthChecker


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def tmp_data_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def rbac(tmp_data_dir):
    return RBACManager(data_dir=tmp_data_dir)


@pytest.fixture
def audit(tmp_data_dir):
    return AuditTrail(data_dir=tmp_data_dir / "audit")


@pytest.fixture
def auth_checker(rbac, audit):
    return AuthChecker(rbac=rbac, audit=audit)


@pytest.fixture
def admin_api_key(rbac):
    """Get the auto-generated admin API key."""
    admin = rbac.get_user("admin")
    assert admin is not None
    return admin.api_key


@pytest.fixture
def viewer_user(rbac):
    """Create a viewer user."""
    from hiveos.rbac.models import User
    viewer = User(username="viewer1", role="viewer", api_key=secrets.token_urlsafe(32))
    rbac.add_user(viewer)
    return viewer


@pytest.fixture
def operator_user(rbac):
    """Create an operator user."""
    from hiveos.rbac.models import User
    op = User(username="operator1", role="operator", api_key=secrets.token_urlsafe(32))
    rbac.add_user(op)
    return op


# ── AuthChecker unit tests ──────────────────────────────────────────


class TestAuthChecker:
    """Unit tests for the AuthChecker class."""

    def test_missing_header_returns_401(self, auth_checker, admin_api_key):
        """No Authorization header → 401."""
        app = FastAPI()

        @app.get("/protected")
        async def protected(_: None = Depends(auth_checker())):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/protected")
        assert resp.status_code == 401
        assert "Missing" in resp.json()["detail"]

    def test_invalid_key_returns_401(self, auth_checker):
        """Invalid Bearer token → 401."""
        app = FastAPI()

        @app.get("/protected")
        async def protected(_: None = Depends(auth_checker())):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/protected", headers={"Authorization": "Bearer totally-fake-key"})
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    def test_valid_key_passes(self, auth_checker, admin_api_key):
        """Valid Bearer token → 200."""
        app = FastAPI()

        @app.get("/protected")
        async def protected(_: None = Depends(auth_checker())):
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/protected", headers={"Authorization": f"Bearer {admin_api_key}"})
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_require_permission_admin_passes(self, auth_checker, admin_api_key):
        """Admin has all permissions → 200 on any resource:action."""
        app = FastAPI()

        @app.get("/admin-only")
        async def admin_only(_: None = Depends(auth_checker.require(Resource.RBAC, Action.DELETE))):
            return {"admin": True}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/admin-only", headers={"Authorization": f"Bearer {admin_api_key}"})
        assert resp.status_code == 200

    def test_require_permission_viewer_denied(self, auth_checker, viewer_user):
        """Viewer lacks domain:create → 403."""
        app = FastAPI()

        @app.post("/install-domain")
        async def install(_: None = Depends(auth_checker.require(Resource.DOMAIN, Action.CREATE))):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/install-domain",
            headers={"Authorization": f"Bearer {viewer_user.api_key}"},
        )
        assert resp.status_code == 403
        assert "Insufficient" in resp.json()["detail"]

    def test_require_permission_operator_passes_flow_read(self, auth_checker, operator_user):
        """Operator can read flows → 200."""
        app = FastAPI()

        @app.get("/flows")
        async def list_flows(_: None = Depends(auth_checker.require(Resource.FLOW, Action.READ))):
            return {"domains": []}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(
            "/flows",
            headers={"Authorization": f"Bearer {operator_user.api_key}"},
        )
        assert resp.status_code == 200

    def test_require_permission_operator_denied_domain_create(self, auth_checker, operator_user):
        """Operator lacks domain:create → 403."""
        app = FastAPI()

        @app.post("/install-domain")
        async def install(_: None = Depends(auth_checker.require(Resource.DOMAIN, Action.CREATE))):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/install-domain",
            headers={"Authorization": f"Bearer {operator_user.api_key}"},
        )
        assert resp.status_code == 403

    def test_disabled_user_returns_401(self, rbac, auth_checker):
        """Disabled user's API key → 401."""
        from hiveos.rbac.models import User
        disabled = User(username="disabled1", role="viewer", api_key=secrets.token_urlsafe(32), enabled=False)
        rbac.add_user(disabled)

        app = FastAPI()

        @app.get("/protected")
        async def protected(_: None = Depends(auth_checker())):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/protected", headers={"Authorization": f"Bearer {disabled.api_key}"})
        assert resp.status_code == 401

    def test_wrong_header_format_returns_401(self, auth_checker, admin_api_key):
        """Header not starting with 'Bearer ' → 401."""
        app = FastAPI()

        @app.get("/protected")
        async def protected(_: None = Depends(auth_checker())):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/protected", headers={"Authorization": f"Basic {admin_api_key}"})
        assert resp.status_code == 401


# ── Audit logging of denied requests ────────────────────────────────


class TestAuditLogging:
    """Verify denied requests produce audit trail entries."""

    def test_401_missing_key_logged(self, auth_checker, audit):
        """Missing Bearer token → audit entry with DENIED result."""
        app = FastAPI()

        @app.get("/protected")
        async def protected(_: None = Depends(auth_checker())):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        client.get("/protected")

        entries = audit.read_today()
        denied = [e for e in entries if e.result == AuditResult.DENIED]
        assert len(denied) >= 1
        assert denied[-1].status_code == 401

    def test_403_permission_denied_logged(self, auth_checker, audit, viewer_user):
        """Insufficient permissions → audit entry with DENIED + 403."""
        app = FastAPI()

        @app.post("/install")
        async def install(_: None = Depends(auth_checker.require(Resource.DOMAIN, Action.CREATE))):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        client.post(
            "/install",
            headers={"Authorization": f"Bearer {viewer_user.api_key}"},
        )

        entries = audit.read_today()
        denied = [e for e in entries if e.result == AuditResult.DENIED and e.status_code == 403]
        assert len(denied) >= 1

    def test_401_invalid_key_logged(self, auth_checker, audit):
        """Invalid API key → audit entry with DENIED result."""
        app = FastAPI()

        @app.get("/protected")
        async def protected(_: None = Depends(auth_checker())):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        client.get("/protected", headers={"Authorization": "Bearer fake-key"})

        entries = audit.read_today()
        denied = [e for e in entries if e.result == AuditResult.DENIED and e.status_code == 401]
        assert len(denied) >= 1


# ── CORS middleware tests ───────────────────────────────────────────


class TestCORSMiddleware:
    """Verify CORS headers on V2 app responses."""

    def test_cors_preflight(self):
        """OPTIONS preflight returns CORS headers."""
        from hiveos.dashboard.app import HiveOSApp
        with tempfile.TemporaryDirectory() as d:
            cp = Path(d) / "cfg.yaml"
            cp.write_text(yaml.dump({
                "server": {"host": "127.0.0.1", "port": 19999},
                "storage": {"data_dir": d, "db_path": str(Path(d) / "test.db")},
            }))
            app = HiveOSApp(cp)
            client = TestClient(app.api)
            resp = client.options(
                "/api/health",
                headers={
                    "Origin": "http://127.0.0.1:8080",
                    "Access-Control-Request-Method": "GET",
                },
            )
            # FastAPI's CORS middleware should reflect the origin
            assert resp.headers.get("access-control-allow-origin") == "http://127.0.0.1:8080"
            app.shutdown()

    def test_cors_rejected_origin(self):
        """Non-localhost origin not reflected."""
        from hiveos.dashboard.app import HiveOSApp
        with tempfile.TemporaryDirectory() as d:
            cp = Path(d) / "cfg.yaml"
            cp.write_text(yaml.dump({
                "server": {"host": "127.0.0.1", "port": 19998},
                "storage": {"data_dir": d, "db_path": str(Path(d) / "test.db")},
            }))
            app = HiveOSApp(cp)
            client = TestClient(app.api)
            resp = client.options(
                "/api/health",
                headers={
                    "Origin": "https://evil.example.com",
                    "Access-Control-Request-Method": "GET",
                },
            )
            # Origin should NOT be reflected for unknown origins
            assert resp.headers.get("access-control-allow-origin") != "https://evil.example.com"
            app.shutdown()


# ── V2 app auth integration ─────────────────────────────────────────


class TestV2AppAuth:
    """Integration tests: V2 HiveOSApp endpoints require auth."""

    @pytest.fixture
    def v2_client(self):
        """Create V2 app with RBAC (admin key auto-generated)."""
        from hiveos.dashboard.app import HiveOSApp
        with tempfile.TemporaryDirectory() as d:
            cp = Path(d) / "cfg.yaml"
            cp.write_text(yaml.dump({
                "server": {"host": "127.0.0.1", "port": 19997},
                "storage": {"data_dir": d, "db_path": str(Path(d) / "test.db")},
            }))
            app_inst = HiveOSApp(cp)
            admin = app_inst.rbac.get_user("admin")
            yield TestClient(app_inst.api), app_inst.rbac, admin.api_key
            app_inst.shutdown()

    def test_health_no_auth_needed(self, v2_client):
        """/api/health is public → 200 without header."""
        client, _, _ = v2_client
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_knowledge_search_requires_auth(self, v2_client):
        """/api/knowledge/search without header → 401."""
        client, _, _ = v2_client
        resp = client.get("/api/knowledge/search?q=test")
        assert resp.status_code == 401

    def test_knowledge_search_with_valid_key(self, v2_client):
        """/api/knowledge/search with valid key → 200."""
        client, _, key = v2_client
        resp = client.get(
            "/api/knowledge/search?q=test",
            headers={"Authorization": f"Bearer {key}"},
        )
        assert resp.status_code == 200

    def test_domains_list_requires_auth(self, v2_client):
        """/api/domains without header → 401."""
        client, _, _ = v2_client
        resp = client.get("/api/domains")
        assert resp.status_code == 401

    def test_domains_list_with_valid_key(self, v2_client):
        """/api/domains with valid key → 200."""
        client, _, key = v2_client
        resp = client.get(
            "/api/domains",
            headers={"Authorization": f"Bearer {key}"},
        )
        assert resp.status_code == 200

    def test_config_requires_auth(self, v2_client):
        """/api/config without header → 401."""
        client, _, _ = v2_client
        resp = client.get("/api/config")
        assert resp.status_code == 401

    def test_config_put_requires_admin_permission(self, v2_client):
        """/api/config PUT needs RBAC:UPDATE → 403 for viewer."""
        from hiveos.rbac.models import User
        client, rbac, _ = v2_client
        viewer = User(username="viewer2", role="viewer", api_key=secrets.token_urlsafe(32))
        rbac.add_user(viewer)
        resp = client.put(
            "/api/config",
            json={"key": "server.port", "value": 9999},
            headers={"Authorization": f"Bearer {viewer.api_key}"},
        )
        assert resp.status_code == 403

    def test_skills_list_requires_auth(self, v2_client):
        """/api/skills without header → 401."""
        client, _, _ = v2_client
        resp = client.get("/api/skills")
        assert resp.status_code == 401

    def test_workflows_list_requires_auth(self, v2_client):
        """/api/workflows without header → 401."""
        client, _, _ = v2_client
        resp = client.get("/api/workflows")
        assert resp.status_code == 401

    def test_history_requires_auth(self, v2_client):
        """/api/history without header → 401."""
        client, _, _ = v2_client
        resp = client.get("/api/history")
        assert resp.status_code == 401

    def test_index_page_no_auth(self, v2_client):
        """/ returns HTML (no auth for dashboard page)."""
        client, _, _ = v2_client
        resp = client.get("/")
        assert resp.status_code == 200


# ── Permission mapping tests ────────────────────────────────────────


class TestPermissionMapping:
    """Verify correct Resource:Action mapping per endpoint category."""

    def test_admin_only_endpoints(self, auth_checker, admin_api_key):
        """Admin-only endpoints succeed with admin key."""
        app = FastAPI()
        # Simulate domain install endpoint
        @app.post("/api/domains/install")
        async def install(_: None = Depends(auth_checker.require(Resource.DOMAIN, Action.CREATE))):
            return {"ok": True}
        # Simulate RBAC user management
        @app.post("/api/rbac/users")
        async def create_user(_: None = Depends(auth_checker.require(Resource.RBAC, Action.CREATE))):
            return {"ok": True}
        # Simulate license actions
        @app.post("/api/license/activate")
        async def activate(_: None = Depends(auth_checker.require(Resource.LICENSE, Action.CREATE))):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        headers = {"Authorization": f"Bearer {admin_api_key}"}

        assert client.post("/api/domains/install", headers=headers).status_code == 200
        assert client.post("/api/rbac/users", headers=headers).status_code == 200
        assert client.post("/api/license/activate", headers=headers).status_code == 200

    def test_viewer_read_access(self, auth_checker, viewer_user):
        """Viewer can read (list) domains, skills, history."""
        app = FastAPI()

        @app.get("/api/domains")
        async def list_domains(_: None = Depends(auth_checker.require(Resource.DOMAIN, Action.READ))):
            return {"domains": []}

        @app.get("/api/skills")
        async def list_skills(_: None = Depends(auth_checker.require(Resource.FLOW, Action.READ))):
            return {"skills": []}

        client = TestClient(app, raise_server_exceptions=False)
        headers = {"Authorization": f"Bearer {viewer_user.api_key}"}

        assert client.get("/api/domains", headers=headers).status_code == 200
        assert client.get("/api/skills", headers=headers).status_code == 200

    def test_viewer_cannot_install(self, auth_checker, viewer_user):
        """Viewer cannot install domains (domain:create)."""
        app = FastAPI()

        @app.post("/api/domains/install")
        async def install(_: None = Depends(auth_checker.require(Resource.DOMAIN, Action.CREATE))):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        headers = {"Authorization": f"Bearer {viewer_user.api_key}"}
        assert client.post("/api/domains/install", headers=headers).status_code == 403

    def test_viewer_cannot_run_flows(self, auth_checker, viewer_user):
        """Viewer cannot execute flows (flow:execute)."""
        app = FastAPI()

        @app.post("/api/playground/run")
        async def run_flow(_: None = Depends(auth_checker.require(Resource.FLOW, Action.EXECUTE))):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        headers = {"Authorization": f"Bearer {viewer_user.api_key}"}
        assert client.post("/api/playground/run", headers=headers).status_code == 403

    def test_operator_can_run_flows(self, auth_checker, operator_user):
        """Operator can execute flows."""
        app = FastAPI()

        @app.post("/api/playground/run")
        async def run_flow(_: None = Depends(auth_checker.require(Resource.FLOW, Action.EXECUTE))):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        headers = {"Authorization": f"Bearer {operator_user.api_key}"}
        assert client.post("/api/playground/run", headers=headers).status_code == 200
