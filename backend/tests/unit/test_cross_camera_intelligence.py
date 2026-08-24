import pytest
from datetime import datetime, timezone, timedelta
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.tracking_service import TrackingService, haversine_distance_meters
from app.models.analytics import Vehicle, VehicleObservation, Entity
from app.models.camera import Camera
from app.models.location import Location
from app.schemas.investigation import VehicleMovementHistory, VehicleSummaryResponse


@pytest.mark.asyncio
async def test_dual_identifier_resolution():
    service = TrackingService()
    session = AsyncMock()

    veh_id = uuid.uuid4()
    mock_entity = Entity(id=veh_id, first_seen_at=datetime.now(timezone.utc), last_seen_at=datetime.now(timezone.utc), total_sightings=2)
    mock_vehicle = Vehicle(id=veh_id, normalized_plate="GJ05AB1234", raw_plate="GJ 05 AB 1234", vehicle_type="CAR")
    mock_vehicle.entity = mock_entity

    # 1. Resolve by UUID
    service.vehicles.get_with_entity = AsyncMock(return_value=mock_vehicle)
    res_by_uuid = await service._resolve_vehicle(session, veh_id)
    assert res_by_uuid.id == veh_id
    assert res_by_uuid.normalized_plate == "GJ05AB1234"

    # 2. Resolve by plate string
    service.vehicles.get_by_plate = AsyncMock(return_value=mock_vehicle)
    res_by_plate = await service._resolve_vehicle(session, "GJ 05 AB 1234")
    assert res_by_plate.id == veh_id
    assert res_by_plate.normalized_plate == "GJ05AB1234"


@pytest.mark.asyncio
async def test_chronological_ordering_asc_and_desc():
    service = TrackingService()
    session = AsyncMock()

    veh_id = uuid.uuid4()
    t0 = datetime(2026, 8, 23, 8, 42, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 8, 23, 8, 51, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 23, 9, 3, 0, tzinfo=timezone.utc)

    mock_entity = Entity(id=veh_id, first_seen_at=t0, last_seen_at=t2, total_sightings=3)
    mock_vehicle = Vehicle(id=veh_id, normalized_plate="GJ05AB1234", raw_plate="GJ 05 AB 1234", vehicle_type="CAR")
    mock_vehicle.entity = mock_entity

    cam1 = Camera(id=uuid.uuid4(), name="CAM-014 (Vadodara)")
    cam1.location = Location(district="Vadodara", latitude=22.30, longitude=73.18)
    cam2 = Camera(id=uuid.uuid4(), name="CAM-021 (Sayajigunj)")
    cam2.location = Location(district="Vadodara", latitude=22.31, longitude=73.19)
    cam3 = Camera(id=uuid.uuid4(), name="CAM-037 (Akota)")
    cam3.location = Location(district="Vadodara", latitude=22.32, longitude=73.20)

    obs1 = VehicleObservation(id=uuid.uuid4(), vehicle_id=veh_id, camera_id=cam1.id, observed_at=t0, plate_confidence=0.95, camera=cam1, location=cam1.location)
    obs2 = VehicleObservation(id=uuid.uuid4(), vehicle_id=veh_id, camera_id=cam2.id, observed_at=t1, plate_confidence=0.92, camera=cam2, location=cam2.location)
    obs3 = VehicleObservation(id=uuid.uuid4(), vehicle_id=veh_id, camera_id=cam3.id, observed_at=t2, plate_confidence=0.94, camera=cam3, location=cam3.location)

    service.vehicles.get_with_entity = AsyncMock(return_value=mock_vehicle)
    service.observations.history_for_vehicle = AsyncMock(return_value=[obs1, obs2, obs3])
    service.audit.log_action = AsyncMock()

    # Test Descending (Newest First)
    history_desc = await service.get_vehicle_history(session, veh_id, sort_order="desc")
    assert history_desc.sighting_count == 3
    assert history_desc.sort_order == "desc"
    assert history_desc.sightings[0].timestamp == t2
    assert history_desc.sightings[-1].timestamp == t0

    # Test Ascending (Oldest First for Route Reconstruction)
    history_asc = await service.get_vehicle_history(session, veh_id, sort_order="asc")
    assert history_asc.sighting_count == 3
    assert history_asc.sort_order == "asc"
    assert history_asc.sightings[0].timestamp == t0
    assert history_asc.sightings[-1].timestamp == t2


@pytest.mark.asyncio
async def test_vehicle_summary_analytics():
    service = TrackingService()
    session = AsyncMock()

    veh_id = uuid.uuid4()
    t0 = datetime(2026, 8, 23, 8, 42, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 8, 23, 9, 21, 0, tzinfo=timezone.utc)

    mock_entity = Entity(id=veh_id, first_seen_at=t0, last_seen_at=t1, total_sightings=2)
    mock_vehicle = Vehicle(
        id=veh_id,
        normalized_plate="GJ05AB1234",
        raw_plate="GJ 05 AB 1234",
        vehicle_type="CAR",
        make="Hyundai",
        model="Creta",
        color="Silver",
        metadata_={"is_demo": True},
    )
    mock_vehicle.entity = mock_entity

    cam1 = Camera(id=uuid.uuid4(), name="CAM-014")
    cam1.location = Location(district="Surat", latitude=21.20, longitude=72.85)
    cam2 = Camera(id=uuid.uuid4(), name="CAM-021")
    cam2.location = Location(district="Vadodara", latitude=22.30, longitude=73.18)

    obs1 = VehicleObservation(id=uuid.uuid4(), vehicle_id=veh_id, camera_id=cam1.id, observed_at=t0, plate_confidence=0.95, camera=cam1, location=cam1.location, metadata_={"matched_watchlist": True, "watchlist_type": "STOLEN_VEHICLE"})
    obs2 = VehicleObservation(id=uuid.uuid4(), vehicle_id=veh_id, camera_id=cam2.id, observed_at=t1, plate_confidence=0.92, camera=cam2, location=cam2.location, metadata_={})

    service.vehicles.get_by_plate = AsyncMock(return_value=mock_vehicle)
    service.vehicles.get_with_entity = AsyncMock(return_value=mock_vehicle)
    service.observations.history_for_vehicle = AsyncMock(return_value=[obs1, obs2])
    service.audit.log_action = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    summary = await service.get_vehicle_summary(session, "GJ05AB1234")
    assert isinstance(summary, VehicleSummaryResponse)
    assert summary.normalized_plate == "GJ05AB1234"
    assert summary.total_sightings == 2
    assert summary.unique_districts == 2
    assert summary.watchlist_status == "MATCH"
    assert summary.speed_disclaimer == "ESTIMATED AVERAGE SPEED BETWEEN CAMERAS"
