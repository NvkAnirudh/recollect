"""HTTP middleware: request IDs, access logging, security headers, rate limiting.

Access logs carry only method, path, status, duration and request_id; never
bodies or query strings, which may contain user content (search queries, URLs).
"""

import time
import uuid

import structlog
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from recollect.core.config import get_settings

logger = structlog.stdlib.get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    # JSON API: nothing should ever be rendered or framed from it.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
HSTS_VALUE = "max-age=63072000; includeSubDomains"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a fresh UUID to each request, its logs, and its response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        await logger.ainfo(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round((time.perf_counter() - start) * 1000, 2),
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, *, hsts: bool) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._hsts = hsts

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        if self._hsts:
            response.headers["Strict-Transport-Security"] = HSTS_VALUE
        return response


def create_limiter() -> Limiter:
    return Limiter(key_func=get_remote_address, default_limits=[get_settings().RATE_LIMIT])


limiter = create_limiter()
