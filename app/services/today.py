"""Gathering one household's day: measured air and the forecast, fetched side by side."""

import asyncio
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.advice.facts import Today
from app.air.cpcb import AirDataUnavailableError
from app.air.forecast import HourlyPm25, fetch_forecast
from app.air.lookup import AirLookup, MeasuredAir
from app.cache import TtlCache
from app.domain.household import Household
from app.domain.timing import day_timing

FORECAST_TTL_S = 60 * 60
FORECAST_KEEP_S = 3 * 60 * 60


@dataclass(frozen=True)
class PlaceChoice:
    """Where the household is: a label to show and the point to look up."""

    label: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Day:
    """Today's data for a household plus the hourly forecast, for the timing strip."""

    today: Today
    hours: tuple[HourlyPm25, ...]


class TodayService:
    """Builds a household's day, caching the forecast per place for an hour."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        air: AirLookup | None,
        forecasts: TtlCache[tuple[HourlyPm25, ...]] | None = None,
    ) -> None:
        self._client = client
        self._air = air
        self._forecasts = forecasts or TtlCache(FORECAST_TTL_S, FORECAST_KEEP_S)

    async def day(self, place: PlaceChoice, household: Household, now: datetime) -> Day:
        """Measured air and forecast for a place, fetched at the same time.

        Either source may be missing (no station reporting, forecast down); the page and
        the advice say so rather than failing.

        Args:
            place: Where the household is.
            household: Who lives there.
            now: The current time.

        Returns:
            The day's data.
        """
        air, hours = await asyncio.gather(self._measured(place, now), self._forecast(place, now))
        today = Today(place.label, now, air, day_timing(hours), household)
        return Day(today, hours)

    async def _measured(self, place: PlaceChoice, now: datetime) -> MeasuredAir | None:
        if self._air is None:
            return None
        return await self._air.measured_air(place.lat, place.lon, now)

    async def _forecast(self, place: PlaceChoice, now: datetime) -> tuple[HourlyPm25, ...]:
        """The forecast from this hour on, cached for an hour.

        When Open-Meteo does not answer, a copy up to three hours old is used instead.
        """
        key = f"{place.lat:.2f},{place.lon:.2f}"
        cached = self._forecasts.get(key)
        if cached is not None and not cached.stale:
            return _from_this_hour(cached.value, now)
        try:
            hours = tuple(await fetch_forecast(self._client, place.lat, place.lon, now))
        except AirDataUnavailableError:
            return _from_this_hour(cached.value, now) if cached is not None else ()
        self._forecasts.put(key, hours)
        return hours


def _from_this_hour(hours: tuple[HourlyPm25, ...], now: datetime) -> tuple[HourlyPm25, ...]:
    this_hour = now.replace(minute=0, second=0, microsecond=0)
    return tuple(hour for hour in hours if hour.starts_at >= this_hour)
