import math
import pytest
from app.services.tracking_service import haversine_distance_meters


def test_haversine_distance_calculation():
    # Distance between Ahmedabad ISKCON Crossroad (23.0280, 72.5074) and Pakwan Crossroad (23.0378, 72.5126)
    # Approx ~1.2 km
    dist = haversine_distance_meters(23.0280, 72.5074, 23.0378, 72.5126)
    assert 1100 <= dist <= 1300

    # Distance to same point is 0
    assert haversine_distance_meters(23.0280, 72.5074, 23.0280, 72.5074) == 0.0


def test_geographic_speed_calculation():
    # 1200 meters in 60 seconds = 20 m/s = 72 km/h
    dist_meters = 1200.0
    time_seconds = 60.0
    speed_kmph = (dist_meters / time_seconds) * 3.6
    assert round(speed_kmph, 1) == 72.0
