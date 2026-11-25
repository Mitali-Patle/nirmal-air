"""What the app remembers about a visitor, kept in a signed cookie (no accounts, no database).

The cookie holds the chosen place, the household profile, the week's log, a theme choice and
the CSRF token (see `app.web.csrf`).
It is signed with SESSION_SECRET, so it cannot be altered, and it is HttpOnly, so page
scripts cannot read it. Nothing about the household is stored on the server.
"""

from datetime import date
from enum import StrEnum

from fastapi import Request
from pydantic import ValidationError

from app.domain.household import Household
from app.domain.week import DayImpact, LogEntry
from app.services.today import PlaceChoice
from app.web.cookie import pack, unpack

PLACE_KEY = "place"
HOUSEHOLD_KEY = "household"
THEME_KEY = "theme"
SAMPLE_KEY = "sample"
LOG_KEY = "log"


class ThemeChoice(StrEnum):
    """How the page picks light or dark."""

    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"


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
    request.session[HOUSEHOLD_KEY] = pack(household.model_dump(mode="json", exclude_defaults=True))
    if sample:
        request.session[SAMPLE_KEY] = sample
    else:
        request.session.pop(SAMPLE_KEY, None)
    request.session.pop(LOG_KEY, None)  # a new household starts a new week


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
    place, household = request.session.get(PLACE_KEY), unpack(request.session.get(HOUSEHOLD_KEY))
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


def load_log(request: Request) -> list[LogEntry]:
    """The household's "This week" log, skipping any entry that no longer reads cleanly.

    Args:
        request: The incoming request.

    Returns:
        The logged steps, oldest first.
    """
    entries = []
    stored = unpack(request.session.get(LOG_KEY))
    for raw in stored if isinstance(stored, list) else []:
        try:
            impact = DayImpact(int(raw["c"]), int(raw["p"]))
            entries.append(
                LogEntry(date.fromisoformat(raw["d"]), str(raw["a"]), str(raw["l"]), impact)
            )
        except (KeyError, TypeError, ValueError):
            continue
    return entries


def save_log(request: Request, entries: list[LogEntry]) -> None:
    """Store the log in the signed cookie, packed with short keys to keep the cookie small.

    Args:
        request: The incoming request.
        entries: The log to keep.
    """
    request.session[LOG_KEY] = pack(
        [
            {
                "d": e.day.isoformat(),
                "a": e.action,
                "l": e.label,
                "c": e.impact.co2_g,
                "p": e.impact.pm25_ug,
            }
            for e in entries
        ]
    )
