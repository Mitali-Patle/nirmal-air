from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.config import Settings
from app.main import create_app


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
