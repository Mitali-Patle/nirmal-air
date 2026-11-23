from datetime import datetime

import httpx
import pytest
import respx

from app.air.cpcb import (
    CPCB_URL,
    IST,
    AirDataUnavailableError,
    Pollutant,
    fetch_station,
    parse_station,
)
from tests.conftest import load_fixture

STATION = "Talkatora Garden, Delhi - DPCC"


def test_a_real_payload_becomes_sub_indices_and_a_time() -> None:
    reading = parse_station(load_fixture("cpcb_talkatora.json"), STATION)
    assert reading.sub_indices[Pollutant.PM25] == 324
    assert len(reading.sub_indices) == 7
    assert reading.measured_at == datetime(2026, 11, 23, 17, tzinfo=IST)


def test_na_values_and_unknown_pollutants_are_skipped() -> None:
    rows = [
        {"pollutant_id": "PM2.5", "avg_value": "NA", "last_update": "23-11-2026 17:00:00"},
        {"pollutant_id": "BENZENE", "avg_value": "4", "last_update": "23-11-2026 17:00:00"},
        {"pollutant_id": "PM10", "avg_value": "180", "last_update": "23-11-2026 16:00:00"},
    ]
    reading = parse_station({"records": rows}, STATION)
    assert dict(reading.sub_indices) == {Pollutant.PM10: 180}
    assert reading.measured_at.hour == 16


@pytest.mark.parametrize(
    "payload",
    [
        {"error": "Rate limit exceeded"},
        {"records": []},
        {"records": [{"pollutant_id": "PM10", "avg_value": "NA", "last_update": "x"}]},
        {"records": [{"pollutant_id": "PM10", "avg_value": "90", "last_update": "yesterday"}]},
    ],
)
def test_unusable_payloads_raise(payload: object) -> None:
    with pytest.raises(AirDataUnavailableError):
        parse_station(payload, STATION)


@respx.mock
async def test_fetch_asks_for_one_station_by_its_exact_name(client: httpx.AsyncClient) -> None:
    route = respx.get(CPCB_URL).respond(json=load_fixture("cpcb_talkatora.json"))
    reading = await fetch_station(client, "test-key", STATION + " ")
    assert reading.station == STATION + " "
    assert route.calls.last.request.url.params["filters[station]"] == STATION + " "


@respx.mock
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(429, json={"error": "Rate limit exceeded"}),
        httpx.Response(200, text="<html>"),
    ],
)
async def test_fetch_failures_raise(client: httpx.AsyncClient, response: httpx.Response) -> None:
    respx.get(CPCB_URL).mock(return_value=response)
    with pytest.raises(AirDataUnavailableError):
        await fetch_station(client, "test-key", STATION)


@respx.mock
async def test_a_timeout_raises(client: httpx.AsyncClient) -> None:
    respx.get(CPCB_URL).mock(side_effect=httpx.ReadTimeout("stalled"))
    with pytest.raises(AirDataUnavailableError, match="ReadTimeout"):
        await fetch_station(client, "test-key", STATION)
