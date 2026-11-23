"""Application factory: the single place where dependencies are wired together."""

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.web.routes import health
from app.web.security import SecurityHeadersMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application.

    Args:
        settings: Configuration to use. Defaults to settings read from the environment.

    Returns:
        The configured application.
    """
    settings = settings or get_settings()
    app = FastAPI(
        title="NirmalAir",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    app.state.settings = settings
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_production)
    app.include_router(health.router)
    return app
