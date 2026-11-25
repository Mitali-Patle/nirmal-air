"""Standard advice: a rules-based plan used when no AI model answers.

It follows CPCB's bands and the same facts the AI would get, and the page labels it
"Standard advice (not AI-generated)". Every reason it gives is a fact sentence, so it carries
the same numbers as the rest of the page.
"""

from app.advice.facts import Fact
from app.advice.plan import EVERYONE, MAX_ITEMS, Plan, PlanContext, PlanItem, Slot
from app.domain.guidance import (
    CHANGE_FROM,
    SENSITIVE_INDOORS_FROM,
    Decision,
    WindowRule,
    routine_decision,
    window_rule,
)
from app.domain.household import Condition, CookingFuel, Household

AFTERNOON_FROM = 12
EVENING_FROM = 17
WINDOW_ACTIONS = {
    WindowRule.OPEN: "Open the windows to air the house.",
    WindowRule.SHUT_EXCEPT_CLEANEST: (
        "Keep windows shut; air the house briefly during the cleanest time."
    ),
    WindowRule.MOSTLY_SHUT: "Keep windows mostly shut until a nearby reading is available.",
}
ACTIONS = {
    Decision.AS_USUAL: "Go ahead with today's {}.",
    Decision.SHORTER: "Keep today's {} short.",
    Decision.CLEANEST_TIME: "Move today's {} to the cleanest time.",
    Decision.INDOORS: "Keep today's {} indoors.",
    Decision.SHORT_WITH_MASK: "Keep today's {} short; wear a well-fitting N95 mask.",
}


def standard_plan(context: PlanContext) -> Plan:
    """Build today's plan from fixed rules.

    Args:
        context: The household's day and its facts.

    Returns:
        A plan whose reasons are fact sentences.
    """
    facts = {fact.id: fact for fact in context.facts}
    air = context.today.air
    aqi = air.aqi.value if air else None
    household = context.today.household
    items = [_windows(aqi, facts), *_routines(aqi, household, facts)]
    items += _commutes(household, facts)
    # People's own steps come before home-wide ones, so a large household's cut keeps them.
    items += _conditions(aqi, household, facts)
    items += _home(aqi, household, facts)
    label = air.aqi.category.label if air else "Unknown"
    headline = f"{label} air today: {_summary(aqi, has_forecast='cleanest' in facts)}"
    return Plan(headline=headline, items=items[:MAX_ITEMS])


def _item(slot: Slot, member: str, action: str, fact: Fact) -> PlanItem:
    return PlanItem(slot=slot, member=member, action=action, why=fact.text, fact_ids=[fact.id])


def _slot(hour: int) -> Slot:
    if hour < AFTERNOON_FROM:
        return Slot.MORNING
    return Slot.AFTERNOON if hour < EVENING_FROM else Slot.EVENING


def _summary(aqi: int | None, *, has_forecast: bool) -> str:
    if aqi is None:
        if has_forecast:
            return "no recent measurement nearby, so use the cleanest time for outdoor plans."
        return "no recent measurement or forecast nearby, so keep outdoor time short."
    if aqi < CHANGE_FROM:
        return "normal routines are fine."
    if aqi < SENSITIVE_INDOORS_FROM:
        return "keep windows shut at the worst times and use the cleanest hours outdoors."
    return "keep windows shut, keep outdoor time short and use the cleanest hours."


def _windows(aqi: int | None, facts: dict[str, Fact]) -> PlanItem:
    rule = window_rule(aqi, has_forecast="cleanest" in facts)
    return _item(Slot.MORNING, EVERYONE, WINDOW_ACTIONS[rule], facts["windows"])


def _routines(aqi: int | None, household: Household, facts: dict[str, Fact]) -> list[PlanItem]:
    sensitive = {member.name for member in household.members if member.sensitive}
    items = []
    for index, routine in enumerate(household.routines, start=1):
        decision = routine_decision(
            aqi,
            routine.activity,
            sensitive=routine.member in sensitive,
            has_forecast="cleanest" in facts,
        )
        action = ACTIONS[decision].format(routine.activity.value)
        reason = (
            facts["cleanest"] if decision is Decision.CLEANEST_TIME else facts[f"routine_{index}"]
        )
        items.append(_item(_slot(routine.hour), routine.member, action, reason))
    return items


def _commutes(household: Household, facts: dict[str, Fact]) -> list[PlanItem]:
    items = []
    for index, commute in enumerate(household.commutes, start=1):
        swap = facts.get(f"swap_{index}_1")
        if swap is not None:
            slot = _slot(commute.leaves_at_hour)
            items.append(_item(slot, commute.member, "Try the lower-CO₂ way for this trip.", swap))
    return items


def _home(aqi: int | None, household: Household, facts: dict[str, Fact]) -> list[PlanItem]:
    home, fact = household.home, facts["home"]
    items = []
    if "indoor_purifier" in facts and (aqi is None or aqi >= CHANGE_FROM):
        action = "Run the purifier in the main room with doors shut."
        items.append(_item(Slot.EVENING, EVERYONE, action, facts["indoor_purifier"]))
    if home.incense_or_coils:
        action = "Skip incense and mosquito coils today; use a net instead."
        items.append(_item(Slot.EVENING, EVERYONE, action, fact))
    if home.smoking_indoors:
        items.append(_item(Slot.EVENING, EVERYONE, "Keep smoking out of the house.", fact))
    if home.cooking_fuel is CookingFuel.SOLID:
        action = "Cook with a window or exhaust open near the stove; keep children away."
        items.append(_item(Slot.EVENING, EVERYONE, action, fact))
    return items


def _conditions(aqi: int | None, household: Household, facts: dict[str, Fact]) -> list[PlanItem]:
    if aqi is None or aqi < CHANGE_FROM:
        return []
    action = "Keep usual medicines handy; see a doctor if breathing gets worse."
    return [
        _item(Slot.MORNING, member.name, action, facts["health"])
        for member in household.members
        if member.conditions & {Condition.LUNG, Condition.HEART}
    ]
