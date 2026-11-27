from datetime import datetime
from types import SimpleNamespace
from typing import Any

import respx

from app.advice.bundle import build_facts
from app.advice.facts import Fact, Kind
from app.advice.plan import Plan, PlanItem, Slot
from app.ai.task import Provenance
from app.air.forecast import FORECAST_URL
from app.air.weather import WEATHER_URL, Weather
from app.cache import TtlCache
from app.domain.household import Mode
from app.domain.readings import IST, HourlyPm25
from app.services.today import PlaceChoice, TodayService
from app.web.cookie import pack
from app.web.household_form import parse_household
from app.web.session import ThemeChoice, load_household, theme_choice
from app.web.share import share_text
from app.web.templating import templates
from app.web.views import plan_board, slot_of
from tests.builders import FAMILY, today


def request_with(session: dict[str, Any]) -> Any:
    return SimpleNamespace(session=session)


def test_late_evening_plans_have_no_next_step_only_earlier_ones() -> None:
    plan = Plan(
        items=[
            PlanItem(slot=Slot.MORNING, member="Asha", action="Walk.", why="Fine.", fact_ids=["x"])
        ],
    )
    board = plan_board(plan, [], datetime(2026, 11, 25, 22, tzinfo=IST))
    assert (board.next, board.later, len(board.earlier)) == (None, (), 1)
    assert slot_of(datetime(2026, 11, 25, 19, tzinfo=IST)) is Slot.EVENING
    assert slot_of(datetime(2026, 11, 25, 8, tzinfo=IST)) is Slot.MORNING


def test_a_damaged_or_old_cookie_is_ignored() -> None:
    assert load_household(request_with({})) is None
    bad = {"place": {"label": "X", "lat": "north", "lon": 1}, "household": pack({"members": []})}
    assert load_household(request_with(bad)) is None
    unpacked = {"place": {"label": "X", "lat": 1, "lon": 1}, "household": {"members": []}}
    assert load_household(request_with(unpacked)) is None
    assert theme_choice(request_with({"theme": "purple"})) is ThemeChoice.AUTO
    assert theme_choice(request_with({"theme": "dark"})) is ThemeChoice.DARK


def test_commute_rows_are_read() -> None:
    household, errors = parse_household(
        {
            "m0_name": "Asha",
            "c0_member": "Asha",
            "c0_mode": "car",
            "c0_km": "12",
            "c0_days": "5",
            "c0_hour": "9",
            "c0_people": "2",
            "c0_metro": "on",
        }
    )
    assert errors == []
    assert household is not None
    assert household.commutes[0].mode is Mode.CAR
    assert household.commutes[0].metro_possible is True


def test_form_errors_read_as_sentences() -> None:
    _, errors = parse_household({"m0_name": "Asha", "m1_name": "Asha"})
    assert errors == ["Each member needs a different name"]
    _, errors = parse_household({"m0_name": "Asha", "home_sqft": "5"})
    assert errors == ["Home main room size: input should be greater than or equal to 50."]
    _, errors = parse_household({})
    assert errors == ["Add at least one person, with a name."]


async def test_without_a_data_key_there_is_no_measured_air(client: Any) -> None:
    forecasts: TtlCache[tuple[HourlyPm25, ...]] = TtlCache(60, 60)
    forecasts.put("28.61,77.21", ())
    service = TodayService(client, None, forecasts)
    day = await service.day(
        PlaceChoice("Delhi", 28.61, 77.21), FAMILY, datetime(2026, 11, 25, 8, tzinfo=IST)
    )
    assert (day.today.air, day.hours) == (None, ())


def test_signs_show_what_the_step_changes_first() -> None:
    facts = [
        Fact("commute_1", Kind.ESTIMATE, "Trip.", "1.68 kg CO₂"),
        Fact("swap_1_1", Kind.ESTIMATE, "Swap.", "Saves 15 kg CO₂/wk"),
        Fact("home", Kind.HOUSEHOLD, "Home."),
        Fact("air_now", Kind.MEASURED, "Air.", "AQI 326"),
    ]
    plan = Plan(
        items=[
            PlanItem(
                slot=Slot.EVENING,
                member="Asha",
                action="Bus.",
                why="Less.",
                fact_ids=["commute_1", "swap_1_1"],
            ),
            PlanItem(
                slot=Slot.EVENING,
                member="Asha",
                action="Home.",
                why="Fine.",
                fact_ids=["air_now", "home"],
            ),
            PlanItem(
                slot=Slot.EVENING, member="Asha", action="Rest.", why="Fine.", fact_ids=["home"]
            ),
        ],
    )
    board = plan_board(plan, facts, datetime(2026, 11, 25, 18, tzinfo=IST))
    assert board.next is not None
    assert [board.next.figure, *(sign.figure for sign in board.later)] == [
        "Saves 15 kg CO₂/wk",
        "AQI 326",
        None,
    ]


