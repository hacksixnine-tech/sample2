from typing import Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.models.health import CameraHealth
from app.models.camera import Camera
from app.repositories.base import BaseRepository


class CameraHealthRepository(BaseRepository[CameraHealth]):
    def __init__(self):
        super().__init__(CameraHealth)

    async def get_latest_for_camera(
        self, session: AsyncSession, camera_id: uuid.UUID
    ) -> Optional[CameraHealth]:
        stmt = (
            select(CameraHealth)
            .where(CameraHealth.camera_id == camera_id)
            .order_by(CameraHealth.checked_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_history_for_camera(
        self, session: AsyncSession, camera_id: uuid.UUID, limit: int = 50
    ) -> List[CameraHealth]:
        stmt = (
            select(CameraHealth)
            .where(CameraHealth.camera_id == camera_id)
            .order_by(CameraHealth.checked_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_system_health_summary(self, session: AsyncSession) -> Dict[str, int]:
        """
        Aggregate camera operational status directly from active cameras.
        """
        total_stmt = select(func.count(Camera.id))
        total = (await session.execute(total_stmt)).scalar_one()

        status_stmt = select(Camera.connectivity_status, func.count(Camera.id)).group_by(
            Camera.connectivity_status
        )
        status_results = (await session.execute(status_stmt)).all()

        counts = {
            "total": total,
            "online": 0,
            "degraded": 0,
            "offline": 0,
            "maintenance": 0,
            "unknown": 0,
        }

        for status_val, count_val in status_results:
            key = str(status_val).lower()
            if key in counts:
                counts[key] = count_val
            else:
                counts["unknown"] += count_val

        return counts
