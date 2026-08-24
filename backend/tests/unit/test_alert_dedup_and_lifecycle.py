from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.models.alert import Alert
from app.models.analytics import Detection, Entity
from app.models.camera import Camera
from app.models.location import Location
from app.models.match import Match
from app.models.watchlist import Watchlist, WatchlistEntry
from app.services.alert_engine import AlertEngine, AlertPolicyEngine
from app.services.event_publisher import event_publisher
from app.services.watchlist_correlation import MatchResult
from app.schemas.alert import VALID_STATE_TRANSITIONS


def test_alert_severity_calculation():
    # Critical priority with high match score -> CRITICAL
    assert AlertPolicyEngine.calculate_severity("CRITICAL", 1.0, 0.95) == "CRITICAL"
    assert AlertPolicyEngine.calculate_severity("CRITICAL", 0.92, 0.90) == "CRITICAL"

    # High priority -> HIGH
    assert AlertPolicyEngine.calculate_severity("HIGH", 1.0, 0.90) == "HIGH"
    
    # Critical with lower match score falls back to HIGH
    assert AlertPolicyEngine.calculate_severity("CRITICAL", 0.80, 0.85) == "HIGH"

    # Medium priority -> MEDIUM
    assert AlertPolicyEngine.calculate_severity("MEDIUM", 1.0, 0.90) == "MEDIUM"

    # Low / Info priority -> LOW
    assert AlertPolicyEngine.calculate_severity("LOW", 1.0, 0.90) == "LOW"
    assert AlertPolicyEngine.calculate_severity("UNKNOWN", 0.5, 0.5) == "LOW"


def test_alert_state_transitions_machine():
    assert "ACKNOWLEDGED" in VALID_STATE_TRANSITIONS["NEW"]
    assert "DISMISSED" in VALID_STATE_TRANSITIONS["NEW"]
    assert "INVESTIGATING" in VALID_STATE_TRANSITIONS["NEW"]
    
    assert "RESOLVED" in VALID_STATE_TRANSITIONS["ACKNOWLEDGED"]
    assert "INVESTIGATING" in VALID_STATE_TRANSITIONS["ACKNOWLEDGED"]
    
    # RESOLVED and DISMISSED are terminal states
    assert VALID_STATE_TRANSITIONS["RESOLVED"] == set()
    assert VALID_STATE_TRANSITIONS["DISMISSED"] == set()


@pytest.mark.asyncio
async def test_alert_deduplication_cooldown():
    engine = AlertEngine(deduplication_cooldown_seconds=300)
    engine.alerts.find_recent_duplicate = AsyncMock()

    now = datetime.now(timezone.utc)
    cam_id = uuid.uuid4()
    ent_id = uuid.uuid4()

    loc = Location(id=uuid.uuid4(), name="SG Highway", district="Ahmedabad", latitude=23.03, longitude=72.58)
    cam = Camera(id=cam_id, camera_code="CAM-001", name="SG Highway Cam 01", location=loc)
    det = Detection(id=uuid.uuid4(), camera_id=cam_id, detection_type="ANPR", detected_at=now, confidence=0.95, bounding_box={})
    entity = Entity(id=ent_id, entity_type="VEHICLE", primary_identifier="GJ01TEST001", first_seen_at=now, last_seen_at=now)

    entry = WatchlistEntry(
        id=uuid.uuid4(),
        watchlist_id=uuid.uuid4(),
        identifier="GJ01TEST001",
        normalized_identifier="GJ01TEST001",
        entity_type="VEHICLE",
        reason="Stolen Car",
        priority="CRITICAL",
        is_active=True,
    )
    entry.watchlist = Watchlist(name="Stolen Car Hotlist", code="WL-01", category="STOLEN_VEHICLE", priority="CRITICAL")

    match = Match(id=uuid.uuid4(), detection_id=det.id, watchlist_entry_id=entry.id, match_score=1.0)
    match_result = MatchResult(match=match, watchlist_entry=entry, match_type="EXACT_PLATE", score=1.0, explanation="Exact hit")

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    # 1. First sight: No duplicate -> creates alert
    engine.alerts.find_recent_duplicate.return_value = None
    created_alert = await engine.process_match(
        session,
        match_result=match_result,
        detection=det,
        entity=entity,
        camera=cam,
        plate="GJ01TEST001",
        confidence=0.95,
        timestamp=now,
    )
    assert created_alert is not None
    assert created_alert.severity == "CRITICAL"
    assert created_alert.status == "NEW"

    # 2. Subsequent frame within 300s: Duplicate detected -> suppressed (returns None)
    existing_alert = Alert(id=uuid.uuid4(), alert_code="ALT-2026-PREV", status="NEW")
    engine.alerts.find_recent_duplicate.return_value = existing_alert

    suppressed = await engine.process_match(
        session,
        match_result=match_result,
        detection=det,
        entity=entity,
        camera=cam,
        plate="GJ01TEST001",
        confidence=0.95,
        timestamp=now + timedelta(seconds=10),
    )
    assert suppressed is None
