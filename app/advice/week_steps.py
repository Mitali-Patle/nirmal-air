"""Steps a household can tick as done today, each with what it changes (see app/domain/week)."""

from dataclasses import dataclass

from app.advice.facts import Today
from app.domain.commute import offered_swaps
from app.domain.guidance import Decision, routine_decision
from app.domain.household import Mode
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
    household = today.household
    sensitive = {member.name for member in household.members if member.sensitive}
    pm25 = today.outdoor_pm25
    options = []
    for index, commute in enumerate(household.commutes, start=1):
        offered = offered_swaps(commute, sensitive=commute.member in sensitive)
        if offered:
            swap = offered[0]
            how = swap.mode.value
            if swap.people_in_vehicle > 1 and swap.mode in {Mode.CAR, Mode.SUV}:
                how = f"a shared {swap.mode.value}"
            options.append(
                StepOption(
                    f"swap-{index}",
                    f"{commute.member} went by {how}",
                    swap_day(commute, swap, pm25),
                )
            )
    indoor = indoor_estimates(pm25, household.home).windows_shut if pm25 is not None else None
    aqi = today.air.aqi.value if today.air else None
    for index, routine in enumerate(household.routines, start=1):
        decision = routine_decision(
            aqi,
            routine.activity,
            sensitive=routine.member in sensitive,
            has_forecast=today.timing is not None,
        )
        if decision is Decision.INDOORS:
            options.append(
                StepOption(
                    f"indoors-{index}",
                    f"{routine.member}'s {routine.activity.value} moved indoors",
                    indoors_day(routine, pm25, indoor),
                )
            )
    return options
