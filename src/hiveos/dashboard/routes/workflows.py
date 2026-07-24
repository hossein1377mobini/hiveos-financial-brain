"""Workflow listing, execution, and editing endpoints.

V1: List, get, run.
V1.5: Edit (PUT/PATCH/DELETE), component-types schema.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .deps import get_current_user, require_permission
from ...rbac import Resource, Action

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Set by app.py
_domain_registry = None
_execution_logger = None
_workflow_service = None


def set_services(registry, execution_logger=None):
    global _domain_registry, _execution_logger
    _domain_registry = registry
    _execution_logger = execution_logger


def set_workflow_service(service):
    global _workflow_service
    _workflow_service = service


def set_auth_deps(checker):
    """Stub: auth deps are resolved from .deps module."""
    pass


# ── Request models ─────────────────────────────────────────────────


class RunWorkflowRequest(BaseModel):
    input: Dict[str, Any] = {}


class PatchWorkflowRequest(BaseModel):
    """Partial update — merge these fields into existing workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    trigger: Optional[Dict[str, Any]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    agents: Optional[List[Dict[str, Any]]] = None
    components: Optional[List[Dict[str, Any]]] = None
    deliver: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None


class PutWorkflowRequest(BaseModel):
    """Full replacement of a workflow definition."""
    name: str
    description: str = ""
    version: str = "0.0.0"
    tags: List[str] = []
    trigger: Optional[Dict[str, Any]] = None
    steps: List[Dict[str, Any]] = []
    agents: List[Dict[str, Any]] = []
    components: List[Dict[str, Any]] = []
    deliver: Dict[str, Any] = {}
    memory: Dict[str, Any] = {}


# ── Read-only endpoints ────────────────────────────────────────────


@router.get("")
async def list_workflows(_: None = Depends(get_current_user)):
    """List all workflows from installed domain packs."""
    if _workflow_service:
        wfs = _workflow_service.load_all_workflows()
        # Slim down for listing (remove _internal fields)
        slim = []
        for wf in wfs:
            slim.append({
                "id": wf.get("id"),
                "name": wf.get("name"),
                "description": wf.get("description"),
                "pack_id": wf.get("pack_id"),
                "pack_name": wf.get("pack_name"),
                "version": wf.get("version"),
                "tags": wf.get("tags", []),
                "step_count": len(wf.get("steps", [])),
                "agent_count": len(wf.get("agents", [])),
                "component_count": len(wf.get("components", [])),
            })
        return {"workflows": slim, "count": len(slim)}

    # Fallback: legacy scan
    wfs = _scan_workflows()
    return {"workflows": wfs, "count": len(wfs)}


@router.get("/component-types")
async def get_component_types(_: None = Depends(get_current_user)):
    """Return metadata about all supported component types (for UI editors)."""
    if _workflow_service:
        return {"component_types": _workflow_service.get_component_types()}
    from ...dsl import FlowDSL
    return {"component_types": FlowDSL.get_component_types()}


@router.get("/edit-schema")
async def get_edit_schema(_: None = Depends(get_current_user)):
    """Return schema describing editable fields (for dynamic UI forms)."""
    if _workflow_service:
        return {"schema": _workflow_service.get_editable_fields()}
    return {"schema": {}}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, _: None = Depends(get_current_user)):
    """Get full workflow detail including raw YAML fields."""
    if _workflow_service:
        data = _workflow_service.load_workflow_yaml(workflow_id)
        if data:
            # Strip internal fields
            clean = {k: v for k, v in data.items() if not k.startswith("_")}
            clean["pack_id"] = data.get("_pack_id")
            return {"workflow": clean}

    # Fallback: legacy scan
    wfs = _scan_workflows()
    for wf in wfs:
        if wf["id"] == workflow_id:
            return {"workflow": wf}
    raise HTTPException(404, f"Workflow '{workflow_id}' not found")


