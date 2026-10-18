import time
import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import TokenFactory


async def test_me_returns_caller_for_valid_token(
    client: AsyncClient, make_token: TokenFactory
) -> None:
    user_id = str(uuid.uuid4())
    response = await client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {make_token(sub=user_id)}"}
    )

    assert response.status_code == 200
    assert response.json() == {"id": user_id, "email": "user@example.com"}


async def test_missing_token_is_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["error"] == {"code": "unauthorized", "message": "Missing bearer token"}


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"exp": int(time.time()) - 10}, "Token expired"),
        ({"aud": "anon"}, "Invalid token"),
        ({"iss": "https://evil.example.com/auth/v1"}, "Invalid token"),
        ({"_key": "a-different-secret-that-is-32-bytes!!"}, "Invalid token"),
        ({"sub": None}, "Invalid token"),
        ({"sub": "not-a-uuid"}, "Invalid token subject"),
    ],
    ids=["expired", "wrong-audience", "wrong-issuer", "bad-signature", "no-sub", "bad-sub"],
)
async def test_invalid_tokens_are_401(
    client: AsyncClient, make_token: TokenFactory, overrides: dict[str, object], message: str
) -> None:
    response = await client.get(
        "/api/v1/me", headers={"Authorization": f"Bearer {make_token(**overrides)}"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == message


async def test_garbage_token_is_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me", headers={"Authorization": "Bearer not.a.jwt"})

    assert response.status_code == 401


async def test_unsigned_alg_none_token_is_rejected(client: AsyncClient) -> None:
    import base64
    import json

    def b64(obj: dict[str, object]) -> str:
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()

    token = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'sub': str(uuid.uuid4())})}."
    response = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


async def test_jwks_es256_token_is_accepted_when_no_shared_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hosted Supabase path: asymmetric key from JWKS, no SUPABASE_JWT_SECRET."""
    from types import SimpleNamespace

    import jwt
    from cryptography.hazmat.primitives.asymmetric import ec

    from recollect.core import security
    from recollect.core.config import Settings

    private_key = ec.generate_private_key(ec.SECP256R1())
    settings = Settings(ENVIRONMENT="test", SUPABASE_URL="https://abc.supabase.co")

    class FakeJwks:
        def get_signing_key_from_jwt(self, _token: str) -> SimpleNamespace:
            return SimpleNamespace(key=private_key.public_key())

    def fake_jwks_client(_url: str) -> FakeJwks:
        return FakeJwks()

    monkeypatch.setattr(security, "_jwks_client", fake_jwks_client)
    user_id = str(uuid.uuid4())
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": user_id,
            "aud": "authenticated",
            "iss": settings.supabase_issuer,
            "exp": now + 60,
        },
        private_key,
        algorithm="ES256",
    )

    claims = security.decode_token(token, settings)

    assert claims["sub"] == user_id
