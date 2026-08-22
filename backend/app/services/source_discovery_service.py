from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.adapters.factory import SourceAdapterFactory
from app.core.exceptions import NotFoundError, ValidationError
from app.models.camera import Camera
from app.models.health import CameraHealth
from app.models.location import Location
from app.models.source_system import SourceSystem
from app.models.stream import CameraStream
from app.repositories.audit import AuditRepository
from app.repositories.camera import CameraRepository
from app.repositories.department import DepartmentRepository
from app.repositories.location import LocationRepository
from app.repositories.source_system import SourceSystemRepository
from app.repositories.stream import StreamRepository
from app.schemas.source_system import (
    SourceDiscoveryCamera,
    SourceDiscoveryResponse,
    SourceSyncResponse,
    SourceSystemCreate,
    SourceSystemUpdate,
)

# Approximate central coordinates for Gujarat districts when onboarding external sources
DISTRICT_COORDINATES = {
    "Ahmedabad": (23.0225, 72.5714),
    "Gandhinagar": (23.2156, 72.6369),
    "Surat": (21.1702, 72.8311),
    "Vadodara": (22.3072, 73.1812),
    "Rajkot": (22.3039, 70.8022),
    "Junagadh": (21.5222, 70.4579),
    "Navsari": (20.9467, 72.9520),
    "Patan": (23.8493, 72.1266),
    "Gir Somnath": (20.9042, 70.3644),
    "Kutch": (23.2420, 69.6669),
    "Kachchh": (23.2420, 69.6669),
    "Bhavnagar": (21.7645, 72.1519),
    "Jamnagar": (22.4707, 70.0577),
    "UNKNOWN": (23.0000, 72.5000),
}


