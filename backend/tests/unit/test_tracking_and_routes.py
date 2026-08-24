from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
import uuid
import pytest

from app.models.analytics import Entity, Vehicle, VehicleObservation
from app.models.camera import Camera
from app.models.location import Location
from app.services.tracking_service import TrackingService, haversine_distance_meters


def test_haversine_distance_meters():
    # Ahmedabad (23.0225, 72.5714) to Gandhinagar (23.2156, 72.6369) ~ 22-25 km
    dist = haversine_distance_meters(23.0225, 72.5714, 23.2156, 72.6369)
    assert 20000 < dist < 30000

    # Same point = 0
    assert haversine_distance_meters(23.0, 72.0, 23.0, 72.0) == 0.0


@pytest.mark.asyncio
async def test_vehicle_route_reconstruction_and_anomaly_detection():
    service = TrackingService()
    service.vehicles.get_with_entity = AsyncMock()
    service.observations.history_for_vehicle = AsyncMock()

    veh_id = uuid.uuid4()
    now = datetime(2026, 8, 23, 10, 0, 0, tzinfo=timezone.utc)

    entity = Entity(
        id=veh_id,
        entity_type="VEHICLE",
        primary_identifier="GJ01TEST001",
        first_seen_at=now,
        last_seen_at=now + timedelta(minutes=15),
        total_sightings=3,
    )
    vehicle = Vehicle(
        id=veh_id,
        normalized_plate="GJ01TEST001",
        raw_plate="GJ 01 TEST 001",
        vehicle_type="CAR",
        entity=entity,
    )
    service.vehicles.get_with_entity.return_value = vehicle

    # Sighting 1: SG Highway Cam 1
    loc1 = Location(id=uuid.uuid4(), name="SG Highway", district="Ahmedabad", latitude=23.0300, longitude=72.5000)
    cam1 = Camera(id=uuid.uuid4(), camera_code="CAM-01", name="SG Cam 1", location=loc1)
    obs1 = VehicleObservation(
        id=uuid.uuid4(),
        vehicle_id=veh_id,
        camera_id=cam1.id,
        camera=cam1,
        location=loc1,
        observed_at=now,
        plate_confidence=0.95,
        vehicle_confidence=0.92,
    )

    # Sighting 2: Vaishno Devi Circle (5km away, 5 minutes later) -> speed ~ 60 km/h
    loc2 = Location(id=uuid.uuid4(), name="Vaishno Devi", district="Ahmedabad", latitude=23.0750, longitude=72.5350)
    cam2 = Camera(id=uuid.uuid4(), camera_code="CAM-02", name="Vaishno Devi Cam", location=loc2)
    obs2 = VehicleObservation(
        id=uuid.uuid4(),
        vehicle_id=veh_id,
        camera_id=cam2.id,
        camera=cam2,
        location=loc2,
        observed_at=now + timedelta(minutes=5),
        plate_confidence=0.94,
        vehicle_confidence=0.90,
    )

    # Sighting 3: Distant Vadodara camera (100km away) only 2 seconds later -> SIMULTANEOUS_DISTANT_SIGHTING anomaly
    loc3 = Location(id=uuid.uuid4(), name="Vadodara Central", district="Vadodara", latitude=22.3072, longitude=73.1812)
    cam3 = Camera(id=uuid.uuid4(), camera_code="CAM-03", name="Vadodara Cam", location=loc3)
    obs3 = VehicleObservation(
        id=uuid.uuid4(),
        vehicle_id=veh_id,
        camera_id=cam3.id,
        camera=cam3,
        location=loc3,
        observed_at=now + timedelta(minutes=5, seconds=2),
        plate_confidence=0.96,
        vehicle_confidence=0.91,
    )

    service.observations.history_for_vehicle.return_value = [obs1, obs2, obs3]

    session = AsyncMock()
    route_resp = await service.get_vehicle_route(session, veh_id)

    assert route_resp.route_type == "OBSERVED_CAMERA_SEQUENCE"
    assert route_resp.point_count == 3
    assert len(route_resp.points) == 3
    assert route_resp.unique_district_count == 2  # Ahmedabad & Vadodara
    assert route_resp.total_geographic_distance_meters > 50000

    # Verify Anomaly Flagging
    assert len(route_resp.anomalies_detected) >= 1
    anomaly_types = [a["anomaly_type"] for a in route_resp.anomalies_detected]
    assert "SIMULTANEOUS_DISTANT_SIGHTING" in anomaly_types or "IMPOSSIBLE_GEOGRAPHIC_SPEED" in anomaly_types
