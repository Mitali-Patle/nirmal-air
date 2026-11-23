"""Search Indian places by name with Open-Meteo's geocoder.

The geocoder knows current official names only, so common older names are translated first
("Bangalore" finds nothing and "Gurgaon" finds villages without this).
"""

from dataclasses import dataclass

import httpx
from pydantic import BaseModel

from app.air.cpcb import AirDataUnavailableError

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
MAX_RESULTS = 5
OLD_NAMES = {
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "gurgaon": "Gurugram",
    "poona": "Pune",
    "baroda": "Vadodara",
    "mysore": "Mysuru",
    "trivandrum": "Thiruvananthapuram",
    "cochin": "Kochi",
    "allahabad": "Prayagraj",
    "benares": "Varanasi",
    "banaras": "Varanasi",
    "mangalore": "Mangaluru",
    "belgaum": "Belagavi",
    "hubli": "Hubballi",
    "pondicherry": "Puducherry",
    "simla": "Shimla",
    "cawnpore": "Kanpur",
}


@dataclass(frozen=True)
class Place:
    """A place in India with enough detail to tell same-named places apart."""

    name: str
    district: str
    state: str
    lat: float
    lon: float

    @property
    def label(self) -> str:
        """For example "Andheri, Mumbai City District, Maharashtra"."""
        parts = [self.name, self.district, self.state]
        return ", ".join(part for i, part in enumerate(parts) if part and part not in parts[:i])


class _Result(BaseModel):
    name: str
    latitude: float
    longitude: float
    admin1: str = ""
    admin2: str = ""


class _Payload(BaseModel):
    results: list[_Result] = []


def search_name(query: str) -> str:
    """The name to send to the geocoder: trimmed, with older city names replaced.

    Args:
        query: What the person typed.

    Returns:
        The name to search for.

    >>> search_name("  bangalore ")
    'Bengaluru'
    """
    cleaned = " ".join(query.split())
    return OLD_NAMES.get(cleaned.casefold(), cleaned)


async def search_places(client: httpx.AsyncClient, query: str) -> list[Place]:
    """Find places in India matching a name.

    Args:
        client: HTTP client with the app's timeouts.
        query: What the person typed.

    Returns:
        Up to five matches, best first; empty when nothing matches.

    Raises:
        AirDataUnavailableError: If the geocoder fails or replies with something unexpected.
    """
    params: dict[str, str | int] = {
        "name": search_name(query),
        "count": MAX_RESULTS,
        "language": "en",
        "countryCode": "IN",
        "format": "json",
    }
    try:
        response = await client.get(GEOCODING_URL, params=params)
        response.raise_for_status()
        results = _Payload.model_validate(response.json()).results
    except (httpx.HTTPError, ValueError) as error:  # ValidationError is a ValueError
        raise AirDataUnavailableError(f"Place search failed: {type(error).__name__}") from error
    return [
        Place(result.name, result.admin2, result.admin1, result.latitude, result.longitude)
        for result in results
    ]
