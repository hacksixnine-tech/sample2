from datetime import datetime
from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from app.models.alert import Alert
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    def __init__(self):
        super().__init__(Alert)

    async def get_by_code(self, session: AsyncSession, alert_code: str) -> Optional[Alert]:
        stmt = (
            select(Alert)
            .where(Alert.alert_code == alert_code.strip())
            .options(
                selectinload(Alert.camera),
                selectinload(Alert.entity),
                selectinload(Alert.source_match),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def find_recent_duplicate(
        self,
        session: AsyncSession,
        camera_id: uuid.UUID,
        entity_id: Optional[uuid.UUID],
        alert_type: str,
        since_time: datetime,
    ) -> Optional[Alert]:
        """
        Deduplication query: Check if an alert for the same entity, same camera,
        and same alert_type was already generated within the cooldown window.
        """
        if not entity_id:
            return None

        stmt = select(Alert).where(
            Alert.camera_id == camera_id,
            Alert.entity_id == entity_id,
            Alert.alert_type == alert_type,
            Alert.created_at >= since_time,
        ).order_by(Alert.created_at.desc())
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_filtered(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        camera_id: Optional[uuid.UUID] = None,
        entity_id: Optional[uuid.UUID] = None,
        alert_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Alert], int]:
        stmt = select(Alert)

        if status:
            stmt = stmt.where(Alert.status == status.upper().strip())
        if severity:
            stmt = stmt.where(Alert.severity == severity.upper().strip())
        if camera_id:
            stmt = stmt.where(Alert.camera_id == camera_id)
        if entity_id:
            stmt = stmt.where(Alert.entity_id == entity_id)
        if alert_type:
            stmt = stmt.where(Alert.alert_type == alert_type.upper().strip())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = (
            stmt.options(
                selectinload(Alert.camera),
                selectinload(Alert.entity),
                selectinload(Alert.source_match),
            )
            .order_by(Alert.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all()), total
