"""Live readings from CPCB's real-time air quality feed, published on data.gov.in.

Each row is one pollutant at one station. `avg_value` is that pollutant's sub-index on the
national AQI scale (CPCB averages the last 24 hours for particles), so the station's AQI is
worked out from these sub-indices in `app.domain.aqi`, never by the AI.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, ValidationError

CPCB_URL = "https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
# data.gov.in stalls requests that carry Python's default User-Agent (python-httpx,
# Python-urllib) until they time out, so every request names the app instead.
USER_AGENT = "NirmalAir/0.1"
IST = ZoneInfo("Asia/Kolkata")
TIME_FORMAT = "%d-%m-%Y %H:%M:%S"
MAX_ROWS = 20


class Pollutant(StrEnum):
    """Pollutants CPCB reports, named as the feed names them."""

    PM25 = "PM2.5"
    PM10 = "PM10"
    NO2 = "NO2"
    SO2 = "SO2"
    CO = "CO"
    OZONE = "OZONE"
    NH3 = "NH3"


class AirDataUnavailableError(Exception):
    """CPCB did not answer in time, or answered without usable readings."""


@dataclass(frozen=True)
class StationReading:
    """The latest sub-index for each pollutant a station reported, and when."""

    station: str
    measured_at: datetime
    sub_indices: Mapping[Pollutant, int]


class _Row(BaseModel):
    pollutant_id: str
    avg_value: str
    last_update: str


class _Payload(BaseModel):
    records: list[_Row]


async def fetch_station(client: httpx.AsyncClient, api_key: str, station: str) -> StationReading:
    """Fetch one station's latest readings.

    Args:
        client: HTTP client with the app's timeouts.
        api_key: data.gov.in API key.
        station: Station name exactly as CPCB writes it.

    Returns:
        The station's readings.

    Raises:
        AirDataUnavailableError: If the request fails or returns no usable readings.
    """
    params: dict[str, str | int] = {
        "api-key": api_key,
        "format": "json",
        "limit": MAX_ROWS,
        "filters[station]": station,
    }
    try:
        response = await client.get(CPCB_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise AirDataUnavailableError(f"CPCB request failed: {type(error).__name__}") from error
    return parse_station(payload, station)


def parse_station(payload: object, station: str) -> StationReading:
    """Turn a CPCB response into a reading, skipping "NA" values and unknown pollutants.

    Args:
        payload: Decoded JSON from the feed.
        station: The station the rows belong to.

    Returns:
        The station's readings, timed by its most recent row.

    Raises:
        AirDataUnavailableError: If the payload is malformed or has no usable rows.
    """
    try:
        rows = _Payload.model_validate(payload).records
    except ValidationError as error:
        raise AirDataUnavailableError("CPCB returned an unexpected payload") from error
    known = {pollutant.value for pollutant in Pollutant}
    usable = [row for row in rows if row.pollutant_id in known and row.avg_value.isdigit()]
    if not usable:
        raise AirDataUnavailableError(f"No readings for {station.strip()}")
    try:
        measured_at = max(
            datetime.strptime(row.last_update, TIME_FORMAT).replace(tzinfo=IST) for row in usable
        )
    except ValueError as error:
        raise AirDataUnavailableError("CPCB returned an unreadable time") from error
    sub_indices = {Pollutant(row.pollutant_id): int(row.avg_value) for row in usable}
    return StationReading(station=station, measured_at=measured_at, sub_indices=sub_indices)
