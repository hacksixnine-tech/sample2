from collections import defaultdict
import time
from typing import Dict, List, Optional, Tuple
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window in-memory rate limiter protecting against brute-force attacks
    and Denial-of-Service on critical API endpoints.
    """

    def __init__(
        self,
        app,
        enabled: bool = True,
        requests_per_window: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ):
        super().__init__(app)
        self.enabled = enabled
        self.default_requests = requests_per_window or 300
        self.default_window = window_seconds or 60

        # Key: (ip, route_type) -> list of timestamp floats
        self._history: Dict[Tuple[str, str], List[float]] = defaultdict(list)

        # Route specific rules: (prefix, max_requests, window_seconds)
        self.rules = [
            ("/api/v1/auth/login", 10, 60),
            ("/api/v1/vehicles/search", 60, 60),
            ("/api/v1/", self.default_requests, self.default_window),
        ]

        # Exempt paths
        self.exempt_prefixes = [
            "/health",
            "/api/v1/health",
            "/api/v1/docs",
            "/api/v1/openapi.json",
            "/api/v1/redoc",
        ]

    def _get_rule_for_path(self, path: str) -> Tuple[str, int, int]:
        for prefix, max_reqs, window in self.rules:
            if path.startswith(prefix):
                return prefix, max_reqs, window
        return "/api/v1/", self.default_requests, self.default_window

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not self.enabled:
            return await call_next(request)

        # Check WebSocket upgrade or exempt routes
        if request.scope.get("type") == "websocket":
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(exempt) for exempt in self.exempt_prefixes):
            return await call_next(request)

        # Extract client IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        prefix, max_requests, window_seconds = self._get_rule_for_path(path)
        key = (client_ip, prefix)
        now = time.time()

        # Clean old timestamps
        cutoff = now - window_seconds
        timestamps = [t for t in self._history[key] if t > cutoff]
        self._history[key] = timestamps

        if len(timestamps) >= max_requests:
            oldest = timestamps[0]
            retry_after = max(1, int(window_seconds - (now - oldest)))
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Too many requests to {prefix}. Rate limit exceeded.",
                        "details": {"retry_after_seconds": retry_after, "limit": max_requests, "window_seconds": window_seconds},
                    },
                    "request_id": request_id,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(oldest + window_seconds)),
                    **({"X-Request-ID": request_id} if request_id else {}),
                },
            )

        # Record this request timestamp
        self._history[key].append(now)
        response = await call_next(request)

        # Attach rate limit remaining headers
        remaining = max_requests - len(self._history[key])
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

        return response
