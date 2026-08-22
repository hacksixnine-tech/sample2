from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.department import Department
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self):
        super().__init__(Department)

    async def get_by_code(self, session: AsyncSession, code: str) -> Optional[Department]:
        stmt = select(Department).where(Department.code == code.upper().strip())
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_filtered(
        self,
        session: AsyncSession,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Department], int]:
        stmt = select(Department)

        if is_active is not None:
            stmt = stmt.where(Department.is_active == is_active)

        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Department.name.ilike(search_pattern),
                    Department.code.ilike(search_pattern),
                    Department.description.ilike(search_pattern),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        # Paginate and order by name
        stmt = stmt.order_by(Department.name.asc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all()), total
