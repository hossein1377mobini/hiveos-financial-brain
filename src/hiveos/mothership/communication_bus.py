"""
Communication Bus — cross-node agent messaging for Mothership.

Provides a message bus for:
- Agent-to-agent messaging (within and across nodes)
- Task assignments and results
- Knowledge sync events
- Heartbeat / health checks
- Control plane commands

Supports multiple backends:
- In-memory (single process, for testing/local)
- File-based (multi-process on same host)
- HTTP/REST (distributed nodes - future)
- NATS/RabbitMQ (production - future)
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
import json
import uuid
import queue
from collections import defaultdict

from rich.console import Console

console = Console()


class MessageType(Enum):
    """Message types on the communication bus."""
    # Control plane
    HEARTBEAT = "heartbeat"
    NODE_REGISTER = "node_register"
    NODE_UNREGISTER = "node_unregister"
    HEALTH_CHECK = "health_check"
    HEALTH_REPORT = "health_report"

    # Task orchestration
    TASK_ASSIGN = "task_assign"
    TASK_START = "task_start"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    TASK_CANCEL = "task_cancel"
    TASK_REROUTE = "task_reroute"

    # Agent communication
    AGENT_MESSAGE = "agent_message"      # Agent-to-agent
    AGENT_BROADCAST = "agent_broadcast"  # Agent-to-all
    AGENT_REPLY = "agent_reply"          # Reply to agent message

    # Knowledge sync
    SYNC_PUSH = "sync_push"
    SYNC_PULL = "sync_pull"
    SYNC_ACK = "sync_ack"
    SKILL_UPDATE = "skill_update"
    KNOWLEDGE_UPDATE = "knowledge_update"
    FLOW_UPDATE = "flow_update"

    # Control
    SHUTDOWN = "shutdown"
    RELOAD_CONFIG = "reload_config"
    PAUSE_FLOW = "pause_flow"
    RESUME_FLOW = "resume_flow"


class MessagePriority(Enum):
    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200


@dataclass
class Message:
    """A message on the communication bus."""
    type: MessageType
    sender: str                    # Node/agent ID
    recipient: Optional[str] = None  # None = broadcast
    payload: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    correlation_id: Optional[str] = None  # For request-response
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ttl: int = 3600  # Time to live in seconds
    retry_count: int = 0
    headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "payload": self.payload,
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "retry_count": self.retry_count,
            "headers": self.headers,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            type=MessageType(data["type"]),
            sender=data["sender"],
            recipient=data.get("recipient"),
            payload=data.get("payload", {}),
            message_id=data.get("message_id", uuid.uuid4().hex[:12]),
            correlation_id=data.get("correlation_id"),
            priority=MessagePriority(data.get("priority", 50)),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            ttl=data.get("ttl", 3600),
            retry_count=data.get("retry_count", 0),
            headers=data.get("headers", {}),
        )

    def is_expired(self) -> bool:
        """Check if message TTL has expired."""
        try:
            sent = datetime.fromisoformat(self.timestamp)
            elapsed = (datetime.utcnow() - sent).total_seconds()
            return elapsed > self.ttl
        except (ValueError, TypeError):
            return False

    def is_for(self, node_id: str) -> bool:
        """Check if this message is for a specific node (or broadcast)."""
        return self.recipient is None or self.recipient == node_id


@dataclass
class Subscription:
    """A subscription to message types."""
    subscriber_id: str
    message_types: Set[MessageType]
    callback: Callable[["Message"], None]
    filter_fn: Optional[Callable[["Message"], bool]] = None


class BusBackend:
    """Abstract base for bus backends."""

    def __init__(self):
        self._subscriptions: List[Subscription] = []

    def publish(self, message: Message) -> bool:
        """Publish a message. Return True if delivered to at least one subscriber."""
        raise NotImplementedError

    def subscribe(
        self,
        subscriber_id: str,
        message_types: List[MessageType],
        callback: Callable[["Message"], None],
        filter_fn: Optional[Callable[["Message"], bool]] = None,
    ) -> bool:
        """Subscribe to message types."""
        sub = Subscription(
            subscriber_id=subscriber_id,
            message_types=set(message_types),
            callback=callback,
            filter_fn=filter_fn,
        )
        self._subscriptions.append(sub)
        return True

    def unsubscribe(self, subscriber_id: str) -> int:
        """Remove all subscriptions for a subscriber. Return count removed."""
        before = len(self._subscriptions)
        self._subscriptions = [s for s in self._subscriptions if s.subscriber_id != subscriber_id]
        return before - len(self._subscriptions)

    def _deliver(self, message: Message) -> int:
        """Deliver message to matching subscriptions. Return count delivered."""
        delivered = 0
        for sub in self._subscriptions:
            if message.type in sub.message_types:
                if sub.filter_fn and not sub.filter_fn(message):
                    continue
                if message.is_for(sub.subscriber_id):
                    try:
                        sub.callback(message)
                        delivered += 1
                    except Exception as e:
                        console.print(f"[red]Bus callback error: {e}[/red]")
        return delivered


class InMemoryBusBackend(BusBackend):
    """In-memory message bus for single-process / testing.

    Delivers messages synchronously in publish() — no background threads needed.
    """

    def __init__(self):
        super().__init__()

    def publish(self, message: Message) -> bool:
        """Deliver message synchronously to matching subscriptions."""
        if message.is_expired():
            return False
        return self._deliver(message) > 0

    def start(self):
        """No-op: delivery is synchronous."""
        pass

    def stop(self):
        """No-op: delivery is synchronous."""
        pass


class FileBusBackend(BusBackend):
    """File-based message bus for multi-process on same host."""

    def __init__(self, bus_dir: Path):
        super().__init__()
        self.bus_dir = bus_dir
        self.bus_dir.mkdir(parents=True, exist_ok=True)
        self._polling = False
        self._poll_thread: Optional[threading.Thread] = None
        self._seen_messages: Set[str] = set()
        self._lock = threading.RLock()

        # Create subdirectories
        (self.bus_dir / "incoming").mkdir(exist_ok=True)
        (self.bus_dir / "outgoing").mkdir(exist_ok=True)
        (self.bus_dir / "processed").mkdir(exist_ok=True)

    def publish(self, message: Message) -> bool:
        """Write message to outgoing directory."""
        try:
            msg_file = self.bus_dir / "outgoing" / f"{message.timestamp}_{message.message_id}.json"
            msg_file.write_text(json.dumps(message.to_dict(), indent=2))
            return True
        except Exception as e:
            console.print(f"[red]File bus publish error: {e}[/red]")
            return False

    def start(self, poll_interval: float = 0.5):
        """Start polling for incoming messages."""
        if self._polling:
            return
        self._polling = True
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            args=(poll_interval,),
            daemon=True,
        )
        self._poll_thread.start()
        console.print(f"[dim]🚌 File bus started at {self.bus_dir}[/dim]")

    def stop(self):
        """Stop polling."""
        self._polling = False
        if self._poll_thread:
            self._poll_thread.join(timeout=2)
        console.print("[dim]🚌 File bus stopped[/dim]")

    def _poll_loop(self, interval: float):
        """Poll for new messages in incoming directory."""
        while self._polling:
            try:
                for msg_file in (self.bus_dir / "incoming").glob("*.json"):
                    if msg_file.name in self._seen_messages:
                        continue

                    try:
                        data = json.loads(msg_file.read_text())
                        message = Message.from_dict(data)

                        if message.is_expired():
                            msg_file.rename(self.bus_dir / "processed" / msg_file.name)
                            continue

                        delivered = self._deliver(message)
                        if delivered > 0:
                            self._seen_messages.add(msg_file.name)
                            # Keep seen set bounded
                            if len(self._seen_messages) > 10000:
                                self._seen_messages = set(list(self._seen_messages)[-5000:])
                            msg_file.rename(self.bus_dir / "processed" / msg_file.name)
                        else:
                            # No subscribers yet, leave for later
                            pass

                    except Exception as e:
                        console.print(f"[red]File bus process error: {e}[/red]")
                        msg_file.rename(self.bus_dir / "processed" / f"error_{msg_file.name}")

            except Exception as e:
                console.print(f"[red]File bus poll error: {e}[/red]")

            time.sleep(interval)


class CommunicationBus:
    """
    High-level communication bus for Mothership.

    Supports multiple backends and provides:
    - Publish/subscribe with message types
    - Request-response patterns
    - Message routing by node
    - Persistence and replay (file backend)
    """

    def __init__(
        self,
        backend: Optional[BusBackend] = None,
        bus_dir: Optional[Path] = None,
        node_id: str = "mothership",
    ):
        self.node_id = node_id
        self.backend = backend or InMemoryBusBackend()
        self._request_futures: Dict[str, queue.Queue] = {}
        self._lock = threading.RLock()

        # Start backend if it has start method
        if hasattr(self.backend, "start"):
            self.backend.start()

        # Subscribe to messages for this node
        self._setup_local_subscriptions()

    def _setup_local_subscriptions(self):
        """Subscribe to messages addressed to this node."""
        self.backend.subscribe(
            subscriber_id=self.node_id,
            message_types=list(MessageType),
            callback=self._on_message,
            filter_fn=lambda m: m.is_for(self.node_id),
        )

    def _on_message(self, message: Message):
        """Handle incoming messages for this node."""
        # Check for response to a pending request
        if message.correlation_id and message.correlation_id in self._request_futures:
            self._request_futures[message.correlation_id].put(message)
            return

        # Handle specific message types
        if message.type == MessageType.HEARTBEAT:
            console.print(f"[dim]💓 Heartbeat from {message.sender}[/dim]")

    # ── Publish/Subscribe ──────────────────────────────────────────

    def publish(
        self,
        msg_type: MessageType,
        payload: Dict[str, Any],
        recipient: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None,
        ttl: int = 3600,
        headers: Optional[Dict[str, str]] = None,
    ) -> Message:
        """Publish a message to the bus."""
        message = Message(
            type=msg_type,
            sender=self.node_id,
            recipient=recipient,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id,
            ttl=ttl,
            headers=headers or {},
        )
        self.backend.publish(message)
        return message

    def subscribe(
        self,
        message_types: List[MessageType],
        callback: Callable[[Message], None],
        filter_fn: Optional[Callable[[Message], bool]] = None,
    ) -> str:
        """Subscribe to message types. Returns the node ID (used for routing)."""
        # Register with this node's ID so messages addressed to it are delivered
        self.backend.subscribe(self.node_id, message_types, callback, filter_fn)
        return self.node_id

    def unsubscribe(self, subscription_id: str) -> int:
        """Unsubscribe by ID."""
        return self.backend.unsubscribe(subscription_id)

    # ── Request-Response ──────────────────────────────────────────

    def request(
        self,
        msg_type: MessageType,
        payload: Dict[str, Any],
        recipient: str,
        timeout: float = 30.0,
    ) -> Optional[Message]:
        """Send a request and wait for a response."""
        correlation_id = uuid.uuid4().hex
        response_queue: queue.Queue = queue.Queue()

        with self._lock:
            self._request_futures[correlation_id] = response_queue

        try:
            self.publish(
                msg_type=msg_type,
                payload=payload,
                recipient=recipient,
                correlation_id=correlation_id,
                priority=MessagePriority.HIGH,
            )

            response = response_queue.get(timeout=timeout)
            return response
        except queue.Empty:
            return None
        finally:
            with self._lock:
                self._request_futures.pop(correlation_id, None)

    def reply(
        self,
        original: Message,
        payload: Dict[str, Any],
        msg_type: MessageType = MessageType.AGENT_REPLY,
    ) -> Message:
        """Reply to a request message."""
        return self.publish(
            msg_type=msg_type,
            payload=payload,
            recipient=original.sender,
            correlation_id=original.correlation_id or original.message_id,
        )

    # ── Task Orchestration Helpers ────────────────────────────────

    def assign_task(
        self,
        node: str,
        task_id: str,
        agent_id: str,
        capability: str,
        input_data: Dict[str, Any],
    ) -> Message:
        """Assign a task to a node."""
        return self.publish(
            msg_type=MessageType.TASK_ASSIGN,
            payload={
                "task_id": task_id,
                "agent_id": agent_id,
                "capability": capability,
                "input": input_data,
            },
            recipient=node,
            priority=MessagePriority.HIGH,
            correlation_id=task_id,
        )

    def task_complete(
        self,
        node: str,
        task_id: str,
        output: Dict[str, Any],
        success: bool = True,
    ) -> Message:
        """Report task completion from a node."""
        msg_type = MessageType.TASK_COMPLETE if success else MessageType.TASK_FAILED
        return self.publish(
            msg_type=msg_type,
            payload={
                "task_id": task_id,
                "output": output,
                "success": success,
            },
            recipient=self.node_id,
            correlation_id=task_id,
        )

    def task_progress(
        self,
        node: str,
        task_id: str,
        progress: float,
        message: str = "",
    ) -> Message:
        """Report task progress from a node."""
        return self.publish(
            msg_type=MessageType.TASK_PROGRESS,
            payload={
                "task_id": task_id,
                "progress": progress,
                "message": message,
            },
            recipient=self.node_id,
            correlation_id=task_id,
        )

    def reroute_task(self, node: str, task_id: str, new_node: str) -> Message:
        """Instruct a node to reroute a task."""
        return self.publish(
            msg_type=MessageType.TASK_REROUTE,
            payload={"task_id": task_id, "new_node": new_node},
            recipient=node,
            priority=MessagePriority.HIGH,
            correlation_id=task_id,
        )

    def broadcast(self, msg_type: MessageType, payload: Dict[str, Any]) -> Message:
        """Broadcast to all nodes."""
        return self.publish(
            msg_type=msg_type,
            payload=payload,
            recipient=None,  # broadcast
        )

    # ── Health & Control ──────────────────────────────────────────

    def send_heartbeat(self, load: int = 0, capabilities: Optional[List[str]] = None) -> Message:
        """Send a heartbeat message."""
        return self.publish(
            msg_type=MessageType.HEARTBEAT,
            payload={
                "load": load,
                "capabilities": capabilities or [],
                "timestamp": datetime.utcnow().isoformat(),
            },
            recipient=self.node_id,  # to mothership
            priority=MessagePriority.LOW,
        )

    def request_health(self, node: str) -> Optional[Message]:
        """Request health report from a node."""
        return self.request(
            msg_type=MessageType.HEALTH_CHECK,
            payload={},
            recipient=node,
            timeout=10.0,
        )

    def shutdown_node(self, node: str) -> Message:
        """Tell a node to shut down gracefully."""
        return self.publish(
            msg_type=MessageType.SHUTDOWN,
            payload={},
            recipient=node,
            priority=MessagePriority.CRITICAL,
        )

    def reload_config(self, node: Optional[str] = None) -> Message:
        """Tell node(s) to reload configuration."""
        return self.publish(
            msg_type=MessageType.RELOAD_CONFIG,
            payload={},
            recipient=node,  # None = broadcast
            priority=MessagePriority.HIGH,
        )

    # ── Lifecycle ──────────────────────────────────────────────────

    def close(self):
        """Shut down the bus."""
        if hasattr(self.backend, "stop"):
            self.backend.stop()
        console.print("[dim]🚌 Communication bus closed[/dim]")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()