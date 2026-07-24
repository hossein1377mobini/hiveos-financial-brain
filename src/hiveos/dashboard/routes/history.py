"""Execution history endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/history", tags=["history"])

# Set by app.py
_execution_logger = None


def set_execution_logger(logger):
    global _execution_logger
    _execution_logger = logger


def _logger():
    return _execution_logger


@router.get("")
async def list_history(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="completed|failed"),
    skill_id: Optional[str] = Query(None),
):
    log = _logger()
    if not log:
        return {"executions": [], "count": 0}

    flow_name = skill_id
    entries = log.get_executions(limit=limit, flow_name=flow_name, status=status)

    return {
        "executions": entries,
        "count": len(entries),
    }


@router.get("/{execution_id}")
async def get_execution(execution_id: str):
    log = _logger()
    if not log:
        return {"execution": None}

    # Search by execution_id
    entries = log.get_executions(limit=200)
    for e in entries:
        if e.get("execution_id") == execution_id:
            return {"execution": e}

    return {"execution": None, "error": "Not found"}
