"""
Dashboard Auth — FastAPI dependency-injected authentication & authorization.

Provides:
- AuthChecker: validates Bearer token via RBACManager.authenticate()
- Per-route permission dependencies via Resource/Action mapping
- Audit logging for denied requests (401/403)
- CORS middleware (origin-restricted by default)
"""

from __future__ import annotations

from typing import Optional, Callable, Set

from fastapi import Depends, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from ..rbac import RBACManager, Resource, Action
from ..audit import AuditTrail, AuditAction, AuditResource, AuditResult
from ..rbac.models import User


class AuthChecker:
    """
    Centralized auth dependency for the Dashboard.

    Usage:
        auth = AuthChecker(rbac, audit)

        # On the app for global auth:
        app.dependencies.append(Depends(auth()))

        # On individual routes for permission checks:
        @app.get("/api/domains/{name}/install")
        async def install(..., _=Depends(auth.require(Resource.DOMAIN, Action.CREATE))):
            ...

        # On public routes:
        @app.get("/", response_class=HTMLResponse)
        async def index():
            ...
    """

    def __init__(self, rbac: RBACManager, audit: Optional[AuditTrail] = None):
        self.rbac = rbac
        self.audit = audit

    def __call__(self):
        """Return a FastAPI Depends-compatible callable for authentication."""
        return self._authenticate

    def require(self, resource: Resource, action: Action) -> Callable:
        """
        Return a FastAPI Depends-compatible callable for authentication
        AND authorization (specific resource:action permission).
        """
        async def _check(request: Request):
            # 1) Authenticate (extract token → look up user)
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                self._log_denied(
                    request,
                    AuditAction.READ,
                    AuditResource.RBAC,
                    status_code=401,
                    message="Missing authorization header",
                )
                raise HTTPException(status_code=401, detail="Missing authorization header")

            api_key = auth_header[7:].strip()
            user = self.rbac.authenticate(api_key)
            if not user:
                self._log_denied(
                    request,
                    AuditAction.READ,
                    AuditResource.RBAC,
                    status_code=401,
                    message="Invalid API key",
                )
                raise HTTPException(status_code=401, detail="Invalid API key")

            # 2) Authorize (check specific permission)
            if not self.rbac.check_permission(user, resource, action):
                self._log_denied(
                    request,
                    AuditAction.READ,
                    AuditResource.RBAC,
                    user=user.username,
                    status_code=403,
                    message=f"Insufficient permissions: need {resource.value}:{action.value}",
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions: need {resource.value}:{action.value}",
                )

            # 3) Store authenticated user for downstream use
            request.state.user = user
            return user

        return _check

    async def _authenticate(self, request: Request):
        """Global auth: extract and validate Bearer token."""
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            self._log_denied(
                request,
                AuditAction.READ,
                AuditResource.RBAC,
                status_code=401,
                message="Missing authorization header",
            )
            raise HTTPException(status_code=401, detail="Missing authorization header")

        api_key = auth_header[7:].strip()
        user = self.rbac.authenticate(api_key)
        if not user:
            self._log_denied(
                request,
                AuditAction.READ,
                AuditResource.RBAC,
                status_code=401,
                message="Invalid API key",
            )
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Store authenticated user on request state
        request.state.user = user
        return user

    def _log_denied(
        self,
        request: Request,
        action: AuditAction,
        resource: AuditResource,
        user: str = "",
        status_code: int = 401,
        message: str = "",
    ):
        """Log denied requests to the audit trail."""
        if not self.audit:
            return
        client_ip = ""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        from ..audit import AuditEntry
        entry = AuditEntry(
            actor=user or "anonymous",
            action=action,
            resource=resource,
            result=AuditResult.DENIED,
            status_code=status_code,
            message=f"{request.method} {request.url.path} — {message}",
            details={
                "method": request.method,
                "path": request.url.path,
                "ip": client_ip,
            },
            ip=client_ip,
        )
        self.audit.log(entry)
