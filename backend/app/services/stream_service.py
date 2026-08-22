from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.models.stream import CameraStream
from app.repositories.stream import StreamRepository
from app.repositories.camera import CameraRepository
from app.repositories.audit import AuditRepository
from app.schemas.stream import CameraStreamCreate, CameraStreamUpdate


class StreamService:
    def __init__(
        self,
        stream_repo: Optional[StreamRepository] = None,
        camera_repo: Optional[CameraRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.stream_repo = stream_repo or StreamRepository()
        self.camera_repo = camera_repo or CameraRepository()
        self.audit_repo = audit_repo or AuditRepository()

    async def get_stream(self, session: AsyncSession, stream_id: uuid.UUID) -> CameraStream:
        stream = await self.stream_repo.get_by_id(session, stream_id)
        if not stream:
            raise NotFoundError(f"Stream with ID {stream_id} was not found.")
        return stream

    async def list_camera_streams(
        self, session: AsyncSession, camera_id: uuid.UUID
    ) -> List[CameraStream]:
        camera = await self.camera_repo.get_by_id(session, camera_id)
        if not camera:
            raise NotFoundError(f"Camera with ID {camera_id} was not found.")
        return await self.stream_repo.get_by_camera_id(session, camera_id)

    async def create_stream(
        self,
        session: AsyncSession,
        camera_id: uuid.UUID,
        data: CameraStreamCreate,
        actor_id: Optional[uuid.UUID] = None,
    ) -> CameraStream:
        camera = await self.camera_repo.get_by_id(session, camera_id)
        if not camera:
            raise NotFoundError(f"Camera with ID {camera_id} was not found.")

        # If this stream is designated primary, demote any existing primary streams
        if data.is_primary:
            existing_streams = await self.stream_repo.get_by_camera_id(session, camera_id)
            for s in existing_streams:
                if s.is_primary:
                    s.is_primary = False

        stream = CameraStream(
            camera_id=camera_id,
            protocol=data.protocol,
            stream_url=data.stream_url,
            secret_ref=data.secret_ref,
            resolution=data.resolution,
            fps=data.fps,
            codec=data.codec,
            bitrate_kbps=data.bitrate_kbps,
            is_primary=data.is_primary,
            is_active=data.is_active,
            metadata_=data.metadata,
        )
        created = await self.stream_repo.create(session, stream)

        await self.audit_repo.log_action(
            session,
            action="CREATE_STREAM",
            resource_type="STREAM",
            resource_id=str(created.id),
            user_id=actor_id,
            details=f"Created {created.protocol} stream for camera '{camera.camera_code}'",
        )
        return created

    async def update_stream(
        self,
        session: AsyncSession,
        stream_id: uuid.UUID,
        data: CameraStreamUpdate,
        actor_id: Optional[uuid.UUID] = None,
    ) -> CameraStream:
        stream = await self.get_stream(session, stream_id)

        update_dict = data.model_dump(exclude_unset=True)
        if update_dict.get("is_primary") is True:
            await self.stream_repo.set_primary_stream(session, stream.camera_id, stream_id)

        if "metadata" in update_dict:
            stream.metadata_ = update_dict.pop("metadata")

        for key, value in update_dict.items():
            setattr(stream, key, value)

        await session.flush()
        await session.refresh(stream)

        await self.audit_repo.log_action(
            session,
            action="UPDATE_STREAM",
            resource_type="STREAM",
            resource_id=str(stream.id),
            user_id=actor_id,
            details=f"Updated stream {stream.id} on camera {stream.camera_id}",
        )
        return stream

    async def delete_stream(
        self, session: AsyncSession, stream_id: uuid.UUID, actor_id: Optional[uuid.UUID] = None
    ) -> bool:
        stream = await self.get_stream(session, stream_id)
        success = await self.stream_repo.delete(session, stream_id)

        if success:
            await self.audit_repo.log_action(
                session,
                action="DELETE_STREAM",
                resource_type="STREAM",
                resource_id=str(stream_id),
                user_id=actor_id,
                details=f"Deleted stream {stream_id} on camera {stream.camera_id}",
            )
        return success
