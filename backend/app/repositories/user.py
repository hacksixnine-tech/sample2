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

    async def list_by_department(
        self, session: AsyncSession, department_id: uuid.UUID
    ) -> List[User]:
        stmt = select(User).where(User.department_id == department_id, User.is_active == True)
        result = await session.execute(stmt)
        return list(result.scalars().all())
