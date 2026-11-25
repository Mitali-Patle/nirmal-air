"""The sky over a place: sunrise, sunset, the phase of the day, and how hazy the air makes it.

The page's background follows the phase (morning, afternoon, evening, dusk, night) and is
dulled by the measured AQI band, so the screen looks the way the sky outside does. Sunrise
and sunset use NOAA's solar equations, accurate to a few minutes, with no network call.
"""

import math
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from enum import StrEnum

from app.domain.aqi import Category

# The sun's upper edge at the horizon, with refraction (NOAA).
ZENITH_DEG = 90.833
MORNING_ENDS = time(11)
EVENING_HOURS = 2
NIGHT_FROM = time(21)


class Phase(StrEnum):
    """Part of the day, which sets the page's background."""

    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    DUSK = "dusk"
    NIGHT = "night"


@dataclass(frozen=True)
class SunTimes:
    """Local sunrise and sunset."""

    sunrise: datetime
    sunset: datetime


def sun_times(lat: float, lon: float, day: datetime) -> SunTimes:
    """Sunrise and sunset at a place on a day, in the day's time zone.

    Args:
        lat: Latitude in degrees.
        lon: Longitude in degrees, east positive.
        day: Any time on that day; its time zone is used for the answer.

    Returns:
        Sunrise and sunset.

    >>> from app.air.cpcb import IST
    >>> times = sun_times(28.61, 77.21, datetime(2026, 11, 25, tzinfo=IST))
    >>> f"{times.sunrise:%H:%M} {times.sunset:%H:%M}"
    '06:51 17:25'
    """
    gamma = 2 * math.pi / 365 * (day.timetuple().tm_yday - 1)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )
    phi = math.radians(lat)
    cos_ha = math.cos(math.radians(ZENITH_DEG)) / (math.cos(phi) * math.cos(decl)) - math.tan(
        phi
    ) * math.tan(decl)
    hour_angle = math.degrees(math.acos(max(-1.0, min(1.0, cos_ha))))
    # NOAA's minutes count from midnight UTC on the same calendar date.
    midnight_utc = datetime.combine(day.date(), time(), UTC)

    def at(minutes_utc: float) -> datetime:
        return (midnight_utc + timedelta(minutes=minutes_utc)).astimezone(day.tzinfo)

    return SunTimes(
        sunrise=at(720 - 4 * (lon + hour_angle) - eqtime),
        sunset=at(720 - 4 * (lon - hour_angle) - eqtime),
    )


def phase_at(now: datetime, sun: SunTimes) -> Phase:
    """The phase of the day at a moment.

    Morning runs from sunrise to 11 am, afternoon to two hours before sunset, evening to
    sunset, dusk to 9 pm, and night until sunrise.

    Args:
        now: The moment, in the place's time zone.
        sun: That day's sunrise and sunset.

    Returns:
        The phase.
    """
    clock = now.timetz().replace(tzinfo=None)
    if clock < sun.sunrise.time() or clock >= NIGHT_FROM:
        return Phase.NIGHT
    if clock < MORNING_ENDS:
        return Phase.MORNING
    if now < sun.sunset - timedelta(hours=EVENING_HOURS):
        return Phase.AFTERNOON
    return Phase.EVENING if now < sun.sunset else Phase.DUSK


def haze_level(category: Category | None) -> int:
    """How much the measured air dulls the sky, from 0 (clear) to 5 (Severe).

    Args:
        category: Today's AQI band, or None when nothing was measured.

    Returns:
        The band's position on CPCB's scale; 0 when nothing was measured, so the page never
        looks hazier than the data shows.

    >>> haze_level(Category.VERY_POOR)
    4
    """
    return 0 if category is None else list(Category).index(category)