async def test_an_old_forecast_is_used_when_open_meteo_is_down(client: Any) -> None:
    forecasts: TtlCache[tuple[HourlyPm25, ...]] = TtlCache(0, 3 * 3600)
    earlier = datetime(2026, 11, 25, 7, tzinfo=IST)
    hours = tuple(HourlyPm25(earlier.replace(hour=h), 50.0) for h in range(7, 12))
    forecasts.put("28.61,77.21", hours)
    service = TodayService(client, None, forecasts)
    with respx.mock:
        respx.get(FORECAST_URL).respond(503)
        respx.get(WEATHER_URL).respond(json={"current": {"cloud_cover": 90, "precipitation": 1.2}})
        day = await service.day(
            PlaceChoice("Delhi", 28.61, 77.21),
            FAMILY,
            earlier.replace(hour=9, minute=40),
            weather=True,
        )
    assert [hour.starts_at.hour for hour in day.hours] == [9, 10, 11]
    assert day.weather == Weather(90, raining=True)


def test_signs_about_the_home_are_blue_whoever_they_are_for() -> None:
    facts = [Fact("windows", Kind.GUIDANCE, "Windows."), Fact("routine_1", Kind.GUIDANCE, "Walk.")]
    plan = Plan(
        items=[
            PlanItem(
                slot=Slot.EVENING,
                member="Asha",
                action="Shut it.",
                why="Air.",
                fact_ids=["windows"],
            ),
            PlanItem(
                slot=Slot.EVENING,
                member="Everyone",
                action="Walk in.",
                why="Air.",
                fact_ids=["routine_1"],
            ),
            PlanItem(
                slot=Slot.EVENING, member="Everyone", action="Rest.", why="Air.", fact_ids=["gone"]
            ),
        ],
    )
    board = plan_board(plan, facts, datetime(2026, 11, 25, 18, tzinfo=IST))
    assert board.next is not None
    assert [board.next.home, *(sign.home for sign in board.later)] == [True, False, True]


def test_a_day_with_no_steps_left_says_so() -> None:
    item = PlanItem(slot=Slot.MORNING, member="Asha", action="Walk.", why="Fine.", fact_ids=["x"])
    plan = Plan(items=[item])
    board = plan_board(plan, [], datetime(2026, 11, 25, 22, tzinfo=IST))
    provenance = Provenance(
        task="plan",
        prompt_version="plan-v6",
        provider="fake:model",
        cached=False,
        latency_ms=1,
        attempts=(),
        request={"facts": []},
        reply=None,
    )
    page = templates.get_template("partials/plan.html").render(
        board=board, provenance=provenance, lang="en"
    )
    assert "Nothing more is planned for today" in page
    assert "Earlier today (1)" in page


def test_the_shared_summary_states_the_reading_and_its_source() -> None:
    day = today()
    facts = {fact.id: fact for fact in build_facts(day)}
    text = share_text(day, facts, "https://nirmal-air.vercel.app/")
    lines = text.splitlines()
    assert lines[0].startswith(
        "Air today in ITO, New Delhi: AQI 326, Very Poor (CPCB, measured 24 Nov, 8 am IST"
    )
    assert "Cleanest" in text and "Worst" in text
    assert lines[-1] == "Plan for your own family: https://nirmal-air.vercel.app/"
    no_air = today(with_air=False, with_timing=False)
    empty = share_text(no_air, {fact.id: fact for fact in build_facts(no_air)}, "x")
    assert "no CPCB station nearby has reported in the last 3 hours" in empty
    assert "Cleanest" not in empty


async def test_a_forecast_or_weather_that_just_failed_is_not_asked_again(client: Any) -> None:
    service = TodayService(client, None)
    place = PlaceChoice("Delhi", 28.61, 77.21)
    now = datetime(2026, 11, 25, 9, tzinfo=IST)
    with respx.mock:
        forecast = respx.get(FORECAST_URL).respond(503)
        weather = respx.get(WEATHER_URL).respond(503)
        first = await service.day(place, FAMILY, now, weather=True)
        second = await service.day(place, FAMILY, now, weather=True)
    assert (first.hours, first.weather, second.hours, second.weather) == ((), None, (), None)
    assert (forecast.call_count, weather.call_count) == (1, 1)


def test_a_step_moved_to_the_cleanest_time_shows_that_time() -> None:
    facts = [
        Fact("routine_1", Kind.HOUSEHOLD, "Walk at 6 am.", "6 am"),
        Fact("cleanest", Kind.FORECAST, "Cleanest 1 pm to 4 pm.", "1 to 4 pm"),
    ]
    item = PlanItem(
        slot=Slot.AFTERNOON,
        member="Asha",
        action="Walk at the cleanest time.",
        why="Less PM2.5.",
        fact_ids=["routine_1", "cleanest"],
    )
    board = plan_board(Plan(items=[item]), facts, datetime(2026, 11, 25, 12, tzinfo=IST))
    assert board.next is not None and board.next.figure == "1 to 4 pm"
