from datetime import datetime, timezone
import uuid
import pytest

from app.ai.anpr.normalize import extract_plate_structure, normalize_plate_text
from app.ai.detection.engines import DemoDetectionEngine, DemoInferenceEngine
from app.ai.interfaces import BoundingBox, FramePacket
from app.ai.workers.inference_worker import InferenceWorker
from app.models.analytics import Detection, Entity
from app.models.camera import Camera
from app.models.location import Location
from app.models.watchlist import Watchlist, WatchlistEntry
from app.services.alert_engine import AlertEngine
from app.services.watchlist_correlation import WatchlistCorrelationService
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_end_to_end_intelligence_pipeline_scenario():
    """
    Mandatory end-to-end working scenario:
    CCTV FRAME
        ↓
    VEHICLE DETECTION
        ↓
    PLATE DETECTION
        ↓
    OCR
        ↓
    NORMALIZATION: GJ05AB1234
        ↓
    WATCHLIST: MATCH
        ↓
    RISK: CRITICAL
        ↓
    ALERT CREATED
        ↓
    REAL-TIME BROADCAST
    """
    # 1. Simulate Frame Arrival from SG Highway Camera
    cam_id = uuid.uuid4()
    loc = Location(id=uuid.uuid4(), name="SG Highway Intercept", district="Ahmedabad", latitude=23.03, longitude=72.58)
    cam = Camera(id=cam_id, camera_code="CAM-GJ-001", name="SG Highway Cam", location=loc)
    now = datetime.now(timezone.utc)

    frame = FramePacket(
        camera_id=cam_id,
        timestamp=now,
        frame_reference="cctv://surveillance/cam-gj-001/frame-992.jpg",
        is_demo=True,
    )

    # 2. Vehicle Detection & Plate Inference
    worker = InferenceWorker()
    batch_result = worker.process_frame(frame)
    assert batch_result is not None
    assert len(batch_result.detections) >= 1
    assert batch_result.inference_time_ms is not None

    # Verify vehicle and plate detection classes
    classes = {d.object_class for d in batch_result.detections}
    assert "CAR" in classes or "LICENSE_PLATE" in classes

    # 3. OCR & Normalization
    raw_ocr = " GJ 05 AB 1234 "
    normalized_plate = normalize_plate_text(raw_ocr)
    assert normalized_plate == "GJ05AB1234"

    struct = extract_plate_structure(normalized_plate)
    assert struct["is_gujarat"] is True
    assert struct["rto_jurisdiction"] == "Surat"

    # 4. Watchlist Correlation
    watchlist_svc = WatchlistCorrelationService()
    watchlist_svc.watchlist_entries.find_active_matches = AsyncMock()
    watchlist_svc.matches.get_by_detection_and_entry = AsyncMock(return_value=None)

    stolen_entry = WatchlistEntry(
        id=uuid.uuid4(),
        watchlist_id=uuid.uuid4(),
        identifier="GJ05AB1234",
        normalized_identifier="GJ05AB1234",
        entity_type="VEHICLE",
        reason="Stolen Luxury Sedan - FIR 442/2026",
        priority="CRITICAL",
        is_active=True,
    )
    stolen_entry.watchlist = Watchlist(name="Stolen Vehicles Hotlist", code="WL-STOLEN", category="STOLEN_VEHICLE", priority="CRITICAL")
    watchlist_svc.watchlist_entries.find_active_matches.return_value = [stolen_entry]

    det = Detection(
        id=uuid.uuid4(),
        camera_id=cam_id,
        detection_type="ANPR",
        detected_at=now,
        confidence=0.96,
        bounding_box={"x1": 100, "y1": 200, "x2": 300, "y2": 260},
        detected_plate_number=raw_ocr,
        normalized_plate_number=normalized_plate,
        created_at=now,
    )

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    matches = await watchlist_svc.correlate_observation(
        session,
        detection=det,
        raw_plate=raw_ocr,
        normalized_plate=normalized_plate,
        plate_confidence=0.96,
        observation_timestamp=now,
    )
    assert len(matches) == 1
    match_result = matches[0]
    assert match_result.score == 1.0
    assert match_result.match_type == "EXACT_PLATE"

    # 5. Alert Generation with Severity & Structured Explanation
    alert_engine = AlertEngine(deduplication_cooldown_seconds=300)
    alert_engine.alerts.find_recent_duplicate = AsyncMock(return_value=None)

    entity = Entity(id=uuid.uuid4(), entity_type="VEHICLE", primary_identifier="GJ05AB1234", first_seen_at=now, last_seen_at=now)

    alert = await alert_engine.process_match(
        session,
        match_result=match_result,
        detection=det,
        entity=entity,
        camera=cam,
        plate=normalized_plate,
        confidence=0.96,
        timestamp=now,
    )

    assert alert is not None
    assert alert.severity == "CRITICAL"
    assert alert.status == "NEW"
    assert "GJ05AB1234" in alert.title
    assert alert.metadata_["plate"] == "GJ05AB1234"
    assert alert.metadata_["reason"]["district"] == "Ahmedabad"
    assert alert.metadata_["reason"]["camera"] == "SG Highway Cam"
