from datetime import datetime, timedelta

from app.domain.readings import IST, HourlyPm25
from app.domain.timing import Level, day_timing, levels

START = datetime(2026, 11, 24, 0, tzinfo=IST)


def forecast(values: list[float], start: datetime = START) -> list[HourlyPm25]:
    return [HourlyPm25(start + timedelta(hours=i), value) for i, value in enumerate(values)]


def test_cleanest_and_worst_windows_lie_in_waking_hours() -> None:
    # Night hours are the cleanest and dirtiest of all, but nobody plans a walk at 3 am.
    values = (
        [5.0] * 6
        + [80, 90, 100, 60, 40, 30, 20, 20, 20, 50, 70, 120, 130, 140, 110, 90]
        + [200.0] * 2
    )
    timing = day_timing(forecast(values))
    assert timing is not None
    assert (timing.cleanest.starts_at.hour, timing.cleanest.ends_at.hour) == (12, 15)
    assert timing.cleanest.mean_pm25 == 20
    assert (timing.worst.starts_at.hour, timing.worst.ends_at.hour) == (17, 20)
    assert timing.worst_vs_cleanest == 6.5


def test_windows_do_not_cross_midnight_or_gaps() -> None:
    late = forecast([10.0] * 3, START.replace(hour=23) - timedelta(days=1))
    assert day_timing(late) is None
    gap = forecast([10.0, 10.0], START.replace(hour=9)) + forecast([10.0], START.replace(hour=12))
    assert day_timing(gap) is None


def test_hours_are_levelled_against_the_median() -> None:
    assert levels(forecast([50, 100, 100, 120, 200])) == [
        Level.CLEANER,
        Level.TYPICAL,
        Level.TYPICAL,
        Level.DIRTIER,
        Level.DIRTIER,
    ]
    assert levels([]) == []
