"""The cleanest and worst times of day, from the hourly forecast.

The forecast is compared only with itself: hours are ranked against each other, and its
values are never shown as the air quality.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from statistics import fmean, median

from app.domain.readings import HourlyPm25

WINDOW_HOURS = 3
# Windows are kept between 6 am and 10 pm, when people are up and about.
FIRST_HOUR = 6
LAST_HOUR = 22
# An hour counts as cleaner or dirtier than usual if it is 15% off the day's median.
TYPICAL_BAND = 0.15
ONE_HOUR = timedelta(hours=1)


class Level(StrEnum):
    """How an hour compares with the rest of the forecast day."""

    CLEANER = "cleaner"
    TYPICAL = "typical"
    DIRTIER = "dirtier"


@dataclass(frozen=True)
class Window:
    """A run of hours with its average forecast PM2.5."""

    starts_at: datetime
    ends_at: datetime
    mean_pm25: float


@dataclass(frozen=True)
class DayTiming:
    """The cleanest and worst windows and how many times dirtier the worst one is."""

    cleanest: Window
    worst: Window
    worst_vs_cleanest: float


def day_timing(hours: Sequence[HourlyPm25]) -> DayTiming | None:
    """Find the cleanest and the worst three-hour windows in the forecast.

    Args:
        hours: Consecutive hourly forecasts.

    Returns:
        The two windows, or None if the forecast has no full window in waking hours.
    """
    found = _windows(hours)
    if not found:
        return None
    cleanest = min(found, key=lambda window: window.mean_pm25)
    worst = max(found, key=lambda window: window.mean_pm25)
    ratio = worst.mean_pm25 / max(cleanest.mean_pm25, 0.1)
    return DayTiming(cleanest, worst, round(ratio, 1))


def levels(hours: Sequence[HourlyPm25]) -> list[Level]:
    """Mark each hour as cleaner, typical or dirtier than the day's median.

    Args:
        hours: Hourly forecasts.

    Returns:
        One level per hour, in the same order.
    """
    if not hours:
        return []
    middle = median(hour.pm25 for hour in hours)
    return [_level(hour.pm25, middle) for hour in hours]


def _level(value: float, middle: float) -> Level:
    if value < middle * (1 - TYPICAL_BAND):
        return Level.CLEANER
    if value > middle * (1 + TYPICAL_BAND):
        return Level.DIRTIER
    return Level.TYPICAL


def _windows(hours: Sequence[HourlyPm25]) -> list[Window]:
    """Every run of consecutive hours, WINDOW_HOURS long, that lies within waking hours."""
    found = []
    for start in range(len(hours) - WINDOW_HOURS + 1):
        run = hours[start : start + WINDOW_HOURS]
        first, last = run[0].starts_at, run[-1].starts_at
        consecutive = last - first == ONE_HOUR * (WINDOW_HOURS - 1)
        # The middle comparison rules out runs that cross midnight (11 pm to 1 am).
        if consecutive and FIRST_HOUR <= first.hour <= last.hour < LAST_HOUR:
            mean = round(fmean(hour.pm25 for hour in run), 1)
            found.append(Window(first, last + ONE_HOUR, mean))
    return found
