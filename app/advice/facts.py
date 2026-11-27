"""Facts: short sentences written by code, each with an id the AI cites and a kind.

The number guard only accepts numbers that appear in facts, so the AI can explain the
numbers but never invent one.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.air.lookup import MeasuredAir
from app.domain.aqi import PM25_BREAKPOINTS, pm25_from_sub_index
from app.domain.household import Household
from app.domain.readings import IST, Pollutant
from app.domain.timing import DayTiming

NOON = 12
# A station further than this may not reflect the air where the household is.
FAR_STATION_KM = 25
# Typographic marks for figures: an en dash for ranges, a true minus for reductions.
EN_DASH = "\u2013"
MINUS = "\u2212"
TIMES = "\u00d7"


class Kind(StrEnum):
    """Where a fact comes from, shown next to it on screen."""

    MEASURED = "measured"
    GUIDANCE = "CPCB guidance"
    FORECAST = "forecast"
    ESTIMATE = "estimate"
    HOUSEHOLD = "your household"

    @property
    def label(self) -> str:
        """The kind as a tag on screen, capitalised.

        >>> Kind.HOUSEHOLD.label
        'Your household'
        """
        return self.value[0].upper() + self.value[1:]


class FactId(StrEnum):
    """Ids of the facts a day has at most once; the helpers below name the numbered ones."""

    AIR_NOW = "air_now"
    HEALTH = "health"
    FAR_STATION = "far_station"
    PM25 = "pm25"
    CIGARETTES = "cigarettes"
    WINDOWS = "windows"
    CLEANEST = "cleanest"
    WORST = "worst"
    HOME = "home"
    INDOOR_OPEN = "indoor_open"
    INDOOR_SHUT = "indoor_shut"
    INDOOR_PURIFIER = "indoor_purifier"
    INDOOR_PURIFIER_IF = "indoor_purifier_if"
    PLANTS = "plants"


MEMBER_PREFIX = "member_"
ROUTINE_PREFIX = "routine_"
COMMUTE_PREFIX = "commute_"
SWAP_PREFIX = "swap_"
INDOOR_PREFIX = "indoor_"
# Facts about the home rather than about people, which the page draws as blue signs.
HOME_FACT_IDS = frozenset(
    {
        FactId.WINDOWS,
        FactId.HOME,
        FactId.INDOOR_OPEN,
        FactId.INDOOR_SHUT,
        FactId.INDOOR_PURIFIER,
        FactId.INDOOR_PURIFIER_IF,
        FactId.PLANTS,
    }
)


def member_id(index: int) -> str:
    """The id of a household member's fact (`index` counts from 1)."""
    return f"{MEMBER_PREFIX}{index}"


def routine_id(index: int) -> str:
    """The id of a routine's fact (`index` counts from 1)."""
    return f"{ROUTINE_PREFIX}{index}"


def commute_id(index: int) -> str:
    """The id of a commute's fact (`index` counts from 1)."""
    return f"{COMMUTE_PREFIX}{index}"


def swap_id(commute: int, rank: int) -> str:
    """The id of a commute's swap; rank 1 is the swap code chose to offer.

    >>> swap_id(2, 1)
    'swap_2_1'
    """
    return f"{SWAP_PREFIX}{commute}_{rank}"


@dataclass(frozen=True)
class Fact:
    """One sentence of fact with an id the AI can cite.

    `figure` is the fact's key number in a few characters ("6 am", "103 µg/m³"), shown on the
    right edge of a plan sign the way a road sign shows a distance. `label` names the fact in a
    few words ("Windows shut") for one-line rows, with the full sentence one tap away.
    """

    id: str
    kind: Kind
    text: str
    figure: str | None = None
    label: str | None = None


@dataclass(frozen=True)
class Today:
    """Everything known for one household on one day."""

    place: str
    now: datetime
    air: MeasuredAir | None
    timing: DayTiming | None
    household: Household

    @property
    def outdoor_pm25(self) -> float | None:
        """Outdoor PM2.5 in µg/m³ from the station's PM2.5 sub-index, if it reports one."""
        if self.air is None or Pollutant.PM25 not in self.air.reading.sub_indices:
            return None
        return pm25_from_sub_index(self.air.reading.sub_indices[Pollutant.PM25])

    @property
    def approx(self) -> str:
        """How to qualify PM2.5 figures: "at least" above CPCB's scale, else "about".

        CPCB's PM2.5 scale ends at sub-index 400 (250 µg/m³), so beyond it every figure built
        on PM2.5 is a lower bound.
        """
        sub_index = self.air.reading.sub_indices.get(Pollutant.PM25, 0) if self.air else 0
        return "at least" if sub_index > PM25_BREAKPOINTS[-1][0] else "about"


def clock(moment: datetime | int) -> str:
    """A time of day as people say it.

    Args:
        moment: A time, or an hour from 0 to 23.

    Returns:
        For example "6 am", "12 pm" or "9 pm".

    >>> clock(0), clock(12), clock(21)
    ('12 am', '12 pm', '9 pm')
    """
    hour = moment if isinstance(moment, int) else moment.astimezone(IST).hour
    suffix = "am" if hour < NOON else "pm"
    return f"{(hour % NOON) or NOON} {suffix}"


def stamp(moment: datetime) -> str:
    """When a reading was measured: the date, the time and the time zone.

    Args:
        moment: The measurement time.

    Returns:
        For example "27 Nov, 8 pm IST".

    >>> stamp(datetime(2026, 11, 27, 20, tzinfo=IST))
    '27 Nov, 8 pm IST'
    """
    local = moment.astimezone(IST)
    return f"{local.day} {local:%b}, {clock(local)} IST"


def clock_span(start: datetime, end: datetime) -> str:
    """A short time range, sharing am or pm when both ends do.

    >>> from app.domain.readings import IST
    >>> one, four = (datetime(2026, 11, 25, hour, tzinfo=IST) for hour in (13, 16))
    >>> clock_span(one, four) == f"1{EN_DASH}4 pm"
    True
    >>> clock_span(one.replace(hour=11), four) == f"11 am{EN_DASH}4 pm"
    True
    """
    first, last = clock(start), clock(end)
    if first[-2:] == last[-2:]:
        return f"{first[:-3]}{EN_DASH}{last}"
    return f"{first}{EN_DASH}{last}"


def distance_label(km: float) -> str:
    """A station distance as people say it.

    >>> distance_label(0.4), distance_label(12.34)
    ('under 1 km', '12.3 km')
    """
    return "under 1 km" if km < 1 else f"{number(round(km, 1))} km"


def number(value: float) -> str:
    """A number without a trailing ".0".

    >>> number(12.0), number(1.68)
    ('12', '1.68')
    """
    return f"{value:g}"
