"""Authentication: verify Supabase-issued JWTs and expose the caller.

Every route except `/health` depends on `get_current_user`. Tokens are verified
locally, without a network call per request:
- Hosted Supabase: asymmetric signing keys fetched (and cached) from JWKS.
- Local Supabase (`supabase start`): HS256 with SUPABASE_JWT_SECRET.
"""

import functools
import uuid
from dataclasses import dataclass
from typing import Annotated, Any

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from recollect.core.config import Settings, get_settings
from recollect.core.errors import AppError

ASYMMETRIC_ALGORITHMS = ["ES256", "RS256", "EdDSA"]

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: uuid.UUID
    email: str | None


def _unauthorized(message: str) -> AppError:
    return AppError(401, "unauthorized", message)


@functools.lru_cache
def _jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)


def decode_token(token: str, settings: Settings) -> dict[str, Any]:
    """Validate signature, expiry, issuer and audience. Raises AppError(401)."""
    try:
        if settings.SUPABASE_JWT_SECRET:
            key: Any = settings.SUPABASE_JWT_SECRET
            algorithms = ["HS256"]
        else:
            key = _jwks_client(settings.supabase_jwks_url).get_signing_key_from_jwt(token).key
            algorithms = ASYMMETRIC_ALGORITHMS
        return jwt.decode(
            token,
            key,
            algorithms=algorithms,
            audience=settings.SUPABASE_JWT_AUDIENCE,
            issuer=settings.supabase_issuer,
            options={"require": ["exp", "sub", "iss", "aud"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise _unauthorized("Token expired") from exc
    except (jwt.PyJWTError, ValueError) as exc:
        raise _unauthorized("Invalid token") from exc


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if credentials is None:
        raise _unauthorized("Missing bearer token")
    claims = decode_token(credentials.credentials, settings)
    try:
        user_id = uuid.UUID(str(claims["sub"]))
    except ValueError as exc:
        raise _unauthorized("Invalid token subject") from exc
    email = claims.get("email")
    return CurrentUser(id=user_id, email=email if isinstance(email, str) else None)


AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