class SourceDiscoveryService:
    def __init__(
        self,
        source_repo: Optional[SourceSystemRepository] = None,
        camera_repo: Optional[CameraRepository] = None,
        dept_repo: Optional[DepartmentRepository] = None,
        location_repo: Optional[LocationRepository] = None,
        stream_repo: Optional[StreamRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.source_repo = source_repo or SourceSystemRepository()
        self.camera_repo = camera_repo or CameraRepository()
        self.dept_repo = dept_repo or DepartmentRepository()
        self.location_repo = location_repo or LocationRepository()
        self.stream_repo = stream_repo or StreamRepository()
        self.audit_repo = audit_repo or AuditRepository()

    async def get_source(self, session: AsyncSession, source_id: uuid.UUID) -> SourceSystem:
        source = await self.source_repo.get_by_id(session, source_id)
        if not source:
            raise NotFoundError(f"Source system with ID {source_id} was not found.")
        return source

    async def list_sources(self, session: AsyncSession) -> List[SourceSystem]:
        return await self.source_repo.list_active(session)

    async def create_source(
        self, session: AsyncSession, data: SourceSystemCreate
    ) -> SourceSystem:
        existing = await self.source_repo.get_by_code(session, data.code)
        if existing:
            raise ValidationError(f"Source system code '{data.code}' already exists.")

        source = SourceSystem(
            name=data.name,
            code=data.code,
            base_url=data.base_url,
            source_type=data.source_type,
            status=data.status,
            auth_config=data.auth_config,
            metadata_=data.metadata,
        )
        return await self.source_repo.create(session, source)

    async def probe_source(self, session: AsyncSession, source_id: uuid.UUID) -> Dict[str, Any]:
        source = await self.get_source(session, source_id)
        adapter = SourceAdapterFactory.get_adapter(source.source_type, source.base_url)
        probe_result = await adapter.probe(source.base_url, source.auth_config)

        # Update source status if degraded/offline
        if not probe_result.get("accessible"):
            source.status = "DEGRADED"
        else:
            source.status = "ACTIVE"
        await session.flush()

        return {
            "source_id": source.id,
            "source_name": source.name,
            "base_url": source.base_url,
            "probe_result": probe_result,
            "checked_at": datetime.now(timezone.utc),
        }

    async def discover_cameras(
        self, session: AsyncSession, source_id: uuid.UUID
    ) -> SourceDiscoveryResponse:
        source = await self.get_source(session, source_id)
        adapter = SourceAdapterFactory.get_adapter(source.source_type, source.base_url)
        discovery_data = await adapter.discover_cameras(source.base_url, source.auth_config)

        return SourceDiscoveryResponse(
            source_system_id=source.id,
            source_name=source.name,
            base_url=source.base_url,
            total_discovered=discovery_data["total_discovered"],
            catalog_state=discovery_data["catalog_state"],
            scanned_at=discovery_data["scanned_at"],
            cameras=discovery_data["cameras"],
        )

    async def sync_and_onboard_cameras(
        self,
        session: AsyncSession,
        source_id: uuid.UUID,
        default_department_code: str = "GUJ-POLICE",
        actor_id: Optional[uuid.UUID] = None,
    ) -> SourceSyncResponse:
        source = await self.get_source(session, source_id)
        dept = await self.dept_repo.get_by_code(session, default_department_code)
        if not dept:
            # Fallback to first active department
            depts, _ = await self.dept_repo.list_filtered(session, limit=1)
            if not depts:
                raise ValidationError("No active departments found to assign external cameras.")
            dept = depts[0]

        adapter = SourceAdapterFactory.get_adapter(source.source_type, source.base_url)
        discovery_data = await adapter.discover_cameras(source.base_url, source.auth_config)
        discovered_cameras: List[SourceDiscoveryCamera] = discovery_data["cameras"]

        created_count = 0
        updated_count = 0
        errors: List[Dict[str, Any]] = []
        synced_codes: List[str] = []

        for cam_data in discovered_cameras:
            try:
                # Deterministic camera code
                camera_code = f"SRC-CORP8-{cam_data.source_camera_id.zfill(3)}"

                # 1. Resolve Location
                loc_name = cam_data.raw_location_string or f"CCTV Source Point {cam_data.source_camera_id}"
                city = cam_data.inferred_city if cam_data.inferred_city != "UNKNOWN" else "Ahmedabad"
                district = cam_data.inferred_district if cam_data.inferred_district != "UNKNOWN" else "Ahmedabad"

                coords = DISTRICT_COORDINATES.get(district, DISTRICT_COORDINATES["UNKNOWN"])
                lat, lon = coords[0], coords[1]

                loc = await self.location_repo.get_by_name_and_city(session, loc_name, city)
                if not loc:
                    loc = Location(
                        name=loc_name,
                        state="Gujarat",
                        district=district,
                        city=city,
                        latitude=lat,
                        longitude=lon,
                        metadata_={
                            "external_source": source.name,
                            "raw_location_string": cam_data.raw_location_string,
                        },
                    )
                    loc = await self.location_repo.create(session, loc)

                # 2. Check if camera already exists
                existing_cam = await self.camera_repo.get_by_code(session, camera_code)
                if existing_cam:
                    # Update status and telemetry
                    existing_cam.name = f"{cam_data.name} ({loc_name})"
                    existing_cam.connectivity_status = "ONLINE" if cam_data.status == "LIVE" else "OFFLINE"
                    existing_cam.source_metadata = cam_data.raw_metadata
                    existing_cam.last_connected_at = datetime.now(timezone.utc)
                    updated_count += 1
                    target_cam_id = existing_cam.id
                else:
                    # Create new camera
                    new_cam = Camera(
                        camera_code=camera_code,
                        name=f"{cam_data.name} ({loc_name})",
                        department_id=dept.id,
                        location_id=loc.id,
                        camera_type="FIXED",
                        ownership="Gujarat Government",
                        status="ACTIVE",
                        connectivity_status="ONLINE" if cam_data.status == "LIVE" else "OFFLINE",
                        storage_type="EDGE_AND_CENTRAL",
                        retention_days=30,
                        source_system_id=source.id,
                        source_camera_id=cam_data.source_camera_id,
                        source_reference=cam_data.delivery,
                        source_metadata=cam_data.raw_metadata,
                        last_connected_at=datetime.now(timezone.utc),
                        metadata_={
                            "source_provider": source.name,
                            "source_system_code": source.code,
                        },
                    )
                    created_cam = await self.camera_repo.create(session, new_cam)
                    target_cam_id = created_cam.id
                    created_count += 1

                # 3. Synchronize Streams
                existing_streams = await self.stream_repo.get_by_camera_id(session, target_cam_id)
                existing_proto_urls = {(s.protocol, s.stream_url) for s in existing_streams}

                for s_in in cam_data.streams:
                    if (s_in.protocol, s_in.stream_url) not in existing_proto_urls:
                        stream_model = CameraStream(
                            camera_id=target_cam_id,
                            protocol=s_in.protocol,
                            stream_url=s_in.stream_url,
                            resolution=s_in.resolution,
                            fps=s_in.fps,
                            codec=s_in.codec,
                            bitrate_kbps=s_in.bitrate_kbps,
                            is_primary=s_in.is_primary,
                            is_active=True,
                        )
                        await self.stream_repo.create(session, stream_model)

                # 4. Record Initial Health observation
                health_log = CameraHealth(
                    camera_id=target_cam_id,
                    status="ONLINE" if cam_data.status == "LIVE" else "OFFLINE",
                    latency_ms=15,
                    current_fps=cam_data.streams[0].fps if cam_data.streams else 25.0,
                    bitrate_kbps=cam_data.streams[0].bitrate_kbps if cam_data.streams else None,
                    health_score=100.0 if cam_data.status == "LIVE" else 0.0,
                    last_seen_at=datetime.now(timezone.utc),
                    checked_at=datetime.now(timezone.utc),
                    metadata_={"source_synced": True},
                )
                session.add(health_log)

                synced_codes.append(camera_code)

            except Exception as ex:
                errors.append({
                    "source_camera_id": cam_data.source_camera_id,
                    "error": str(ex),
                })

        # Update last synced at
        await self.source_repo.update_last_synced(session, source.id)

        # Audit Log
        await self.audit_repo.log_action(
            session,
            action="UPDATE_CAMERA",
            resource_type="SOURCE_SYSTEM",
            resource_id=str(source.id),
            user_id=actor_id,
            details=f"Synchronized {len(synced_codes)} cameras from external source '{source.name}'",
            metadata={
                "created": created_count,
                "updated": updated_count,
                "errors": len(errors),
            },
        )

        return SourceSyncResponse(
            source_system_id=source.id,
            total_discovered=len(discovered_cameras),
            created_count=created_count,
            updated_count=updated_count,
            error_count=len(errors),
            errors=errors,
            synced_camera_codes=synced_codes,
        )
