from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.models.analytics import Detection
from app.models.watchlist import Watchlist, WatchlistEntry
from app.services.watchlist_correlation import WatchlistCorrelationService


@pytest.mark.asyncio
async def test_watchlist_correlation_exact_match():
    svc = WatchlistCorrelationService()
    svc.watchlist_entries.find_active_matches = AsyncMock()
    svc.matches.get_by_detection_and_entry = AsyncMock(return_value=None)

    now = datetime.now(timezone.utc)
    entry = WatchlistEntry(
        id=uuid.uuid4(),
        watchlist_id=uuid.uuid4(),
        identifier="GJ01TEST001",
        normalized_identifier="GJ01TEST001",
        entity_type="VEHICLE",
        reason="Stolen vehicle in Ahmedabad",
        priority="CRITICAL",
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=30),
        is_active=True,
    )
    entry.watchlist = Watchlist(name="Stolen Vehicles Hotlist", code="WL-STOLEN", category="STOLEN_VEHICLE", priority="CRITICAL")

    svc.watchlist_entries.find_active_matches.return_value = [entry]

    det = Detection(
        id=uuid.uuid4(),
        camera_id=uuid.uuid4(),
        detection_type="ANPR",
        detected_at=now,
        confidence=0.96,
        bounding_box={"x1": 10, "y1": 10, "x2": 100, "y2": 50},
        detected_plate_number="GJ 01 TEST 001",
        normalized_plate_number="GJ01TEST001",
        created_at=now,
    )

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    results = await svc.correlate_observation(
        session,
        detection=det,
        raw_plate="GJ 01 TEST 001",
        normalized_plate="GJ01TEST001",
        plate_confidence=0.96,
        observation_timestamp=now,
    )

    assert len(results) == 1
    res = results[0]
    assert res.match_type == "EXACT_PLATE"
    assert res.score == 1.0
    assert res.watchlist_entry.normalized_identifier == "GJ01TEST001"
    assert "GJ01TEST001" in res.explanation
    assert res.to_dict()["priority"] == "CRITICAL"


@pytest.mark.asyncio
async def test_watchlist_correlation_no_match_returns_empty():
    svc = WatchlistCorrelationService()
    svc.watchlist_entries.find_active_matches = AsyncMock(return_value=[])

    now = datetime.now(timezone.utc)
    det = Detection(
        id=uuid.uuid4(),
        camera_id=uuid.uuid4(),
        detection_type="ANPR",
        detected_at=now,
        confidence=0.90,
        bounding_box={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
        detected_plate_number="GJ05CLEAN001",
        normalized_plate_number="GJ05CLEAN001",
        created_at=now,
    )

    session = AsyncMock()
    results = await svc.correlate_observation(
        session,
        detection=det,
        raw_plate="GJ05CLEAN001",
        normalized_plate="GJ05CLEAN001",
        plate_confidence=0.90,
    )
    assert len(results) == 0


@pytest.mark.asyncio
async def test_watchlist_correlation_handles_blank_or_invalid_plate():
    svc = WatchlistCorrelationService()
    session = AsyncMock()
    det = Detection(
        id=uuid.uuid4(),
        camera_id=uuid.uuid4(),
        detection_type="VEHICLE",
        detected_at=datetime.now(timezone.utc),
        confidence=0.85,
        bounding_box={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
        created_at=datetime.now(timezone.utc),
    )

    # Empty string or None plate should safely return []
    res_none = await svc.correlate_observation(session, detection=det, raw_plate=None, normalized_plate=None)
    assert res_none == []

    res_blank = await svc.correlate_observation(session, detection=det, raw_plate="", normalized_plate="")
    assert res_blank == []
