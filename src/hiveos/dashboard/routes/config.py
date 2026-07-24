"""Configuration endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/config", tags=["config"])

# Set by app.py
_config_service = None


def set_config_service(svc):
    global _config_service
    _config_service = svc


def _svc():
    if _config_service is None:
        raise HTTPException(503, "Config service not initialized")
    return _config_service


class ConfigUpdate(BaseModel):
    key: str
    value: Any


@router.get("")
async def get_config():
    return _svc().to_dict()


@router.put("")
async def update_config(body: ConfigUpdate):
    try:
        _svc().set(body.key, body.value)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"status": "ok", "key": body.key, "value": _svc().get(body.key)}
