"""Facts about the measured air, its health meaning and the best and worst times today."""

from datetime import datetime

from app.advice.facts import (
    FAR_STATION_KM,
    TIMES,
    Fact,
    FactId,
    Kind,
    Today,
    clock,
    clock_span,
    distance_label,
    number,
)
from app.air.lookup import MAX_AGE_HOURS
from app.domain.guidance import WindowRule, window_rule
from app.domain.indoor import cigarettes
from app.domain.readings import IST

# India's 24-hour PM2.5 standard (CPCB, National Ambient Air Quality Standards, 2009).
PM25_DAILY_LIMIT = 60


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
                FactId.AIR_NOW,
                Kind.MEASURED,
                f"No CPCB station near {today.place} has reported "
                f"in the last {MAX_AGE_HOURS} hours.",
            ),
            *_timing_facts(today),
            _windows_fact(today),
        ]
    air = today.air
    station = air.nearby
    km = station.distance_km
    distance = distance_label(km)
    facts = [
        Fact(
            FactId.AIR_NOW,
            Kind.MEASURED,
            f"AQI {air.aqi.value} ({air.aqi.category.label}) at {station.station.label}, "
            f"{distance} away, measured at {clock(air.reading.measured_at)}. "
            f"Main pollutant: {air.aqi.dominant.value}.",
            f"AQI {air.aqi.value}",
        ),
        Fact(
            FactId.HEALTH,
            Kind.GUIDANCE,
            f"CPCB health advice for {air.aqi.category.label} air: {air.aqi.category.health}",
        ),
    ]
    if station.distance_km > FAR_STATION_KM:
        facts.append(
            Fact(
                FactId.FAR_STATION,
                Kind.MEASURED,
                "The station is far away, so local air may differ.",
            )
        )
    pm25 = today.outdoor_pm25
    if pm25 is not None:
        facts += _pm25_facts(pm25, today.approx)
    return [*facts, *_timing_facts(today), _windows_fact(today)]


def _pm25_facts(pm25: float, approx: str) -> list[Fact]:
    floor = "at least " if approx == "at least" else ""
    return [
        Fact(
            FactId.PM25,
            Kind.ESTIMATE,
            f"Outdoor PM2.5 is {approx} {round(pm25)} µg/m³ (24-hour average), "
            f"{floor}{number(round(pm25 / PM25_DAILY_LIMIT, 1))} times India's daily limit of "
            f"{PM25_DAILY_LIMIT} µg/m³.",
            f"{round(pm25)} µg/m³",
        ),
        Fact(
            FactId.CIGARETTES,
            Kind.ESTIMATE,
            "Breathing this outdoor air all day is as harmful as smoking "
            f"{approx} {number(cigarettes(pm25))} cigarettes (Berkeley Earth).",
            f"{number(cigarettes(pm25))} cig/day",
            "Outdoor air all day, as cigarettes",
        ),
    ]


def _span(today: Today, start: datetime, end: datetime) -> str:
    day = "today" if start.date() == today.now.astimezone(IST).date() else "tomorrow"
    return f"{clock(start)} to {clock(end)} {day}"


def _windows_fact(today: Today) -> Fact:
    """Today's rule for the windows, decided by code (see `app.domain.guidance`)."""
    air, timing = today.air, today.timing
    rule = window_rule(air.aqi.value if air else None, has_forecast=timing is not None)
    band = f"{air.aqi.category.label} air" if air else "no recent measurement"
    if rule is WindowRule.SHUT_EXCEPT_CLEANEST and timing is not None:
        when = _span(today, timing.cleanest.starts_at, timing.cleanest.ends_at)
        figure = clock_span(timing.cleanest.starts_at, timing.cleanest.ends_at)
        return Fact(
            FactId.WINDOWS,
            Kind.GUIDANCE,
            f"Today's rule for windows on {band}: {rule.value}, {when}.",
            figure,
        )
    return Fact(FactId.WINDOWS, Kind.GUIDANCE, f"Today's rule for windows on {band}: {rule.value}.")


def _timing_facts(today: Today) -> list[Fact]:
    timing = today.timing
    if timing is None:
        return []

    def span(start: datetime, end: datetime) -> str:
        return _span(today, start, end)

    cleanest, worst = timing.cleanest, timing.worst
    return [
        Fact(
            FactId.CLEANEST,
            Kind.FORECAST,
            f"Cleanest time: {span(cleanest.starts_at, cleanest.ends_at)}.",
            clock_span(cleanest.starts_at, cleanest.ends_at),
            f"Cleanest {span(cleanest.starts_at, cleanest.ends_at)}",
        ),
        Fact(
            FactId.WORST,
            Kind.FORECAST,
            f"Worst time: {span(worst.starts_at, worst.ends_at)}, with about "
            f"{number(timing.worst_vs_cleanest)} times the PM2.5 of the cleanest time.",
            clock_span(worst.starts_at, worst.ends_at),
            f"Worst {span(worst.starts_at, worst.ends_at)}, "
            f"{number(timing.worst_vs_cleanest)}{TIMES} the cleanest",
        ),
    ]
