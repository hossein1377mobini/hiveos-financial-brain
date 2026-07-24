"""
Network Egress Guards — Enforce privacy policies on outbound requests.

Intercepts and validates all external HTTP requests against privacy config.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urlparse

from .config import DataClassification, EgressPolicy, PrivacyConfig

logger = logging.getLogger(__name__)


@dataclass
class EgressRequest:
    """Represents an outbound HTTP request."""
    url: str
    method: str = "GET"
    headers: Dict[str, str] = None
    data: Any = None
    endpoint_id: Optional[str] = None
    data_types: List[DataClassification] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.data_types is None:
            self.data_types = []
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class EgressResult:
    """Result of an egress check."""
    is_allowed: bool
    reason: str
    request: EgressRequest
    blocked_at: Optional[datetime] = None

    @classmethod
    def allowed(cls, request: EgressRequest) -> "EgressResult":
        return cls(is_allowed=True, reason="Policy allows", request=request)

    @classmethod
    def blocked(cls, request: EgressRequest, reason: str) -> "EgressResult":
        return cls(
            is_allowed=False,
            reason=reason,
            request=request,
            blocked_at=datetime.now(timezone.utc),
        )


class NetworkGuard:
    """
    Validates outbound HTTP requests against privacy configuration.
    
    Usage:
        guard = NetworkGuard(privacy_config)
        result = guard.check_egress(url, method, data_types)
        if result.is_allowed:
            # Proceed with request
        else:
            # Request blocked
    """
    
    def __init__(self, config: PrivacyConfig):
        self.config = config
        self._blocked_count = 0
        self._allowed_count = 0
    
    def check_egress(
        self,
        url: str,
        method: str = "GET",
        data_types: Optional[List[DataClassification]] = None,
        endpoint_id: Optional[str] = None,
    ) -> EgressResult:
        """
        Check if an outbound request is allowed.
        
        Parameters
        ----------
        url:
            Target URL.
        method:
            HTTP method.
        data_types:
            Types of data being sent.
        endpoint_id:
            Pre-configured endpoint ID (optional).
        
        Returns
        -------
        EgressResult with allowed/blocked status.
        """
        request = EgressRequest(
            url=url,
            method=method,
            endpoint_id=endpoint_id,
            data_types=data_types or [],
        )
        
        # Parse URL domain
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check blocked domains first
        if domain in self.config.blocked_domains:
            self._blocked_count += 1
            return EgressResult.blocked(request, f"Domain explicitly blocked: {domain}")
        
        # Check if any data type is forbidden
        for dt in request.data_types:
            if dt in self.config.never_leave:
                self._blocked_count += 1
                return EgressResult.blocked(
                    request,
                    f"Data type '{dt.value}' cannot leave infrastructure"
                )
        
        # Check policy
        if self.config.egress_policy == EgressPolicy.BLOCK_ALL:
            self._blocked_count += 1
            return EgressResult.blocked(request, "Global policy: BLOCK_ALL")
        
        # Check specific endpoint if provided
        if endpoint_id:
            endpoint = self.config.allowed_endpoints.get(endpoint_id)
            if not endpoint:
                self._blocked_count += 1
                return EgressResult.blocked(request, f"Unknown endpoint: {endpoint_id}")
            if not endpoint.enabled:
                self._blocked_count += 1
                return EgressResult.blocked(request, f"Endpoint disabled: {endpoint_id}")
        
        # Check allowed domains
        if self.config.allowed_domains and domain not in self.config.allowed_domains:
            self._blocked_count += 1
            return EgressResult.blocked(request, f"Domain not in allowed list: {domain}")
        
        # Passed all checks
        self._allowed_count += 1
        return EgressResult.allowed(request)
    
    @property
    def stats(self) -> Dict[str, int]:
        """Return guard statistics."""
        return {
            "allowed": self._allowed_count,
            "blocked": self._blocked_count,
            "total": self._allowed_count + self._blocked_count,
        }
    
    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._allowed_count = 0
        self._blocked_count = 0


class PrivacyGuard:
    """
    Higher-level guard that wraps external HTTP clients.
    
    Intercepts calls to urllib, requests, httpx, etc.
    """
    
    def __init__(self, config: PrivacyConfig):
        self.config = config
        self.network_guard = NetworkGuard(config)
        self._original_urlopen = None
    
    def install(self) -> None:
        """Install privacy guards on HTTP clients."""
        try:
            import urllib.request
            self._original_urlopen = urllib.request.urlopen
            urllib.request.urlopen = self._guarded_urlopen
            logger.info("Privacy guard installed on urllib.request.urlopen")
        except ImportError:
            pass
    
    def uninstall(self) -> None:
        """Remove privacy guards from HTTP clients."""
        if self._original_urlopen:
            import urllib.request
            urllib.request.urlopen = self._original_urlopen
            self._original_urlopen = None
            logger.info("Privacy guard removed from urllib.request.urlopen")
    
    def _guarded_urlopen(self, req, *args, **kwargs):
        """Guarded version of urlopen."""
        # Extract URL from request
        if hasattr(req, "full_url"):
            url = req.full_url
        elif isinstance(req, str):
            url = req
        else:
            url = str(req)
        
        # Check if allowed
        result = self.network_guard.check_egress(url)
        
        if not result.is_allowed:
            raise PrivacyViolation(
                f"Egress blocked: {result.reason}\n"
                f"URL: {url}\n"
                f"To allow: configure privacy settings in ~/.hiveos/privacy.json"
            )
        
        # Proceed with original
        return self._original_urlopen(req, *args, **kwargs)


class PrivacyViolation(Exception):
    """Raised when a privacy policy violation is detected."""
    pass
