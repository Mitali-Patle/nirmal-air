"""The Jinja environment every page shares.

Autoescaping is always on and undefined variables raise, so a template mistake fails in tests
instead of rendering an empty gap. AI and user text is never marked safe.
"""

import os
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.advice.facts import clock, distance_label, number
from app.web.csrf import csrf_token

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
# Vercel sets the commit of each deploy; locally the version is simply "dev".
ASSET_VERSION = os.environ.get("VERCEL_GIT_COMMIT_SHA", "dev")[:8]

environment = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True, undefined=StrictUndefined
)


def kilograms(grams: int) -> str:
    """Grams as kilograms to one decimal place.

    >>> kilograms(3000), kilograms(1680)
    ('3', '1.7')
    """
    return number(round(grams / 1000, 1))


def asset_url(path: str) -> str:
    """A static file's URL with this deploy's version, so browsers never keep an old copy.

    >>> asset_url("css/today.css").startswith("/static/css/today.css?v=")
    True
    """
    return f"/static/{path}?v={ASSET_VERSION}"


def common_context(request: Request) -> dict[str, Any]:
    """Values every page needs.

    Args:
        request: The incoming request.

    Returns:
        The CSRF token for forms and htmx requests.
    """
    return {"csrf_token": csrf_token(request)}


environment.filters["asset"] = asset_url
environment.filters["clock"] = clock
environment.filters["km"] = distance_label
environment.filters["kg"] = kilograms
environment.filters["num"] = number

templates = Jinja2Templates(env=environment, context_processors=[common_context])
