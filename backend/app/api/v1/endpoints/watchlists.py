import math
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_auth import (
    Principal,
    require_watchlist_manage,
    require_watchlist_read,
)
from app.db.dependencies import get_db
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistEntryCreate,
    WatchlistEntryResponse,
    WatchlistEntryUpdate,
    WatchlistResponse,
    WatchlistUpdate,
)
from app.services.watchlist_service import WatchlistService

router = APIRouter(prefix="/watchlists", tags=["Watchlists & Hotlists"])
service = WatchlistService()


def _client_meta(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


# -----------------------------------------------------------------------------
# Watchlists CRUD
# -----------------------------------------------------------------------------


@router.post(
    "",
    response_model=ApiResponse[WatchlistResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Watchlist",
    description="Registers a new hotlist or category-specific watchlist.",
)
async def create_watchlist(
    data: WatchlistCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_watchlist_manage),
) -> ApiResponse[WatchlistResponse]:
    created = await service.create_watchlist(
        db,
        data,
        user_id=principal.user_id,
        user_department_id=principal.department_id,
        **_client_meta(request),
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=WatchlistResponse.model_validate(created),
        request_id=req_id,
    )


@router.get(
    "",
    response_model=PaginatedResponse[WatchlistResponse],
    summary="List Watchlists",
)
async def list_watchlists(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Category filter"),
    is_active: Optional[bool] = Query(None, description="Active status filter"),
    search: Optional[str] = Query(None, description="Search by name, code or description"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_watchlist_read),
) -> PaginatedResponse[WatchlistResponse]:
    watchlists, total = await service.list_watchlists(
        db,
        department_id=principal.department_id if "SYSTEM_ADMIN" not in principal.roles else None,
        category=category,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    req_id = getattr(request.state, "request_id", None)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        success=True,
        data=[WatchlistResponse.model_validate(w) for w in watchlists],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
        request_id=req_id,
    )


@router.get(
    "/{watchlist_id}",
    response_model=ApiResponse[WatchlistResponse],
    summary="Get Watchlist Details",
)
async def get_watchlist(
    watchlist_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_watchlist_read),
) -> ApiResponse[WatchlistResponse]:
    wl = await service.get_watchlist(db, watchlist_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=WatchlistResponse.model_validate(wl),
        request_id=req_id,
    )


@router.patch(
    "/{watchlist_id}",
    response_model=ApiResponse[WatchlistResponse],
    summary="Update Watchlist",
)
async def update_watchlist(
    watchlist_id: uuid.UUID,
    data: WatchlistUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_watchlist_manage),
) -> ApiResponse[WatchlistResponse]:
    updated = await service.update_watchlist(
        db,
        watchlist_id,
        data,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=WatchlistResponse.model_validate(updated),
        request_id=req_id,
    )


@router.delete(
    "/{watchlist_id}",
    response_model=ApiResponse[dict],
    summary="Deactivate Watchlist",
)
async def delete_watchlist(
    watchlist_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_watchlist_manage),
) -> ApiResponse[dict]:
    await service.delete_watchlist(
        db, watchlist_id, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data={"message": f"Watchlist {watchlist_id} deactivated successfully."},
        request_id=req_id,
    )


# -----------------------------------------------------------------------------
# Watchlist Entries CRUD
# -----------------------------------------------------------------------------


@router.post(
    "/{watchlist_id}/entries",
    response_model=ApiResponse[WatchlistEntryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add Watchlist Entry",
)
async def create_watchlist_entry(
    watchlist_id: uuid.UUID,
    data: WatchlistEntryCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_watchlist_manage),
) -> ApiResponse[WatchlistEntryResponse]:
    entry = await service.create_entry(
        db,
        watchlist_id,
        data,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=WatchlistEntryResponse.model_validate(entry),
        request_id=req_id,
    )


@router.get(
    "/{watchlist_id}/entries",
    response_model=PaginatedResponse[WatchlistEntryResponse],
    summary="List Watchlist Entries",
)
async def list_watchlist_entries(
    watchlist_id: uuid.UUID,
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Active status filter"),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_watchlist_read),
) -> PaginatedResponse[WatchlistEntryResponse]:
    entries, total = await service.list_entries(
        db, watchlist_id, is_active=is_active, page=page, page_size=page_size
    )
    req_id = getattr(request.state, "request_id", None)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        success=True,
        data=[WatchlistEntryResponse.model_validate(e) for e in entries],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
        request_id=req_id,
    )


@router.get(
    "/{watchlist_id}/entries/{entry_id}",
    response_model=ApiResponse[WatchlistEntryResponse],
    summary="Get Watchlist Entry Details",
)
async def get_watchlist_entry(
    watchlist_id: uuid.UUID,
    entry_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_watchlist_read),
) -> ApiResponse[WatchlistEntryResponse]:
    entry = await service.get_entry(db, watchlist_id, entry_id)
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=WatchlistEntryResponse.model_validate(entry),
        request_id=req_id,
    )


@router.patch(
    "/{watchlist_id}/entries/{entry_id}",
    response_model=ApiResponse[WatchlistEntryResponse],
    summary="Update Watchlist Entry",
)
async def update_watchlist_entry(
    watchlist_id: uuid.UUID,
    entry_id: uuid.UUID,
    data: WatchlistEntryUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_watchlist_manage),
) -> ApiResponse[WatchlistEntryResponse]:
    updated = await service.update_entry(
        db,
        watchlist_id,
        entry_id,
        data,
        user_id=principal.user_id,
        **_client_meta(request),
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=WatchlistEntryResponse.model_validate(updated),
        request_id=req_id,
    )


@router.delete(
    "/{watchlist_id}/entries/{entry_id}",
    response_model=ApiResponse[dict],
    summary="Deactivate Watchlist Entry",
)
async def delete_watchlist_entry(
    watchlist_id: uuid.UUID,
    entry_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_watchlist_manage),
) -> ApiResponse[dict]:
    await service.delete_entry(
        db, watchlist_id, entry_id, user_id=principal.user_id, **_client_meta(request)
    )
    req_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data={"message": f"Watchlist entry {entry_id} deactivated successfully."},
        request_id=req_id,
    )
