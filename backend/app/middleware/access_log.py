import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import logger, user_id_ctx_var


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Logs structured information about every incoming HTTP request and outgoing response:
    method, path, status code, latency (ms), client IP, and authenticated user ID.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        
        # Process request
        response = await call_next(request)
        
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        request_id = getattr(request.state, "request_id", None)
        user_id = user_id_ctx_var.get()

        log_data = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query) if request.url.query else None,
            "status_code": response.status_code,
            "latency_ms": duration_ms,
            "client_ip": request.client.host if request.client else None,
        }

        # Filter out noisy health checks in normal logs if needed, or log at info level
        extra = {"extra_fields": log_data, "request_id": request_id}
        if user_id:
            extra["user_id"] = user_id

        if response.status_code >= 500:
            logger.error(
                f"{request.method} {request.url.path} returned {response.status_code} ({duration_ms}ms)",
                extra=extra,
            )
        elif response.status_code >= 400:
            logger.warning(
                f"{request.method} {request.url.path} returned {response.status_code} ({duration_ms}ms)",
                extra=extra,
            )
        else:
            logger.info(
                f"{request.method} {request.url.path} returned {response.status_code} ({duration_ms}ms)",
                extra=extra,
            )

        return response
