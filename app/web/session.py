"""What the app remembers about a visitor, kept in a signed cookie (no accounts, no database).

The cookie holds the chosen place, the household profile, a CSRF token and a theme choice.
It is signed with SESSION_SECRET, so it cannot be altered, and it is HttpOnly, so page
scripts cannot read it. Nothing about the household is stored on the server.
"""

import secrets
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, Form, HTTPException, Request, status
from pydantic import ValidationError

from app.domain.household import Household
from app.services.today import PlaceChoice

CSRF_KEY = "csrf"
PLACE_KEY = "place"
HOUSEHOLD_KEY = "household"
THEME_KEY = "theme"
SAMPLE_KEY = "sample"
CSRF_HEADER = "x-csrf-token"


class ThemeChoice(StrEnum):
    """How the page picks light or dark."""

    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"


def csrf_token(request: Request) -> str:
    """This visitor's CSRF token, created on first use.

    Args:
        request: The incoming request.

    Returns:
        A random token kept in the session.
    """
    token = request.session.get(CSRF_KEY)
    if not isinstance(token, str):
        token = secrets.token_urlsafe(32)
        request.session[CSRF_KEY] = token
    return token


async def require_csrf(request: Request, csrf: Annotated[str | None, Form()] = None) -> None:
    """Reject a POST whose CSRF token (form field or htmx header) does not match the session.

    Args:
        request: The incoming request.
        csrf: The token sent in the form, if any.

    Raises:
        HTTPException: 403 when the token is missing or wrong.
    """
    sent = csrf or request.headers.get(CSRF_HEADER, "")
    expected = request.session.get(CSRF_KEY)
    if not isinstance(expected, str) or not secrets.compare_digest(sent, expected):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "The form expired. Reload and try again.")


CsrfChecked = Depends(require_csrf)


def save_household(
    request: Request, place: PlaceChoice, household: Household, sample: str | None = None
) -> None:
    """Remember a household and its place.

    Args:
        request: The incoming request.
        place: Where the household is.
        household: The validated profile.
        sample: The sample's title when this is a sample household, so the page can say so.
    """
    request.session[PLACE_KEY] = {"label": place.label, "lat": place.lat, "lon": place.lon}
    request.session[HOUSEHOLD_KEY] = household.model_dump(mode="json", exclude_defaults=True)
    if sample:
        request.session[SAMPLE_KEY] = sample
    else:
        request.session.pop(SAMPLE_KEY, None)


def sample_title(request: Request) -> str | None:
    """The sample household's title, if the saved household is a sample.

    Args:
        request: The incoming request.

    Returns:
        The title, or None for the visitor's own household.
    """
    title = request.session.get(SAMPLE_KEY)
    return title if isinstance(title, str) else None


def load_household(request: Request) -> tuple[PlaceChoice, Household] | None:
    """The remembered household and place, if any.

    Args:
        request: The incoming request.

    Returns:
        The place and household, or None when nothing (or nothing valid) is stored.
    """
    place, household = request.session.get(PLACE_KEY), request.session.get(HOUSEHOLD_KEY)
    if not isinstance(place, dict) or not isinstance(household, dict):
        return None
    try:
        choice = PlaceChoice(str(place["label"]), float(place["lat"]), float(place["lon"]))
        return choice, Household.model_validate(household)
    except (KeyError, TypeError, ValueError, ValidationError):
        return None


def theme_choice(request: Request) -> ThemeChoice:
    """The visitor's theme choice; time of day unless they picked light or dark.

    Args:
        request: The incoming request.

    Returns:
        The choice.
    """
    try:
        return ThemeChoice(request.session.get(THEME_KEY, ThemeChoice.AUTO))
    except ValueError:
        return ThemeChoice.AUTO
