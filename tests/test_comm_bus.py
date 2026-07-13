"""Tests for Mothership Communication Bus."""

import pytest
from src.hiveos.mothership.communication_bus import (
    CommunicationBus,
    InMemoryBusBackend,
    Message,
    MessagePriority,
    MessageType,
)


@pytest.fixture
def bus():
    backend = InMemoryBusBackend()
    bus = CommunicationBus(backend=backend, node_id="test-mothership")
    return bus


class TestMessage:
    """Message dataclass tests."""

    def test_message_creation(self):
        msg = Message(
            type=MessageType.HEARTBEAT,
            sender="node-a",
            recipient="mothership",
            payload={"load": 5},
        )
        assert msg.type == MessageType.HEARTBEAT
        assert msg.sender == "node-a"
        assert msg.recipient == "mothership"
        assert msg.payload["load"] == 5
        assert msg.message_id is not None

    def test_message_to_dict(self):
        msg = Message(
            type=MessageType.TASK_ASSIGN,
            sender="mothership",
            recipient="node-a",
            payload={"task_id": "t1"},
        )
        d = msg.to_dict()
        assert d["type"] == "task_assign"
        assert d["sender"] == "mothership"
        assert d["payload"]["task_id"] == "t1"

    def test_message_from_dict(self):
        data = {
            "type": "heartbeat",
            "sender": "node-b",
            "recipient": "mothership",
            "payload": {},
            "message_id": "abc123",
        }
        msg = Message.from_dict(data)
        assert msg.type == MessageType.HEARTBEAT
        assert msg.message_id == "abc123"

    def test_message_is_for(self):
        msg = Message(
            type=MessageType.TASK_ASSIGN,
            sender="mothership",
            recipient="node-a",
        )
        assert msg.is_for("node-a") is True
        assert msg.is_for("node-b") is False

    def test_message_broadcast(self):
        msg = Message(
            type=MessageType.AGENT_BROADCAST,
            sender="node-a",
            recipient=None,
        )
        assert msg.is_for("node-a") is True
        assert msg.is_for("anyone") is True

    def test_message_not_expired(self):
        msg = Message(
            type=MessageType.HEARTBEAT,
            sender="node-a",
            ttl=3600,
        )
        assert msg.is_expired() is False

    def test_message_expired(self):
        msg = Message(
            type=MessageType.HEARTBEAT,
            sender="node-a",
            timestamp="2000-01-01T00:00:00",
            ttl=1,
        )
        assert msg.is_expired() is True

    def test_message_priority(self):
        low = Message(
            type=MessageType.TASK_PROGRESS,
            sender="node-a",
            priority=MessagePriority.LOW,
        )
        high = Message(
            type=MessageType.TASK_ASSIGN,
            sender="mothership",
            priority=MessagePriority.HIGH,
        )
        assert high.priority.value > low.priority.value


class TestInMemoryBusBackend:
    """In-memory bus backend tests."""

    def test_subscribe_and_publish(self):
        backend = InMemoryBusBackend()
        received = []
        backend.subscribe(
            subscriber_id="listener",
            message_types=[MessageType.HEARTBEAT],
            callback=lambda msg: received.append(msg),
        )
        msg = Message(type=MessageType.HEARTBEAT, sender="node-a")
        backend.publish(msg)
        assert len(received) > 0

    def test_unsubscribe(self):
        backend = InMemoryBusBackend()
        def cb(msg):
            pass
        backend.subscribe(
            subscriber_id="to-remove",
            message_types=[MessageType.HEARTBEAT],
            callback=cb,
        )
        removed = backend.unsubscribe("to-remove")
        assert removed == 1

    def test_filter_function(self):
        backend = InMemoryBusBackend()
        received = []
        backend.subscribe(
            subscriber_id="filtered",
            message_types=[MessageType.AGENT_MESSAGE],
            callback=lambda msg: received.append(msg),
            filter_fn=lambda msg: msg.recipient == "filtered",
        )
        # This should NOT be delivered (wrong recipient)
        msg1 = Message(
            type=MessageType.AGENT_MESSAGE,
            sender="node-a",
            recipient="other",
        )
        backend.publish(msg1)
        # This SHOULD be delivered
        msg2 = Message(
            type=MessageType.AGENT_MESSAGE,
            sender="node-a",
            recipient="filtered",
        )
        backend.publish(msg2)
        # Only the targeted message should be delivered
        assert len(received) == 1


