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
from app.ai.models import default_providers
from app.air.lookup import AirLookup
from app.air.places import PlaceFinder
from app.config import USER_AGENT, Settings, get_settings
from app.domain.readings import IST
from app.services.today import TodayService
from app.web.deps import Services
from app.web.errors import register_error_handlers
from app.web.limits import AI_OVERALL, AI_PER_CLIENT, PAGE_PER_CLIENT, ClientLimits
from app.web.routes import health, start, today, week
from app.web.security import BodySizeLimitMiddleware, SecurityHeadersMiddleware

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
    _add_services(app, settings, http)
    _add_middleware(app, settings)
    register_error_handlers(app)
    for router in (health.router, start.router, today.router, week.router):
        app.include_router(router)
    if not settings.is_production:
        # In production Vercel serves public/ from its CDN; mount it for local runs and tests.
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


def _add_services(app: FastAPI, settings: Settings, http: httpx.AsyncClient) -> None:
    """The air lookup, places, AI chain and limits the routes use, kept on `app.state`."""
    key = settings.data_gov_api_key
    air_lookup = AirLookup(http, key.get_secret_value()) if key else None
    app.state.services = Services(
        settings=settings,
        http=http,
        air_lookup=air_lookup,
        today=TodayService(http, air_lookup),
        places=PlaceFinder(http),
        ai=AIChain(
            default_providers(
                http, _secret(settings.groq_api_key), _secret(settings.gemini_api_key)
            )
        ),
        ai_limits=ClientLimits(AI_PER_CLIENT, AI_OVERALL, behind_proxy=settings.is_production),
        page_limits=ClientLimits(PAGE_PER_CLIENT, behind_proxy=settings.is_production),
        # Tests replace the clock so recorded CPCB and forecast data count as current.
        clock=lambda: datetime.now(IST),
    )


def _add_middleware(app: FastAPI, settings: Settings) -> None:
    """The signed session cookie and the security headers."""
    app.add_middleware(
        SessionMiddleware,
        # Outside production a fresh secret per start is fine: sessions just reset.
        secret_key=_secret(settings.session_secret) or secrets.token_urlsafe(32),
        session_cookie="nirmalair",
        max_age=SESSION_MAX_AGE_S,
        same_site="lax",
        https_only=settings.is_production,
    )
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, https_only=settings.is_production)


def _secret(value: SecretStr | None) -> str | None:
    return value.get_secret_value() if value else None


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Close the shared HTTP client when the server shuts down."""
    yield
    await app.state.services.http.aclose()
