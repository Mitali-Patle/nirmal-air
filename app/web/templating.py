"""The Jinja environment every page shares.

Autoescaping is always on and undefined variables raise, so a template mistake fails in tests
instead of rendering an empty gap. AI and user text is never marked safe.
"""

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.advice.facts import clock, number
from app.web.session import csrf_token

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

environment = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True, undefined=StrictUndefined
)


def distance_label(km: float) -> str:
    """A station distance as people say it.

    >>> distance_label(0.4), distance_label(12.34)
    ('under 1 km', '12.3 km')
    """
    return "under 1 km" if km < 1 else f"{number(round(km, 1))} km"


environment.filters["clock"] = clock
environment.filters["km"] = distance_label


def common_context(request: Request) -> dict[str, Any]:
    """Values every page needs.

    Args:
        request: The incoming request.

    Returns:
        The CSRF token for forms and htmx requests.
    """
    return {"csrf_token": csrf_token(request)}


templates = Jinja2Templates(env=environment, context_processors=[common_context])
