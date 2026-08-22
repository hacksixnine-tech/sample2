from datetime import datetime, timezone
from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import InfoResponse

router = APIRouter(tags=["System Info"])


@router.get(
    "/info",
    response_model=InfoResponse,
    summary="System Architecture & Metadata",
    description="Returns public platform metadata, API versioning, and enabled module extensions without leaking credentials.",
)
async def get_system_info() -> InfoResponse:
    return InfoResponse(
        application=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        api_prefix=settings.API_V1_STR,
        timestamp=datetime.now(timezone.utc),
        active_modules=[
            "core.config",
            "core.security",
            "core.logging",
            "core.exceptions",
            "middleware.request_id",
            "middleware.access_log",
            "db.session.asyncpg",
            "api.v1.health",
            "api.v1.info",
            "api.v1.cameras",
            "api.v1.sources",
            "api.v1.detections",
            "api.v1.anpr",
            "api.v1.vehicles",
            "api.v1.ai.results",
            "api.v1.evidence",
            "ai.workers.separated",
            "api.v1.auth.stub",
            "api.v1.watchlists.stub",
            "api.v1.alerts.stub",
            "api.v1.incidents.stub",
        ],
    )
