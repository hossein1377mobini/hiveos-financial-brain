"""Shared FastAPI auth dependencies for dashboard route modules.

Route modules call ``set_auth_deps(checker)`` during app init, then use
``get_current_user`` or ``require_permission(resource, action)`` as
FastAPI ``Depends()`` on individual endpoints.

IMPORTANT: These functions return callables that resolve the auth checker
at REQUEST TIME (via the module-level global), not at route-definition
time. This is critical because multiple HiveOSApp instances may share
the same router module.
"""

from __future__ import annotations

from typing import Optional, Callable

from fastapi import Depends, Request
from ..auth import AuthChecker
from ...rbac import Resource, Action
from ...privacy import PrivacyConfig, PrivacyAuditTrail

_auth_checker: Optional[AuthChecker] = None
_privacy_config: Optional[PrivacyConfig] = None
_privacy_audit: Optional[PrivacyAuditTrail] = None


def set_auth_deps(checker: AuthChecker) -> None:
    """Called by app factory to inject the shared auth checker."""
    global _auth_checker
    _auth_checker = checker


def set_privacy_deps(config: PrivacyConfig, audit: PrivacyAuditTrail) -> None:
    """Called by app factory to inject privacy deps."""
    global _privacy_config, _privacy_audit
    _privacy_config = config
    _privacy_audit = audit


def get_privacy_config() -> Optional[PrivacyConfig]:
    """Get the privacy config."""
    return _privacy_config


def get_privacy_audit() -> Optional[PrivacyAuditTrail]:
    """Get the privacy audit trail."""
    return _privacy_audit


async def get_current_user(request: Request):
    """FastAPI Depends-compatible: authenticate (any valid API key).

    Resolves the auth checker at request time via the module global.
    """
    if _auth_checker is None:
        return None
    return await _auth_checker._authenticate(request)


def require_permission(resource: Resource, action: Action) -> Callable:
    """FastAPI Depends-compatible: authenticate + authorize (specific permission).

    Returns a callable that resolves the auth checker at request time.
    """
    async def _check(request: Request):
        if _auth_checker is None:
            return None
        return await _auth_checker.require(resource, action)(request)
    return _check
