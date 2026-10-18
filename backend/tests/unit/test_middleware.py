import logging
import uuid

import pytest
from httpx import AsyncClient

from recollect.core.logging import REDACTED, redact_sensitive


async def test_request_id_is_a_fresh_uuid_per_request(client: AsyncClient) -> None:
    first = (await client.get("/health")).headers["x-request-id"]
    second = (await client.get("/health")).headers["x-request-id"]

    assert uuid.UUID(first) != uuid.UUID(second)


async def test_security_headers_are_set(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in response.headers["content-security-policy"]
    # HSTS only in deployed environments (TLS terminates at the platform edge).
    assert "strict-transport-security" not in response.headers


async def test_cors_allows_configured_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


async def test_cors_ignores_unknown_origin(client: AsyncClient) -> None:
    response = await client.options(
        "/health",
        headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "GET"},
    )

    assert "access-control-allow-origin" not in response.headers


async def test_access_log_has_fields_but_no_query_string(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="recollect.core.middleware"):
        await client.get("/health?q=private-search-terms")

    log = " ".join(str(r.msg) for r in caplog.records)
    assert "request_completed" in log
    assert "/health" in log
    assert "duration_ms" in log
    assert "private-search-terms" not in log


def test_sensitive_log_fields_are_redacted() -> None:
    event = {"event": "x", "Authorization": "Bearer abc", "token": "t", "user_id": "u1"}

    result = redact_sensitive(None, "info", event)

    assert result["Authorization"] == REDACTED
    assert result["token"] == REDACTED
    assert result["user_id"] == "u1"
