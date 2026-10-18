from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from recollect.core.errors import AppError


class Body(BaseModel):
    url: str


def _add_test_routes(app: FastAPI) -> None:
    @app.get("/boom")
    async def boom() -> None:  # pyright: ignore[reportUnusedFunction]
        raise RuntimeError("secret internal detail")

    @app.get("/conflict")
    async def conflict() -> None:  # pyright: ignore[reportUnusedFunction]
        raise AppError(409, "already_saved", "Reel already saved")

    @app.post("/validate")
    async def validate(body: Body) -> Body:  # pyright: ignore[reportUnusedFunction]
        return body


async def test_unhandled_exception_is_generic_500(app: FastAPI) -> None:
    _add_test_routes(app)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error"}
    }
    assert "secret internal detail" not in response.text


async def test_app_error_uses_its_code(app: FastAPI, client: AsyncClient) -> None:
    _add_test_routes(app)

    response = await client.get("/conflict")

    assert response.status_code == 409
    assert response.json()["error"] == {"code": "already_saved", "message": "Reel already saved"}


async def test_validation_error_names_fields_not_values(app: FastAPI, client: AsyncClient) -> None:
    _add_test_routes(app)

    response = await client.post("/validate", json={"wrong": "value-should-not-echo"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert "body.url" in response.json()["error"]["message"]
    assert "value-should-not-echo" not in response.text
