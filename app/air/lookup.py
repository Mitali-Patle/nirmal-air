"""Today's measured air for a place: the nearest CPCB station with a valid, recent reading."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx

from app.air.cpcb import AirDataUnavailableError, StationReading, fetch_station
from app.air.stations import NearbyStation, nearest_stations
from app.cache import TtlCache
from app.domain.aqi import StationAqi, station_aqi

STATIONS_TRIED = 3
MAX_AGE = timedelta(hours=3)
READING_TTL_S = 15 * 60
READING_KEEP_S = 6 * 60 * 60


@dataclass(frozen=True)
class MeasuredAir:
    """A station's AQI with everything needed to show where and when it was measured."""

    nearby: NearbyStation
    reading: StationReading
    aqi: StationAqi
    from_cache_after_failure: bool


class AirLookup:
    """Finds measured air for a point, caching each station's reading."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        readings: TtlCache[StationReading] | None = None,
    ) -> None:
        self._client = client
        self._api_key = api_key
        self._readings = readings or TtlCache(READING_TTL_S, READING_KEEP_S)

    async def measured_air(self, lat: float, lon: float, now: datetime) -> MeasuredAir | None:
        """The nearest station with a valid, recent reading among the three closest.

        The nearest station is asked first; the next two only if it has no usable reading.

        Args:
            lat: Latitude in degrees.
            lon: Longitude in degrees.
            now: The current time.

        Returns:
            The measured air, or None when no nearby station has a usable reading.
        """
        nearby = nearest_stations(lat, lon, limit=STATIONS_TRIED)
        for group in (nearby[:1], nearby[1:]):
            results = await asyncio.gather(*(self._reading(item.station.name) for item in group))
            for item, (reading, after_failure) in zip(group, results, strict=True):
                if reading is None or now - reading.measured_at > MAX_AGE:
                    continue
                aqi = station_aqi(reading.sub_indices)
                if aqi is not None:
                    return MeasuredAir(item, reading, aqi, from_cache_after_failure=after_failure)
        return None

    async def _reading(self, station: str) -> tuple[StationReading | None, bool]:
        """A fresh cached reading, else a live one, else a stale cached one."""
        cached = self._readings.get(station)
        if cached is not None and not cached.stale:
            return cached.value, False
        try:
            reading = await fetch_station(self._client, self._api_key, station)
        except AirDataUnavailableError:
            return (cached.value, True) if cached is not None else (None, False)
        self._readings.put(station, reading)
        return reading, False
