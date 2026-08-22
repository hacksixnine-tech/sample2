import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_ctx_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Extracts or generates an X-Request-ID for every incoming HTTP request,
    stores it in contextvars for log correlation, and attaches it to response headers.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check incoming header or generate a new UUIDv4
        req_id = request.headers.get("X-Request-ID")
        if not req_id:
            req_id = str(uuid.uuid4())

        # Store on request state and contextvar
        request.state.request_id = req_id
        token = request_id_ctx_var.set(req_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx_var.reset(token)