class TestCommunicationBus:
    """High-level CommunicationBus tests."""

    def test_publish_and_receive(self, bus):
        """Test basic publish and receive."""
        received = []
        bus.subscribe(
            message_types=[MessageType.TASK_ASSIGN],
            callback=lambda msg: received.append(msg),
        )
        bus.publish(
            msg_type=MessageType.TASK_ASSIGN,
            payload={"task_id": "t1"},
            recipient="test-mothership",
        )
        assert len(received) > 0

    def test_assign_task(self, bus):
        """Test task assignment helper."""
        received = []
        bus.subscribe(
            message_types=[MessageType.TASK_ASSIGN],
            callback=lambda msg: received.append(msg),
        )
        # Subscribe as the intended recipient too
        bus2 = CommunicationBus(backend=bus.backend, node_id="node-a")
        bus2.subscribe(
            message_types=[MessageType.TASK_ASSIGN],
            callback=lambda msg: received.append(msg),
        )
        message = bus.assign_task(
            node="node-a",
            task_id="task-001",
            agent_id="researcher",
            capability="web-search",
            input_data={"query": "test"},
        )
        assert message.type == MessageType.TASK_ASSIGN
        assert message.payload["task_id"] == "task-001"
        assert message.payload["capability"] == "web-search"
        assert len(received) > 0

    def test_task_complete(self, bus):
        """Test task completion helper."""
        received = []
        bus.subscribe(
            message_types=[MessageType.TASK_COMPLETE],
            callback=lambda msg: received.append(msg),
        )
        message = bus.task_complete(
            node="node-a",
            task_id="task-001",
            output={"result": "done"},
            success=True,
        )
        assert message.type == MessageType.TASK_COMPLETE
        assert message.payload["success"] is True
        assert len(received) > 0

    def test_task_failed(self, bus):
        """Test task failure helper."""
        received = []
        bus.subscribe(
            message_types=[MessageType.TASK_FAILED],
            callback=lambda msg: received.append(msg),
        )
        message = bus.task_complete(
            node="node-a",
            task_id="task-001",
            output={},
            success=False,
        )
        assert message.type == MessageType.TASK_FAILED
        assert len(received) > 0

    def test_broadcast(self, bus):
        """Test broadcast message."""
        received = []
        bus.subscribe(
            message_types=[MessageType.SHUTDOWN],
            callback=lambda msg: received.append(msg),
        )
        bus.broadcast(
            msg_type=MessageType.SHUTDOWN,
            payload={"reason": "maintenance"},
        )
        assert len(received) > 0

    def test_send_heartbeat(self, bus):
        """Test heartbeat helper."""
        message = bus.send_heartbeat(load=3, capabilities=["web", "research"])
        assert message.type == MessageType.HEARTBEAT
        assert message.payload["load"] == 3

    def test_send_sync_push(self, bus):
        """Test sync push helper."""
        message = bus.publish(
            msg_type=MessageType.SYNC_PUSH,
            payload={"skills": ["arxiv", "web-search"]},
            recipient="node-a",
        )
        assert message.type == MessageType.SYNC_PUSH
        assert message.payload["skills"] == ["arxiv", "web-search"]

    def test_close_doesnt_crash(self, bus):
        """Closing the bus should not throw."""
        bus.close()

    def test_context_manager(self):
        """Bus can be used as context manager."""
        with CommunicationBus(backend=InMemoryBusBackend()) as b:
            b.publish(msg_type=MessageType.HEARTBEAT, payload={})
