"""HiveOS Flow Library — persistent storage for user-created flows.

Provides CRUD operations on user flows using the StorageEngine.
Every flow is stored under the ``playground:flows`` namespace with
a unique ``flow_id``, creation timestamp, and full YAML definition.

P-08: Flow Library (save/share user flows via StorageEngine)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from hiveos.storage import StorageEngine


class FlowLibrary:
    """Persistent library of user-created (or user-customised) flows.

    All operations go through a :class:`~hiveos.storage.StorageEngine`
    instance, so flows survive restarts.

    Usage::

        lib = FlowLibrary(storage)
        flow_id = lib.save_flow({"name": "My Flow", ...}, user="alice")
        flows = lib.list_flows()
        flow = lib.load_flow(flow_id)
        lib.delete_flow(flow_id)
    """

    _NAMESPACE = "playground:flows"

    def __init__(self, storage: Optional[StorageEngine] = None):
        self._storage = storage

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_flow(
        self,
        flow_definition: dict,
        *,
        flow_id: Optional[str] = None,
        name: Optional[str] = None,
        user: str = "default",
        tags: Optional[List[str]] = None,
    ) -> str:
        """Persist a flow definition and return its unique ``flow_id``.

        If *flow_definition* already has a ``name`` key it is used as the
        display name unless *name* is explicitly passed.
        """
        fid = flow_id or _new_id()
        now = datetime.now(timezone.utc).isoformat()

        record = {
            "flow_id": fid,
            "name": name or flow_definition.get("name", "Untitled Flow"),
            "user": user,
            "tags": tags or [],
            "flow_definition": flow_definition,
            "created_at": now,
            "updated_at": now,
        }

        if self._storage is not None:
            self._storage.upsert(self._NAMESPACE, fid, record)

        return fid

    def load_flow(self, flow_id: str) -> Optional[dict]:
        """Retrieve a flow by its ``flow_id``.

        Returns the full record dict or *None* if not found.
        """
        if self._storage is None:
            return None
        return self._storage.load(self._NAMESPACE, flow_id)

    def list_flows(
        self,
        *,
        user: Optional[str] = None,
        tag: Optional[str] = None,
        sort_by: str = "updated_at",
        limit: int = 100,
    ) -> List[dict]:
        """List persisted flows, optionally filtered.

        When *user* is provided only flows owned by that user are returned.
        When *tag* is provided only flows that include that tag are returned.
        Results are sorted descending by *sort_by* (``created_at`` or
        ``updated_at``) and capped at *limit*.
        """
        if self._storage is None:
            return []

        raw = self._storage.load_all(self._NAMESPACE) or []
        flows: List[dict] = []

        for item in raw:
            if isinstance(item, dict):
                flows.append(item)

        # Filter by user
        if user:
            flows = [f for f in flows if f.get("user") == user]

        # Filter by tag
        if tag:
            flows = [f for f in flows if tag in f.get("tags", [])]

        # Sort (descending — most recent first)
        reverse = True
        flows.sort(key=lambda f: f.get(sort_by, ""), reverse=reverse)

        return flows[:limit]

    def delete_flow(self, flow_id: str) -> bool:
        """Delete a flow by its ``flow_id``. Returns *True* on success."""
        if self._storage is None:
            return False
        existing = self._storage.load(self._NAMESPACE, flow_id)
        if existing is None:
            return False
        self._storage.delete(self._NAMESPACE, flow_id)
        return True

    def update_flow(
        self,
        flow_id: str,
        *,
        name: Optional[str] = None,
        flow_definition: Optional[dict] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Update an existing flow's metadata or definition.

        Only the fields passed are updated; any *None* fields are left
        unchanged. Returns *True* on success, *False* if the flow does
        not exist or storage is unavailable.
        """
        if self._storage is None:
            return False

        existing = self._storage.load(self._NAMESPACE, flow_id)
        if existing is None:
            return False

        if name is not None:
            existing["name"] = name
        if flow_definition is not None:
            existing["flow_definition"] = flow_definition
        if tags is not None:
            existing["tags"] = tags

        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._storage.upsert(self._NAMESPACE, flow_id, existing)
        return True

    def count(self) -> int:
        """Return the total number of flows in the library."""
        if self._storage is None:
            return 0
        return self._storage.count(self._NAMESPACE)


def _new_id() -> str:
    """Generate a short unique flow id."""
    return uuid.uuid4().hex[:12]
