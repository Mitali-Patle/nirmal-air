from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

from app.advice.week_steps import step_options
from app.domain.household import Activity, Household, Routine
from app.domain.week import MAX_ENTRIES, DayImpact, LogEntry, add_entry, indoors_day, week_totals
from app.web.session import load_log, save_log
from app.web.views import week_view
from tests.builders import FAMILY, measured, today

MON = date(2026, 11, 23)


def entry(day: date, action: str = "swap-1", co2: int = 1000, pm: int = -50) -> LogEntry:
    return LogEntry(day, action, "Asha went by bus", DayImpact(co2, pm))


def test_a_step_is_logged_once_a_day_and_kept_a_week() -> None:
    log = add_entry([entry(MON - timedelta(days=7)), entry(MON)], entry(MON))
    assert log == [entry(MON)]
    log = add_entry(log, entry(MON, "indoors-2", 0, 34))
    assert [item.action for item in log] == ["swap-1", "indoors-2"]


def test_the_log_is_capped() -> None:
    log: list[LogEntry] = []
    for offset in range(MAX_ENTRIES + 5):
        log = add_entry(log, entry(MON, f"step-{offset}"))
    assert len(log) == MAX_ENTRIES
    assert log[-1].action == f"step-{MAX_ENTRIES + 4}"


def test_week_totals_add_the_last_seven_days_only() -> None:
    log = [
        entry(MON - timedelta(days=8)),
        entry(MON - timedelta(days=1)),
        entry(MON, "indoors-2", 0, 34),
    ]
    totals = week_totals(log, MON)
    assert (totals.steps, totals.co2_kg, totals.pm25_ug) == (2, 1.0, -16)


def test_indoors_without_a_measurement_changes_nothing() -> None:
    walk = Routine(member="Dadi", activity=Activity.WALK, hour=6, minutes=45)
    assert indoors_day(walk, None, None) == DayImpact(0, 0)


def test_todays_steps_are_the_offered_swap_and_routines_moved_indoors() -> None:
    options = {option.id: option for option in step_options(today())}
    assert set(options) == {"swap-1", "indoors-1", "indoors-2"}
    assert options["swap-1"].label == "Asha went by bus"
    assert options["swap-1"].impact.co2_g == 3000
    assert options["indoors-2"].label == "Dadi's walk moved indoors"
    assert options["indoors-2"].impact.pm25_ug > 0


def test_a_sensitive_commuter_logs_the_shared_car_and_clean_air_moves_nothing_indoors() -> None:
    data = FAMILY.model_dump(mode="json")
    data["members"][0]["conditions"] = ["heart condition"]
    options = {o.id: o for o in step_options(today(measured(80), Household.model_validate(data)))}
    assert set(options) == {"swap-1"}
    assert options["swap-1"].label == "Asha went by a shared car"
    assert options["swap-1"].impact.pm25_ug == 0


def test_the_week_view_marks_todays_ticks_newest_first() -> None:
    log = [entry(MON - timedelta(days=1), "indoors-2"), entry(MON)]
    view = week_view(log, step_options(today()), MON)
    ticked = {option.id for option, done in view.steps if done}
    assert ticked == {"swap-1"}
    assert [item.day for item in view.recent] == [MON, MON - timedelta(days=1)]


def test_the_log_round_trips_through_the_cookie_and_skips_damaged_entries() -> None:
    request: Any = SimpleNamespace(session={})
    save_log(request, [entry(MON)])
    request.session["log"].append({"d": "not a date"})
    assert load_log(request) == [entry(MON)]


def test_a_cycle_commute_has_no_swap_to_log() -> None:
    data = FAMILY.model_dump(mode="json")
    data["commutes"][0] |= {"mode": "cycle", "km_one_way": 5}
    options = step_options(today(household=Household.model_validate(data)))
    assert [option.id for option in options] == ["indoors-1", "indoors-2"]
