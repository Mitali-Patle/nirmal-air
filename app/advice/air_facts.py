"""Facts about the measured air, its health meaning and the best and worst times today."""

from datetime import datetime

from app.advice.facts import Fact, Kind, Today, clock, number
from app.air.cpcb import IST
from app.domain.indoor import cigarettes

# India's 24-hour PM2.5 standard (CPCB, National Ambient Air Quality Standards, 2009).
PM25_DAILY_LIMIT = 60
FAR_STATION_KM = 25


def air_facts(today: Today) -> list[Fact]:
    """Facts about the measured air and today's timing.

    Args:
        today: The day's data.

    Returns:
        The facts, most important first.
    """
    if today.air is None:
        return [
            Fact(
                "air_now",
                Kind.MEASURED,
                f"No CPCB station near {today.place} has reported in the last 3 hours.",
            ),
            *_timing_facts(today),
        ]
    air = today.air
    station = air.nearby
    km = station.distance_km
    distance = "under 1 km" if km < 1 else f"{number(round(km, 1))} km"
    facts = [
        Fact(
            "air_now",
            Kind.MEASURED,
            f"AQI {air.aqi.value} ({air.aqi.category.label}) at {station.station.label}, "
            f"{distance} away, measured at {clock(air.reading.measured_at)}. "
            f"Main pollutant: {air.aqi.dominant.value}.",
        ),
        Fact(
            "health",
            Kind.GUIDANCE,
            f"CPCB health advice for {air.aqi.category.label} air: {air.aqi.category.health}",
        ),
    ]
    if station.distance_km > FAR_STATION_KM:
        facts.append(
            Fact("far_station", Kind.MEASURED, "The station is far away, so local air may differ.")
        )
    pm25 = today.outdoor_pm25
    if pm25 is not None:
        facts += _pm25_facts(pm25, today.approx)
    return facts + _timing_facts(today)


def _pm25_facts(pm25: float, approx: str) -> list[Fact]:
    floor = "at least " if approx == "at least" else ""
    return [
        Fact(
            "pm25",
            Kind.ESTIMATE,
            f"Outdoor PM2.5 is {approx} {round(pm25)} µg/m³ (24-hour average), "
            f"{floor}{number(round(pm25 / PM25_DAILY_LIMIT, 1))} times India's daily limit of "
            f"{PM25_DAILY_LIMIT} µg/m³.",
        ),
        Fact(
            "cigarettes",
            Kind.ESTIMATE,
            "Breathing this outdoor air all day is as harmful as smoking "
            f"{approx} {number(cigarettes(pm25))} cigarettes (Berkeley Earth).",
        ),
    ]


def _timing_facts(today: Today) -> list[Fact]:
    timing = today.timing
    if timing is None:
        return []

    def span(start: datetime, end: datetime) -> str:
        day = "today" if start.date() == today.now.astimezone(IST).date() else "tomorrow"
        return f"{clock(start)} to {clock(end)} {day}"

    cleanest, worst = timing.cleanest, timing.worst
    return [
        Fact(
            "cleanest",
            Kind.FORECAST,
            f"Cleanest time: {span(cleanest.starts_at, cleanest.ends_at)}.",
        ),
        Fact(
            "worst",
            Kind.FORECAST,
            f"Worst time: {span(worst.starts_at, worst.ends_at)}, with about "
            f"{number(timing.worst_vs_cleanest)} times the PM2.5 of the cleanest time.",
        ),
    ]
