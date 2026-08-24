import pytest
from datetime import datetime, timezone, timedelta
import uuid

from app.schemas.events import EventEnvelope, EventType, HistoricalEventsResponse
from app.services.event_publisher import InMemoryEventPublisher


def test_event_envelope_creation():
    env = EventEnvelope(
        event_type="WATCHLIST_MATCH",
        source="anpr-engine",
        camera_id="CAM-021",
        district="Vadodara",
        severity="CRITICAL",
        entity_type="vehicle",
        entity_id="GJ05AB1234",
        payload={"confidence": 0.98, "plate": "GJ05AB1234"},
    )
    assert env.event_id is not None
    assert env.event_type == "WATCHLIST_MATCH"
    assert env.severity == "CRITICAL"
    assert env.entity_id == "GJ05AB1234"
    assert env.payload["confidence"] == 0.98


@pytest.mark.asyncio
async def test_in_memory_event_publisher_routing():
    publisher = InMemoryEventPublisher(max_history=50)
    received_events = []

    def subscriber(envelope: EventEnvelope):
        received_events.append(envelope)

    publisher.subscribe("ALERT_CREATED", subscriber)
    publisher.subscribe("WATCHLIST_MATCH", subscriber)

    # 1. Publish matching event
    env1 = await publisher.publish(
        event_name="ALERT_CREATED",
        payload={"alert_code": "ALT-2026-001", "title": "Suspect Vehicle"},
        severity="HIGH",
        camera_id="CAM-001",
    )
    assert len(received_events) == 1
    assert received_events[0].event_type == "ALERT_CREATED"
    assert received_events[0].event_id == env1.event_id

    # 2. Publish second matching event
    env2 = await publisher.publish(
        event_name="WATCHLIST_MATCH",
        payload={"plate_number": "GJ01TEST001"},
        severity="CRITICAL",
    )
    assert len(received_events) == 2
    assert received_events[1].event_type == "WATCHLIST_MATCH"

    # 3. Publish non-subscribed event (should not trigger callback)
    await publisher.publish(
        event_name="SYSTEM_HEALTH_CHANGED",
        payload={"status": "DEGRADED"},
    )
    assert len(received_events) == 2  # Still 2


@pytest.mark.asyncio
async def test_historical_event_ring_buffer_and_recovery():
    publisher = InMemoryEventPublisher(max_history=5)

    for i in range(10):
        await publisher.publish(
            event_name="ANPR_DETECTED",
            payload={"sequence": i, "plate": f"GJ0{i}AB1234"},
        )

    # Ring buffer capped at max_history=5
    history = publisher.get_history(limit=10)
    assert len(history) == 5
    assert history[-1].payload["sequence"] == 9
    assert history[0].payload["sequence"] == 5

    # Filter by since_timestamp
    recent_since = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    recent_history = publisher.get_history(since_timestamp=recent_since)
    assert len(recent_history) == 5
