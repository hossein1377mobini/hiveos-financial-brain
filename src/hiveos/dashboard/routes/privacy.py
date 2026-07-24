"""
Privacy API Routes — Manage privacy settings and audit logs.

Endpoints for ADR-0017 Privacy-First Architecture.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ...privacy import (
    DataClassification,
    EgressPolicy,
    EndpointConfig,
    PrivacyConfig,
)
from ..routes.deps import get_privacy_config, get_privacy_audit, require_permission
from ...rbac import Resource, Action

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.get("/config")
async def get_config(
    _=require_permission(Resource.CONFIG, Action.READ),
):
    """Get current privacy configuration."""
    config = get_privacy_config()
    if not config:
        raise HTTPException(status_code=500, detail="Privacy config not initialized")
    return config.to_dict()


@router.put("/config/policy")
async def set_policy(
    policy: str,
    _=require_permission(Resource.CONFIG, Action.UPDATE),
):
    """Set global egress policy."""
    config = get_privacy_config()
    if not config:
        raise HTTPException(status_code=500, detail="Privacy config not initialized")
    
    try:
        new_policy = EgressPolicy(policy)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy. Must be one of: {[p.value for p in EgressPolicy]}",
        )
    
    config.set_policy(new_policy)
    return {"policy": config.egress_policy.value}


@router.get("/endpoints")
async def list_endpoints(
    _=require_permission(Resource.CONFIG, Action.READ),
):
    """List all configured external endpoints."""
    config = get_privacy_config()
    if not config:
        raise HTTPException(status_code=500, detail="Privacy config not initialized")
    
    return {
        endpoint_id: {
            "url": ep.url,
            "purpose": ep.purpose,
            "enabled": ep.enabled,
            "data_types": [dt.value for dt in ep.data_types],
        }
        for endpoint_id, ep in config.allowed_endpoints.items()
    }


@router.put("/endpoints/{endpoint_id}/enable")
async def enable_endpoint(
    endpoint_id: str,
    _=require_permission(Resource.CONFIG, Action.UPDATE),
):
    """Enable an external endpoint."""
    config = get_privacy_config()
    if not config:
        raise HTTPException(status_code=500, detail="Privacy config not initialized")
    
    if not config.enable_endpoint(endpoint_id):
        raise HTTPException(status_code=404, detail=f"Endpoint not found: {endpoint_id}")
    
    return {"endpoint_id": endpoint_id, "enabled": True}


@router.put("/endpoints/{endpoint_id}/disable")
async def disable_endpoint(
    endpoint_id: str,
    _=require_permission(Resource.CONFIG, Action.UPDATE),
):
    """Disable an external endpoint."""
    config = get_privacy_config()
    if not config:
        raise HTTPException(status_code=500, detail="Privacy config not initialized")
    
    if not config.disable_endpoint(endpoint_id):
        raise HTTPException(status_code=404, detail=f"Endpoint not found: {endpoint_id}")
    
    return {"endpoint_id": endpoint_id, "enabled": False}


@router.post("/endpoints")
async def add_endpoint(
    endpoint_id: str,
    url: str,
    purpose: str,
    data_types: list[str],
    _=require_permission(Resource.CONFIG, Action.CREATE),
):
    """Add a new external endpoint (disabled by default)."""
    config = get_privacy_config()
    if not config:
        raise HTTPException(status_code=500, detail="Privacy config not initialized")
    
    try:
        classified_types = [DataClassification(dt) for dt in data_types]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data type: {e}")
    
    endpoint = EndpointConfig(
        url=url,
        purpose=purpose,
        data_types=classified_types,
    )
    config.add_endpoint(endpoint_id, endpoint)
    
    return {"endpoint_id": endpoint_id, "enabled": False}


@router.get("/audit")
async def get_audit_log(
    limit: int = Query(100, ge=1, le=1000),
    allowed_only: Optional[bool] = None,
    _=require_permission(Resource.AUDIT, Action.READ),
):
    """Get privacy audit log."""
    audit = get_privacy_audit()
    if not audit:
        raise HTTPException(status_code=500, detail="Privacy audit not initialized")
    
    entries = audit.get_recent(limit=limit, allowed_only=allowed_only)
    return {
        "entries": [
            {
                "id": entry.id,
                "timestamp": entry.timestamp.isoformat(),
                "url": entry.url,
                "method": entry.method,
                "endpoint_id": entry.endpoint_id,
                "data_types": [dt.value for dt in entry.data_types],
                "allowed": entry.allowed,
                "reason": entry.reason,
                "user_id": entry.user_id,
                "response_code": entry.response_code,
            }
            for entry in entries
        ],
        "total": len(entries),
    }


@router.get("/audit/stats")
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365),
    _=require_permission(Resource.AUDIT, Action.READ),
):
    """Get privacy audit statistics."""
    audit = get_privacy_audit()
    if not audit:
        raise HTTPException(status_code=500, detail="Privacy audit not initialized")
    
    return audit.get_stats(days=days)


@router.get("/audit/blocked")
async def get_blocked_requests(
    limit: int = Query(100, ge=1, le=1000),
    _=require_permission(Resource.AUDIT, Action.READ),
):
    """Get blocked egress attempts."""
    audit = get_privacy_audit()
    if not audit:
        raise HTTPException(status_code=500, detail="Privacy audit not initialized")
    
    entries = audit.get_blocked(limit=limit)
    return {
        "entries": [
            {
                "id": entry.id,
                "timestamp": entry.timestamp.isoformat(),
                "url": entry.url,
                "method": entry.method,
                "endpoint_id": entry.endpoint_id,
                "data_types": [dt.value for dt in entry.data_types],
                "allowed": entry.allowed,
                "reason": entry.reason,
                "user_id": entry.user_id,
            }
            for entry in entries
        ],
        "total": len(entries),
    }


@router.delete("/audit/cleanup")
async def cleanup_audit(
    retention_days: int = Query(90, ge=7, le=365),
    _=require_permission(Resource.AUDIT, Action.DELETE),
):
    """Remove old audit entries."""
    audit = get_privacy_audit()
    if not audit:
        raise HTTPException(status_code=500, detail="Privacy audit not initialized")
    
    deleted = audit.cleanup_old(retention_days=retention_days)
    return {"deleted": deleted, "retention_days": retention_days}


@router.get("/status")
async def get_privacy_status(
    _=require_permission(Resource.CONFIG, Action.READ),
):
    """Get overall privacy status."""
    config = get_privacy_config()
    audit = get_privacy_audit()
    
    if not config:
        raise HTTPException(status_code=500, detail="Privacy config not initialized")
    
    enabled_endpoints = [
        ep_id for ep_id, ep in config.allowed_endpoints.items() if ep.enabled
    ]
    
    return {
        "egress_policy": config.egress_policy.value,
        "endpoints_enabled": enabled_endpoints,
        "endpoints_disabled": [
            ep_id for ep_id, ep in config.allowed_endpoints.items() if not ep.enabled
        ],
        "never_leave": [dt.value for dt in config.never_leave],
        "audit_enabled": config.audit_all_egress,
        "audit_stats": audit.get_stats() if audit else None,
    }
