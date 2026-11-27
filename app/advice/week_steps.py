"""Steps a household can tick as done today, each with what it changes (see app/domain/week)."""

from dataclasses import dataclass

from app.advice.facts import Today
from app.domain.commute import offered_swaps, shared_car
from app.domain.guidance import Decision, routine_decision
from app.domain.indoor import indoor_estimates
from app.domain.week import DayImpact, indoors_day, swap_day


@dataclass(frozen=True)
class StepOption:
    """A step that can be ticked: an id for the form, words for the button, its impact."""

    id: str
    label: str
    impact: DayImpact


def step_options(today: Today) -> list[StepOption]:
    """Today's loggable steps: each commute's offered swap and each routine moved indoors.

    Args:
        today: The day's data.

    Returns:
        The steps, commutes first.
    """
    sensitive = today.household.sensitive_names
    return _swap_steps(today, sensitive) + _indoor_steps(today, sensitive)


def _swap_steps(today: Today, sensitive: frozenset[str]) -> list[StepOption]:
    """The swap the plan offers for each commute, if there is one."""
    steps = []
    for index, commute in enumerate(today.household.commutes, start=1):
        offered = offered_swaps(commute, sensitive=commute.member in sensitive)
        if not offered:
            continue
        swap = offered[0]
        how = (
            f"a shared {swap.mode.value}"
            if shared_car(swap.mode, swap.people_in_vehicle)
            else swap.mode.value
        )
        impact = swap_day(commute, swap, today.outdoor_pm25)
        steps.append(StepOption(f"swap-{index}", f"{commute.member} went by {how}", impact))
    return steps


def _indoor_steps(today: Today, sensitive: frozenset[str]) -> list[StepOption]:
    """Each routine that today's rule moves indoors."""
    pm25 = today.outdoor_pm25
    indoor = indoor_estimates(pm25, today.household.home).windows_shut if pm25 is not None else None
    aqi = today.air.aqi.value if today.air else None
    steps = []
    for index, routine in enumerate(today.household.routines, start=1):
        decision = routine_decision(
            aqi,
            routine.activity,
            sensitive=routine.member in sensitive,
            has_forecast=today.timing is not None,
        )
        if decision is Decision.INDOORS:
            label = f"{routine.member}'s {routine.activity.value} moved indoors"
            steps.append(StepOption(f"indoors-{index}", label, indoors_day(routine, pm25, indoor)))
    return steps
