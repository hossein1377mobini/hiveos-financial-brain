"""Domain pack management endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .deps import get_current_user, require_permission
from ...rbac import Resource, Action

router = APIRouter(prefix="/api/domains", tags=["domains"])

# Set by app.py
_domain_registry = None


def set_domain_registry(reg):
    global _domain_registry
    _domain_registry = reg


def set_auth_deps(checker):
    """Stub: auth deps are resolved from .deps module."""
    pass


def _reg():
    if _domain_registry is None:
        raise HTTPException(503, "Domain registry not initialized")
    return _domain_registry


class InstallRequest(BaseModel):
    path: str


# ── Endpoints ───────────────────────────────────────────────────────


@router.get("")
async def list_domains(_: None = Depends(get_current_user)):
    """List all known domains (scans on call)."""
    _reg().scan()
    domains = _reg().list_domains()
    return {"domains": domains}


@router.get("/{pack_id}")
async def get_domain(pack_id: str, _: None = Depends(get_current_user)):
    meta = _reg().get_domain(pack_id)
    if not meta:
        raise HTTPException(404, f"Domain '{pack_id}' not found")
    meta["installed"] = _reg().is_installed(pack_id)
    return {"domain": meta}


@router.post("/install")
async def install_domain(
    body: InstallRequest,
    _: None = Depends(require_permission(Resource.DOMAIN, Action.CREATE)),
):
    source = Path(body.path)
    if not source.exists():
        raise HTTPException(400, f"Path does not exist: {body.path}")
    # Use domain manager for copy-based install
    from hiveos.domain.manager import DomainManager
    mgr = DomainManager(_reg().domains_root)
    try:
        info = mgr.install(source)
    except (ValueError, FileExistsError) as exc:
        raise HTTPException(400, str(exc))
    return {"status": "ok", "domain": info.to_dict()}


@router.delete("/{pack_id}")
async def remove_domain(
    pack_id: str,
    _: None = Depends(require_permission(Resource.DOMAIN, Action.DELETE)),
):
    if not _reg().get_domain(pack_id):
        raise HTTPException(404, f"Domain '{pack_id}' not found")
    _reg().remove(pack_id)
    return {"status": "removed", "domain": pack_id}


@router.post("/{pack_id}/enable")
async def enable_domain(
    pack_id: str,
    _: None = Depends(require_permission(Resource.DOMAIN, Action.UPDATE)),
):
    meta = _reg().get_domain(pack_id)
    if not meta:
        raise HTTPException(404, f"Domain '{pack_id}' not found")
    installed = _reg()._get_installed()
    if pack_id in installed:
        installed[pack_id]["enabled"] = True
        _reg()._save_installed(installed)
    return {"status": "enabled", "domain": pack_id}


@router.post("/{pack_id}/disable")
async def disable_domain(
    pack_id: str,
    _: None = Depends(require_permission(Resource.DOMAIN, Action.UPDATE)),
):
    meta = _reg().get_domain(pack_id)
    if not meta:
        raise HTTPException(404, f"Domain '{pack_id}' not found")
    installed = _reg()._get_installed()
    if pack_id in installed:
        installed[pack_id]["enabled"] = False
        _reg()._save_installed(installed)
    return {"status": "disabled", "domain": pack_id}
