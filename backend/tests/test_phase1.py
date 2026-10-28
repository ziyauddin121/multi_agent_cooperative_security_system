"""
MACSS — Phase 1 Tests
=====================
Tests the project skeleton:
  1. Settings load correctly
  2. Message schema validates correctly
  3. Redis Blackboard connects and publishes/reads
  4. Consumer groups are created

Run with:  pytest backend/tests/test_phase1.py -v
(Redis must be running — use Docker: docker run -p 6379:6379 redis:7-alpine)
"""
import asyncio
import pytest
from datetime import datetime, timezone

# ── Settings ────────────────────────────────────────────────────

def test_settings_load():
    """Settings module loads without errors."""
    from app.config import settings
    assert settings.redis_host is not None
    assert settings.redis_port == 6379
    assert settings.stream_events == "security:events"
    assert settings.stream_alerts == "security:alerts"
    print(f"\n✓ Settings loaded: redis={settings.redis_host}:{settings.redis_port}")


# ── Message Schema ───────────────────────────────────────────────

def test_sensor_event_schema():
    """SensorEvent validates and serializes correctly."""
    from app.schemas.messages import SensorEvent, EventType
    event = SensorEvent(
        event_type=EventType.HIGH_TRAFFIC_RATE,
        source="host-01",
        target="service-01",
        payload={"request_rate": 9500, "normal_rate": 500},
        simulation_phase="phase-1",
        is_attack=True,
    )
    assert event.event_id.startswith("evt-")
    assert event.timestamp is not None
    assert event.payload["request_rate"] == 9500

    # Serialize to Redis dict
    rd = event.to_redis_dict()
    assert "event_id" in rd
    assert "event_type" in rd
    print(f"\n✓ SensorEvent created: {event.event_id}")


def test_alert_message_schema():
    """AlertMessage validates confidence range and required fields."""
    from app.schemas.messages import (
        AlertMessage, EventType, Severity, ActionType
    )
    alert = AlertMessage(
        agent_id="perimeter-agent",
        event_type=EventType.DDOS_SUSPECTED,
        severity=Severity.HIGH,
        confidence=0.91,
        source="host-01",
        target="service-01",
        evidence={"request_rate": 9500},
        recommended_action=ActionType.RATE_LIMIT,
    )
    assert alert.message_id.startswith("msg-")
    assert alert.confidence == 0.91
    assert alert.severity == Severity.HIGH

    # Test invalid confidence
    with pytest.raises(Exception):
        AlertMessage(
            agent_id="perimeter-agent",
            event_type=EventType.DDOS_SUSPECTED,
            severity=Severity.HIGH,
            confidence=1.5,    # invalid: > 1.0
            source="h1",
            target="s1",
        )
    print(f"\n✓ AlertMessage validates correctly: {alert.message_id}")


def test_decision_message_schema():
    """DecisionMessage with conflict entries serializes correctly."""
    from app.schemas.messages import (
        DecisionMessage, ConflictEntry, ActionType, Severity
    )
    decision = DecisionMessage(
        agent_id="coordinator-agent",
        incident_id="INC-001",
        selected_action=ActionType.ISOLATE_ENDPOINT,
        severity=Severity.CRITICAL,
        confidence=0.94,
        reason="Two agents classified CRITICAL; forensic evidence supports endpoint compromise.",
        conflicting_recommendations=[
            ConflictEntry(
                agent_id="perimeter-agent",
                recommended_action=ActionType.RATE_LIMIT,
                severity=Severity.HIGH,
                confidence=0.91,
            ),
            ConflictEntry(
                agent_id="endpoint-agent",
                recommended_action=ActionType.ISOLATE_ENDPOINT,
                severity=Severity.CRITICAL,
                confidence=0.87,
            ),
        ],
        affected_hosts=["host-02"],
    )
    assert decision.selected_action == ActionType.ISOLATE_ENDPOINT
    assert len(decision.conflicting_recommendations) == 2
    print(f"\n✓ DecisionMessage with conflicts: {decision.message_id}")


def test_message_serialization_roundtrip():
    """A message serialized to Redis dict and back should be identical."""
    from app.schemas.messages import AlertMessage, EventType, Severity, ActionType
    alert = AlertMessage(
        agent_id="endpoint-agent",
        event_type=EventType.FILE_RENAME_SPIKE,
        severity=Severity.CRITICAL,
        confidence=0.87,
        source="host-02",
        target="host-02",
        evidence={"rename_count": 500},
        recommended_action=ActionType.ISOLATE_ENDPOINT,
    )
    rd = alert.to_redis_dict()
    restored = AlertMessage.from_redis_dict(rd)
    assert restored.message_id == alert.message_id
    assert restored.confidence == alert.confidence
    assert restored.severity == alert.severity
    print(f"\n✓ Serialization roundtrip OK: {alert.message_id}")


