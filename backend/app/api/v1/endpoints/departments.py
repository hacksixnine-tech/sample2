import math
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentCameraSummaryResponse,
)
from app.services.department_service import DepartmentService

router = APIRouter(prefix="/departments", tags=["Departments"])
department_service = DepartmentService()


@router.post(
    "",
    response_model=ApiResponse[DepartmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Government Department",
    description="Registers a new Gujarat government department with unique code and contact information.",
)
async def create_department(
    data: DepartmentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DepartmentResponse]:
    created = await department_service.create_department(db, data)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=DepartmentResponse.model_validate(created),
        request_id=req_id,
    )


@router.get(
    "",
    response_model=PaginatedResponse[DepartmentResponse],
    summary="List Departments",
    description="Returns a paginated list of departments with optional search and active status filter.",
)
async def list_departments(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, code or description"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive departments"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[DepartmentResponse]:
    departments, total = await department_service.list_departments(
        db, search=search, is_active=is_active, page=page, page_size=page_size
    )
    req_id = getattr(request.state, "request_id", None)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        success=True,
        data=[DepartmentResponse.model_validate(d) for d in departments],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
        request_id=req_id,
    )


@router.get(
    "/{department_id}",
    response_model=ApiResponse[DepartmentResponse],
    summary="Get Department Details",
)
async def get_department(
    department_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DepartmentResponse]:
    dept = await department_service.get_department(db, department_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=DepartmentResponse.model_validate(dept),
        request_id=req_id,
    )


@router.patch(
    "/{department_id}",
    response_model=ApiResponse[DepartmentResponse],
    summary="Update Department",
)
async def update_department(
    department_id: uuid.UUID,
    data: DepartmentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DepartmentResponse]:
    updated = await department_service.update_department(db, department_id, data)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=DepartmentResponse.model_validate(updated),
        request_id=req_id,
    )


@router.delete(
    "/{department_id}",
    response_model=ApiResponse[dict],
    summary="Deactivate Department",
)
async def delete_department(
    department_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict]:
    await department_service.delete_department(db, department_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data={"message": f"Department {department_id} deactivated successfully."},
        request_id=req_id,
    )


@router.get(
    "/{department_id}/cameras",
    response_model=ApiResponse[DepartmentCameraSummaryResponse],
    summary="Department Camera Intelligence Summary",
    description="Returns real-time analytics on cameras owned by this department including operational health, types, and district distribution.",
)
async def get_department_cameras_summary(
    department_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DepartmentCameraSummaryResponse]:
    summary = await department_service.get_department_cameras_summary(db, department_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=summary,
        request_id=req_id,
    )
