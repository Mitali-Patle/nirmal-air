"""The facts bundle: all facts for one household today, in the order they matter."""

from app.advice.air_facts import air_facts
from app.advice.facts import Fact, Today
from app.advice.home_facts import household_facts


def build_facts(today: Today) -> tuple[Fact, ...]:
    """Every fact the AI may use for this household today.

    Args:
        today: The day's data.

    Returns:
        Air facts first, then household facts. Ids are unique.
    """
    return (*air_facts(today), *household_facts(today))
