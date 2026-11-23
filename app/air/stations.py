"""CPCB monitoring stations and the nearest ones to a point.

The list in `stations.json` holds names and positions only (rebuilt by
`scripts/refresh_stations.py`); readings are always fetched live.
"""

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

STATIONS_FILE = Path(__file__).with_name("stations.json")
EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True)
class Station:
    """A monitoring station. `name` is exactly as CPCB writes it, for the live query."""

    name: str
    city: str
    state: str
    lat: float
    lon: float

    @property
    def label(self) -> str:
        """The name as shown to people."""
        return self.name.strip()


@dataclass(frozen=True)
class NearbyStation:
    """A station and its distance from the place asked about."""

    station: Station
    distance_km: float


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points.

    Args:
        lat1: Latitude of the first point, in degrees.
        lon1: Longitude of the first point, in degrees.
        lat2: Latitude of the second point, in degrees.
        lon2: Longitude of the second point, in degrees.

    Returns:
        The distance in kilometres.

    >>> round(distance_km(28.6139, 77.2090, 19.0760, 72.8777))
    1148
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi, d_lambda = phi2 - phi1, math.radians(lon2 - lon1)
    h = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


@lru_cache(maxsize=1)
def all_stations() -> tuple[Station, ...]:
    """Load the station list once per process.

    Returns:
        Every known station.
    """
    rows = json.loads(STATIONS_FILE.read_text(encoding="utf-8"))
    return tuple(Station(**row) for row in rows)


def nearest_stations(
    lat: float, lon: float, limit: int = 3, stations: tuple[Station, ...] | None = None
) -> list[NearbyStation]:
    """The stations closest to a point, nearest first.

    Args:
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        limit: How many stations to return.
        stations: Stations to search; defaults to the full list.

    Returns:
        Up to `limit` stations with their distances.
    """
    candidates = all_stations() if stations is None else stations
    nearby = [
        NearbyStation(station, distance_km(lat, lon, station.lat, station.lon))
        for station in candidates
    ]
    return sorted(nearby, key=lambda item: item.distance_km)[:limit]
