from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest

from app.models.alert import Alert
from app.models.analytics import Detection, Entity, Evidence, Vehicle, VehicleObservation
from app.models.camera import Camera
from app.models.incident import Incident
from app.models.location import Location
from app.schemas.investigation import (
    CameraInvestigationContext,
    DetectionClassificationResponse,
    DistrictInvestigationContext,
    EvidenceVerificationResponse,
    ForensicReportResponse,
    InvestigationSearchResult,
    InvestigationTimelineResponse,
    VehicleInvestigationDossier,
    VehicleRouteResponse,
    VehicleSummaryResponse,
)
from app.services.investigation_service import InvestigationService


@pytest.mark.asyncio
async def test_multi_source_investigation_search():
    """Verify multi-criteria search safely normalizes plates and queries across entities."""
    service = InvestigationService()
    session = AsyncMock()

    veh_id = uuid.uuid4()
    t0 = datetime(2026, 8, 23, 10, 0, 0, tzinfo=timezone.utc)
    mock_entity = Entity(id=veh_id, first_seen_at=t0, last_seen_at=t0, total_sightings=3)
    mock_vehicle = Vehicle(
        id=veh_id,
        normalized_plate="GJ05AB1234",
        raw_plate="gj 05 ab 1234",
        vehicle_type="CAR",
    )
    mock_vehicle.entity = mock_entity

    service.vehicles.get_by_plate = AsyncMock(return_value=mock_vehicle)
    service.observations.search_observations = AsyncMock(return_value=[])
    service.alerts.list_filtered = AsyncMock(return_value=([], 0))
    service.incidents.list_filtered = AsyncMock(return_value=([], 0))
    service.audit.log_action = AsyncMock()

    res = await service.search(session, plate="  gj 05 ab 1234  ", district="Surat")
    assert isinstance(res, InvestigationSearchResult)
    assert res.query["normalized_plate"] == "GJ05AB1234"
    assert res.total_vehicles == 1
    assert res.vehicles[0]["normalized_plate"] == "GJ05AB1234"


@pytest.mark.asyncio
async def test_detection_classification_false_positive_workflow():
    """Verify classification does not mutate raw detection, only updates metadata and audits."""
    service = InvestigationService()
    session = AsyncMock()

    det_id = uuid.uuid4()
    mock_det = Detection(
        id=det_id,
        camera_id=uuid.uuid4(),
        detection_type="ANPR",
        confidence=0.92,
        detected_at=datetime.now(timezone.utc),
        metadata_={"raw_text": "GJ05AB1234"},
    )
    service.detections.get_by_id = AsyncMock(return_value=mock_det)
    service.observations.get_by_id = AsyncMock(return_value=None)
    service.audit.log_action = AsyncMock()

    user_id = uuid.uuid4()
    resp = await service.classify_detection(
        session,
        detection_id=det_id,
        classification="CONFIRMED",
        notes="Matches silver Creta in FIR #104",
        user_id=user_id,
    )

    assert isinstance(resp, DetectionClassificationResponse)
    assert resp.classification == "CONFIRMED"
    assert resp.notes == "Matches silver Creta in FIR #104"
    assert mock_det.metadata_["review_classification"] == "CONFIRMED"
    assert mock_det.metadata_["reviewed_by"] == str(user_id)


@pytest.mark.asyncio
async def test_evidence_cryptographic_integrity_verification():
    """Verify SHA-256 integrity verification against the recorded hash."""
    service = InvestigationService()
    session = AsyncMock()

    ev_id = uuid.uuid4()
    sha_val = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    mock_ev = Evidence(
        id=ev_id,
        evidence_code="EVD-2026-001",
        evidence_type="FRAME_CROP",
        object_key="frames/cam014_crop.jpg",
        file_format="JPEG",
        file_hash_sha256=sha_val,
        captured_at=datetime.now(timezone.utc),
        camera_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        metadata_={},
    )
    service.evidence.get_by_id = AsyncMock(return_value=mock_ev)
    service.audit.log_action = AsyncMock()

    resp = await service.verify_evidence_integrity(session, ev_id)
    assert isinstance(resp, EvidenceVerificationResponse)
    assert resp.status == "INTEGRITY_VERIFIED"
    assert resp.sha256_hash == sha_val


