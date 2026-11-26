from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest
import respx
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.air.cpcb import CPCB_URL
from app.config import Settings
from app.domain.readings import IST
from app.main import create_app
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
    assert "strict-transport-security" not in response.headers


def test_production_adds_hsts_and_hides_the_api_docs() -> None:
    client = make_client(
        app_env="production",
        data_gov_api_key=SecretStr("key"),
        session_secret=SecretStr("s" * 32),
    )
    assert "max-age" in client.get("/healthz").headers["strict-transport-security"]
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
    with patch("app.web.routes.health.datetime") as clock:
        clock.now.return_value = datetime(2026, 11, 23, 18, tzinfo=IST)
        assert client.get("/readyz").json() == {"status": "ok"}
    assert route.calls.last.request.headers["user-agent"] == "NirmalAir/0.1"

    respx.get(CPCB_URL).respond(503)
    client = make_client(data_gov_api_key=SecretStr("key"))  # a fresh, empty cache
    assert client.get("/readyz").status_code == 503
