import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from recollect.api.main import create_app
from recollect.core.config import Settings

PROD_OK = {
    "ENVIRONMENT": "production",
    "SUPABASE_URL": "https://abc.supabase.co",
    "DATABASE_URL": "postgresql://u:p@db.abc.supabase.co:5432/postgres",
    "CORS_ORIGINS": ["https://recollect.app"],
    "LOG_FORMAT": "json",
}


def test_development_defaults_load_without_env() -> None:
    settings = Settings()

    assert settings.ENVIRONMENT == "development"
    assert settings.supabase_jwks_url == "http://127.0.0.1:54321/auth/v1/.well-known/jwks.json"


def test_valid_production_config_loads() -> None:
    assert Settings(**PROD_OK).is_deployed  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("override", "problem"),
    [
        ({"SUPABASE_URL": "http://abc.supabase.co"}, "SUPABASE_URL must be https"),
        ({"SUPABASE_JWT_SECRET": "x"}, "local dev only"),
        ({"DATABASE_URL": "postgresql://postgres@localhost/db"}, "DATABASE_URL"),
        ({"CORS_ORIGINS": ["*"]}, "CORS_ORIGINS"),
        ({"CORS_ORIGINS": ["http://localhost:3000"]}, "CORS_ORIGINS"),
        ({"LOG_FORMAT": "console"}, "LOG_FORMAT"),
    ],
)
def test_production_rejects_local_defaults(override: dict[str, object], problem: str) -> None:
    with pytest.raises(ValidationError, match=problem):
        Settings(**{**PROD_OK, **override})  # type: ignore[arg-type]


async def test_docs_hidden_and_hsts_on_when_deployed() -> None:
    app: FastAPI = create_app(Settings(**PROD_OK))  # type: ignore[arg-type]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as client:
        assert (await client.get("/docs")).status_code == 404
        assert (await client.get("/openapi.json")).status_code == 404
        health = await client.get("/health")

    assert health.headers["strict-transport-security"].startswith("max-age=")
