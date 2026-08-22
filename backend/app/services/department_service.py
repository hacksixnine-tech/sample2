from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError
from app.models.department import Department
from app.repositories.department import DepartmentRepository
from app.repositories.camera import CameraRepository
from app.repositories.audit import AuditRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentCameraSummaryResponse


class DepartmentService:
    def __init__(
        self,
        dept_repo: Optional[DepartmentRepository] = None,
        camera_repo: Optional[CameraRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
    ):
        self.dept_repo = dept_repo or DepartmentRepository()
        self.camera_repo = camera_repo or CameraRepository()
        self.audit_repo = audit_repo or AuditRepository()

    async def get_department(self, session: AsyncSession, department_id: uuid.UUID) -> Department:
        dept = await self.dept_repo.get_by_id(session, department_id)
        if not dept:
            raise NotFoundError(f"Department with ID {department_id} was not found.")
        return dept

    async def list_departments(
        self,
        session: AsyncSession,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Department], int]:
        skip = (page - 1) * page_size
        return await self.dept_repo.list_filtered(
            session, search=search, is_active=is_active, skip=skip, limit=page_size
        )

    async def create_department(
        self, session: AsyncSession, data: DepartmentCreate, actor_id: Optional[uuid.UUID] = None
    ) -> Department:
        # Check code uniqueness
        existing = await self.dept_repo.get_by_code(session, data.code)
        if existing:
            raise ConflictError(f"Department code '{data.code}' already exists.")

        dept = Department(
            name=data.name,
            code=data.code,
            description=data.description,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            is_active=data.is_active,
        )
        created = await self.dept_repo.create(session, dept)

        await self.audit_repo.log_action(
            session,
            action="CREATE_DEPARTMENT",
            resource_type="DEPARTMENT",
            resource_id=str(created.id),
            user_id=actor_id,
            details=f"Created department '{created.name}' ({created.code})",
        )
        return created

    async def update_department(
        self,
        session: AsyncSession,
        department_id: uuid.UUID,
        data: DepartmentUpdate,
        actor_id: Optional[uuid.UUID] = None,
    ) -> Department:
        dept = await self.get_department(session, department_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(dept, key, value)

        await session.flush()
        await session.refresh(dept)

        await self.audit_repo.log_action(
            session,
            action="UPDATE_DEPARTMENT",
            resource_type="DEPARTMENT",
            resource_id=str(dept.id),
            user_id=actor_id,
            details=f"Updated department '{dept.name}' ({dept.code})",
        )
        return dept

    async def delete_department(
        self, session: AsyncSession, department_id: uuid.UUID, actor_id: Optional[uuid.UUID] = None
    ) -> bool:
        dept = await self.get_department(session, department_id)

        # Soft deactivation rather than destructive cascade deletion
        dept.is_active = False
        await session.flush()

        await self.audit_repo.log_action(
            session,
            action="DEACTIVATE_DEPARTMENT",
            resource_type="DEPARTMENT",
            resource_id=str(dept.id),
            user_id=actor_id,
            details=f"Deactivated department '{dept.name}' ({dept.code})",
        )
        return True

    async def get_department_cameras_summary(
        self, session: AsyncSession, department_id: uuid.UUID
    ) -> DepartmentCameraSummaryResponse:
        summary_dict = await self.camera_repo.get_department_camera_summary(session, department_id)
        if not summary_dict:
            raise NotFoundError(f"Department with ID {department_id} was not found.")
        return DepartmentCameraSummaryResponse(**summary_dict)
