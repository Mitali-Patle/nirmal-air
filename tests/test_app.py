from datetime import datetime
from typing import Any

import pytest
import respx
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.air.cpcb import CPCB_URL
from app.config import Settings
from app.domain.readings import IST
from app.main import create_app
from app.web.security import BodySizeLimitMiddleware
from tests.conftest import load_fixture


def make_settings(**values: Any) -> Settings:
    return Settings(_env_file=None, **{"app_env": "test", **values})


def make_client(**values: Any) -> TestClient:
    return TestClient(create_app(make_settings(**values)))


def test_health_answers_get_and_head() -> None:
    client = make_client()
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.head("/healthz").status_code == 200


def test_every_response_carries_the_security_headers() -> None:
    with make_client() as client:  # also runs the lifespan, which the headers skip
        response = client.get("/healthz")
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["x-frame-options"] == "DENY"
    assert "geolocation=(self)" in response.headers["permissions-policy"]
    assert response.headers["cross-origin-resource-policy"] == "same-origin"
    assert response.headers["x-permitted-cross-domain-policies"] == "none"
    assert "strict-transport-security" not in response.headers
    assert "upgrade-insecure-requests" not in response.headers["content-security-policy"]


def test_production_adds_hsts_and_hides_the_api_docs() -> None:
    client = make_client(
        app_env="production",
        data_gov_api_key=SecretStr("key"),
        session_secret=SecretStr("s" * 32),
    )
    headers = client.get("/healthz").headers
    assert "max-age" in headers["strict-transport-security"]
    assert headers["content-security-policy"].endswith("; upgrade-insecure-requests")
    assert client.get("/docs").status_code == 404


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"session_secret": SecretStr("s" * 32)}, "DATA_GOV_API_KEY"),
        ({"data_gov_api_key": SecretStr("key"), "session_secret": SecretStr("short")}, "32"),
    ],
)
def test_production_refuses_to_start_without_its_secrets(
    overrides: dict[str, Any], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        make_settings(app_env="production", **overrides)


def test_readyz_is_unavailable_without_a_data_key() -> None:
    response = make_client().get("/readyz")
    assert (response.status_code, response.json()) == (503, {"status": "unavailable"})


@respx.mock
def test_readyz_reports_whether_cpcb_answers() -> None:
    client = make_client(data_gov_api_key=SecretStr("key"))
    route = respx.get(CPCB_URL).respond(json=load_fixture("cpcb_talkatora.json"))
    client.app.state.services.clock = lambda: datetime(2026, 11, 23, 18, tzinfo=IST)  # type: ignore[attr-defined]
    assert client.get("/readyz").json() == {"status": "ok"}
    assert route.calls.last.request.headers["user-agent"] == "NirmalAir/0.1"

    respx.get(CPCB_URL).respond(503)
    client = make_client(data_gov_api_key=SecretStr("key"))  # a fresh, empty cache
    assert client.get("/readyz").status_code == 503


async def _call(app: Any, headers: list[tuple[bytes, bytes]], chunks: list[bytes]) -> list[Any]:
    """Send one raw ASGI request with the given body chunks; return what the app sent."""
    sent: list[Any] = []
    messages = [{"type": "http.request", "body": chunk, "more_body": True} for chunk in chunks]
    messages.append({"type": "http.request", "body": b"", "more_body": False})

    async def receive() -> Any:
        return messages.pop(0)

    async def send(message: Any) -> None:
        sent.append(message)

    scope = {"type": "http", "method": "POST", "path": "/", "headers": headers}
    await app(scope, receive, send)
    return sent


async def _reads_the_body(scope: Any, receive: Any, send: Any) -> None:
    while (await receive()).get("more_body"):
        pass
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


async def test_bodies_over_the_limit_are_refused_even_without_a_length() -> None:
    guard = BodySizeLimitMiddleware(_reads_the_body, max_bytes=10)
    small = await _call(guard, [(b"content-length", b"4")], [b"tiny"])
    assert small[0]["status"] == 200
    declared = await _call(guard, [(b"content-length", b"11")], [b"x" * 11])
    assert declared[0]["status"] == 413
    undeclared = await _call(guard, [], [b"x" * 6, b"x" * 6])
    assert undeclared[0]["status"] == 413
    garbled = await _call(guard, [(b"content-length", b"ten")], [b""])
    assert garbled[0]["status"] == 413


async def test_a_client_that_disconnects_is_passed_through() -> None:
    seen: list[str] = []

    async def app(scope: Any, receive: Any, send: Any) -> None:
        seen.append((await receive())["type"])

    async def receive() -> Any:
        return {"type": "http.disconnect"}

    async def send(message: Any) -> None:
        return None

    guard = BodySizeLimitMiddleware(app, max_bytes=10)
    await guard({"type": "http", "method": "POST", "path": "/", "headers": []}, receive, send)
    assert seen == ["http.disconnect"]
