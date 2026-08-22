from datetime import datetime, timezone
from fastapi import APIRouter, Response, status

from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Health & Diagnostics"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Liveness Probe",
    description="Returns the operational status of the API service without inspecting downstream dependencies.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        environment=settings.APP_ENV,
        version=settings.APP_VERSION,
    )


@router.get(
    "/health/live",
    response_model=HealthResponse,
    summary="Kubernetes / Container Liveness Check",
    description="Confirms that the FastAPI process is alive and accepting incoming connections.",
)
async def liveness_check() -> HealthResponse:
    return HealthResponse(
        status="live",
        timestamp=datetime.now(timezone.utc),
        environment=settings.APP_ENV,
        version=settings.APP_VERSION,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Kubernetes / Container Readiness Check",
    description="Validates database connectivity and service readiness before routing traffic.",
)
async def readiness_check(response: Response) -> ReadinessResponse:
    db_status = await check_db_connection()
    is_ready = db_status.get("connected", False)

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        timestamp=datetime.now(timezone.utc),
        database=db_status,
    )
