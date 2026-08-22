import pytest
from pydantic import ValidationError
from app.schemas.department import DepartmentCreate
from app.schemas.location import LocationCreate
from app.schemas.camera import CameraCreate
from app.schemas.stream import CameraStreamCreate
from app.schemas.health import CameraHealthCreate
import uuid


def test_coordinate_validation():
    # Valid Gujarat coordinates
    loc = LocationCreate(
        name="Test Junction",
        district="Ahmedabad",
        city="Ahmedabad",
        latitude=23.0225,
        longitude=72.5714,
    )
    assert loc.latitude == 23.0225
    assert loc.longitude == 72.5714

    # Invalid latitude > 90
    with pytest.raises(ValidationError):
        LocationCreate(
            name="Invalid Lat",
            district="Ahmedabad",
            city="Ahmedabad",
            latitude=95.0,
            longitude=72.5,
        )

    # Invalid longitude < -180
    with pytest.raises(ValidationError):
        LocationCreate(
            name="Invalid Lon",
            district="Ahmedabad",
            city="Ahmedabad",
            latitude=23.0,
            longitude=-185.0,
        )


def test_department_code_normalization():
    dept = DepartmentCreate(
        name="Gujarat Maritime Board",
        code="  guj-maritime  ",
        description="Ports & Maritime",
    )
    assert dept.code == "GUJ-MARITIME"


def test_stream_protocol_validation():
    stream = CameraStreamCreate(
        protocol="rtsp",
        stream_url="rtsp://cctv.gujarat.gov.in/live/cam01",
    )
    assert stream.protocol == "RTSP"

    with pytest.raises(ValidationError):
        CameraStreamCreate(
            protocol="INVALID_PROTO",
            stream_url="rtsp://test",
        )


def test_camera_health_status_validation():
    health = CameraHealthCreate(status="online", latency_ms=12)
    assert health.status == "ONLINE"

    with pytest.raises(ValidationError):
        CameraHealthCreate(status="SUPER_FINE")
