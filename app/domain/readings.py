"""The shared vocabulary of air readings: India's time zone, CPCB's pollutants, forecast hours.

These live in the domain so the calculations never depend on the code that fetches data;
the clients in `app.air` build these types, not the other way round.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class Pollutant(StrEnum):
    """Pollutants CPCB reports, named as the feed names them."""

    PM25 = "PM2.5"
    PM10 = "PM10"
    NO2 = "NO2"
    SO2 = "SO2"
    CO = "CO"
    OZONE = "OZONE"
    NH3 = "NH3"


@dataclass(frozen=True)
class HourlyPm25:
    """Forecast PM2.5 for the hour starting at `starts_at` (India time)."""

    starts_at: datetime
    pm25: float
