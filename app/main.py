"""Application factory: the single place where dependencies are wired together."""

import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import SecretStr
from starlette.middleware.sessions import SessionMiddleware

from app.ai.chain import AIChain
from app.ai.providers import default_providers
from app.air.cpcb import IST, USER_AGENT
from app.air.lookup import AirLookup
from app.air.places import PlaceFinder
from app.config import Settings, get_settings
from app.services.today import TodayService
from app.web.errors import register_error_handlers
from app.web.limits import AILimits
from app.web.routes import health, start, today, week
from app.web.security import SecurityHeadersMiddleware

# Outside services get 8 seconds: long enough for a slow CPCB reply, short enough that a
# stalled one falls back to cached or labelled data instead of a hanging page.
HTTP_TIMEOUT = httpx.Timeout(8.0, connect=4.0)
STATIC_DIR = Path(__file__).resolve().parent.parent / "public" / "static"
SESSION_MAX_AGE_S = 30 * 24 * 3600


def create_app(settings: Settings | None = None, http: httpx.AsyncClient | None = None) -> FastAPI:
    """Build the FastAPI application.

    Args:
        settings: Configuration to use. Defaults to settings read from the environment.
        http: Client for outside services (tests pass a mocked one). Defaults to a shared
            client with the app's timeouts and User-Agent.

    Returns:
        The configured application.
    """
    settings = settings or get_settings()
    http = http or httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers={"User-Agent": USER_AGENT})
    app = FastAPI(
        title="NirmalAir",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=_lifespan,
    )
    app.state.settings = settings
    app.state.http = http
    key = settings.data_gov_api_key
    app.state.air_lookup = AirLookup(http, key.get_secret_value()) if key else None
    app.state.today = TodayService(http, app.state.air_lookup)
    app.state.places = PlaceFinder(http)
    # Tests replace the clock so recorded CPCB and forecast data count as current.
    app.state.clock = lambda: datetime.now(IST)
    app.state.ai_limits = AILimits()
    app.state.ai = AIChain(
        default_providers(http, _secret(settings.groq_api_key), _secret(settings.gemini_api_key))
    )
    app.add_middleware(
        SessionMiddleware,
        # Outside production a fresh secret per start is fine: sessions just reset.
        secret_key=_secret(settings.session_secret) or secrets.token_urlsafe(32),
        session_cookie="nirmalair",
        max_age=SESSION_MAX_AGE_S,
        same_site="lax",
        https_only=settings.is_production,
    )
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_production)
    register_error_handlers(app)
    for router in (health.router, start.router, today.router, week.router):
        app.include_router(router)
    if not settings.is_production:
        # In production Vercel serves public/ from its CDN; mount it for local runs and tests.
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


def _secret(value: SecretStr | None) -> str | None:
    return value.get_secret_value() if value else None


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Close the shared HTTP client when the server shuts down."""
    yield
    await app.state.http.aclose()
