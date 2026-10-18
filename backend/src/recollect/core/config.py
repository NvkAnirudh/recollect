"""Application configuration loaded from environment variables.

Development defaults let the API boot with zero configuration against a local
Supabase stack (`supabase start`). Staging and production must set real values;
`Settings` refuses to load if they still point at localhost.
"""

import functools
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENVIRONMENT: Environment = "development"

    # --- Database (local Supabase defaults) ---
    DATABASE_URL: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

    # --- Supabase Auth ---
    SUPABASE_URL: str = "http://127.0.0.1:54321"
    # Only for the local Supabase stack, which signs JWTs with a shared HS256 secret.
    # Hosted projects use asymmetric signing keys, verified via JWKS instead.
    SUPABASE_JWT_SECRET: str | None = None
    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    # --- Logging ---
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["console", "json"] = "console"

    # --- HTTP ---
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    RATE_LIMIT: str = "100/minute"
    API_V1_PREFIX: str = "/api/v1"

    @property
    def supabase_issuer(self) -> str:
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_issuer}/.well-known/jwks.json"

    @property
    def is_deployed(self) -> bool:
        return self.ENVIRONMENT in ("staging", "production")

    @model_validator(mode="after")
    def _reject_local_defaults_when_deployed(self) -> Self:
        if not self.is_deployed:
            return self
        problems: list[str] = []
        if not self.SUPABASE_URL.startswith("https://"):
            problems.append("SUPABASE_URL must be https")
        if self.SUPABASE_JWT_SECRET:
            problems.append("SUPABASE_JWT_SECRET is for local dev only; use JWKS")
        if "127.0.0.1" in self.DATABASE_URL or "localhost" in self.DATABASE_URL:
            problems.append("DATABASE_URL points at localhost")
        if any("localhost" in o or "127.0.0.1" in o or o == "*" for o in self.CORS_ORIGINS):
            problems.append("CORS_ORIGINS must list real origins (no localhost, no '*')")
        if self.LOG_FORMAT != "json":
            problems.append("LOG_FORMAT must be json")
        if problems:
            raise ValueError(f"Invalid {self.ENVIRONMENT} config: " + "; ".join(problems))
        return self


@functools.lru_cache
def get_settings() -> Settings:
    """Settings singleton, read once per process."""
    return Settings()
