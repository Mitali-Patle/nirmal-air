"""Facts about the household: who lives here, routines, commutes and swaps, and the home."""

from app.advice.facts import (
    MINUS,
    Fact,
    Kind,
    Today,
    clock,
    commute_id,
    member_id,
    number,
    routine_id,
    swap_id,
)
from app.advice.indoor_facts import home_fact, indoor_facts
from app.domain.commute import Swap, offered_swaps, shared_car, trip_impact
from app.domain.guidance import routine_decision
from app.domain.household import Commute, Household, Mode

SWAPS_PER_COMMUTE = 2


def household_facts(today: Today) -> list[Fact]:
    """Facts about the household and the estimates worked out for it.

    Args:
        today: The day's data.

    Returns:
        Member, routine, commute, swap, home and indoor facts.
    """
    household = today.household
    pm25 = today.outdoor_pm25
    facts = _member_facts(household) + _routine_facts(today)
    sensitive = household.sensitive_names
    for index, commute in enumerate(household.commutes, start=1):
        facts.append(_commute_fact(index, commute, pm25, today.approx))
        ranked = offered_swaps(commute, sensitive=commute.member in sensitive)
        for rank, swap in enumerate(ranked[:SWAPS_PER_COMMUTE], start=1):
            facts.append(_swap_fact(swap_id(index, rank), commute.member, swap))
    facts.append(home_fact(household.home))
    if pm25 is not None:
        facts += indoor_facts(pm25, household.home, today.approx)
    return facts


def _member_facts(household: Household) -> list[Fact]:
    facts = []
    for index, member in enumerate(household.members, start=1):
        details = [member.role.value, *sorted(member.conditions)]
        if member.sensitive:
            details.append("more sensitive to polluted air")
        facts.append(
            Fact(member_id(index), Kind.HOUSEHOLD, f"{member.name}: {', '.join(details)}.")
        )
    return facts


def _routine_facts(today: Today) -> list[Fact]:
    """Each routine with today's decision for it (see `app.domain.guidance`)."""
    air = today.air
    aqi = air.aqi.value if air else None
    band = f"{air.aqi.category.label} air" if air else "no recent measurement"
    sensitive = today.household.sensitive_names
    facts = []
    for index, routine in enumerate(today.household.routines, start=1):
        decision = routine_decision(
            aqi,
            routine.activity,
            sensitive=routine.member in sensitive,
            has_forecast=today.timing is not None,
        )
        who = "a more sensitive person" if routine.member in sensitive else "this person"
        facts.append(
            Fact(
                routine_id(index),
                Kind.GUIDANCE,
                f"{routine.member}'s usual {routine.activity.value}: {clock(routine.hour)}, "
                f"for {routine.minutes} minutes. Today's rule for {band} and {who}: "
                f"{decision.value}.",
                clock(routine.hour),
            )
        )
    return facts


def _commute_fact(index: int, commute: Commute, pm25: float | None, approx: str) -> Fact:
    trip = trip_impact(commute.mode, commute.km_one_way, commute.people_in_vehicle)
    inhaled = ""
    if pm25 is not None:
        inhaled = f", and {approx} {number(trip.inhaled_ug(pm25))} µg of PM2.5 breathed in"
    mode = _mode_label(commute.mode, commute.people_in_vehicle, commute.member)
    return Fact(
        commute_id(index),
        Kind.ESTIMATE,
        f"{commute.member} goes by {mode}, "
        f"{number(commute.km_one_way)} km each way, {commute.days_per_week} days a week, "
        f"leaving at {clock(commute.leaves_at_hour)}. Each trip: about {trip.minutes} minutes, "
        f"{number(trip.co2_kg)} kg CO₂{inhaled}.",
        f"{number(trip.co2_kg)} kg CO₂/trip",
        f"{commute.member} by {mode}, {number(commute.km_one_way)} km",
    )


def _swap_fact(fact_id: str, member: str, swap: Swap) -> Fact:
    return Fact(
        fact_id,
        Kind.ESTIMATE,
        f"If {member} went by {_mode_label(swap.mode, swap.people_in_vehicle, member)} instead: "
        f"{number(swap.co2_saved_kg_week)} kg less CO₂ a week; "
        f"{_change(swap.air_change_pct, '% more', '% less', 'polluted air breathed on the way')}; "
        f"{_change(swap.minutes_change, ' minutes longer', ' minutes shorter', 'travel time')}.",
        f"{MINUS}{number(swap.co2_saved_kg_week)} kg CO₂/wk",
        _swap_label(member, swap),
    )


def _change(value: int, up: str, down: str, what: str) -> str:
    """Describe a signed change: "393% more polluted air…" or "no change in travel time".

    >>> _change(-5, " minutes longer", " minutes shorter", "travel time")
    '5 minutes shorter travel time'
    """
    if value == 0:
        return f"no change in {what}"
    return f"{abs(value)}{up if value > 0 else down} {what}"


def _swap_label(member: str, swap: Swap) -> str:
    """A swap in a few words, such as "Asha by bus instead" or "Asha in a shared car"."""
    if shared_car(swap.mode, swap.people_in_vehicle):
        return f"{member} in a shared {swap.mode.value}"
    return f"{member} by {swap.mode.value} instead"


def _mode_label(mode: Mode, people: int, member: str) -> str:
    if shared_car(mode, people):
        return f"{mode.value} shared by {people} people ({member} and {people - 1} others)"
    return mode.value
