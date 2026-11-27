"""The "Share today's air" summary, for a family, building, school or society group.

Built from the same measured facts as the page: no AI and no new numbers.
"""

from app.advice.facts import Fact, FactId, Today, distance_label, stamp
from app.air.lookup import MAX_AGE_HOURS


def share_text(today: Today, facts: dict[str, Fact], site: str) -> str:
    """A short, plain summary of today's air at the household's place.

    Args:
        today: The day's data.
        facts: The day's facts by id (the cleanest and worst hours come from here).
        site: The app's address, so others can open their own plan.

    Returns:
        The summary, one sentence per line.
    """
    air = today.air
    if air is None:
        lines = [
            f"Air today in {today.place}: no CPCB station nearby has reported in the last "
            f"{MAX_AGE_HOURS} hours."
        ]
    else:
        lines = [
            f"Air today in {today.place}: AQI {air.aqi.value}, {air.aqi.category.label} "
            f"(CPCB, measured {stamp(air.reading.measured_at)} at "
            f"{air.nearby.station.label}, {distance_label(air.nearby.distance_km)} away).",
            f"{air.aqi.category.label}: {air.aqi.category.health}",
        ]
    lines += [f"{facts[key].label}." for key in (FactId.CLEANEST, FactId.WORST) if key in facts]
    lines.append(f"Plan for your own family: {site}")
    return "\n".join(lines)
