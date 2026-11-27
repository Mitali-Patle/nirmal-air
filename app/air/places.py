"""Search Indian places by name with Open-Meteo's geocoder.

The geocoder knows current official names only, so common older names are translated first
("Bangalore" finds nothing and "Gurgaon" finds villages without this).
"""

from dataclasses import dataclass

import httpx
from pydantic import BaseModel

from app.air.errors import PlaceSearchError
from app.cache import TtlCache

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
MAX_RESULTS = 5
SEARCH_TTL_S = 24 * 60 * 60
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
        PlaceSearchError: If the geocoder fails or replies with something unexpected.
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
        raise PlaceSearchError(f"Place search failed: {type(error).__name__}") from error
    places = [
        Place(result.name, result.admin2, result.admin1, result.latitude, result.longitude)
        for result in results
    ]
    # The geocoder sometimes lists the same village twice; a reader sees one choice per name.
    unique = {place.label: place for place in reversed(places)}
    return [place for place in places if unique[place.label] is place]


class PlaceFinder:
    """Place search with a day's cache, so typing and saving do not repeat the same lookup."""

    def __init__(
        self, client: httpx.AsyncClient, cache: TtlCache[list[Place]] | None = None
    ) -> None:
        self._client = client
        self._cache = cache or TtlCache(SEARCH_TTL_S, SEARCH_TTL_S)

    async def search(self, query: str) -> list[Place]:
        """Places matching a name, from the cache when the same name was searched today.

        Args:
            query: What the person typed.

        Returns:
            Up to five matches, best first.

        Raises:
            PlaceSearchError: If the geocoder fails (failures are not cached).
        """
        key = search_name(query).casefold()
        cached = self._cache.get(key)
        if cached is not None:
            return cached.value
        found = await search_places(self._client, query)
        if found:  # a miss is not kept: a typo corrected a moment later should be searched
            self._cache.put(key, found)
        return found
