"""Browser tests against the real app running in a background thread.

CPCB, Open-Meteo and the place search answer with recorded replies (respx), the clock is
fixed, and no AI model is configured, so the plan is the labelled standard advice. Run with
`uv run pytest -m e2e`. Set E2E_CHROMIUM to a Chromium binary to use one that is already
installed instead of Playwright's download.
"""

import os
import socket
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest
import respx
import uvicorn
from fastapi import FastAPI
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
from pydantic import SecretStr

from app.air.cpcb import CPCB_URL
from app.air.forecast import FORECAST_URL
from app.air.places import GEOCODING_URL
from app.air.weather import WEATHER_URL
from app.config import Settings
from app.domain.readings import IST
from app.main import create_app
from tests.conftest import load_fixture

DUSK = datetime(2026, 11, 23, 18, 30, tzinfo=IST)


@dataclass
class LiveApp:
    """The running app and its address."""

    url: str
    app: FastAPI

    def at(self, moment: datetime) -> None:
        """Set the app's clock (the recorded reading is from 5 pm on 23 Nov 2026)."""
        self.app.state.services.clock = lambda: moment


NewPage = Callable[..., Page]


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


@pytest.fixture(scope="session")
def live() -> Iterator[LiveApp]:
    settings = Settings(_env_file=None, app_env="development", data_gov_api_key=SecretStr("key"))
    app = create_app(settings)
    with respx.mock(assert_all_called=False) as router:
        router.route(host="127.0.0.1").pass_through()
        router.get(CPCB_URL).respond(json=load_fixture("cpcb_talkatora.json"))
        router.get(FORECAST_URL).respond(json=load_fixture("forecast_delhi.json"))
        router.get(WEATHER_URL).respond(json=load_fixture("weather_delhi.json"))
        router.get(GEOCODING_URL).respond(json=load_fixture("places_andheri.json"))
        port = _free_port()
        server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
        )
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        deadline = time.monotonic() + 10
        while not server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("the e2e server did not start")
            time.sleep(0.05)
        live_app = LiveApp(f"http://127.0.0.1:{port}", app)
        live_app.at(DUSK)
        yield live_app
        server.should_exit = True
        thread.join(timeout=5)


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        launched = playwright.chromium.launch(
            executable_path=os.environ.get("E2E_CHROMIUM") or None
        )
        yield launched
        launched.close()


@pytest.fixture
def new_page(browser: Browser, live: LiveApp) -> Iterator[NewPage]:
    """Open a page in a fresh context (its own cookie session) with the given options."""
    contexts: list[BrowserContext] = []

    def open_page(**options: Any) -> Page:
        options = {"reduced_motion": "reduce", **options}
        context = browser.new_context(base_url=live.url, locale="en-IN", **options)
        contexts.append(context)
        return context.new_page()

    yield open_page
    for context in contexts:
        context.close()
    live.at(DUSK)
