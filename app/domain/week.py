"""The "This week" log: what one day's step changed, and the totals over seven days.

Each logged step stores its numbers as worked out on that day, from that day's measured air,
so the week's totals do not shift when today's air changes.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.assumptions import ACTIVITY_BREATHING_L_PER_MIN
from app.domain.commute import LITRES_PER_M3, Swap, trip_impact
from app.domain.household import MAX_COMMUTES, MAX_ROUTINES, Commute, Routine

WEEK = timedelta(days=7)
# Every step a household can tick, for a week: a swap per commute and one per routine.
# The largest such log still fits the session cookie (tests/test_cookie_size.py).
MAX_ENTRIES = 7 * (MAX_COMMUTES + MAX_ROUTINES)
GRAMS_PER_KG = 1000
TRIPS_PER_DAY = 2


@dataclass(frozen=True)
class DayImpact:
    """What one day's step changed.

    Attributes:
        co2_g: CO₂ avoided, in grams.
        pm25_ug: PM2.5 not breathed, in µg; negative when the step meant breathing more.
    """

    co2_g: int
    pm25_ug: int


@dataclass(frozen=True)
class LogEntry:
    """One step someone ticked as done."""

    day: date
    action: str
    label: str
    impact: DayImpact


@dataclass(frozen=True)
class WeekTotals:
    """The last seven days, added up."""

    steps: int
    co2_kg: float
    pm25_ug: int


def swap_day(commute: Commute, swap: Swap, outdoor_pm25: float | None) -> DayImpact:
    """One day of a commute made the other way, both directions.

    Args:
        commute: The usual trip.
        swap: The way it was made instead.
        outdoor_pm25: That day's outdoor PM2.5 in µg/m³, if measured.

    Returns:
        CO₂ avoided and PM2.5 not breathed (negative if the swap meant breathing more).

    >>> from app.domain.household import Mode
    >>> trip = Commute(
    ...     member="Asha", mode=Mode.CAR, km_one_way=12, days_per_week=5, leaves_at_hour=9
    ... )
    >>> bus = Swap(Mode.BUS, 1, 15.0, 393, 30)
    >>> swap_day(trip, bus, 150)
    DayImpact(co2_g=3000, pm25_ug=-212)
    """
    usual = trip_impact(commute.mode, commute.km_one_way, commute.people_in_vehicle)
    other = trip_impact(swap.mode, commute.km_one_way, swap.people_in_vehicle)
    co2 = round((usual.co2_kg - other.co2_kg) * TRIPS_PER_DAY * GRAMS_PER_KG)
    if outdoor_pm25 is None:
        return DayImpact(co2, 0)
    return DayImpact(co2, round((usual.air_m3 - other.air_m3) * TRIPS_PER_DAY * outdoor_pm25))


def indoors_day(
    routine: Routine, outdoor_pm25: float | None, indoor_pm25: float | None
) -> DayImpact:
    """One day of a routine done indoors with the windows shut instead of outside.

    Args:
        routine: The routine.
        outdoor_pm25: That day's outdoor PM2.5 in µg/m³, if measured.
        indoor_pm25: The estimated indoor level with windows shut, if known.

    Returns:
        PM2.5 not breathed; no CO₂ changes.

    >>> from app.domain.household import Activity
    >>> walk = Routine(member="Dadi", activity=Activity.WALK, hour=6, minutes=45)
    >>> indoors_day(walk, 150, 100)
    DayImpact(co2_g=0, pm25_ug=34)
    """
    if outdoor_pm25 is None or indoor_pm25 is None:
        return DayImpact(0, 0)
    air_m3 = routine.minutes * ACTIVITY_BREATHING_L_PER_MIN[routine.activity] / LITRES_PER_M3
    return DayImpact(0, round(air_m3 * (outdoor_pm25 - indoor_pm25)))


def add_entry(entries: Sequence[LogEntry], entry: LogEntry) -> list[LogEntry]:
    """Log a step, once per action per day, keeping only the last seven days.

    Args:
        entries: The log so far.
        entry: The step just ticked.

    Returns:
        The new log, oldest first.
    """
    kept = [
        old
        for old in entries
        if entry.day - old.day < WEEK and (old.day, old.action) != (entry.day, entry.action)
    ]
    return [*kept, entry][-MAX_ENTRIES:]


def week_totals(entries: Iterable[LogEntry], today: date) -> WeekTotals:
    """Add up the last seven days.

    Args:
        entries: The log.
        today: Today's date.

    Returns:
        The number of steps, CO₂ avoided in kg and PM2.5 not breathed in µg.
    """
    recent = [entry for entry in entries if timedelta(0) <= today - entry.day < WEEK]
    return WeekTotals(
        steps=len(recent),
        co2_kg=round(sum(entry.impact.co2_g for entry in recent) / GRAMS_PER_KG, 1),
        pm25_ug=sum(entry.impact.pm25_ug for entry in recent),
    )
