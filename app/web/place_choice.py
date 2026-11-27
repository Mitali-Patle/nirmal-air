"""Turning what the start form sends into a trusted place.

The place is a search result found again on the server, or the browser's location; either
way the server writes its label.
"""

import math

from fastapi import Request

from app.air.errors import PlaceSearchError
from app.air.places import PlaceFinder
from app.air.stations import nearest_stations
from app.services.today import PlaceChoice
from app.web.deps import get_services
from app.web.session import load_household

# India's bounding box, so a location outside it is refused before any lookup.
LAT_RANGE = (6.0, 37.5)
LON_RANGE = (68.0, 97.5)


async def place_from_form(request: Request, form: dict[str, str]) -> PlaceChoice | None:
    """The chosen place: a search result found again on the server, or the browser's location.

    The label always comes from the geocoder or the station list, never from the form, so
    nothing a visitor types reaches the AI as a place name.

    Args:
        request: The incoming request.
        form: The submitted form fields.

    Returns:
        The place, or None when none was chosen or it could not be found.
    """
    if form.get("geo_lat") and form.get("geo_lon"):
        return near_me(form["geo_lat"], form["geo_lon"])
    # No suggestion picked yet means the best match: typing "Lucknow" and saving just works.
    query, index = form.get("place_query", "").strip()[:60], form.get("place_index") or "0"
    if not query and form.get("place_keep") == "1":
        saved = load_household(request)  # the place saved in the session, never the form's
        return saved[0] if saved else None
    if not query or not (index.isascii() and index.isdigit()):
        return None
    try:
        results = await place_finder(request).search(query)
    except PlaceSearchError:
        return None
    if int(index) >= len(results):
        return None
    chosen = results[int(index)]
    return PlaceChoice(chosen.label, chosen.lat, chosen.lon)


def place_finder(request: Request) -> PlaceFinder:
    """The app's cached place search.

    Args:
        request: The incoming request.

    Returns:
        The place finder.
    """
    return get_services(request).places


def near_me(lat_text: str, lon_text: str) -> PlaceChoice | None:
    """The browser's location as a place named after its nearest station's city.

    Args:
        lat_text: Latitude as sent by the browser.
        lon_text: Longitude as sent by the browser.

    Returns:
        The place, or None when the point is unreadable or outside India.
    """
    point = read_point(lat_text, lon_text)
    if point is None:
        return None
    lat, lon = point
    if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]):
        return None
    city = nearest_stations(lat, lon, limit=1)[0].station.city
    return PlaceChoice(f"Your location, near {city}", lat, lon)


def read_point(lat_text: str, lon_text: str) -> tuple[float, float] | None:
    """A latitude and longitude as finite numbers, rounded to about 10 m.

    Args:
        lat_text: Latitude as sent by the browser.
        lon_text: Longitude as sent by the browser.

    Returns:
        The point, or None when either value is not a finite number.

    >>> read_point("28.61394", "77.2090"), read_point("abc", "77"), read_point("nan", "77")
    ((28.6139, 77.209), None, None)
    """
    try:
        lat, lon = float(lat_text), float(lon_text)
    except ValueError:
        return None
    if not (math.isfinite(lat) and math.isfinite(lon)):
        return None
    return round(lat, 4), round(lon, 4)