@pytest.mark.asyncio
async def test_certified_forensic_report_generation():
    """Verify complete certified forensic report with cryptographic seal."""
    service = InvestigationService()
    session = AsyncMock()

    veh_id = uuid.uuid4()
    t0 = datetime(2026, 8, 23, 10, 0, 0, tzinfo=timezone.utc)
    mock_entity = Entity(id=veh_id, first_seen_at=t0, last_seen_at=t0, total_sightings=2)
    mock_vehicle = Vehicle(
        id=veh_id,
        normalized_plate="GJ05AB1234",
        raw_plate="GJ 05 AB 1234",
        vehicle_type="CAR",
        make="Hyundai",
        model="Creta",
        color="Silver",
    )
    mock_vehicle.entity = mock_entity

    service.vehicles.get_by_plate = AsyncMock(return_value=mock_vehicle)
    service.vehicles.get_with_entity = AsyncMock(return_value=mock_vehicle)
    service.observations.history_for_vehicle = AsyncMock(return_value=[])
    service.tracking.get_vehicle_summary = AsyncMock(
        return_value=VehicleSummaryResponse(
            vehicle_id=veh_id,
            normalized_plate="GJ05AB1234",
            raw_plate="GJ 05 AB 1234",
            vehicle_type="CAR",
            make="Hyundai",
            model="Creta",
            color="Silver",
            total_sightings=2,
            unique_cameras=2,
            unique_districts=1,
            watchlist_status="CLEAR",
        )
    )
    service.tracking.get_vehicle_route = AsyncMock(
        return_value=VehicleRouteResponse(
            vehicle_id=veh_id,
            normalized_plate="GJ05AB1234",
            point_count=2,
            points=[],
            anomalies_detected=[],
        )
    )
    service.audit.log_action = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalars.return_value.first.return_value = "Inspector_Patel"
    session.execute.return_value = mock_result

    user_id = uuid.uuid4()
    report = await service.generate_forensic_report(session, "GJ05AB1234", user_id=user_id)

    assert isinstance(report, ForensicReportResponse)
    assert report.vehicle.normalized_plate == "GJ05AB1234"
    assert report.sha256_report_checksum is not None
    assert len(report.sha256_report_checksum) == 64  # Valid SHA-256 hex string


@pytest.mark.asyncio
async def test_camera_and_district_investigation_context():
    """Verify camera and district intelligence context queries."""
    service = InvestigationService()
    session = AsyncMock()

    cam_id = uuid.uuid4()
    loc = Location(
        id=uuid.uuid4(),
        name="Varachha Junction",
        district="Surat",
        city="Surat",
        latitude=21.218,
        longitude=72.868,
    )
    mock_cam = Camera(
        id=cam_id,
        camera_code="CAM-SURAT-014",
        name="Ring Road Toll Plaza",
        status="ACTIVE",
        location=loc,
    )
    service.cameras.get_by_id = AsyncMock(return_value=mock_cam)
    service.observations.search_observations = AsyncMock(return_value=[])
    service.alerts.list_filtered = AsyncMock(return_value=([], 0))
    service.audit.log_action = AsyncMock()

    # 1. Camera Context
    cam_ctx = await service.get_camera_investigation_context(session, cam_id)
    assert isinstance(cam_ctx, CameraInvestigationContext)
    assert cam_ctx.camera_code == "CAM-SURAT-014"
    assert cam_ctx.district == "Surat"

    # 2. District Context
    dist_ctx = await service.get_district_investigation_context(session, "Surat")
    assert isinstance(dist_ctx, DistrictInvestigationContext)
    assert dist_ctx.district == "Surat"
