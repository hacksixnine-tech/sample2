from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.source_system import SourceSystem
from app.repositories.base import BaseRepository


class SourceSystemRepository(BaseRepository[SourceSystem]):
    def __init__(self):
        super().__init__(SourceSystem)

    async def get_by_code(self, session: AsyncSession, code: str) -> Optional[SourceSystem]:
        stmt = select(SourceSystem).where(SourceSystem.code == code.upper().strip())
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_active(self, session: AsyncSession) -> List[SourceSystem]:
        stmt = select(SourceSystem).order_by(SourceSystem.name.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_last_synced(self, session: AsyncSession, source_id: uuid.UUID) -> None:
        await session.execute(
            update(SourceSystem)
            .where(SourceSystem.id == source_id)
            .values(last_synced_at=datetime.now(timezone.utc))
        )
