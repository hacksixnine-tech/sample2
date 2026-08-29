from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import PhantomException
from app.core.logging import logger, setup_logging
from app.db.session import check_db_connection, close_db_connection
from app.middleware.access_log import AccessLogMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.api.router import api_v1_router
from app.api.v1.health import router as root_health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager handling startup and shutdown events."""
    # 1. Initialize structured logging
    setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in [{settings.APP_ENV}] mode..."
    )

    # 2. Test database connectivity on startup
    db_health = await check_db_connection()
    if db_health.get("connected"):
        logger.info(
            f"Database connected successfully: {db_health.get('postgres_version')} | {db_health.get('postgis_version')}"
        )
    else:
        logger.warning(
            f"Database connection check warning: {db_health.get('error', 'Unable to reach DB')}"
        )

    yield

    # 3. Graceful shutdown
    logger.info("Initiating graceful shutdown...")
    from app.services.stream_gateway_service import stream_gateway_service
    stream_gateway_service.cleanup_all()
    await close_db_connection()
    logger.info("Application shutdown complete.")


def create_application() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Statewide Video Intelligence & Investigation Platform for Gujarat CCTV Hackathon 2026",
        docs_url=f"{settings.API_V1_STR}/docs" if not settings.is_production else None,
        redoc_url=f"{settings.API_V1_STR}/redoc" if not settings.is_production else None,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # 1. Register Middlewares (Order: Outer to Inner)
    # Trusted Hosts
    if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Security Headers (XSS, clickjacking, CSP, HSTS)
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate Limiting (120 req/min general, 30 req/min for auth endpoints)
    app.add_middleware(RateLimitMiddleware, requests_per_window=120, window_seconds=60)

    # Access Logging & Correlation Request ID
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # 2. Register Global Exception Handlers for Unified API Error Format
    @app.exception_handler(PhantomException)
    async def phantom_exception_handler(request: Request, exc: PhantomException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        formatted_errors = []
        for error in exc.errors():
            loc = " -> ".join(str(l) for l in error.get("loc", []))
            formatted_errors.append({
                "field": loc,
                "message": error.get("msg"),
                "type": error.get("type"),
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed. Please check request parameters.",
                    "details": formatted_errors,
                },
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": None,
                },
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception(f"Unhandled server exception: {str(exc)}", extra={"request_id": request_id})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact system administrator.",
                    "details": None,
                },
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    # 3. Mount Routers
    # Root-level health endpoints (e.g. /health, /health/ready, /health/live)
    app.include_router(root_health_router)

    # Versioned API routes under /api/v1
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # 4. Mount Visual Command Center Dashboard
    import os
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")

        @app.get("/", include_in_schema=False)
        async def root_redirect():
            return FileResponse("static/index.html")

        @app.get("/dashboard", include_in_schema=False)
        async def dashboard_view():
            return FileResponse("static/index.html")

    return app


app = create_application()
