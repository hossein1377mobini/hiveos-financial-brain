"""HiveOS Brain — Approval Gate Engine.

Human-in-the-loop approval workflow. Critical decisions require human
approval before execution proceeds. Supports timeout-based expiry.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ApprovalGateEngine:
    """Manages approval gates — human checkpoints in automated workflows, restored from storage."""

    def __init__(self, storage: Optional["StorageEngine"] = None):
        self._storage = storage
        self._gates: Dict[str, dict] = {}
        self._namespace = "brain:gates"

        if self._storage:
            self._restore()

    def _restore(self):
        """Rehydrate gates from persistent storage."""
        for gate in self._storage.load_all(self._namespace):
            gid = gate.get("gate_id", "")
            if gid:
                self._gates[gid] = gate

    def _persist(self, gate_id: str):
        if self._storage and gate_id in self._gates:
            self._storage.upsert(self._namespace, gate_id, self._gates[gate_id])

    def create_gate(
        self,
        gate_id: Optional[str] = None,
        title: str = "",
        description: str = "",
        requestor: str = "",
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 86400,  # 24 hours default
    ) -> Dict[str, Any]:
        """Create a new approval gate in 'pending' status."""
        gid = gate_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        gate = {
            "gate_id": gid,
            "title": title,
            "description": description,
            "requestor": requestor,
            "context": context or {},
            "status": "pending",
            "approver": "",
            "notes": "",
            "resolution_reason": "",
            "created_at": now.isoformat(),
            "resolved_at": "",
            "timeout_seconds": timeout_seconds,
            "expires_at": datetime.fromtimestamp(
                now.timestamp() + timeout_seconds, tz=timezone.utc
            ).isoformat(),
        }
        self._gates[gid] = gate
        self._persist(gid)
        return dict(gate)

    def _check_expired(self, gate: dict) -> bool:
        """Check if a pending gate has expired. Updates status if so."""
        if gate["status"] != "pending":
            return False
        now = datetime.now(timezone.utc)
        try:
            expires = datetime.fromisoformat(gate["expires_at"])
            if now > expires:
                gate["status"] = "expired"
                gate["resolved_at"] = now.isoformat()
                gate["resolution_reason"] = "Auto-expired (timeout)"
                self._persist(gate.get("gate_id", ""))
                return True
        except (ValueError, TypeError):
            pass
        return False

    def approve(
        self,
        gate_id: str,
        approver: str,
        notes: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Approve a gate. Returns updated gate or None if not found."""
        gate = self._gates.get(gate_id)
        if gate is None:
            return None
        if gate["status"] != "pending":
            return gate
        gate["status"] = "approved"
        gate["approver"] = approver
        gate["notes"] = notes
        gate["resolution_reason"] = "Approved"
        gate["resolved_at"] = datetime.now(timezone.utc).isoformat()
        self._persist(gate_id)
        return gate

    def reject(
        self,
        gate_id: str,
        approver: str,
        reason: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Reject a gate. Returns updated gate or None if not found."""
        gate = self._gates.get(gate_id)
        if gate is None:
            return None
        if gate["status"] != "pending":
            return gate
        gate["status"] = "rejected"
        gate["approver"] = approver
        gate["resolution_reason"] = reason or "Rejected"
        gate["resolved_at"] = datetime.now(timezone.utc).isoformat()
        self._persist(gate_id)
        return gate

    def get_gate(self, gate_id: str) -> Optional[Dict[str, Any]]:
        """Get gate details. Checks expiry on access."""
        gate = self._gates.get(gate_id)
        if gate is None:
            return None
        self._check_expired(gate)
        return dict(gate)

    def list_gates(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List gates, optionally filtered by status. Checks expiry on all pending."""
        results = []
        for g in self._gates.values():
            if g["status"] == "pending":
                self._check_expired(g)
            if status and g["status"] != status:
                continue
            results.append(dict(g))
        results.sort(key=lambda g: g["created_at"], reverse=True)
        return results[:limit]

    def pending_for_user(self) -> List[Dict[str, Any]]:
        """Get all pending (non-expired) gates."""
        results = []
        for g in self._gates.values():
            if g["status"] == "pending":
                expired = self._check_expired(g)
                if not expired:
                    results.append(dict(g))
        results.sort(key=lambda g: g["created_at"], reverse=True)
        return results

    def stats(self) -> Dict[str, Any]:
        """Get gate statistics."""
        counts: Dict[str, int] = defaultdict(int)
        total_resolution_seconds = 0.0
        resolved_count = 0

        now = datetime.now(timezone.utc)
        for g in self._gates.values():
            counts[g["status"]] += 1
            if g["resolved_at"] and g["status"] in ("approved", "rejected"):
                try:
                    created = datetime.fromisoformat(g["created_at"])
                    resolved = datetime.fromisoformat(g["resolved_at"])
                    total_resolution_seconds += (resolved - created).total_seconds()
                    resolved_count += 1
                except (ValueError, TypeError):
                    pass

        avg_resolution_s = (
            round(total_resolution_seconds / resolved_count, 1)
            if resolved_count > 0
            else 0.0
        )

        return {
            "total_gates": len(self._gates),
            "by_status": dict(counts),
            "resolved_count": resolved_count,
            "avg_resolution_seconds": avg_resolution_s,
        }
