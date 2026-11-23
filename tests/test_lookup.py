from datetime import datetime, timedelta

import httpx
import pytest
import respx

from app.air.cpcb import CPCB_URL, IST
from app.air.lookup import AirLookup
from app.air.stations import nearest_stations
from app.cache import Cached, TtlCache
from tests.conftest import load_fixture

DELHI = (28.6139, 77.209)
FIVE_PM = datetime(2026, 11, 23, 17, 30, tzinfo=IST)


def rows(*pairs: tuple[str, str], at: str = "23-11-2026 17:00:00") -> dict[str, object]:
    return {
        "records": [
            {"pollutant_id": pollutant, "avg_value": value, "last_update": at}
            for pollutant, value in pairs
        ]
    }


def by_station(**payloads: object) -> respx.Route:
    """Answer each nearby station with its own payload (by position: first, second, third)."""
    names = [item.station.name for item in nearest_stations(*DELHI)]
    answers = dict(zip(names, payloads.values(), strict=False))

    def respond(request: httpx.Request) -> httpx.Response:
        payload = answers.get(request.url.params["filters[station]"])
        if isinstance(payload, Exception):
            raise payload
        return httpx.Response(200, json=payload if payload is not None else {"records": []})

    return respx.get(CPCB_URL).mock(side_effect=respond)


@respx.mock
async def test_the_nearest_valid_station_wins(client: httpx.AsyncClient) -> None:
    by_station(first=load_fixture("cpcb_talkatora.json"), second=rows(("PM10", "90")))
    air = await AirLookup(client, "key").measured_air(*DELHI, FIVE_PM)
    assert air is not None
    assert air.aqi.value == 324
    assert air.nearby == nearest_stations(*DELHI)[0]
    assert not air.from_cache_after_failure


@respx.mock
async def test_a_station_without_particle_readings_is_skipped(client: httpx.AsyncClient) -> None:
    by_station(
        first=rows(("OZONE", "56"), ("CO", "24"), ("NO2", "30")),
        second=rows(("PM2.5", "210"), ("PM10", "180"), ("NO2", "40")),
    )
    air = await AirLookup(client, "key").measured_air(*DELHI, FIVE_PM)
    assert air is not None
    assert (air.aqi.value, air.nearby) == (210, nearest_stations(*DELHI)[1])


@respx.mock
async def test_old_readings_and_failures_give_no_measured_air(client: httpx.AsyncClient) -> None:
    old = rows(("PM2.5", "210"), ("PM10", "180"), ("NO2", "40"), at="23-11-2026 09:00:00")
    by_station(first=old, second=httpx.ReadTimeout("stalled"), third={"error": "x"})
    assert await AirLookup(client, "key").measured_air(*DELHI, FIVE_PM) is None


@respx.mock
async def test_a_cached_reading_saves_a_request_and_covers_an_outage(
    client: httpx.AsyncClient,
) -> None:
    now = [0.0]
    route = by_station(first=load_fixture("cpcb_talkatora.json"))
    lookup = AirLookup(client, "key", TtlCache(ttl_s=900, keep_s=3600, clock=lambda: now[0]))
    await lookup.measured_air(*DELHI, FIVE_PM)
    calls = route.call_count
    await lookup.measured_air(*DELHI, FIVE_PM)
    assert calls == 1  # the nearest station was valid, so the others were not asked
    assert route.call_count == calls  # and the second lookup came from the cache

    now[0] = 1200  # past the 15-minute time to live, inside the fallback window
    by_station(first=httpx.ReadTimeout("stalled"))
    air = await lookup.measured_air(*DELHI, FIVE_PM + timedelta(minutes=20))
    assert air is not None
    assert air.from_cache_after_failure


def test_cache_entries_expire_and_are_dropped_after_the_fallback_window() -> None:
    now = [0.0]
    cache: TtlCache[str] = TtlCache(ttl_s=10, keep_s=60, clock=lambda: now[0])
    cache.put("k", "v")
    assert cache.get("k") == Cached("v", stale=False)
    now[0] = 30
    assert cache.get("k") == Cached("v", stale=True)
    now[0] = 61
    assert cache.get("k") is None
    assert cache.get("missing") is None


@pytest.mark.parametrize("hours_old", [2, 4])
@respx.mock
async def test_readings_older_than_three_hours_are_not_used(
    client: httpx.AsyncClient, hours_old: int
) -> None:
    stamp = (FIVE_PM - timedelta(hours=hours_old)).strftime("%d-%m-%Y %H:00:00")
    by_station(first=rows(("PM2.5", "210"), ("PM10", "180"), ("NO2", "40"), at=stamp))
    air = await AirLookup(client, "key").measured_air(*DELHI, FIVE_PM)
    assert (air is not None) == (hours_old < 3)


def test_the_cache_drops_its_oldest_entry_when_full() -> None:
    cache: TtlCache[int] = TtlCache(ttl_s=10, keep_s=60, max_items=2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 3)  # refreshing "a" makes "b" the oldest
    cache.put("c", 4)
    assert cache.get("b") is None
    kept = [cache.get(key) for key in ("a", "c")]
    assert [entry.value for entry in kept if entry is not None] == [3, 4]
