"""Ready-made days and households for the advice and AI tests."""

from datetime import datetime

from app.advice.bundle import build_facts
from app.advice.facts import Today
from app.advice.plan import Language, PlanContext
from app.air.cpcb import StationReading
from app.air.lookup import MeasuredAir
from app.air.stations import NearbyStation, Station
from app.domain.aqi import station_aqi
from app.domain.household import Household
from app.domain.readings import IST, Pollutant
from app.domain.timing import DayTiming, Window

NOW = datetime(2026, 11, 24, 8, 30, tzinfo=IST)
ITO = Station("ITO, Delhi - CPCB", "Delhi", "Delhi", 28.6289, 77.2412)

FAMILY = Household.model_validate(
    {
        "members": [
            {"name": "Asha", "role": "adult"},
            {"name": "Aarav", "role": "child"},
            {"name": "Dadi", "role": "senior", "conditions": ["asthma or lung condition"]},
        ],
        "commutes": [
            {
                "member": "Asha",
                "mode": "car",
                "km_one_way": 12,
                "days_per_week": 5,
                "leaves_at_hour": 9,
                "metro_possible": True,
            }
        ],
        "routines": [
            {"member": "Aarav", "activity": "outdoor play", "hour": 17, "minutes": 60},
            {"member": "Dadi", "activity": "walk", "hour": 6, "minutes": 45},
        ],
        "home": {"room_sqft": 150, "purifier_cadr_m3h": 250, "incense_or_coils": True},
    }
)


def measured(aqi: int = 326, distance_km: float = 0.4, pm25: bool = True) -> MeasuredAir:
    """Measured air whose AQI is set by PM2.5 (or by PM10 when `pm25` is False)."""
    sub_indices = {Pollutant.NO2: 40, Pollutant.CO: 60}
    sub_indices[Pollutant.PM25 if pm25 else Pollutant.PM10] = aqi
    aqi_value = station_aqi(sub_indices)
    assert aqi_value is not None
    reading = StationReading(ITO.name, NOW.replace(hour=8, minute=0), sub_indices)
    return MeasuredAir(NearbyStation(ITO, distance_km), reading, aqi_value, False)


def timing(day: int = 24) -> DayTiming:
    """Cleanest 1 pm to 4 pm, worst 7 pm to 10 pm, 2.3 times dirtier."""

    def at(hour: int) -> datetime:
        return NOW.replace(day=day, hour=hour, minute=0)

    return DayTiming(Window(at(13), at(16), 60.0), Window(at(19), at(22), 138.0), 2.3)


def today(
    air: MeasuredAir | None = None,
    household: Household = FAMILY,
    *,
    with_air: bool = True,
    with_timing: bool = True,
) -> Today:
    """A day in central Delhi."""
    if with_air and air is None:
        air = measured()
    return Today("ITO, New Delhi", NOW, air, timing() if with_timing else None, household)


def context(day: Today | None = None, language: Language = Language.ENGLISH) -> PlanContext:
    """The plan context for a day, with its facts."""
    day = day or today()
    return PlanContext(day, build_facts(day), language)
