from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.user import Role, User
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self):
        super().__init__(Role)

    async def get_by_name(self, session: AsyncSession, name: str) -> Optional[Role]:
        stmt = select(Role).where(Role.name == name.upper().strip())
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_all_roles(self, session: AsyncSession) -> List[Role]:
        stmt = select(Role).order_by(Role.name)
        result = await session.execute(stmt)
        return list(result.scalars().all())


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_username(self, session: AsyncSession, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username.strip())
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.strip().lower())
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_identifier(self, session: AsyncSession, identifier: str) -> Optional[User]:
        clean_id = identifier.strip()
        stmt = select(User).where(
            or_(
                func.lower(User.username) == clean_id.lower(),
                func.lower(User.email) == clean_id.lower(),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_by_department(
        self, session: AsyncSession, department_id: uuid.UUID
    ) -> List[User]:
        stmt = select(User).where(User.department_id == department_id, User.is_active == True)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_users(
        self,
        session: AsyncSession,
        department_id: Optional[uuid.UUID] = None,
        role_id: Optional[uuid.UUID] = None,
        role_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[User], int]:
        stmt = select(User)
        count_stmt = select(func.count()).select_from(User)

        if department_id:
            stmt = stmt.where(User.department_id == department_id)
            count_stmt = count_stmt.where(User.department_id == department_id)

        if role_id:
            stmt = stmt.where(User.role_id == role_id)
            count_stmt = count_stmt.where(User.role_id == role_id)

        if role_name:
            stmt = stmt.join(Role).where(func.upper(Role.name) == role_name.upper().strip())
            count_stmt = count_stmt.join(Role).where(func.upper(Role.name) == role_name.upper().strip())

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
            count_stmt = count_stmt.where(User.is_active == is_active)

        if search:
            search_pattern = f"%{search.strip()}%"
            filter_cond = or_(
                User.username.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.badge_number.ilike(search_pattern),
            )
            stmt = stmt.where(filter_cond)
            count_stmt = count_stmt.where(filter_cond)

        total = await session.scalar(count_stmt) or 0
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all()), total


user_repo = UserRepository()
role_repo = RoleRepository()
