"""The start page: pick a sample household or describe your own, and choose a place."""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response

from app.advice.facts import distance_label
from app.air.errors import PlaceSearchError
from app.air.places import MAX_RESULTS
from app.air.stations import nearest_stations
from app.services.samples import SAMPLES
from app.web.csrf import CsrfChecked
from app.web.deps import PageLimited
from app.web.household_form import (
    COMMUTES,
    MEMBERS,
    ROUTINES,
    SECTIONS,
    hidden_rows_in_use,
    parse_household,
)
from app.web.place_choice import near_me, place_finder, place_from_form, read_point
from app.web.session import load_household, save_household
from app.web.templating import templates

# The place search returns at most MAX_RESULTS results, numbered from 0.
MAX_PLACE_INDEX = MAX_RESULTS - 1
router = APIRouter(dependencies=[PageLimited])


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
    save_household(request, chosen.place, chosen.household, chosen.title)
    return RedirectResponse("/today", status.HTTP_303_SEE_OTHER)


@router.get("/places", response_class=HTMLResponse)
async def places(
    request: Request,
    place_query: Annotated[str, Query(max_length=60)] = "",
    chosen: Annotated[int, Query(ge=0, le=MAX_PLACE_INDEX)] = 0,
) -> Response:
    """Place suggestions for the search box (an htmx fragment).

    Args:
        request: The incoming request.
        place_query: What the person has typed (the search box's own field name).
        chosen: Which suggestion to tick, so a form shown again keeps the visitor's pick.

    Returns:
        Up to five places to choose from, or a short message.
    """
    query = place_query.strip()
    results, failed = [], False
    if len(query) >= 2:  # noqa: PLR2004 - two letters before searching
        try:
            results = await place_finder(request).search(query)
        except PlaceSearchError:
            failed = True
    context = {"query": query, "results": results, "failed": failed, "chosen": chosen}
    return templates.TemplateResponse(request, "partials/places.html", context)


@router.get("/near", response_class=PlainTextResponse)
def near(
    lat: Annotated[str, Query(max_length=12)] = "",
    lon: Annotated[str, Query(max_length=12)] = "",
) -> str:
    """Name the browser's location and its nearest station, so the visitor sees what was found.

    Args:
        lat: Latitude from the browser.
        lon: Longitude from the browser.

    Returns:
        One plain sentence for the status line (shown as text, never as HTML).
    """
    place = near_me(lat, lon)
    if place is None and read_point(lat, lon) is None:
        return "That location could not be read. Type a place instead."
    if place is None:
        return "That location is outside India, so NirmalAir cannot use it. Type a place instead."
    nearest = nearest_stations(place.lat, place.lon, limit=1)[0]
    return (
        f"Found: {place.label}. Nearest CPCB station: {nearest.station.label}, "
        f"{distance_label(nearest.distance_km)} away."
    )


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
    place = await place_from_form(request, form)
    if place is None:
        errors.insert(0, "Choose a place from the list, or use your location.")
    if household is None or place is None:
        return _start_page(request, errors, form, status.HTTP_422_UNPROCESSABLE_CONTENT)
    save_household(request, place, household)
    return RedirectResponse("/today", status.HTTP_303_SEE_OTHER)


def _start_page(
    request: Request, errors: list[str], form: dict[str, str], code: int = status.HTTP_200_OK
) -> Response:
    context = {
        "samples": SAMPLES,
        "saved": load_household(request),
        "errors": errors,
        "form": form,
        "member_rows": range(MEMBERS.rows),
        "routine_rows": range(ROUTINES.rows),
        "commute_rows": range(COMMUTES.rows),
        "shown": {section.name: section.shown for section in SECTIONS},
        "open_more": hidden_rows_in_use(form),
    }
    return templates.TemplateResponse(request, "start.html", context, status_code=code)
