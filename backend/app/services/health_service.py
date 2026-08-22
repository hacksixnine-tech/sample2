from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.models.health import CameraHealth
from app.repositories.health import CameraHealthRepository
from app.repositories.camera import CameraRepository
from app.schemas.health import CameraHealthCreate, CameraHealthSummaryResponse


class CameraHealthService:
    def __init__(
        self,
        health_repo: Optional[CameraHealthRepository] = None,
        camera_repo: Optional[CameraRepository] = None,
    ):
        self.health_repo = health_repo or CameraHealthRepository()
        self.camera_repo = camera_repo or CameraRepository()

    async def get_latest_health(
        self, session: AsyncSession, camera_id: uuid.UUID
    ) -> CameraHealth:
        camera = await self.camera_repo.get_by_id(session, camera_id)
        if not camera:
            raise NotFoundError(f"Camera with ID {camera_id} was not found.")

        latest = await self.health_repo.get_latest_for_camera(session, camera_id)
        if not latest:
            # Fallback to camera's current connectivity status
            return CameraHealth(
                camera_id=camera.id,
                status=camera.connectivity_status,
                health_score=100.0 if camera.connectivity_status == "ONLINE" else 0.0,
                last_seen_at=camera.updated_at,
                checked_at=datetime.now(timezone.utc),
            )
        return latest

    async def get_health_history(
        self, session: AsyncSession, camera_id: uuid.UUID, limit: int = 50
    ) -> List[CameraHealth]:
        camera = await self.camera_repo.get_by_id(session, camera_id)
        if not camera:
            raise NotFoundError(f"Camera with ID {camera_id} was not found.")
        return await self.health_repo.get_history_for_camera(session, camera_id, limit=limit)

    async def record_camera_health(
        self, session: AsyncSession, camera_id: uuid.UUID, data: CameraHealthCreate
    ) -> CameraHealth:
        camera = await self.camera_repo.get_by_id(session, camera_id)
        if not camera:
            raise NotFoundError(f"Camera with ID {camera_id} was not found.")

        # Sync camera's top-level connectivity_status
        camera.connectivity_status = data.status
        if data.status in ("MAINTENANCE", "INACTIVE"):
            camera.status = data.status

        health_log = CameraHealth(
            camera_id=camera_id,
            status=data.status,
            latency_ms=data.latency_ms,
            packet_loss_pct=data.packet_loss_pct,
            current_fps=data.current_fps,
            bitrate_kbps=data.bitrate_kbps,
            health_score=data.health_score,
            last_error=data.last_error,
            last_seen_at=datetime.now(timezone.utc),
            checked_at=datetime.now(timezone.utc),
            metadata_=data.metadata,
        )
        return await self.health_repo.create(session, health_log)

    async def get_summary(self, session: AsyncSession) -> CameraHealthSummaryResponse:
        counts = await self.health_repo.get_system_health_summary(session)
        return CameraHealthSummaryResponse(
            total=counts["total"],
            online=counts["online"],
            degraded=counts["degraded"],
            offline=counts["offline"],
            maintenance=counts["maintenance"],
            unknown=counts["unknown"],
            timestamp=datetime.now(timezone.utc),
        )
