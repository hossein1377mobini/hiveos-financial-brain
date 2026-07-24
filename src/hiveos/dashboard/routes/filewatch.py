"""File Watch Folder API — manage customer drop folders."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .deps import get_current_user, require_permission
from ...rbac import Resource, Action

router = APIRouter(prefix="/api/filewatch", tags=["filewatch"])

# Set by app.py during startup
_filewatch_service = None


def set_filewatch_service(svc):
    global _filewatch_service
    _filewatch_service = svc


def _svc():
    if _filewatch_service is None:
        raise HTTPException(503, "FileWatch service not initialized")
    return _filewatch_service


# ── Pydantic models ────────────────────────────────────────────────────


class AddFolderRequest(BaseModel):
    name: str
    path: str
    source_type: str = "customer"
    customer_id: str = ""
    tags: List[str] = []
    supported_extensions: Optional[List[str]] = None


class UpdateFolderRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None  # active | paused
    tags: Optional[List[str]] = None
    supported_extensions: Optional[List[str]] = None


# ── Endpoints ──────────────────────────────────────────────────────────


@router.get("/folders")
async def list_folders(
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    _: None = Depends(get_current_user),
):
    """List all watch folders."""
    folders = _svc().list_folders(customer_id=customer_id)
    return {
        "folders": [f.to_dict() for f in folders],
        "count": len(folders),
    }


@router.post("/folders")
async def add_folder(
    body: AddFolderRequest,
    _: None = Depends(require_permission(Resource.DOMAIN, Action.CREATE)),
):
    """Register a new customer watch folder."""
    folder = _svc().add_folder(
        name=body.name,
        path=body.path,
        source_type=body.source_type,
        customer_id=body.customer_id,
        tags=body.tags,
        supported_extensions=body.supported_extensions,
    )
    return {"status": "ok", "folder": folder.to_dict()}


@router.get("/folders/{folder_id}")
async def get_folder(
    folder_id: str,
    _: None = Depends(get_current_user),
):
    """Get a single watch folder by ID."""
    folder = _svc().get_folder(folder_id)
    if not folder:
        raise HTTPException(404, "Folder not found")
    return {"folder": folder.to_dict()}


@router.patch("/folders/{folder_id}")
async def update_folder(
    folder_id: str,
    body: UpdateFolderRequest,
    _: None = Depends(require_permission(Resource.DOMAIN, Action.UPDATE)),
):
    """Update a watch folder (name, status, tags, extensions)."""
    from ...filewatch.models import WatchFolderStatus

    status = None
    if body.status:
        try:
            status = WatchFolderStatus(body.status)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {body.status}")

    folder = _svc().update_folder(
        folder_id,
        name=body.name,
        status=status,
        tags=body.tags,
        supported_extensions=body.supported_extensions,
    )
    if not folder:
        raise HTTPException(404, "Folder not found")
    return {"status": "ok", "folder": folder.to_dict()}


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str,
    _: None = Depends(require_permission(Resource.DOMAIN, Action.DELETE)),
):
    """Remove a watch folder (stops watcher, deletes record, keeps files)."""
    deleted = _svc().remove_folder(folder_id)
    if not deleted:
        raise HTTPException(404, "Folder not found")
    return {"status": "ok", "deleted": folder_id}


@router.post("/folders/{folder_id}/scan")
async def scan_folder(
    folder_id: str,
    _: None = Depends(require_permission(Resource.DOMAIN, Action.CREATE)),
):
    """One-shot scan: ingest all files currently in the folder."""
    count = _svc().scan_folder(folder_id)
    return {"status": "ok", "chunks_ingested": count}


@router.get("/events")
async def list_events(
    folder_id: Optional[str] = Query(None, description="Filter by folder"),
    limit: int = Query(50, ge=1, le=500),
    _: None = Depends(get_current_user),
):
    """List recent file events (newest first)."""
    events = _svc().get_events(folder_id=folder_id, limit=limit)
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }
