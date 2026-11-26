"""Current cloud cover and rain from Open-Meteo, for the sky drawn at the top of the page.

Decoration only: the advice never depends on it, and when it cannot be fetched the sky is
simply drawn clear.
"""

from dataclasses import dataclass

import httpx
from pydantic import BaseModel

from app.air.errors import WeatherUnavailableError

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
RAIN_MM = 0.1


@dataclass(frozen=True)
class Weather:
    """The sky right now: cloud cover in percent and whether it is raining."""

    cloud_cover: int
    raining: bool


class _Current(BaseModel):
    cloud_cover: float
    precipitation: float


class _Payload(BaseModel):
    current: _Current


async def fetch_weather(client: httpx.AsyncClient, lat: float, lon: float) -> Weather:
    """The current cloud cover and rain at a point.

    Args:
        client: HTTP client with the app's timeouts.
        lat: Latitude in degrees.
        lon: Longitude in degrees.

    Returns:
        The weather now.

    Raises:
        WeatherUnavailableError: If the request fails or the reply is malformed.
    """
    params: dict[str, str | float] = {
        "latitude": round(lat, 3),
        "longitude": round(lon, 3),
        "current": "cloud_cover,precipitation",
        "timezone": "Asia/Kolkata",
    }
    try:
        response = await client.get(WEATHER_URL, params=params)
        response.raise_for_status()
        return parse_weather(response.json())
    except (httpx.HTTPError, ValueError) as error:
        raise WeatherUnavailableError(f"Weather request failed: {type(error).__name__}") from error


def parse_weather(payload: object) -> Weather:
    """Read the current weather from Open-Meteo's reply.

    Args:
        payload: Decoded JSON.

    Returns:
        The weather now.

    Raises:
        ValueError: If the payload is malformed (a ValidationError is a ValueError).

    >>> parse_weather({"current": {"cloud_cover": 64, "precipitation": 0.4}})
    Weather(cloud_cover=64, raining=True)
    """
    current = _Payload.model_validate(payload).current
    return Weather(round(current.cloud_cover), current.precipitation >= RAIN_MM)
