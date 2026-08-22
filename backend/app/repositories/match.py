from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.match import Match
from app.repositories.base import BaseRepository


class MatchRepository(BaseRepository[Match]):
    def __init__(self):
        super().__init__(Match)

    async def get_by_detection_and_entry(
        self, session: AsyncSession, detection_id: uuid.UUID, watchlist_entry_id: uuid.UUID
    ) -> Optional[Match]:
        stmt = select(Match).where(
            Match.detection_id == detection_id,
            Match.watchlist_entry_id == watchlist_entry_id,
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_by_detection(
        self, session: AsyncSession, detection_id: uuid.UUID
    ) -> List[Match]:
        stmt = (
            select(Match)
            .where(Match.detection_id == detection_id)
            .options(selectinload(Match.watchlist_entry))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_watchlist_entry(
        self, session: AsyncSession, watchlist_entry_id: uuid.UUID, limit: int = 50
    ) -> List[Match]:
        stmt = (
            select(Match)
            .where(Match.watchlist_entry_id == watchlist_entry_id)
            .order_by(Match.matched_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
