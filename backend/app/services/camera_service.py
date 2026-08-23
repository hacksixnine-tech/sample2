from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.camera import Camera
from app.repositories.camera import CameraRepository
from app.repositories.department import DepartmentRepository
from app.repositories.location import LocationRepository
from app.repositories.health import CameraHealthRepository
from app.repositories.audit import AuditRepository
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraDetailResponse,
    CameraNearbyResponse,
    CameraCoverageResponse,
)
from app.schemas.health import CameraHealthResponse


class CameraService:
    def __init__(
        self,
        camera_repo: Optional[CameraRepository] = None,
        dept_repo: Optional[DepartmentRepository] = None,
        location_repo: Optional[LocationRepository] = None,
        health_repo: Optional[CameraHealthRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.camera_repo = camera_repo or CameraRepository()
        self.dept_repo = dept_repo or DepartmentRepository()
        self.location_repo = location_repo or LocationRepository()
        self.health_repo = health_repo or CameraHealthRepository()
        self.audit_repo = audit_repo or AuditRepository()

    async def get_camera(self, session: AsyncSession, camera_id: uuid.UUID) -> Camera:
        camera = await self.camera_repo.get_by_id(session, camera_id)
        if not camera:
            raise NotFoundError(f"Camera with ID {camera_id} was not found.")
        return camera

    async def get_camera_detail(
        self, session: AsyncSession, camera_id: uuid.UUID
    ) -> CameraDetailResponse:
        camera = await self.camera_repo.get_by_id_with_relations(session, camera_id)
        if not camera:
            raise NotFoundError(f"Camera with ID {camera_id} was not found.")

        # Fetch latest health log
        latest_health_model = await self.health_repo.get_latest_for_camera(session, camera_id)
        latest_health_schema = (
            CameraHealthResponse.model_validate(latest_health_model)
            if latest_health_model
            else None
        )

        response = CameraDetailResponse.model_validate(camera)
        response.current_health = latest_health_schema
        return response

    async def list_cameras(
        self,
        session: AsyncSession,
        department_id: Optional[uuid.UUID] = None,
        district: Optional[str] = None,
        city: Optional[str] = None,
        camera_type: Optional[str] = None,
        status: Optional[str] = None,
        connectivity_status: Optional[str] = None,
        manufacturer: Optional[str] = None,
        ownership: Optional[str] = None,
        search: Optional[str] = None,
        location_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Camera], int]:
        skip = (page - 1) * page_size
        return await self.camera_repo.list_filtered(
            session=session,
            department_id=department_id,
            district=district,
            city=city,
            camera_type=camera_type,
            status=status,
            connectivity_status=connectivity_status,
            manufacturer=manufacturer,
            ownership=ownership,
            search=search,
            location_id=location_id,
            skip=skip,
            limit=page_size,
        )

    async def find_nearby_cameras(
        self,
        session: AsyncSession,
        latitude: float,
        longitude: float,
        radius_meters: float = 5000.0,
        limit: int = 50,
    ) -> List[CameraNearbyResponse]:
        if not (-90.0 <= latitude <= 90.0):
            raise ValidationError(f"Invalid latitude: {latitude}. Must be between -90 and +90.")
        if not (-180.0 <= longitude <= 180.0):
            raise ValidationError(f"Invalid longitude: {longitude}. Must be between -180 and +180.")
        if radius_meters <= 0:
            raise ValidationError("Radius in meters must be greater than zero.")

        raw_results = await self.camera_repo.find_nearby_cameras(
            session, latitude=latitude, longitude=longitude, radius_meters=radius_meters, limit=limit
        )
        return [CameraNearbyResponse(**row) for row in raw_results]

    async def create_camera(
        self, session: AsyncSession, data: CameraCreate, actor_id: Optional[uuid.UUID] = None
    ) -> Camera:
        # 1. Check duplicate camera_code
        existing = await self.camera_repo.get_by_code(session, data.camera_code)
        if existing:
            raise ConflictError(f"Camera code '{data.camera_code}' already exists.")

        # 2. Verify Department exists
        dept = await self.dept_repo.get_by_id(session, data.department_id)
        if not dept:
            raise NotFoundError(f"Department with ID {data.department_id} does not exist.")

        # 3. Verify Location exists
        loc = await self.location_repo.get_by_id(session, data.location_id)
        if not loc:
            raise NotFoundError(f"Location with ID {data.location_id} does not exist.")

        camera = Camera(
            camera_code=data.camera_code,
            name=data.name,
            department_id=data.department_id,
            location_id=data.location_id,
            camera_type=data.camera_type,
            manufacturer=data.manufacturer,
            model=data.model,
            serial_number=data.serial_number,
            mac_address=data.mac_address,
            ip_address=data.ip_address,
            ownership=data.ownership,
            installation_date=data.installation_date,
            status=data.status,
            connectivity_status=data.connectivity_status,
            storage_type=data.storage_type,
            retention_days=data.retention_days,
            field_of_view_deg=data.field_of_view_deg,
            azimuth_angle_deg=data.azimuth_angle_deg,
            metadata_=data.metadata,
        )
        created = await self.camera_repo.create(session, camera)

        await self.audit_repo.log_action(
            session,
            action="CREATE_CAMERA",
            resource_type="CAMERA",
            resource_id=str(created.id),
            user_id=actor_id,
            details=f"Registered camera '{created.camera_code}' ({created.name})",
        )
        return created

    async def update_camera(
        self,
        session: AsyncSession,
        camera_id: uuid.UUID,
        data: CameraUpdate,
        actor_id: Optional[uuid.UUID] = None,
    ) -> Camera:
        camera = await self.get_camera(session, camera_id)

        update_dict = data.model_dump(exclude_unset=True)

        if "department_id" in update_dict:
            dept = await self.dept_repo.get_by_id(session, update_dict["department_id"])
            if not dept:
                raise NotFoundError(f"Department {update_dict['department_id']} not found.")

        if "location_id" in update_dict:
            loc = await self.location_repo.get_by_id(session, update_dict["location_id"])
            if not loc:
                raise NotFoundError(f"Location {update_dict['location_id']} not found.")

        if "metadata" in update_dict:
            camera.metadata_ = update_dict.pop("metadata")

        for key, value in update_dict.items():
            setattr(camera, key, value)

        await session.flush()
        await session.refresh(camera)

        await self.audit_repo.log_action(
            session,
            action="UPDATE_CAMERA",
            resource_type="CAMERA",
            resource_id=str(camera.id),
            user_id=actor_id,
            details=f"Updated camera '{camera.camera_code}'",
        )
        return camera

    async def delete_camera(
        self, session: AsyncSession, camera_id: uuid.UUID, actor_id: Optional[uuid.UUID] = None
    ) -> bool:
        camera = await self.get_camera(session, camera_id)

        # Decommission / soft delete to preserve historical integrity
        camera.status = "DECOMMISSIONED"
        camera.connectivity_status = "OFFLINE"
        await session.flush()

        await self.audit_repo.log_action(
            session,
            action="DECOMMISSION_CAMERA",
            resource_type="CAMERA",
            resource_id=str(camera.id),
            user_id=actor_id,
            details=f"Decommissioned camera '{camera.camera_code}'",
        )
        return True

    async def get_coverage_metrics(self, session: AsyncSession) -> CameraCoverageResponse:
        metrics = await self.camera_repo.get_coverage_metrics(session)
        metrics["timestamp"] = datetime.now(timezone.utc)
        return CameraCoverageResponse(**metrics)

    async def find_cameras_in_bbox(
        self,
        session: AsyncSession,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        department_id: Optional[uuid.UUID] = None,
        district: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        if not (-90.0 <= min_lat <= 90.0) or not (-90.0 <= max_lat <= 90.0):
            raise ValidationError("Latitude must be between -90 and +90.")
        if not (-180.0 <= min_lon <= 180.0) or not (-180.0 <= max_lon <= 180.0):
            raise ValidationError("Longitude must be between -180 and +180.")

        return await self.camera_repo.find_cameras_in_bbox(
            session,
            min_lat=min_lat,
            min_lon=min_lon,
            max_lat=max_lat,
            max_lon=max_lon,
            department_id=department_id,
            district=district,
            status=status,
            limit=limit,
        )

    async def find_cameras_in_corridor(
        self,
        session: AsyncSession,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        buffer_meters: float = 1000.0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        for lat in (start_lat, end_lat):
            if not (-90.0 <= lat <= 90.0):
                raise ValidationError(f"Invalid latitude: {lat}. Must be between -90 and +90.")
        for lon in (start_lon, end_lon):
            if not (-180.0 <= lon <= 180.0):
                raise ValidationError(f"Invalid longitude: {lon}. Must be between -180 and +180.")
        if buffer_meters <= 0:
            raise ValidationError("Corridor buffer in meters must be positive.")

        return await self.camera_repo.find_cameras_in_corridor(
            session,
            start_lat=start_lat,
            start_lon=start_lon,
            end_lat=end_lat,
            end_lon=end_lon,
            buffer_meters=buffer_meters,
            limit=limit,
        )

    async def analyze_coverage_gaps(
        self,
        session: AsyncSession,
        district: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        result = await self.camera_repo.analyze_coverage_gaps(
            session, district=district, department_id=department_id
        )
        result["timestamp"] = datetime.now(timezone.utc)
        return result

