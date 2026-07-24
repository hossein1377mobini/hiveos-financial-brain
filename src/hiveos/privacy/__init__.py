"""
HiveOS Privacy-First Architecture Module

Enforces ADR-0017: All customer data stays on customer infrastructure.
No data leaves unless explicitly configured.

Usage:
    from hiveos.privacy import PrivacyConfig, NetworkGuard, PrivacyAuditTrail
    
    # Load config
    config = PrivacyConfig.load(Path("~/.hiveos/privacy.json"))
    
    # Check if egress is allowed
    guard = NetworkGuard(config)
    result = guard.check_egress("https://api.example.com", data_types=[...])
    
    # Install global guard
    from hiveos.privacy import PrivacyGuard
    privacy_guard = PrivacyGuard(config)
    privacy_guard.install()
"""

from .audit import EgressAuditEntry, PrivacyAuditTrail
from .config import (
    DataClassification,
    EgressPolicy,
    EndpointConfig,
    PrivacyConfig,
)
from .guards import (
    EgressRequest,
    EgressResult,
    NetworkGuard,
    PrivacyGuard,
    PrivacyViolation,
)

# Middleware imports are optional — only available with FastAPI
try:
    from .middleware import EgressGuardMiddleware, PrivacyMiddleware
    __all___extras = ["PrivacyMiddleware", "EgressGuardMiddleware"]
except ImportError:
    __all___extras = []

__all__ = [
    # Config
    "PrivacyConfig",
    "EgressPolicy",
    "DataClassification",
    "EndpointConfig",
    
    # Guards
    "NetworkGuard",
    "PrivacyGuard",
    "EgressRequest",
    "EgressResult",
    "PrivacyViolation",
    
    # Audit
    "PrivacyAuditTrail",
    "EgressAuditEntry",
] + __all___extras