# ── Write endpoints (V1.5) ────────────────────────────────────────


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    body: PutWorkflowRequest,
    user=Depends(require_permission(Resource.FLOW, Action.UPDATE)),
):
    """Full replacement of a workflow definition (PUT semantics)."""
    if not _workflow_service:
        raise HTTPException(503, "Workflow service not available")

    data = body.model_dump()
    success, message = _workflow_service.save_workflow(workflow_id, data)
    if not success:
        raise HTTPException(400, message)

    # Return the saved state
    saved = _workflow_service.load_workflow_yaml(workflow_id)
    clean = {k: v for k, v in saved.items() if not k.startswith("_")} if saved else data
    clean["pack_id"] = saved.get("_pack_id") if saved else None

    return {"status": "ok", "message": message, "workflow": clean}


@router.patch("/{workflow_id}")
async def patch_workflow(
    workflow_id: str,
    body: PatchWorkflowRequest,
    user=Depends(require_permission(Resource.FLOW, Action.UPDATE)),
):
    """Partial update — merge fields into existing workflow (PATCH semantics)."""
    if not _workflow_service:
        raise HTTPException(503, "Workflow service not available")

    # Build updates dict from non-None fields
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")

    success, message = _workflow_service.patch_workflow(workflow_id, updates)
    if not success:
        raise HTTPException(400, message)

    # Return the updated state
    saved = _workflow_service.load_workflow_yaml(workflow_id)
    clean = {k: v for k, v in saved.items() if not k.startswith("_")} if saved else {}
    clean["pack_id"] = saved.get("_pack_id") if saved else None

    return {"status": "ok", "message": message, "workflow": clean}


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    user=Depends(require_permission(Resource.FLOW, Action.DELETE)),
):
    """Delete a workflow (creates .bak backup before removal)."""
    if not _workflow_service:
        raise HTTPException(503, "Workflow service not available")

    success, message = _workflow_service.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(400, message)

    return {"status": "ok", "message": message}


@router.post("/{workflow_id}/validate")
async def validate_workflow(
    workflow_id: str,
    body: Dict[str, Any],
    _: None = Depends(get_current_user),
):
    """Validate a proposed workflow update without saving.

    Send the full or partial workflow dict; returns validation errors.
    """
    if not _workflow_service:
        raise HTTPException(503, "Workflow service not available")

    errors = _workflow_service.validate_workflow(body)
    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


# ── Run endpoint (unchanged from V1) ──────────────────────────────


@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: str,
    body: RunWorkflowRequest,
    _: None = Depends(require_permission(Resource.FLOW, Action.EXECUTE)),
):
    """Execute a workflow."""
    wfs = _scan_workflows()
    target = None
    for wf in wfs:
        if wf["id"] == workflow_id:
            target = wf
            break
    if not target:
        raise HTTPException(404, f"Workflow '{workflow_id}' not found")

    exec_id = str(uuid.uuid4())
    step_count = len(target.get("steps", []))
    if _execution_logger:
        _execution_logger.log_execution(
            flow_name=workflow_id,
            execution_id=exec_id,
            agent_id="dashboard",
            status="completed",
            duration_ms=0,
            input_summary=f"Workflow with {step_count} steps",
            output_summary="Workflow execution stub (V1)",
        )
    return {
        "status": "ok",
        "execution_id": exec_id,
        "workflow": target,
    }


# ── Legacy helper (kept for fallback) ──────────────────────────────


def _scan_workflows() -> List[Dict[str, Any]]:
    """Aggregate workflows from all installed domain packs (legacy fallback)."""
    from hiveos.domain_pack.loader import load_pack
    from pathlib import Path
    workflows: List[Dict[str, Any]] = []
    if _domain_registry is None:
        return workflows
    installed = _domain_registry._get_installed()
    for name, meta in installed.items():
        pack_path = Path(meta.get("path", ""))
        if not pack_path.exists():
            continue
        try:
            pack = load_pack(pack_path)
            for wf in pack.workflows:
                workflows.append({
                    "id": wf.id,
                    "name": wf.name,
                    "description": wf.description,
                    "steps": [
                        {"id": s.id, "skill_id": s.skill_id, "input_mapping": s.input_mapping}
                        for s in wf.steps
                    ],
                    "pack_id": wf.pack_id,
                    "pack_name": pack.name,
                })
        except Exception:
            continue
    return workflows
