"""Facts about the home: the main room, its habits, and the indoor PM2.5 estimates."""

from app.advice.facts import Fact, FactId, Kind, number
from app.domain.assumptions import (
    PLANT_CADR_M3H,
    PLANTS_PER_M2_TO_MATCH_AIR_EXCHANGE,
    TYPICAL_PURIFIER_CADR_M3H,
)
from app.domain.household import Home
from app.domain.indoor import cigarettes, indoor_estimates


def home_fact(home: Home) -> Fact:
    """The main room and the habits that affect its air.

    Args:
        home: The household's home.

    Returns:
        A household fact.
    """
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
        FactId.HOME,
        Kind.HOUSEHOLD,
        f"Main room {home.room_sqft} sq ft with {purifier}; {'; '.join(habits)}.",
    )


def _purifier_if_fact(pm25: float, home: Home, approx: str) -> Fact:
    """What a typical purifier would change, for a home that has none."""
    typical = home.model_copy(update={"purifier_cadr_m3h": TYPICAL_PURIFIER_CADR_M3H})
    level = indoor_estimates(pm25, typical).with_purifier
    return Fact(
        FactId.INDOOR_PURIFIER_IF,
        Kind.ESTIMATE,
        f"A typical air purifier ({TYPICAL_PURIFIER_CADR_M3H} m³/h) running with windows shut "
        f"would bring the main room to {approx} {level} µg/m³.",
        f"{level} µg/m³",
        f"Main room with a {TYPICAL_PURIFIER_CADR_M3H} m³/h purifier",
    )


def plants_fact() -> Fact:
    """What houseplants do for a room's air: honestly, almost nothing.

    Returns:
        An estimate fact with its source, so the advice never suggests plants as a fix.
    """
    fewest, most = PLANTS_PER_M2_TO_MATCH_AIR_EXCHANGE
    return Fact(
        FactId.PLANTS,
        Kind.ESTIMATE,
        "Potted plants do not measurably clean a room's air: in 196 sealed-chamber tests the "
        f"median plant cleaned {PLANT_CADR_M3H} m³ an hour, so matching a home's own air "
        f"exchange would take {fewest} to {most:,} plants per m² of floor (Cummings and Waring, "
        "2019, for indoor chemicals); leaves catch only a little PM2.5. Shut windows at the "
        "worst times and a purifier do the work.",
        f"{PLANT_CADR_M3H} m³/h",
        "One houseplant cleans",
    )


def indoor_facts(pm25: float, home: Home, approx: str) -> list[Fact]:
    """Estimated PM2.5 in the main room with windows open, shut, and with a purifier.

    Args:
        pm25: Outdoor PM2.5 in µg/m³.
        home: The household's home.
        approx: "about", or "at least" beyond CPCB's scale.

    Returns:
        Estimate facts, including what a typical purifier would do in a home without one, and
        what houseplants would (almost nothing).
    """
    estimate = indoor_estimates(pm25, home)
    shut_pct = round((1 - estimate.windows_shut / pm25) * 100)
    facts = [
        Fact(
            FactId.INDOOR_OPEN,
            Kind.ESTIMATE,
            f"With windows open, the main room is {approx} {estimate.windows_open} µg/m³ of PM2.5.",
            f"{estimate.windows_open} µg/m³",
            "Main room, windows open",
        ),
        Fact(
            FactId.INDOOR_SHUT,
            Kind.ESTIMATE,
            f"With windows shut, the main room is {approx} {estimate.windows_shut} µg/m³, "
            f"{shut_pct}% below outdoors.",
            f"{estimate.windows_shut} µg/m³",
            "Main room, windows shut",
        ),
    ]
    if estimate.with_purifier is None:
        facts.append(_purifier_if_fact(pm25, home, approx))
    else:
        facts.append(
            Fact(
                FactId.INDOOR_PURIFIER,
                Kind.ESTIMATE,
                f"With windows shut and the purifier on, {approx} {estimate.with_purifier} µg/m³: "
                f"{approx} {number(cigarettes(estimate.with_purifier))} cigarettes a day instead "
                f"of {approx} {number(cigarettes(pm25))} outdoors.",
                f"{estimate.with_purifier} µg/m³",
                "Main room, purifier on",
            )
        )
    facts.append(plants_fact())
    return facts
