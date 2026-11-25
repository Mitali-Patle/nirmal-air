"""The start page: pick a sample household or describe your own, and choose a place."""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.air.cpcb import AirDataUnavailableError
from app.air.places import search_places
from app.air.stations import nearest_stations
from app.services.samples import SAMPLES
from app.services.today import PlaceChoice
from app.web.household_form import (
    COMMUTE_ROWS,
    MEMBER_ROWS,
    ROUTINE_ROWS,
    parse_household,
)
from app.web.session import CsrfChecked, ThemeChoice, load_household, save_household
from app.web.templating import templates

router = APIRouter()
# India's bounding box, so a location outside it is refused before any lookup.
LAT_RANGE = (6.0, 37.5)
LON_RANGE = (68.0, 97.5)


@router.get("/", response_class=HTMLResponse)
def start(request: Request) -> Response:
    """The start page.

    Args:
        request: The incoming request.

    Returns:
        Sample households, the household form, and a link back to today if one is saved.
    """
    return _start_page(request, [], {})


@router.post("/sample", dependencies=[CsrfChecked])
def use_sample(request: Request, sample: Annotated[str, Form(max_length=40)]) -> Response:
    """Load a sample household and go to its day.

    Args:
        request: The incoming request.
        sample: The sample's id.

    Returns:
        A redirect to the Today page.

    Raises:
        HTTPException: 404 for an unknown sample.
    """
    chosen = SAMPLES.get(sample)
    if chosen is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such sample household.")
    save_household(request, chosen.place, chosen.household)
    return RedirectResponse("/today", status.HTTP_303_SEE_OTHER)


@router.get("/places", response_class=HTMLResponse)
async def places(request: Request, q: Annotated[str, Query(max_length=60)] = "") -> Response:
    """Place suggestions for the search box (an htmx fragment).

    Args:
        request: The incoming request.
        q: What the person has typed.

    Returns:
        Up to five places to choose from, or a short message.
    """
    query = q.strip()
    results, failed = [], False
    if len(query) >= 2:  # noqa: PLR2004 - two letters before searching
        try:
            results = await search_places(request.app.state.http, query)
        except AirDataUnavailableError:
            failed = True
    context = {"query": query, "results": results, "failed": failed}
    return templates.TemplateResponse(request, "partials/places.html", context)


@router.post("/household", dependencies=[CsrfChecked])
async def save_profile(request: Request) -> Response:
    """Save the household from the form and go to its day, or show what to fix.

    Args:
        request: The incoming request.

    Returns:
        A redirect to Today, or the start page with errors (422).
    """
    form = {key: value for key, value in (await request.form()).items() if isinstance(value, str)}
    household, errors = parse_household(form)
    place = await _place_from(request, form)
    if place is None:
        errors.insert(0, "Choose a place from the list, or use your location.")
    if household is None or place is None:
        return _start_page(request, errors, form, status.HTTP_422_UNPROCESSABLE_CONTENT)
    save_household(request, place, household)
    return RedirectResponse("/today", status.HTTP_303_SEE_OTHER)


@router.post("/theme", dependencies=[CsrfChecked])
def set_theme(request: Request, theme: Annotated[ThemeChoice, Form()]) -> Response:
    """Remember the visitor's theme choice.

    Args:
        request: The incoming request.
        theme: Time of day, light or dark.

    Returns:
        A redirect back to Today.
    """
    request.session["theme"] = theme.value
    return RedirectResponse("/today", status.HTTP_303_SEE_OTHER)


async def _place_from(request: Request, form: dict[str, str]) -> PlaceChoice | None:
    """The chosen place: a search result found again on the server, or the browser's location.

    The label always comes from the geocoder or the station list, never from the form, so
    nothing a visitor types reaches the AI as a place name.
    """
    if form.get("geo_lat") and form.get("geo_lon"):
        return _near_me(form["geo_lat"], form["geo_lon"])
    # No suggestion picked yet means the best match: typing "Lucknow" and saving just works.
    query, index = form.get("place_query", "").strip()[:60], form.get("place_index") or "0"
    if not query or not index.isdigit():
        return None
    try:
        results = await search_places(request.app.state.http, query)
    except AirDataUnavailableError:
        return None
    if int(index) >= len(results):
        return None
    chosen = results[int(index)]
    return PlaceChoice(chosen.label, chosen.lat, chosen.lon)


def _near_me(lat_text: str, lon_text: str) -> PlaceChoice | None:
    try:
        lat, lon = round(float(lat_text), 4), round(float(lon_text), 4)
    except ValueError:
        return None
    if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]):
        return None
    city = nearest_stations(lat, lon, limit=1)[0].station.city
    return PlaceChoice(f"Your location, near {city}", lat, lon)


def _start_page(
    request: Request, errors: list[str], form: dict[str, str], code: int = status.HTTP_200_OK
) -> Response:
    context = {
        "samples": SAMPLES,
        "saved": load_household(request),
        "errors": errors,
        "form": form,
        "member_rows": range(MEMBER_ROWS),
        "routine_rows": range(ROUTINE_ROWS),
        "commute_rows": range(COMMUTE_ROWS),
    }
    return templates.TemplateResponse(request, "start.html", context, status_code=code)
