from datetime import datetime

import httpx
import pytest
import respx

from app.air.cpcb import IST, AirDataUnavailableError
from app.air.forecast import FORECAST_URL, fetch_forecast, parse_forecast
from app.air.places import GEOCODING_URL, Place, search_name, search_places
from app.air.stations import all_stations, nearest_stations
from tests.conftest import load_fixture

FIVE_PM = datetime(2026, 11, 23, 17, 20, tzinfo=IST)


@pytest.mark.parametrize(
    ("typed", "sent"),
    [("Bangalore", "Bengaluru"), (" GURGAON ", "Gurugram"), ("Salt   Lake", "Salt Lake")],
)
def test_older_city_names_are_translated(typed: str, sent: str) -> None:
    assert search_name(typed) == sent


@respx.mock
async def test_search_returns_indian_places_with_state_and_district(
    client: httpx.AsyncClient,
) -> None:
    route = respx.get(GEOCODING_URL).respond(json=load_fixture("places_andheri.json"))
    places = await search_places(client, "Andheri")
    assert places[0].label == "Andheri, Mumbai City District, Maharashtra"
    assert route.calls.last.request.url.params["countryCode"] == "IN"


@respx.mock
async def test_no_match_is_an_empty_list(client: httpx.AsyncClient) -> None:
    respx.get(GEOCODING_URL).respond(json={"generationtime_ms": 0.2})
    assert await search_places(client, "Atlantis") == []


@respx.mock
async def test_search_failure_raises(client: httpx.AsyncClient) -> None:
    respx.get(GEOCODING_URL).respond(503)
    with pytest.raises(AirDataUnavailableError):
        await search_places(client, "Pune")


def test_a_label_does_not_repeat_a_district_named_like_the_town() -> None:
    assert Place("Nirmal", "Nirmal", "Telangana", 19.1, 78.3).label == "Nirmal, Telangana"


def test_forecast_keeps_the_next_24_hours_from_the_current_one() -> None:
    hours = parse_forecast(load_fixture("forecast_delhi.json"), FIVE_PM)
    assert len(hours) == 24
    assert hours[0].starts_at == datetime(2026, 11, 23, 17, tzinfo=IST)
    assert hours[-1].starts_at == datetime(2026, 11, 24, 16, tzinfo=IST)


def test_forecast_skips_hours_without_a_value() -> None:
    payload = {"hourly": {"time": ["2026-11-23T17:00", "2026-11-23T18:00"], "pm2_5": [None, 80.5]}}
    assert [hour.pm25 for hour in parse_forecast(payload, FIVE_PM)] == [80.5]


@respx.mock
async def test_forecast_fetch_and_failure(client: httpx.AsyncClient) -> None:
    respx.get(FORECAST_URL).respond(json=load_fixture("forecast_delhi.json"))
    assert len(await fetch_forecast(client, 28.6139, 77.209, FIVE_PM)) == 24
    respx.get(FORECAST_URL).respond(json={"reason": "bad"})
    with pytest.raises(AirDataUnavailableError):
        await fetch_forecast(client, 28.6139, 77.209, FIVE_PM)
    respx.get(FORECAST_URL).mock(side_effect=httpx.ConnectError("down"))
    with pytest.raises(AirDataUnavailableError):
        await fetch_forecast(client, 28.6139, 77.209, FIVE_PM)


def test_the_station_list_covers_india() -> None:
    stations = all_stations()
    assert len(stations) > 500
    assert len({station.state for station in stations}) > 25


def test_nearest_stations_are_sorted_by_distance() -> None:
    nearby = nearest_stations(28.6139, 77.209, limit=3)
    assert [item.station.city for item in nearby] == ["Delhi"] * 3
    assert nearby[0].distance_km <= nearby[1].distance_km <= nearby[2].distance_km
    assert nearby[0].station.label == nearby[0].station.name.strip()
