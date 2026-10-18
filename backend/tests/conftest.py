import time
import uuid
from collections.abc import AsyncIterator, Callable
from typing import Any

import jwt
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from recollect.api.main import create_app
from recollect.core.config import Settings, get_settings

TEST_JWT_SECRET = "test-secret-at-least-32-bytes-long!!"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ENVIRONMENT="test",
        SUPABASE_URL="http://supabase.test",
        SUPABASE_JWT_SECRET=TEST_JWT_SECRET,
        CORS_ORIGINS=["http://localhost:3000"],
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    application = create_app(settings)
    application.dependency_overrides[get_settings] = lambda: settings
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


TokenFactory = Callable[..., str]


@pytest.fixture
def make_token(settings: Settings) -> TokenFactory:
    """Mint a Supabase-shaped HS256 access token; override any claim via kwargs."""

    def _make(**overrides: Any) -> str:
        key = overrides.pop("_key", TEST_JWT_SECRET)
        now = int(time.time())
        claims: dict[str, Any] = {
            "sub": str(uuid.uuid4()),
            "email": "user@example.com",
            "aud": settings.SUPABASE_JWT_AUDIENCE,
            "iss": settings.supabase_issuer,
            "iat": now,
            "exp": now + 3600,
            "role": "authenticated",
        }
        claims.update(overrides)
        claims = {k: v for k, v in claims.items() if v is not None}
        return jwt.encode(claims, key, algorithm="HS256")

    return _make
