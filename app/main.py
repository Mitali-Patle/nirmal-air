"""Application factory: the single place where dependencies are wired together."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.air.cpcb import USER_AGENT
from app.air.lookup import AirLookup
from app.config import Settings, get_settings
from app.web.routes import health
from app.web.security import SecurityHeadersMiddleware

# Outside services get 8 seconds: long enough for a slow CPCB reply, short enough that a
# stalled one falls back to cached or labelled data instead of a hanging page.
HTTP_TIMEOUT = httpx.Timeout(8.0, connect=4.0)


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
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_production)
    app.include_router(health.router)
    return app


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Close the shared HTTP client when the server shuts down."""
    yield
    await app.state.http.aclose()
