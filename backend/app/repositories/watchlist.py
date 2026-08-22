from datetime import datetime, timezone
from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from app.models.watchlist import Watchlist, WatchlistEntry
from app.repositories.base import BaseRepository


class WatchlistRepository(BaseRepository[Watchlist]):
    def __init__(self):
        super().__init__(Watchlist)

    async def get_by_code(self, session: AsyncSession, code: str) -> Optional[Watchlist]:
        stmt = select(Watchlist).where(Watchlist.code == code.upper().strip())
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_name(self, session: AsyncSession, name: str) -> Optional[Watchlist]:
        stmt = select(Watchlist).where(Watchlist.name.ilike(name.strip()))
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_filtered(
        self,
        session: AsyncSession,
        department_id: Optional[uuid.UUID] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Watchlist], int]:
        stmt = select(Watchlist)

        if department_id:
            stmt = stmt.where(Watchlist.department_id == department_id)

        if category:
            stmt = stmt.where(Watchlist.category == category.upper().strip())

        if is_active is not None:
            stmt = stmt.where(Watchlist.is_active == is_active)

        if search:
            pat = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Watchlist.name.ilike(pat),
                    Watchlist.code.ilike(pat),
                    Watchlist.description.ilike(pat),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Watchlist.created_at.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all()), total


class WatchlistEntryRepository(BaseRepository[WatchlistEntry]):
    def __init__(self):
        super().__init__(WatchlistEntry)

    async def list_by_watchlist(
        self,
        session: AsyncSession,
        watchlist_id: uuid.UUID,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[WatchlistEntry], int]:
        stmt = select(WatchlistEntry).where(WatchlistEntry.watchlist_id == watchlist_id)

        if is_active is not None:
            stmt = stmt.where(WatchlistEntry.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(WatchlistEntry.created_at.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all()), total

    async def find_active_matches(
        self,
        session: AsyncSession,
        normalized_identifier: str,
        entity_type: str = "VEHICLE",
        reference_time: Optional[datetime] = None,
    ) -> List[WatchlistEntry]:
        """
        Query all active watchlist entries matching normalized identifier where:
        - entry is active
        - parent watchlist is active
        - reference_time is between valid_from and valid_until (if valid_until is set)
        """
        ref_time = reference_time or datetime.now(timezone.utc)
        stmt = (
            select(WatchlistEntry)
            .join(Watchlist, WatchlistEntry.watchlist_id == Watchlist.id)
            .where(
                Watchlist.is_active == True,
                WatchlistEntry.is_active == True,
                WatchlistEntry.entity_type == entity_type.upper(),
                WatchlistEntry.normalized_identifier == normalized_identifier.upper().strip(),
                WatchlistEntry.valid_from <= ref_time,
                or_(
                    WatchlistEntry.valid_until == None,
                    WatchlistEntry.valid_until >= ref_time,
                ),
            )
            .options(selectinload(WatchlistEntry.watchlist))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
