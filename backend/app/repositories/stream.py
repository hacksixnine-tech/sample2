from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.stream import CameraStream
from app.repositories.base import BaseRepository


class StreamRepository(BaseRepository[CameraStream]):
    def __init__(self):
        super().__init__(CameraStream)

    async def get_by_camera_id(
        self, session: AsyncSession, camera_id: uuid.UUID
    ) -> List[CameraStream]:
        stmt = (
            select(CameraStream)
            .where(CameraStream.camera_id == camera_id)
            .order_by(CameraStream.is_primary.desc(), CameraStream.created_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_primary_stream(
        self, session: AsyncSession, camera_id: uuid.UUID
    ) -> Optional[CameraStream]:
        stmt = (
            select(CameraStream)
            .where(CameraStream.camera_id == camera_id, CameraStream.is_primary == True)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def set_primary_stream(
        self, session: AsyncSession, camera_id: uuid.UUID, stream_id: uuid.UUID
    ) -> None:
        # Demote all existing streams for this camera to non-primary
        await session.execute(
            update(CameraStream)
            .where(CameraStream.camera_id == camera_id)
            .values(is_primary=False)
        )
        # Promote specified stream
        await session.execute(
            update(CameraStream)
            .where(CameraStream.id == stream_id)
            .values(is_primary=True)
        )
