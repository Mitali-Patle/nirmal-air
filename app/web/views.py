"""Turns the day's data into the plan's signs and the 24-hour strip.

The page's sky lives in `sky_view` and the "This week" section in `week_view`.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.advice.facts import (
    HOME_FACT_IDS,
    INDOOR_PREFIX,
    ROUTINE_PREFIX,
    SWAP_PREFIX,
    Fact,
    FactId,
    clock,
)
from app.advice.plan import EVERYONE, Plan, PlanItem, Slot
from app.domain.readings import IST, HourlyPm25
from app.domain.timing import DayTiming, Level, levels

SLOT_ORDER = (Slot.MORNING, Slot.AFTERNOON, Slot.EVENING)
TICK_EVERY_HOURS = 6
# Steps about the home (`HOME_FACT_IDS`) are blue signs; steps people take are green.
# A sign shows the figure of what its step changes before the day's background numbers.
FIGURE_PREFERENCE = (
    SWAP_PREFIX,
    ROUTINE_PREFIX,
    FactId.WINDOWS,
    INDOOR_PREFIX,
    FactId.CLEANEST,
    FactId.WORST,
)


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


def slot_of(now: datetime) -> Slot:
    """The part of the day a moment falls in.

    >>> slot_of(datetime(2026, 11, 25, 13, tzinfo=IST)).value
    'afternoon'
    """
    return Slot.of_hour(now.astimezone(IST).hour)


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
    home = any(fact.id in HOME_FACT_IDS for fact in cited) if cited else item.member == EVERYONE
    return Sign(item.member, item.action, item.why, figure, home, item.slot, cited)


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
