"""Workflow listing and execution endpoints."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Set by app.py
_domain_registry = None
_execution_logger = None


def set_services(registry, execution_logger=None):
    global _domain_registry, _execution_logger
    _domain_registry = registry
    _execution_logger = execution_logger


def _scan_workflows() -> List[Dict[str, Any]]:
    """Aggregate workflows from all installed domain packs."""
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


class RunWorkflowRequest(BaseModel):
    input: Dict[str, Any] = {}


@router.get("")
async def list_workflows():
    wfs = _scan_workflows()
    return {"workflows": wfs, "count": len(wfs)}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    wfs = _scan_workflows()
    for wf in wfs:
        if wf["id"] == workflow_id:
            return {"workflow": wf}
    raise HTTPException(404, f"Workflow '{workflow_id}' not found")


@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str, body: RunWorkflowRequest):
    wfs = _scan_workflows()
    target = None
    for wf in wfs:
        if wf["id"] == workflow_id:
            target = wf
            break
    if not target:
        raise HTTPException(404, f"Workflow '{workflow_id}' not found")

    # V1: record workflow execution stub
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
