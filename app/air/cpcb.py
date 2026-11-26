"""Live readings from CPCB's real-time air quality feed, published on data.gov.in.

Each row is one pollutant at one station. `avg_value` is that pollutant's sub-index on the
national AQI scale (CPCB averages the last 24 hours for particles), so the station's AQI is
worked out from these sub-indices in `app.domain.aqi`, never by the AI.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

import httpx
from pydantic import BaseModel, ValidationError

from app.air.errors import AirDataUnavailableError
from app.domain.readings import IST, Pollutant

CPCB_URL = "https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
TIME_FORMAT = "%d-%m-%Y %H:%M:%S"
MAX_ROWS = 20


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
    readings = [reading for row in rows if (reading := _read_row(row)) is not None]
    if not readings:
        raise AirDataUnavailableError(f"No readings for {station.strip()}")
    measured_at = max(time for _, _, time in readings)
    sub_indices = {pollutant: value for pollutant, value, _ in readings}
    return StationReading(station=station, measured_at=measured_at, sub_indices=sub_indices)


def _read_row(row: _Row) -> tuple[Pollutant, int, datetime] | None:
    """One row's pollutant, sub-index and time, or None for "NA", unknown or unreadable rows.

    Each row is read on its own, so one bad row never hides the station's other pollutants.
    Values such as "123.0" are accepted and rounded.
    """
    try:
        pollutant = Pollutant(row.pollutant_id)
        value = round(float(row.avg_value))
        measured_at = datetime.strptime(row.last_update, TIME_FORMAT).replace(tzinfo=IST)
    except (ValueError, OverflowError):  # "NA", "nan", "inf", unknown ids, bad times
        return None
    if value < 0:
        return None
    return pollutant, value, measured_at
