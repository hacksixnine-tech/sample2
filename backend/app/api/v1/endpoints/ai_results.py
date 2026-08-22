from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.metrics import metrics
from app.api.deps_auth import Principal, require_ai_ingest, require_detection_read
from app.db.dependencies import get_db
from app.schemas.analytics import AIResultIngestRequest, AIResultIngestResponse
from app.schemas.common import ApiResponse
from app.services.analytics_service import AnalyticsIngestionService

router = APIRouter(prefix="/ai", tags=["AI Result Ingestion"])
service = AnalyticsIngestionService()


def _client_meta(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.post(
    "/results",
    response_model=ApiResponse[AIResultIngestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest normalized AI worker results",
    description="Control-plane ingestion contract for the compute plane. Idempotent when inference_event_id is reused.",
)
async def ingest_ai_results(
    payload: AIResultIngestRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_ai_ingest),
) -> ApiResponse[AIResultIngestResponse]:
    result = await service.ingest_ai_results(
        db, payload, actor=principal.subject, user_id=principal.user_id, **_client_meta(request)
    )
    code = status.HTTP_200_OK if result.idempotent_replay else status.HTTP_201_CREATED
    response = ApiResponse(
        success=True,
        data=result,
        request_id=getattr(request.state, "request_id", None),
    )
    return response


@router.get(
    "/metrics",
    response_model=ApiResponse[dict],
    summary="AI operational metrics",
    description="Process-local counters for frames, detections, ANPR, latency, and errors. Not an accuracy benchmark.",
)
async def ai_metrics(
    request: Request,
    principal: Principal = Depends(require_detection_read),
) -> ApiResponse[dict]:
    return ApiResponse(
        success=True,
        data=metrics.snapshot(),
        request_id=getattr(request.state, "request_id", None),
    )
