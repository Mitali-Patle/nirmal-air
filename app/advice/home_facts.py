"""Facts about the household: who lives here, routines, commutes and swaps, and the home."""

from app.advice.facts import MINUS, Fact, Kind, Today, clock, number
from app.domain.commute import Swap, swaps, trip_impact
from app.domain.guidance import routine_decision
from app.domain.household import Commute, Home, Household, Mode
from app.domain.indoor import cigarettes, indoor_estimates

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
    sensitive = {member.name for member in household.members if member.sensitive}
    for index, commute in enumerate(household.commutes, start=1):
        facts.append(_commute_fact(index, commute, pm25, today.approx))
        ranked = _ranked_swaps(commute, sensitive=commute.member in sensitive)
        for rank, swap in enumerate(ranked[:SWAPS_PER_COMMUTE], start=1):
            facts.append(_swap_fact(f"swap_{index}_{rank}", commute.member, swap))
    facts.append(_home_fact(household.home))
    if pm25 is not None:
        facts += _indoor_facts(pm25, household.home, today.approx)
    return facts


def _ranked_swaps(commute: Commute, *, sensitive: bool) -> list[Swap]:
    """Swaps in the order to suggest them; the first is the one the plan offers.

    For someone more sensitive to polluted air, swaps that do not add to the air breathed on
    the way come first, so the plan never trades their health for CO₂.
    """
    found = swaps(commute)
    if not sensitive:
        return found
    return sorted(found, key=lambda swap: swap.air_change_pct > 0)


def _member_facts(household: Household) -> list[Fact]:
    facts = []
    for index, member in enumerate(household.members, start=1):
        details = [member.role.value, *sorted(member.conditions)]
        if member.sensitive:
            details.append("more sensitive to polluted air")
        facts.append(
            Fact(f"member_{index}", Kind.HOUSEHOLD, f"{member.name}: {', '.join(details)}.")
        )
    return facts


def _routine_facts(today: Today) -> list[Fact]:
    """Each routine with today's decision for it (see `app.domain.guidance`)."""
    air = today.air
    aqi = air.aqi.value if air else None
    band = f"{air.aqi.category.label} air" if air else "no recent measurement"
    sensitive = {member.name for member in today.household.members if member.sensitive}
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
                f"routine_{index}",
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
        f"commute_{index}",
        Kind.ESTIMATE,
        f"{commute.member} goes by {mode}, "
        f"{number(commute.km_one_way)} km each way, {commute.days_per_week} days a week, "
        f"leaving at {clock(commute.leaves_at_hour)}. Each trip: about {trip.minutes} minutes, "
        f"{number(trip.co2_kg)} kg CO₂{inhaled}.",
        f"{number(trip.co2_kg)} kg CO₂",
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
    )


def _change(value: int, up: str, down: str, what: str) -> str:
    """Describe a signed change: "393% more polluted air…" or "no change in travel time".

    >>> _change(-5, " minutes longer", " minutes shorter", "travel time")
    '5 minutes shorter travel time'
    """
    if value == 0:
        return f"no change in {what}"
    return f"{abs(value)}{up if value > 0 else down} {what}"


def _mode_label(mode: Mode, people: int, member: str) -> str:
    if people > 1 and mode in {Mode.CAR, Mode.SUV}:
        return f"{mode.value} shared by {people} people ({member} and {people - 1} others)"
    return mode.value


def _home_fact(home: Home) -> Fact:
    habits = [f"cooking on {home.cooking_fuel.value}"]
    if home.incense_or_coils:
        habits.append("incense or mosquito coils are used")
    if home.smoking_indoors:
        habits.append("someone smokes indoors")
    purifier = (
        f"an air purifier ({home.purifier_cadr_m3h} m³/h)"
        if home.purifier_cadr_m3h
        else "no air purifier"
    )
    return Fact(
        "home",
        Kind.HOUSEHOLD,
        f"Main room {home.room_sqft} sq ft with {purifier}; {'; '.join(habits)}.",
    )


def _indoor_facts(pm25: float, home: Home, approx: str) -> list[Fact]:
    estimate = indoor_estimates(pm25, home)
    shut_pct = round((1 - estimate.windows_shut / pm25) * 100)
    facts = [
        Fact(
            "indoor_open",
            Kind.ESTIMATE,
            f"With windows open, the main room is {approx} {estimate.windows_open} µg/m³ of PM2.5.",
            f"{estimate.windows_open} µg/m³",
        ),
        Fact(
            "indoor_shut",
            Kind.ESTIMATE,
            f"With windows shut, the main room is {approx} {estimate.windows_shut} µg/m³, "
            f"{shut_pct}% below outdoors.",
            f"{estimate.windows_shut} µg/m³",
        ),
    ]
    if estimate.with_purifier is not None:
        facts.append(
            Fact(
                "indoor_purifier",
                Kind.ESTIMATE,
                f"With windows shut and the purifier on, {approx} {estimate.with_purifier} µg/m³: "
                f"{approx} {number(cigarettes(estimate.with_purifier))} cigarettes a day instead "
                f"of {approx} {number(cigarettes(pm25))} outdoors.",
                f"{estimate.with_purifier} µg/m³",
            )
        )
    return facts
