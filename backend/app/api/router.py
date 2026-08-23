from fastapi import APIRouter

from app.api.v1.health import router as system_health_router
from app.api.v1.info import router as info_router
from app.api.v1.endpoints import (
    departments_router,
    districts_router,
    locations_router,
    cameras_router,
    streams_router,
    health_router as camera_health_router,
    gis_router,
    sources_router,
    auth_router,
    users_router,
    detections_router,
    anpr_router,
    vehicles_router,
    ai_results_router,
    watchlists_router,
    alerts_router,
    incidents_router,
    investigations_router,
    evidence_router,
    audit_router,
)

api_v1_router = APIRouter()

api_v1_router.include_router(system_health_router)
api_v1_router.include_router(info_router)

api_v1_router.include_router(departments_router)
api_v1_router.include_router(districts_router)
api_v1_router.include_router(locations_router)
api_v1_router.include_router(cameras_router)
api_v1_router.include_router(streams_router)
api_v1_router.include_router(camera_health_router)
api_v1_router.include_router(gis_router)
api_v1_router.include_router(sources_router)

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(detections_router)
api_v1_router.include_router(anpr_router)
api_v1_router.include_router(vehicles_router)
api_v1_router.include_router(ai_results_router)
api_v1_router.include_router(watchlists_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(incidents_router)
api_v1_router.include_router(investigations_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(audit_router)
