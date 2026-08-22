from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api.deps_auth import Principal, require_evidence_access
from app.db.dependencies import get_db
from app.schemas.analytics import EvidenceResponse
from app.schemas.common import ApiResponse
from app.services.analytics_service import AnalyticsIngestionService

router = APIRouter(prefix="/evidence", tags=["Evidence & Object Storage"])
service = AnalyticsIngestionService()


@router.get(
    "/{evidence_id}",
    response_model=ApiResponse[EvidenceResponse],
    summary="Get evidence metadata",
    description="Returns integrity metadata and an opaque storage reference. Internal filesystem/object keys are not exposed.",
)
async def get_evidence(
    evidence_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_evidence_access),
) -> ApiResponse[EvidenceResponse]:
    data = await service.get_evidence(
        db,
        evidence_id,
        user_id=principal.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return ApiResponse(success=True, data=data, request_id=getattr(request.state, "request_id", None))
