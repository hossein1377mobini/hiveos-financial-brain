"""Tests for WorkflowService and workflow editing API endpoints.

V1.5: Workflow Customization (Edit)
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
import yaml


# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def tmp_pack(tmp_path):
    """Create a temporary domain pack with one workflow."""
    pack_dir = tmp_path / "test-pack"
    pack_dir.mkdir()
    wf_dir = pack_dir / "workflows"
    wf_dir.mkdir()

    # Manifest
    manifest = {
        "id": "test-pack",
        "version": "1.0.0",
        "name": "Test Pack",
        "description": "A test pack",
        "workflows": [{"id": "my-workflow"}],
    }
    (pack_dir / "domain.yaml").write_text(
        yaml.dump(manifest, default_flow_style=False), encoding="utf-8"
    )

    # Workflow YAML
    wf_data = {
        "id": "my-workflow",
        "name": "My Workflow",
        "description": "A test workflow",
        "version": "1.0.0",
        "steps": [
            {"id": "step-1", "skill_id": "skill-a", "input_mapping": {"file": "input"}},
            {"id": "step-2", "skill_id": "skill-b", "input_mapping": {}},
        ],
    }
    (wf_dir / "my-workflow.yaml").write_text(
        yaml.dump(wf_data, default_flow_style=False), encoding="utf-8"
    )

    return pack_dir, wf_data


@pytest.fixture
def mock_registry(tmp_pack):
    """Mock DomainRegistry pointing to our test pack."""
    pack_dir, _ = tmp_pack
    registry = MagicMock()
    registry._get_installed.return_value = {
        "test-pack": {"path": str(pack_dir)},
    }
    return registry


@pytest.fixture
def workflow_service(mock_registry):
    """WorkflowService backed by mock registry."""
    from hiveos.dashboard.workflow_service import WorkflowService
    return WorkflowService(mock_registry)


# ── WorkflowService tests ──────────────────────────────────────────


class TestWorkflowServiceFind:
    def test_find_existing_workflow(self, workflow_service, tmp_pack):
        fpath, pack_id = workflow_service.find_workflow_file("my-workflow")
        assert fpath is not None
        assert fpath.name == "my-workflow.yaml"
        assert pack_id == "test-pack"

    def test_find_nonexistent_workflow(self, workflow_service):
        fpath, pack_id = workflow_service.find_workflow_file("does-not-exist")
        assert fpath is None
        assert pack_id is None

    def test_load_workflow_yaml(self, workflow_service):
        data = workflow_service.load_workflow_yaml("my-workflow")
        assert data is not None
        assert data["name"] == "My Workflow"
        assert len(data["steps"]) == 2
        assert data["_pack_id"] == "test-pack"

    def test_load_nonexistent(self, workflow_service):
        data = workflow_service.load_workflow_yaml("nope")
        assert data is None


class TestWorkflowServiceValidate:
    def test_valid_workflow(self, workflow_service):
        errors = workflow_service.validate_workflow({
            "name": "Test",
            "steps": [{"id": "s1", "skill_id": "sk1"}],
        })
        assert errors == []

    def test_missing_name(self, workflow_service):
        errors = workflow_service.validate_workflow({"steps": []})
        assert any("name" in e for e in errors)

    def test_step_missing_skill(self, workflow_service):
        errors = workflow_service.validate_workflow({
            "name": "Test",
            "steps": [{"id": "s1"}],
        })
        assert any("skill_id" in e for e in errors)

    def test_duplicate_step_ids(self, workflow_service):
        errors = workflow_service.validate_workflow({
            "name": "Test",
            "steps": [
                {"id": "s1", "skill_id": "sk1"},
                {"id": "s1", "skill_id": "sk2"},
            ],
        })
        assert any("Duplicate" in e for e in errors)

    def test_invalid_trigger_type(self, workflow_service):
        errors = workflow_service.validate_workflow({
            "name": "Test",
            "trigger": {"type": "invalid_type"},
        })
        assert any("trigger" in e for e in errors)


class TestWorkflowServiceSave:
    def test_patch_workflow(self, workflow_service):
        success, msg = workflow_service.patch_workflow(
            "my-workflow", {"description": "Updated description"}
        )
        assert success
        data = workflow_service.load_workflow_yaml("my-workflow")
        assert data["description"] == "Updated description"
        # Original fields preserved
        assert data["name"] == "My Workflow"
        assert len(data["steps"]) == 2

    def test_patch_steps(self, workflow_service):
        new_steps = [
            {"id": "new-step-1", "skill_id": "new-skill", "input_mapping": {}},
        ]
        success, msg = workflow_service.patch_workflow(
            "my-workflow", {"steps": new_steps}
        )
        assert success
        data = workflow_service.load_workflow_yaml("my-workflow")
        assert len(data["steps"]) == 1
        assert data["steps"][0]["id"] == "new-step-1"

    def test_patch_nonexistent(self, workflow_service):
        success, msg = workflow_service.patch_workflow(
            "nope", {"name": "Fail"}
        )
        assert not success
        assert "not found" in msg

    def test_patch_validates_before_save(self, workflow_service):
        success, msg = workflow_service.patch_workflow(
            "my-workflow",
            {"steps": [{"id": "s1"}]}  # missing skill_id
        )
        assert not success
        assert "Validation" in msg

    def test_put_full_workflow(self, workflow_service):
        new_data = {
            "name": "Replaced Workflow",
            "description": "Fully replaced",
            "version": "2.0.0",
            "steps": [{"id": "replaced-step", "skill_id": "new-skill"}],
        }
        success, msg = workflow_service.save_workflow("my-workflow", new_data)
        assert success
        data = workflow_service.load_workflow_yaml("my-workflow")
        assert data["name"] == "Replaced Workflow"
        assert data["version"] == "2.0.0"
        assert len(data["steps"]) == 1

    def test_delete_workflow(self, workflow_service, tmp_pack):
        pack_dir, _ = tmp_pack
        wf_path = pack_dir / "workflows" / "my-workflow.yaml"
        assert wf_path.exists()

        success, msg = workflow_service.delete_workflow("my-workflow")
        assert success
        assert not wf_path.exists()
        # Backup exists
        assert (pack_dir / "workflows" / "my-workflow.yaml.bak").exists()


class TestWorkflowServiceHelpers:
    def test_component_types(self, workflow_service):
        types = workflow_service.get_component_types()
        assert isinstance(types, list)
        assert len(types) > 0
        assert any(t["type"] == "agent" for t in types)

    def test_editable_fields(self, workflow_service):
        schema = workflow_service.get_editable_fields()
        assert "top_level" in schema
        assert "name" in schema["top_level"]
        assert "trigger" in schema


# ── API endpoint tests (integration) ──────────────────────────────


@pytest.fixture
def api_client(mock_registry, workflow_service):
    """FastAPI TestClient with mocked auth."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from hiveos.dashboard.routes import workflows
    from hiveos.dashboard.routes import deps

    app = FastAPI()

    # Mock auth — bypass token check
    deps.set_auth_deps(MagicMock(
        verify_token=MagicMock(return_value={"username": "test", "role": "admin"}),
    ))

    workflows.set_services(mock_registry)
    workflows.set_workflow_service(workflow_service)
    app.include_router(workflows.router)

    # Dependency overrides for auth
    def _mock_user():
        return "test"

    app.dependency_overrides[deps.get_current_user] = _mock_user

    # Set _auth_checker to None so require_permission returns None (no auth check)
    deps._auth_checker = None

    return TestClient(app)


