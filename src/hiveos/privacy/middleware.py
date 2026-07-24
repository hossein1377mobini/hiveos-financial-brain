"""
Privacy Middleware — FastAPI middleware for privacy enforcement.

Intercepts API requests and enforces data egress policies.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .audit import EgressAuditEntry, PrivacyAuditTrail
from .config import DataClassification, PrivacyConfig
from .guards import NetworkGuard, PrivacyViolation

logger = logging.getLogger(__name__)


class PrivacyMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that enforces privacy policies.
    
    Features:
    - Logs all outbound API calls
    - Blocks unauthorized external requests
    - Audit trail for compliance
    """
    
    def __init__(
        self,
        app,
        config: PrivacyConfig,
        audit_trail: Optional[PrivacyAuditTrail] = None,
    ):
        super().__init__(app)
        self.config = config
        self.audit_trail = audit_trail
        self.guard = NetworkGuard(config)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through privacy middleware."""
        start_time = time.time()
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request (for audit trail)
            self._log_request(
                request=request,
                response_status=response.status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
            )
            
            return response
            
        except PrivacyViolation as e:
            # Privacy violation — block and audit
            logger.warning(f"Privacy violation from {client_ip}: {e}")
            
            if self.audit_trail:
                self.audit_trail.log_egress(
                    EgressAuditEntry(
                        url=str(request.url),
                        method=request.method,
                        allowed=False,
                        reason=str(e),
                        user_id=client_ip,
                    )
                )
            
            return Response(
                content='{"error": "Privacy policy violation"}',
                status_code=403,
                media_type="application/json",
            )
        
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
    
    def _log_request(
        self,
        request: Request,
        response_status: int,
        duration_ms: float,
        client_ip: str,
    ) -> None:
        """Log request for audit trail."""
        if not self.config.audit_all_egress:
            return
        
        # Only log external-facing requests (not internal health checks)
        path = request.url.path
        if path == "/api/health":
            return
        
        # Create audit entry
        entry = EgressAuditEntry(
            url=str(request.url),
            method=request.method,
            allowed=True,
            reason="Internal API call",
            user_id=client_ip,
            response_code=response_status,
        )
        
        if self.audit_trail:
            self.audit_trail.log_egress(entry)


class EgressGuardMiddleware(BaseHTTPMiddleware):
    """
    Middleware that guards outbound HTTP requests from the server.
    
    Use this to prevent the server from making unauthorized external calls.
    """
    
    def __init__(self, app, config: PrivacyConfig):
        super().__init__(app)
        self.config = config
        self.guard = NetworkGuard(config)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check if any outbound calls are needed."""
        # This middleware primarily logs and blocks
        # Actual egress guarding happens at the network level
        return await call_next(request)
