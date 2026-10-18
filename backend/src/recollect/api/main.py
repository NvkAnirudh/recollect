"""FastAPI application factory.

Run locally: `uv run uvicorn recollect.api.main:app --reload`
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from recollect.api.v1.me import router as me_router
from recollect.core.config import Settings, get_settings
from recollect.core.errors import register_error_handlers
from recollect.core.logging import setup_logging
from recollect.core.middleware import (
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    limiter,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings)

    app = FastAPI(
        title="Recollect API",
        version="0.1.0",
        # Interactive docs only outside deployed environments.
        docs_url=None if settings.is_deployed else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_deployed else "/openapi.json",
    )

    app.state.limiter = limiter
    register_error_handlers(app)

    # Starlette runs middleware in reverse order of registration: the last added is outermost.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=False,  # bearer tokens, not cookies
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Timezone"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_deployed)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    app.include_router(me_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        return {"status": "ok"}

    return app


app = create_app()
