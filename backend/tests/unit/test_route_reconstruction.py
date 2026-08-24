import pytest
from datetime import datetime, timezone, timedelta
import uuid
from unittest.mock import AsyncMock

from app.services.tracking_service import TrackingService, haversine_distance_meters
from app.models.analytics import Vehicle, VehicleObservation, Entity
from app.models.camera import Camera
from app.models.location import Location
from app.schemas.investigation import VehicleRouteResponse


def test_haversine_distance():
    # Ahmedabad (23.0225, 72.5714) to Gandhinagar (23.2156, 72.6369) ~ 22.5 km
    dist = haversine_distance_meters(23.0225, 72.5714, 23.2156, 72.6369)
    assert 21000 < dist < 24000
    assert haversine_distance_meters(23.0, 72.0, 23.0, 72.0) == 0.0


@pytest.mark.asyncio
async def test_route_anomaly_detection_cloned_plate():
    service = TrackingService()
    session = AsyncMock()

    veh_id = uuid.uuid4()
    t0 = datetime(2026, 8, 23, 10, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(seconds=5)  # 5 seconds later in a completely different city!

    mock_entity = Entity(id=veh_id, first_seen_at=t0, last_seen_at=t1, total_sightings=2)
    mock_vehicle = Vehicle(id=veh_id, normalized_plate="GJ01TEST001", raw_plate="GJ-01-TEST-001", vehicle_type="CAR")
    mock_vehicle.entity = mock_entity

    # Ahmedabad Camera
    cam1 = Camera(id=uuid.uuid4(), name="CAM-AH-01")
    cam1.location = Location(district="Ahmedabad", latitude=23.0225, longitude=72.5714)

    # Surat Camera (260 km away, observed 5 seconds later!)
    cam2 = Camera(id=uuid.uuid4(), name="CAM-ST-01")
    cam2.location = Location(district="Surat", latitude=21.1702, longitude=72.8311)

    obs1 = VehicleObservation(id=uuid.uuid4(), vehicle_id=veh_id, camera_id=cam1.id, observed_at=t0, plate_confidence=0.95, camera=cam1, location=cam1.location)
    obs2 = VehicleObservation(id=uuid.uuid4(), vehicle_id=veh_id, camera_id=cam2.id, observed_at=t1, plate_confidence=0.96, camera=cam2, location=cam2.location)

    service.vehicles.get_with_entity = AsyncMock(return_value=mock_vehicle)
    service.observations.history_for_vehicle = AsyncMock(return_value=[obs1, obs2])
    service.audit.log_action = AsyncMock()

    route = await service.get_vehicle_route(session, veh_id)
    assert isinstance(route, VehicleRouteResponse)
    assert route.route_type == "OBSERVED_CAMERA_SEQUENCE"
    assert route.point_count == 2
    assert len(route.anomalies_detected) >= 1
    assert route.anomalies_detected[0]["anomaly_type"] == "SIMULTANEOUS_DISTANT_SIGHTING"


@pytest.mark.asyncio
async def test_csv_export_formatting():
    service = TrackingService()
    session = AsyncMock()

    veh_id = uuid.uuid4()
    t0 = datetime(2026, 8, 23, 8, 42, 0, tzinfo=timezone.utc)
    mock_entity = Entity(id=veh_id, first_seen_at=t0, last_seen_at=t0, total_sightings=1)
    mock_vehicle = Vehicle(id=veh_id, normalized_plate="GJ05AB1234", raw_plate="GJ 05 AB 1234", vehicle_type="CAR")
    mock_vehicle.entity = mock_entity

    cam1 = Camera(id=uuid.uuid4(), name="CAM-014")
    cam1.location = Location(district="Surat", latitude=21.20, longitude=72.85)
    obs1 = VehicleObservation(
        id=uuid.uuid4(),
        vehicle_id=veh_id,
        camera_id=cam1.id,
        observed_at=t0,
        plate_confidence=0.95,
        camera=cam1,
        location=cam1.location,
        metadata_={"matched_watchlist": True, "watchlist_type": "STOLEN_VEHICLE"},
    )

    service.vehicles.get_by_plate = AsyncMock(return_value=mock_vehicle)
    service.observations.history_for_vehicle = AsyncMock(return_value=[obs1])
    service.audit.log_action = AsyncMock()

    csv_out = await service.export_vehicle_history_csv(session, "GJ05AB1234")
    assert "Normalized_Plate" in csv_out
    assert "Estimated_Average_Speed_Kmph" in csv_out
    assert "GJ05AB1234" in csv_out
    assert "STOLEN_VEHICLE" in csv_out