# ── Redis Blackboard (requires Redis running) ────────────────────

@pytest.mark.asyncio
async def test_blackboard_connect():
    """Blackboard connects to Redis successfully."""
    from app.blackboard import Blackboard
    bb = Blackboard()
    try:
        await bb.connect()
        assert await bb.health_check() is True
        print("\n✓ Blackboard connected to Redis")
    finally:
        await bb.disconnect()


@pytest.mark.asyncio
async def test_blackboard_publish_and_read_event():
    """Publish a SensorEvent and read it back from the stream."""
    from app.blackboard import Blackboard
    from app.schemas.messages import SensorEvent, EventType
    from app.config import settings

    bb = Blackboard()
    await bb.connect()

    try:
        # Ensure consumer group exists
        group = "test_group_events"
        consumer = "test_consumer"
        await bb.ensure_consumer_group(settings.stream_events, group)

        event = SensorEvent(
            event_type=EventType.HIGH_TRAFFIC_RATE,
            source="test-host",
            target="test-service",
            payload={"request_rate": 9500},
        )
        entry_id = await bb.publish_event(event)
        assert entry_id is not None

        # Read back
        entries = await bb.read_stream(
            settings.stream_events, group, consumer, count=200, block_ms=500
        )
        assert len(entries) >= 1
        found = any(data.get("event_type") == EventType.HIGH_TRAFFIC_RATE.value for _, data in entries)
        assert found, "Published event not found in stream"

        print(f"\n✓ Event published and read: {entry_id}")
    finally:
        await bb.disconnect()


@pytest.mark.asyncio
async def test_blackboard_publish_and_read_alert():
    """Publish an AlertMessage and read it from the stream."""
    from app.blackboard import Blackboard
    from app.schemas.messages import AlertMessage, EventType, Severity, ActionType
    from app.config import settings

    bb = Blackboard()
    await bb.connect()

    try:
        group = "test_group_alerts"
        consumer = "test_consumer"
        await bb.ensure_consumer_group(settings.stream_alerts, group)

        alert = AlertMessage(
            agent_id="perimeter-agent",
            event_type=EventType.DDOS_SUSPECTED,
            severity=Severity.HIGH,
            confidence=0.91,
            source="host-01",
            target="service-01",
            evidence={"request_rate": 9500},
            recommended_action=ActionType.RATE_LIMIT,
        )
        entry_id = await bb.publish_alert(alert)
        assert entry_id is not None

        entries = await bb.read_stream(
            settings.stream_alerts, group, consumer, count=10, block_ms=500
        )
        assert len(entries) >= 1
        eid, data = entries[0]
        assert data["agent_id"] == "perimeter-agent"
        await bb.ack(settings.stream_alerts, group, eid)

        print(f"\n✓ Alert published and read: {entry_id}")
    finally:
        await bb.disconnect()


@pytest.mark.asyncio
async def test_agent_status_hash():
    """Agent status can be written and read from Redis hash."""
    from app.blackboard import Blackboard

    bb = Blackboard()
    await bb.connect()

    try:
        await bb.set_agent_status("test-agent", {
            "agent_id": "test-agent",
            "status": "running",
            "alerts_published": 5,
            "uptime_seconds": 30.0,
        })
        status = await bb.get_agent_status("test-agent")
        assert status["status"] == "running"
        assert status["agent_id"] == "test-agent"
        print(f"\n✓ Agent status hash OK: {status}")
    finally:
        await bb.disconnect()


@pytest.mark.asyncio
async def test_simulation_state_hash():
    """Simulation state can be written and read from Redis hash."""
    from app.blackboard import Blackboard

    bb = Blackboard()
    await bb.connect()

    try:
        state = {
            "phase": "ddos",
            "start_time": "2026-10-28T10:00:00Z",
            "active": True,
            "experiment_id": "exp-test",
        }
        await bb.set_simulation_state(state)
        result = await bb.get_simulation_state()
        assert result["phase"] == "ddos"
        assert result["active"] is True
        print(f"\n✓ Simulation state hash OK: {result}")
    finally:
        await bb.disconnect()
