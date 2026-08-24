from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api.deps_auth import Principal, require_evidence_access
from app.db.dependencies import get_db
from app.schemas.analytics import EvidenceResponse
from app.schemas.common import ApiResponse
from app.schemas.investigation import EvidenceVerificationResponse
from app.services.analytics_service import AnalyticsIngestionService
from app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/evidence", tags=["Evidence & Object Storage"])
analytics_service = AnalyticsIngestionService()
investigation_service = InvestigationService()


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
    data = await analytics_service.get_evidence(
        db,
        evidence_id,
        user_id=principal.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return ApiResponse(success=True, data=data, request_id=getattr(request.state, "request_id", None))


@router.get(
    "/{evidence_id}/verify",
    response_model=ApiResponse[EvidenceVerificationResponse],
    summary="Verify Cryptographic Evidence Integrity",
    description="Validates cryptographic checksum integrity (SHA-256) of an evidence object against the immutable ledger.",
)
async def verify_evidence_integrity(
    evidence_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_evidence_access),
) -> ApiResponse[EvidenceVerificationResponse]:
    data = await investigation_service.verify_evidence_integrity(
        db,
        evidence_id,
        user_id=principal.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return ApiResponse(success=True, data=data, request_id=getattr(request.state, "request_id", None))
