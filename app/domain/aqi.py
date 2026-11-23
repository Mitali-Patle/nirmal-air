"""India's National Air Quality Index (CPCB, 2014): categories, the station AQI and PM2.5.

The station AQI is the highest pollutant sub-index, and it is only valid when at least three
pollutants are reported and one of them is PM2.5 or PM10.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from itertools import pairwise

from app.air.cpcb import Pollutant

MIN_POLLUTANTS = 3
PARTICLES = frozenset({Pollutant.PM25, Pollutant.PM10})
# (sub-index, PM2.5 µg/m³ averaged over 24 hours) at each band edge, from CPCB's table.
PM25_BREAKPOINTS = ((0, 0.0), (50, 30.0), (100, 60.0), (200, 90.0), (300, 120.0), (400, 250.0))


class Category(Enum):
    """AQI bands, each with the health statement CPCB publishes for it (lightly worded)."""

    GOOD = ("Good", 0, "Minimal impact.")
    SATISFACTORY = ("Satisfactory", 51, "Minor breathing discomfort to sensitive people.")
    MODERATE = (
        "Moderate",
        101,
        "Breathing discomfort to people with lung disease such as asthma, and heart disease.",
    )
    POOR = ("Poor", 201, "Breathing discomfort to most people on prolonged exposure.")
    VERY_POOR = ("Very Poor", 301, "Respiratory illness on prolonged exposure.")
    SEVERE = (
        "Severe",
        401,
        "Affects healthy people and seriously impacts those with existing diseases.",
    )

    def __init__(self, label: str, lowest: int, health: str) -> None:
        self.label = label
        self.lowest = lowest
        self.health = health


@dataclass(frozen=True)
class StationAqi:
    """A station's AQI, its band and the pollutant that set it."""

    value: int
    category: Category
    dominant: Pollutant


def category_for(aqi: int) -> Category:
    """The band an AQI value falls in.

    Args:
        aqi: An AQI value (0 or more).

    Returns:
        Its category.

    >>> category_for(324).label
    'Very Poor'
    """
    return next(category for category in reversed(Category) if aqi >= category.lowest)


def station_aqi(sub_indices: Mapping[Pollutant, int]) -> StationAqi | None:
    """Work out a station's AQI from its pollutant sub-indices, following CPCB's rule.

    Args:
        sub_indices: Sub-index per pollutant reported.

    Returns:
        The AQI, or None when the readings are too few to give a valid one.
    """
    if len(sub_indices) < MIN_POLLUTANTS or not PARTICLES & sub_indices.keys():
        return None
    dominant = max(sub_indices, key=lambda pollutant: sub_indices[pollutant])
    value = sub_indices[dominant]
    return StationAqi(value=value, category=category_for(value), dominant=dominant)


def pm25_from_sub_index(sub_index: int) -> float:
    """Estimate the 24-hour PM2.5 concentration behind a PM2.5 sub-index.

    Reverses CPCB's straight-line steps between band edges. Above 400 ("Severe") CPCB gives
    no upper concentration, so the result is the band's floor, 250 µg/m³: an underestimate.

    Args:
        sub_index: The PM2.5 sub-index (0 or more).

    Returns:
        PM2.5 in µg/m³.

    >>> pm25_from_sub_index(324)
    151.2
    """
    for (low_index, low_pm), (high_index, high_pm) in pairwise(PM25_BREAKPOINTS):
        if sub_index <= high_index:
            share = (sub_index - low_index) / (high_index - low_index)
            return round(low_pm + share * (high_pm - low_pm), 1)
    return PM25_BREAKPOINTS[-1][1]
