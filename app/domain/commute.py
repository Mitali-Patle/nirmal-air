"""Commute impact: time, CO₂ and the polluted air breathed on a trip, and what a swap changes.

"Air breathed" is the air a traveller inhales on the way, weighted by how polluted it is
relative to outdoors. Multiplied by the outdoor PM2.5 level it gives the PM2.5 inhaled. Using
the weighted volume lets two modes be compared even when a station reports no PM2.5.
"""

from dataclasses import dataclass

from app.domain.assumptions import (
    ACCESS_WALK_MIN,
    CARPOOL_PEOPLE,
    CYCLABLE_KM,
    MODES,
    WAIT_BREATHING_L_PER_MIN,
    WAIT_EXPOSURE_RATIO,
    WAIT_MIN,
    WALKABLE_KM,
)
from app.domain.household import Commute, Mode

LITRES_PER_M3 = 1000


@dataclass(frozen=True)
class TripImpact:
    """One one-way trip.

    Attributes:
        minutes: Time on the way, including walking to and waiting for public transport.
        co2_kg: CO₂ for this traveller's share of the vehicle.
        air_m3: Polluted air breathed, in cubic metres at the outdoor level.
    """

    minutes: int
    co2_kg: float
    air_m3: float

    def inhaled_ug(self, outdoor_pm25: float) -> float:
        """PM2.5 inhaled on the trip at a given outdoor level.

        Args:
            outdoor_pm25: Outdoor PM2.5 in µg/m³.

        Returns:
            Micrograms of PM2.5, rounded to whole micrograms.
        """
        return round(self.air_m3 * outdoor_pm25)


@dataclass(frozen=True)
class Swap:
    """What changes for one commute if it is made another way.

    Attributes:
        mode: The other way of travelling.
        people_in_vehicle: People sharing the vehicle (more than one for a carpool).
        co2_saved_kg_week: CO₂ avoided per week, both directions.
        air_change_pct: Change in polluted air breathed; negative means less.
        minutes_change: Change in minutes per one-way trip; negative means faster.
    """

    mode: Mode
    people_in_vehicle: int
    co2_saved_kg_week: float
    air_change_pct: int
    minutes_change: int


def trip_impact(mode: Mode, km: float, people_in_vehicle: int = 1) -> TripImpact:
    """Work out one one-way trip.

    Args:
        mode: How the trip is made.
        km: One-way distance.
        people_in_vehicle: People sharing a car, auto or two-wheeler.

    Returns:
        Its time, CO₂ share and polluted air breathed.

    >>> trip_impact(Mode.CAR, 10).co2_kg
    1.4
    """
    facts = MODES[mode]
    minutes = km / facts.speed_kmh * 60
    air_litres = minutes * facts.exposure_ratio * facts.breathing_l_per_min
    if mode in WAIT_EXPOSURE_RATIO:
        walk = MODES[Mode.WALK]
        air_litres += ACCESS_WALK_MIN * walk.exposure_ratio * walk.breathing_l_per_min
        air_litres += WAIT_MIN * WAIT_EXPOSURE_RATIO[mode] * WAIT_BREATHING_L_PER_MIN
        minutes += ACCESS_WALK_MIN + WAIT_MIN
    sharers = people_in_vehicle if facts.co2_shared else 1
    return TripImpact(
        minutes=round(minutes),
        co2_kg=round(km * facts.co2_kg_per_km / sharers, 2),
        air_m3=round(air_litres / LITRES_PER_M3, 3),
    )


def swaps(commute: Commute) -> list[Swap]:
    """Lower-CO₂ ways to make a commute, the biggest saving first.

    Walking and cycling are offered only for short trips, the metro only where the household
    says it is an option, and a carpool for car and SUV trips with fewer than three people.

    Args:
        commute: The trip as made today.

    Returns:
        Each swap that saves CO₂, with what it changes.
    """
    now = trip_impact(commute.mode, commute.km_one_way, commute.people_in_vehicle)
    trips_per_week = 2 * commute.days_per_week
    found = []
    for mode, people in _candidates(commute):
        other = trip_impact(mode, commute.km_one_way, people)
        saved = round((now.co2_kg - other.co2_kg) * trips_per_week, 1)
        if saved <= 0:
            continue
        found.append(
            Swap(
                mode=mode,
                people_in_vehicle=people,
                co2_saved_kg_week=saved,
                air_change_pct=round((other.air_m3 / now.air_m3 - 1) * 100),
                minutes_change=other.minutes - now.minutes,
            )
        )
    return sorted(found, key=lambda swap: swap.co2_saved_kg_week, reverse=True)


def _candidates(commute: Commute) -> list[tuple[Mode, int]]:
    """The other ways this trip could reasonably be made, with people per vehicle."""
    options = [(Mode.BUS, 1)]
    if commute.km_one_way <= WALKABLE_KM:
        options.append((Mode.WALK, 1))
    if commute.km_one_way <= CYCLABLE_KM:
        options.append((Mode.CYCLE, 1))
    if commute.metro_possible:
        options.append((Mode.METRO, 1))
    if commute.mode in {Mode.CAR, Mode.SUV} and commute.people_in_vehicle < CARPOOL_PEOPLE:
        options.append((commute.mode, CARPOOL_PEOPLE))
    return [option for option in options if option[0] is not commute.mode or option[1] > 1]
