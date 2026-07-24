"""Knowledge search and ingestion endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

# Set by app.py during startup
_knowledge_service = None


def set_knowledge_service(svc):
    global _knowledge_service
    _knowledge_service = svc


def _svc():
    if _knowledge_service is None:
        raise HTTPException(503, "Knowledge service not initialized")
    return _knowledge_service


# ── Pydantic request models ─────────────────────────────────────────


class IngestRequest(BaseModel):
    path: str
    source_type: str = "org"


# ── Endpoints ───────────────────────────────────────────────────────


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    source: Optional[str] = Query(None, description="Filter: domain:<pack_id> or org"),
    tags: Optional[str] = Query(None, description="Comma-separated tag filter"),
    limit: int = Query(10, ge=1, le=100),
):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    results = await _svc().search(q, source_filter=source, tags=tag_list, limit=limit)
    return {
        "results": [
            {
                "id": r.doc_id,
                "source_type": r.source_type,
                "source_path": r.source_path,
                "title": r.title,
                "snippet": r.snippet,
                "score": r.score,
                "chunk_id": r.chunk_id,
                "tags": r.tags,
            }
            for r in results
        ],
        "count": len(results),
    }


@router.post("/ingest")
async def ingest(body: IngestRequest):
    try:
        count = await _svc().ingest_directory(body.path, body.source_type)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    return {"status": "ok", "chunks_ingested": count}


@router.get("/stats")
async def stats():
    s = await _svc().stats()
    return {
        "total_documents": s.total_documents,
        "total_chunks": s.total_chunks,
        "total_sources": s.total_sources,
        "source_breakdown": [
            {"source_type": b.source_type, "document_count": b.document_count}
            for b in s.source_breakdown
        ],
    }


@router.get("/sources")
async def sources():
    srcs = await _svc().list_sources()
    return {
        "sources": [
            {
                "source_type": s.source_type,
                "document_count": s.document_count,
                "paths": s.paths,
            }
            for s in srcs
        ]
    }
