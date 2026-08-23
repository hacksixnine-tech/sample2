from app.api.v1.endpoints.departments import router as departments_router
from app.api.v1.endpoints.districts import router as districts_router
from app.api.v1.endpoints.locations import router as locations_router
from app.api.v1.endpoints.cameras import router as cameras_router
from app.api.v1.endpoints.streams import router as streams_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.gis import router as gis_router
from app.api.v1.endpoints.sources import router as sources_router
from app.api.v1.endpoints.detections import router as detections_router
from app.api.v1.endpoints.anpr import router as anpr_router
from app.api.v1.endpoints.vehicles import router as vehicles_router
from app.api.v1.endpoints.ai_results import router as ai_results_router
from app.api.v1.endpoints.evidence import router as evidence_router
from app.api.v1.endpoints.watchlists import router as watchlists_router
from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints.incidents import router as incidents_router
from app.api.v1.endpoints.investigations import router as investigations_router
from fastapi import APIRouter

# Future Step 7 routers
auth_router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])
users_router = APIRouter(prefix="/users", tags=["Users Management"])
audit_router = APIRouter(prefix="/audit", tags=["Governance & Audit Trails"])

__all__ = [
    "departments_router",
    "districts_router",
    "locations_router",
    "cameras_router",
    "streams_router",
    "health_router",
    "gis_router",
    "sources_router",
    "auth_router",
    "users_router",
    "detections_router",
    "anpr_router",
    "vehicles_router",
    "ai_results_router",
    "watchlists_router",
    "alerts_router",
    "incidents_router",
    "investigations_router",
    "evidence_router",
    "audit_router",
]
