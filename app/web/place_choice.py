"""Turning what the start form sends into a trusted place.

The place is a search result found again on the server, or the browser's location; either
way the server writes its label.
"""

from fastapi import Request

from app.air.cpcb import AirDataUnavailableError
from app.air.places import PlaceFinder
from app.air.stations import nearest_stations
from app.services.today import PlaceChoice

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
    if not query or not index.isdigit():
        return None
    try:
        results = await place_finder(request).search(query)
    except AirDataUnavailableError:
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
    finder: PlaceFinder = request.app.state.places
    return finder


def near_me(lat_text: str, lon_text: str) -> PlaceChoice | None:
    """The browser's location as a place named after its nearest station's city.

    Args:
        lat_text: Latitude as sent by the browser.
        lon_text: Longitude as sent by the browser.

    Returns:
        The place, or None when the point is unreadable or outside India.
    """
    try:
        lat, lon = round(float(lat_text), 4), round(float(lon_text), 4)
    except ValueError:
        return None
    if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]):
        return None
    city = nearest_stations(lat, lon, limit=1)[0].station.city
    return PlaceChoice(f"Your location, near {city}", lat, lon)