class TestWorkflowAPI:
    def test_list_workflows(self, api_client):
        resp = api_client.get("/api/workflows")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        ids = [w["id"] for w in data["workflows"]]
        assert "my-workflow" in ids

    def test_get_workflow(self, api_client):
        resp = api_client.get("/api/workflows/my-workflow")
        assert resp.status_code == 200
        wf = resp.json()["workflow"]
        assert wf["name"] == "My Workflow"
        assert "steps" in wf

    def test_get_workflow_not_found(self, api_client):
        resp = api_client.get("/api/workflows/nonexistent")
        assert resp.status_code == 404

    def test_patch_workflow(self, api_client):
        resp = api_client.patch(
            "/api/workflows/my-workflow",
            json={"description": "Patched via API"},
        )
        assert resp.status_code == 200
        assert resp.json()["workflow"]["description"] == "Patched via API"

    def test_put_workflow(self, api_client):
        resp = api_client.put(
            "/api/workflows/my-workflow",
            json={
                "name": "API Replaced",
                "steps": [{"id": "api-step", "skill_id": "api-skill"}],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["workflow"]["name"] == "API Replaced"

    def test_delete_workflow(self, api_client):
        resp = api_client.delete("/api/workflows/my-workflow")
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

    def test_validate_workflow(self, api_client):
        resp = api_client.post(
            "/api/workflows/my-workflow/validate",
            json={"name": "Valid", "steps": [{"id": "s1", "skill_id": "k1"}]},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_validate_invalid(self, api_client):
        resp = api_client.post(
            "/api/workflows/my-workflow/validate",
            json={"steps": []},  # missing name
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is False
        assert len(resp.json()["errors"]) > 0

    def test_component_types_endpoint(self, api_client):
        resp = api_client.get("/api/workflows/component-types")
        assert resp.status_code == 200
        types = resp.json()["component_types"]
        assert isinstance(types, list)

    def test_edit_schema_endpoint(self, api_client):
        resp = api_client.get("/api/workflows/edit-schema")
        assert resp.status_code == 200
        schema = resp.json()["schema"]
        assert "top_level" in schema
