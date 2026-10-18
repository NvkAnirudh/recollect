"""One error shape for every response: `{"error": {"code", "message"}}`.

Unhandled exceptions are logged with their traceback and returned as a generic
500, so internal details never reach the client.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from recollect.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Raise from services/routes for expected, client-facing failures."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_body(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


_HTTP_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
}


async def _app_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):  # registered only for AppError
        raise exc
    return JSONResponse(error_body(exc.code, exc.message), status_code=exc.status_code)


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):  # registered only for StarletteHTTPException
        raise exc
    code = _HTTP_CODES.get(exc.status_code, "http_error")
    return JSONResponse(
        error_body(code, str(exc.detail)), status_code=exc.status_code, headers=exc.headers
    )


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):  # registered only for RequestValidationError
        raise exc
    fields = ", ".join(".".join(str(p) for p in e["loc"]) for e in exc.errors())
    return JSONResponse(
        error_body("validation_error", f"Invalid request: {fields}"), status_code=422
    )


async def _rate_limited(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(error_body("rate_limited", "Too many requests"), status_code=429)


async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
    await logger.aexception("unhandled_exception", exc_type=type(exc).__name__)
    return JSONResponse(error_body("internal_error", "Internal server error"), status_code=500)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(RateLimitExceeded, _rate_limited)
    app.add_exception_handler(Exception, _unhandled)
