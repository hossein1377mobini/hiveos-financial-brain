"""Configuration endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .deps import get_current_user, require_permission
from ...rbac import Resource, Action

router = APIRouter(prefix="/api/config", tags=["config"])

# Set by app.py
_config_service = None


def set_config_service(svc):
    global _config_service
    _config_service = svc


def set_auth_deps(checker):
    """Stub: auth deps are resolved from .deps module."""
    pass


def _svc():
    if _config_service is None:
        raise HTTPException(503, "Config service not initialized")
    return _config_service


class ConfigUpdate(BaseModel):
    key: str
    value: Any


@router.get("")
async def get_config(_: None = Depends(get_current_user)):
    return _svc().to_dict()


@router.put("")
async def update_config(
    body: ConfigUpdate,
    _: None = Depends(require_permission(Resource.RBAC, Action.UPDATE)),
):
    try:
        _svc().set(body.key, body.value)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"status": "ok", "key": body.key, "value": _svc().get(body.key)}
