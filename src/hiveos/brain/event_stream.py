"""HiveOS Brain — Event Stream Pipeline.

Real-time agent lifecycle events — the nervous system of HiveOS.
Every operation (agent spawn, task assignment, flow execution, gate creation)
emits an event that flows through this pipeline.
"""

from __future__ import annotations

import uuid
from collections import deque, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class EventStream:
    """In-memory event stream for agent lifecycle and system events.

    Thread-safe for single-threaded use. Stores up to 10,000 events.
    """

    def __init__(self, maxlen: int = 10_000):
        self._maxlen = maxlen
        self._events: deque = deque(maxlen=maxlen)
        self._events_by_id: Dict[str, dict] = {}

    def emit(
        self,
        event_type: str,
        source: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Emit a new event. Returns the event ID."""
        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            "event_type": event_type,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {},
        }
        self._events.append(event)
        self._events_by_id[event_id] = event
        return event_id

    def get_events(
        self,
        limit: int = 50,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent events, optionally filtered by type."""
        if event_type is None:
            result = list(self._events)
        else:
            result = [e for e in self._events if e["event_type"] == event_type]
        return result[-limit:]

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a single event by ID."""
        return self._events_by_id.get(event_id)

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()
        self._events_by_id.clear()

    def stats(self) -> Dict[str, Any]:
        """Count events by type."""
        counts: Dict[str, int] = defaultdict(int)
        for e in self._events:
            counts[e["event_type"]] += 1
        return {
            "total_events": len(self._events),
            "by_type": dict(counts),
            "maxlen": self._maxlen,
        }

    @property
    def count(self) -> int:
        return len(self._events)
