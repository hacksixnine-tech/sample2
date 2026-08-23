import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from app.services.camera_service import CameraService
from app.services.bulk_import_service import BulkCameraImportService
from app.core.exceptions import ValidationError, ConflictError


@pytest.mark.asyncio
async def test_camera_service_nearby_coordinate_validation():
    service = CameraService()
    mock_session = AsyncMock()

    # Invalid latitude > 90
    with pytest.raises(ValidationError):
        await service.find_nearby_cameras(mock_session, latitude=95.0, longitude=72.0, radius_meters=1000)

    # Invalid longitude < -180
    with pytest.raises(ValidationError):
        await service.find_nearby_cameras(mock_session, latitude=23.0, longitude=-190.0, radius_meters=1000)

    # Invalid radius <= 0
    with pytest.raises(ValidationError):
        await service.find_nearby_cameras(mock_session, latitude=23.0, longitude=72.0, radius_meters=-50)


@pytest.mark.asyncio
async def test_camera_service_corridor_validation():
    service = CameraService()
    mock_session = AsyncMock()

    # Invalid start lat
    with pytest.raises(ValidationError):
        await service.find_cameras_in_corridor(
            mock_session,
            start_lat=100.0,
            start_lon=72.0,
            end_lat=23.0,
            end_lon=73.0,
            buffer_meters=1000,
        )

    # Invalid buffer meters
    with pytest.raises(ValidationError):
        await service.find_cameras_in_corridor(
            mock_session,
            start_lat=22.0,
            start_lon=72.0,
            end_lat=23.0,
            end_lon=73.0,
            buffer_meters=-100,
        )


@pytest.mark.asyncio
async def test_camera_service_bbox_validation():
    service = CameraService()
    mock_session = AsyncMock()

    # Invalid bbox lat range
    with pytest.raises(ValidationError):
        await service.find_cameras_in_bbox(
            mock_session,
            min_lat=-95.0,
            min_lon=70.0,
            max_lat=25.0,
            max_lon=75.0,
        )


@pytest.mark.asyncio
async def test_bulk_import_validation():
    service = BulkCameraImportService()
    mock_session = AsyncMock()

    # Test missing camera_code
    invalid_rows = [
        {"name": "No Code Camera", "department_code": "POLICE", "latitude": 23.0, "longitude": 72.0},
        {"camera_code": "CAM-01", "name": "Duplicate Code", "department_code": "POLICE", "latitude": 23.0, "longitude": 72.0},
        {"camera_code": "CAM-01", "name": "Duplicate Code in Batch", "department_code": "POLICE", "latitude": 23.0, "longitude": 72.0},
    ]

    report = await service.import_rows(mock_session, invalid_rows)
    assert report.total_rows == 3
    assert len(report.errors) >= 2
