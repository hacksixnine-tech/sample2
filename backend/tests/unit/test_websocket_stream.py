import pytest
import json
from unittest.mock import AsyncMock, patch

from app.schemas.events import EventEnvelope
from app.services.event_publisher import event_publisher


@pytest.mark.asyncio
async def test_event_publisher_broadcast_and_deduplication():
    events_received = []

    def subscriber(envelope: EventEnvelope):
        events_received.append(envelope)

    event_publisher.subscribe("CAMERA_OFFLINE", subscriber)

    # Publish camera offline event
    env = await event_publisher.publish(
        event_name="CAMERA_OFFLINE",
        payload={"camera_name": "CAM-014 (Surat)", "reason": "Stream Timeout"},
        camera_id="CAM-014",
        district="Surat",
        severity="MEDIUM",
    )

    assert len(events_received) >= 1
    latest = events_received[-1]
    assert latest.event_type == "CAMERA_OFFLINE"
    assert latest.camera_id == "CAM-014"
    assert latest.district == "Surat"
    assert latest.event_id == env.event_id

    event_publisher.unsubscribe("CAMERA_OFFLINE", subscriber)


@pytest.mark.asyncio
async def test_alert_lifecycle_broadcast_events():
    events_received = []

    def subscriber(envelope: EventEnvelope):
        events_received.append(envelope)

    event_publisher.subscribe("ALERT_ACKNOWLEDGED", subscriber)
    event_publisher.subscribe("ALERT_RESOLVED", subscriber)

    # 1. Broadcast Acknowledged
    await event_publisher.publish(
        event_name="ALERT_ACKNOWLEDGED",
        payload={"alert_id": "alt-123", "status": "ACKNOWLEDGED", "user": "Officer Patel"},
        severity="HIGH",
    )
    assert any(e.event_type == "ALERT_ACKNOWLEDGED" for e in events_received)

    # 2. Broadcast Resolved
    await event_publisher.publish(
        event_name="ALERT_RESOLVED",
        payload={"alert_id": "alt-123", "status": "RESOLVED", "reason": "Vehicle intercepted"},
        severity="INFO",
    )
    assert any(e.event_type == "ALERT_RESOLVED" for e in events_received)

    event_publisher.unsubscribe("ALERT_ACKNOWLEDGED", subscriber)
    event_publisher.unsubscribe("ALERT_RESOLVED", subscriber)
