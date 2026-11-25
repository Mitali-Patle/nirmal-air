"""What to do with an outdoor routine today, decided by code from CPCB's AQI bands.

The AI explains this decision but does not make it, and the standard advice uses the same
rule, so both always agree.
"""

from enum import StrEnum

from app.domain.aqi import Category
from app.domain.household import Activity

# Sensitive people (children, seniors, people with conditions) stay in from Poor air;
# everyone from Very Poor air (CPCB's health statements for these bands).
SENSITIVE_INDOORS_FROM = Category.POOR.lowest
EVERYONE_INDOORS_FROM = Category.VERY_POOR.lowest
# Below Moderate, routines need no change.
CHANGE_FROM = Category.MODERATE.lowest
# Routines that can move indoors or to another time; a school run or errands cannot.
FLEXIBLE = frozenset({Activity.WALK, Activity.PLAY, Activity.SPORT})


class WindowRule(StrEnum):
    """What to do with the windows today."""

    OPEN = "open the windows to air the house"
    SHUT_EXCEPT_CLEANEST = "keep windows shut; open them briefly only during the cleanest time"
    MOSTLY_SHUT = "keep windows mostly shut"


def window_rule(aqi: int | None, *, has_forecast: bool) -> WindowRule:
    """Decide what to do with the windows today.

    Args:
        aqi: Today's measured AQI, or None when no station reported.
        has_forecast: Whether a cleanest time is known.

    Returns:
        The rule.

    >>> window_rule(80, has_forecast=True).name
    'OPEN'
    """
    if aqi is not None and aqi < CHANGE_FROM:
        return WindowRule.OPEN
    return WindowRule.SHUT_EXCEPT_CLEANEST if has_forecast else WindowRule.MOSTLY_SHUT


class Decision(StrEnum):
    """What to do with one routine today."""

    AS_USUAL = "go ahead as usual"
    SHORTER = "keep it short today"
    CLEANEST_TIME = "move it to the cleanest time"
    INDOORS = "move it indoors today"
    SHORT_WITH_MASK = "keep it short and wear a well-fitting N95 mask"


def routine_decision(
    aqi: int | None, activity: Activity, *, sensitive: bool, has_forecast: bool
) -> Decision:
    """Decide what to do with a routine.

    Args:
        aqi: Today's measured AQI, or None when no station reported.
        activity: The routine.
        sensitive: Whether the person is a child, a senior or has a condition.
        has_forecast: Whether a cleanest time is known.

    Returns:
        The decision.

    >>> routine_decision(326, Activity.WALK, sensitive=True, has_forecast=True).value
    'move it indoors today'
    >>> routine_decision(150, Activity.PLAY, sensitive=False, has_forecast=True).value
    'move it to the cleanest time'
    """
    indoors_from = SENSITIVE_INDOORS_FROM if sensitive else EVERYONE_INDOORS_FROM
    if aqi is not None and aqi >= indoors_from:
        return Decision.INDOORS if activity in FLEXIBLE else Decision.SHORT_WITH_MASK
    if aqi is not None and aqi < CHANGE_FROM:
        return Decision.AS_USUAL
    if activity in FLEXIBLE and has_forecast:
        return Decision.CLEANEST_TIME
    # Moderate air for a fixed routine, or no measurement and no forecast to go by.
    return Decision.SHORTER if aqi is None else Decision.AS_USUAL
