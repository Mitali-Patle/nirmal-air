"""Hourly PM2.5 forecast from Open-Meteo (a CAMS model estimate, not a measurement).

The app uses it only to rank hours against each other (cleanest and worst times of day),
never as the air quality value it shows: its absolute values can be far from what CPCB
stations measure.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
from pydantic import BaseModel, ValidationError

from app.air.cpcb import IST, AirDataUnavailableError

FORECAST_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
HOURS_AHEAD = 24


@dataclass(frozen=True)
class HourlyPm25:
    """Forecast PM2.5 for the hour starting at `starts_at` (India time)."""

    starts_at: datetime
    pm25: float


class _Hourly(BaseModel):
    time: list[str]
    pm2_5: list[float | None]


class _Payload(BaseModel):
    hourly: _Hourly


async def fetch_forecast(
    client: httpx.AsyncClient, lat: float, lon: float, now: datetime
) -> list[HourlyPm25]:
    """Fetch the next 24 hours of forecast PM2.5 for a point.

    Args:
        client: HTTP client with the app's timeouts.
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        now: The current time, so past hours are dropped.

    Returns:
        Up to 24 hourly values, starting with the current hour.

    Raises:
        AirDataUnavailableError: If the request fails or the reply is malformed.
    """
    params: dict[str, str | float] = {
        "latitude": round(lat, 3),
        "longitude": round(lon, 3),
        "hourly": "pm2_5",
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }
    try:
        response = await client.get(FORECAST_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise AirDataUnavailableError(f"Forecast request failed: {type(error).__name__}") from error
    return parse_forecast(payload, now)


def parse_forecast(payload: object, now: datetime) -> list[HourlyPm25]:
    """Keep the hours from the current one onwards that have a value.

    Args:
        payload: Decoded JSON from Open-Meteo.
        now: The current time.

    Returns:
        Up to 24 hourly values in time order.

    Raises:
        AirDataUnavailableError: If the payload is malformed.
    """
    try:
        hourly = _Payload.model_validate(payload).hourly
    except ValidationError as error:
        raise AirDataUnavailableError("Forecast returned an unexpected payload") from error
    this_hour = now.astimezone(IST).replace(minute=0, second=0, microsecond=0)
    hours = []
    for stamp, value in zip(hourly.time, hourly.pm2_5, strict=False):
        starts_at = datetime.fromisoformat(stamp).replace(tzinfo=IST)
        if value is not None and this_hour <= starts_at < this_hour + timedelta(hours=HOURS_AHEAD):
            hours.append(HourlyPm25(starts_at=starts_at, pm25=value))
    return hours
