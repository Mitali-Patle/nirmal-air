"""Turns the day's data into what the Today page draws: the sky, the signs and the time strip."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.advice.facts import Fact, Kind, clock
from app.advice.plan import EVERYONE, Plan, PlanItem, Slot
from app.air.cpcb import IST
from app.air.forecast import HourlyPm25
from app.domain.aqi import Category
from app.domain.sky import Phase, haze_level, phase_at, sun_times
from app.domain.timing import DayTiming, Level, levels
from app.services.today import PlaceChoice
from app.web.session import ThemeChoice

AFTERNOON_FROM = 12
EVENING_FROM = 17
DARK_PHASES = frozenset({Phase.DUSK, Phase.NIGHT})
SLOT_ORDER = (Slot.MORNING, Slot.AFTERNOON, Slot.EVENING)
TICK_EVERY_HOURS = 6
FIGURE_PREFERENCE = ("swap_", "routine_", "windows", "indoor_", "cleanest", "worst")


@dataclass(frozen=True)
class Sky:
    """How the page is painted: phase of day, haze from the AQI, and whether it is dark."""

    phase: Phase
    haze: int
    theme: ThemeChoice


@dataclass(frozen=True)
class Sign:
    """One step of the plan, drawn as a road sign."""

    member: str
    action: str
    why: str
    figure: str | None
    home: bool
    slot: Slot
    facts: tuple[Fact, ...]


@dataclass(frozen=True)
class SignBoard:
    """The plan in reading order: the next step, the rest of today, and what has passed."""

    next: Sign | None
    later: tuple[Sign, ...]
    earlier: tuple[Sign, ...]


@dataclass(frozen=True)
class StripHour:
    """One hour of the forecast strip."""

    label: str
    level: Level
    cleanest: bool
    worst: bool
    tick: bool


def sky_for(
    place: PlaceChoice, now: datetime, category: Category | None, theme: ThemeChoice
) -> Sky:
    """The page's sky: the real phase of day at the place, unless the visitor picked a theme.

    Args:
        place: Where the household is.
        now: The current time.
        category: Today's measured AQI band, if any.
        theme: The visitor's theme choice.

    Returns:
        The sky to paint.
    """
    phase = phase_at(now.astimezone(IST), sun_times(place.lat, place.lon, now.astimezone(IST)))
    if theme is ThemeChoice.DARK:
        phase = Phase.NIGHT
    elif theme is ThemeChoice.LIGHT and phase in DARK_PHASES:
        phase = Phase.MORNING
    return Sky(phase, haze_level(category), theme)


def slot_of(now: datetime) -> Slot:
    """The part of the day a moment falls in.

    >>> slot_of(datetime(2026, 11, 25, 13, tzinfo=IST)).value
    'afternoon'
    """
    hour = now.astimezone(IST).hour
    if hour < AFTERNOON_FROM:
        return Slot.MORNING
    return Slot.AFTERNOON if hour < EVENING_FROM else Slot.EVENING


def sign_board(plan: Plan, facts: Sequence[Fact], now: datetime) -> SignBoard:
    """Order the plan's steps: the first one still ahead leads, past ones go last.

    Args:
        plan: The checked plan (AI or standard advice).
        facts: The facts it cites.
        now: The current time.

    Returns:
        The signs in reading order.
    """
    by_id = {fact.id: fact for fact in facts}
    current = SLOT_ORDER.index(slot_of(now))
    signs = sorted(
        (_sign(item, by_id) for item in plan.items),
        key=lambda sign: SLOT_ORDER.index(sign.slot),
    )
    ahead = [sign for sign in signs if SLOT_ORDER.index(sign.slot) >= current]
    passed = tuple(sign for sign in signs if SLOT_ORDER.index(sign.slot) < current)
    if not ahead:
        return SignBoard(None, (), passed)
    return SignBoard(ahead[0], tuple(ahead[1:]), passed)


def _sign(item: PlanItem, by_id: dict[str, Fact]) -> Sign:
    cited = tuple(by_id[fact_id] for fact_id in item.fact_ids if fact_id in by_id)
    with_figures = sorted((fact for fact in cited if fact.figure), key=_figure_rank)
    figure = with_figures[0].figure if with_figures else None
    return Sign(
        item.member, item.action, item.why, figure, item.member == EVERYONE, item.slot, cited
    )


def _figure_rank(fact: Fact) -> int:
    """Which cited figure a sign shows: what the step changes before background numbers."""
    for rank, prefix in enumerate(FIGURE_PREFERENCE):
        if fact.id.startswith(prefix):
            return rank
    return len(FIGURE_PREFERENCE)


def strip(hours: Sequence[HourlyPm25], timing: DayTiming | None) -> tuple[StripHour, ...]:
    """The forecast strip: each hour's level against the day, with the windows marked.

    Args:
        hours: Hourly forecast from now.
        timing: The cleanest and worst windows, if found.

    Returns:
        One entry per hour, ticks every six hours.
    """

    def inside(moment: datetime, start: datetime, end: datetime) -> bool:
        return start <= moment < end

    marks = levels(hours)
    return tuple(
        StripHour(
            label=clock(hour.starts_at),
            level=level,
            cleanest=timing is not None
            and inside(hour.starts_at, timing.cleanest.starts_at, timing.cleanest.ends_at),
            worst=timing is not None
            and inside(hour.starts_at, timing.worst.starts_at, timing.worst.ends_at),
            tick=index % TICK_EVERY_HOURS == 0,
        )
        for index, (hour, level) in enumerate(zip(hours, marks, strict=True))
    )


KIND_LABELS = {
    Kind.MEASURED: "Measured",
    Kind.GUIDANCE: "CPCB guidance",
    Kind.FORECAST: "Forecast",
    Kind.ESTIMATE: "Estimate",
    Kind.HOUSEHOLD: "Your household",
}
