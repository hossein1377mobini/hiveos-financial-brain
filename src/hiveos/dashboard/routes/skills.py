"""Skill listing and execution endpoints."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .deps import get_current_user, require_permission
from ...rbac import Resource, Action

router = APIRouter(prefix="/api/skills", tags=["skills"])

# Set by app.py
_domain_registry = None
_execution_logger = None


def set_services(registry, execution_logger=None):
    global _domain_registry, _execution_logger
    _domain_registry = registry
    _execution_logger = execution_logger


def set_auth_deps(checker):
    """Stub: auth deps are resolved from .deps module."""
    pass


def _scan_skills() -> List[Dict[str, Any]]:
    """Aggregate skills from all installed domain packs."""
    from hiveos.domain_pack.loader import load_pack
    from pathlib import Path

    skills: List[Dict[str, Any]] = []
    if _domain_registry is None:
        return skills

    installed = _domain_registry._get_installed()
    for name, meta in installed.items():
        pack_path = Path(meta.get("path", ""))
        if not pack_path.exists():
            continue
        try:
            pack = load_pack(pack_path)
            for sk in pack.skills:
                skills.append({
                    "id": sk.id,
                    "name": sk.name,
                    "version": sk.version,
                    "description": sk.description,
                    "input_schema": sk.input_schema,
                    "output_schema": sk.output_schema,
                    "pack_id": sk.pack_id,
                    "pack_name": pack.name,
                })
        except Exception:
            continue
    return skills

class RunSkillRequest(BaseModel):
    input: Dict[str, Any] = {}


@router.get("")
async def list_skills(_: None = Depends(get_current_user)):
    skills = _scan_skills()
    return {"skills": skills, "count": len(skills)}


@router.get("/{skill_id}")
async def get_skill(skill_id: str, _: None = Depends(get_current_user)):
    skills = _scan_skills()
    for sk in skills:
        if sk["id"] == skill_id:
            return {"skill": sk}
    raise HTTPException(404, f"Skill '{skill_id}' not found")


@router.post("/{skill_id}/run")
async def run_skill(
    skill_id: str,
    body: RunSkillRequest,
    _: None = Depends(require_permission(Resource.FLOW, Action.EXECUTE)),
):
    skills = _scan_skills()
    target = None
    for sk in skills:
        if sk["id"] == skill_id:
            target = sk
            break
    if not target:
        raise HTTPException(404, f"Skill '{skill_id}' not found")

    # V1: record execution stub (no real AI execution yet)
    exec_id = str(uuid.uuid4())
    entry = {
        "execution_id": exec_id,
        "type": "skill",
        "skill_id": skill_id,
        "input": body.input,
        "status": "completed",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "duration_ms": 0,
    }
    if _execution_logger:
        _execution_logger.log_execution(
            flow_name=skill_id,
            execution_id=exec_id,
            agent_id="dashboard",
            status="completed",
            duration_ms=0,
            input_summary=str(body.input)[:500],
            output_summary="Skill execution stub (V1)",
        )
    return {"status": "ok", "execution_id": exec_id, "skill": target}
