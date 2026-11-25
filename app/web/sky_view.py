"""How the Today page is painted: the phase of the sky, the AQI haze, and the sky band's scene."""

from dataclasses import dataclass
from datetime import datetime

from app.air.cpcb import IST
from app.air.weather import Weather
from app.domain.aqi import Category
from app.domain.scene import Scene, scene
from app.domain.sky import Phase, haze_level, phase_at, sun_times
from app.services.today import PlaceChoice
from app.web.session import ThemeChoice

DARK_PHASES = frozenset({Phase.DUSK, Phase.NIGHT})


@dataclass(frozen=True)
class Sky:
    """How the page is painted: phase of day, haze from the AQI, and whether it is dark."""

    phase: Phase
    haze: int
    theme: ThemeChoice


def sky_for(
    place: PlaceChoice, now: datetime, category: Category | None, theme: ThemeChoice
) -> Sky:
    """The page's sky: the real phase of day at the place, unless the visitor picked a theme.

    Args:
        place: Where the household is.
        now: The current time.
        category: Today's measured AQI band, if any.
        theme: The visitor's theme choice.

    Returns:
        The sky to paint.
    """
    phase = phase_at(now.astimezone(IST), sun_times(place.lat, place.lon, now.astimezone(IST)))
    if theme is ThemeChoice.DARK:
        phase = Phase.NIGHT
    elif theme is ThemeChoice.LIGHT and phase in DARK_PHASES:
        phase = Phase.MORNING
    return Sky(phase, haze_level(category), theme)


def scene_for(place: PlaceChoice, now: datetime, sky: Sky, weather: Weather | None) -> Scene:
    """The sky band's drawing for this page.

    Args:
        place: Where the household is.
        now: The current time.
        sky: The page's sky (phase and haze).
        weather: Cloud cover and rain, if known.

    Returns:
        The scene to draw.
    """
    local = now.astimezone(IST)
    sun = sun_times(place.lat, place.lon, local)
    known = (weather.cloud_cover, weather.raining) if weather else None
    return scene(local, sun, sky.phase, sky.haze, known)
