"""What the "This week" section shows: today's steps, which are ticked, and the totals."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.advice.week_steps import StepOption
from app.domain.week import WEEK, LogEntry, WeekTotals, week_totals


@dataclass(frozen=True)
class WeekView:
    """The "This week" section: today's steps (and whether each is ticked) and the totals."""

    steps: tuple[tuple[StepOption, bool], ...]
    totals: WeekTotals
    recent: tuple[LogEntry, ...]


def week_view(entries: Sequence[LogEntry], options: Sequence[StepOption], today: date) -> WeekView:
    """What the "This week" section shows.

    Args:
        entries: The household's log.
        options: Today's steps that can be ticked.
        today: Today's date.

    Returns:
        Steps with their ticked state, the week's totals and the last week's entries, newest
        first.
    """
    done = {entry.action for entry in entries if entry.day == today}
    recent = tuple(reversed([entry for entry in entries if today - entry.day < WEEK]))
    return WeekView(
        steps=tuple((option, option.id in done) for option in options),
        totals=week_totals(entries, today),
        recent=recent,
    )
