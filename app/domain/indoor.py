"""Indoor PM2.5 estimated from outdoor PM2.5, and what shutting windows or a purifier changes.

Uses the steady-state mass balance in `app.domain.assumptions`. Indoor sources (cooking,
incense, smoking) are left out, so real rooms with those sources are worse than estimated.
"""

from dataclasses import dataclass

from app.domain.assumptions import (
    AIR_CHANGES_WINDOWS_OPEN,
    AIR_CHANGES_WINDOWS_SHUT,
    CEILING_HEIGHT_M,
    CIGARETTE_PM25_DAY,
    DEPOSITION_PER_HOUR,
    PENETRATION_WINDOWS_OPEN,
    PENETRATION_WINDOWS_SHUT,
    SQ_M_PER_SQ_FT,
)
from app.domain.household import Home


@dataclass(frozen=True)
class IndoorEstimate:
    """Estimated PM2.5 in the main room, in µg/m³.

    Attributes:
        windows_open: With windows open.
        windows_shut: With windows and doors shut.
        with_purifier: Windows shut and the purifier running, or None without a purifier.
        purifier_air_changes: Times per hour the purifier cleans the room's air, if any.
    """

    windows_open: int
    windows_shut: int
    with_purifier: int | None
    purifier_air_changes: float | None


def room_volume_m3(room_sqft: int) -> float:
    """Volume of a room from its floor area, with a ten-foot ceiling.

    Args:
        room_sqft: Floor area in square feet.

    Returns:
        Volume in cubic metres.

    >>> round(room_volume_m3(150), 1)
    41.8
    """
    return room_sqft * SQ_M_PER_SQ_FT * CEILING_HEIGHT_M


def indoor_pm25(
    outdoor: float, penetration: float, air_changes: float, cleaning_per_hour: float = 0.0
) -> float:
    """Steady-state indoor PM2.5 from outdoor air alone.

    Args:
        outdoor: Outdoor PM2.5 in µg/m³.
        penetration: Share of particles that get in with the air (0 to 1).
        air_changes: Outdoor air exchanges per hour.
        cleaning_per_hour: Purifier clean-air delivery rate divided by room volume.

    Returns:
        Indoor PM2.5 in µg/m³.

    >>> round(indoor_pm25(100, 0.8, 1.0), 1)
    66.7
    """
    removal = air_changes + DEPOSITION_PER_HOUR + cleaning_per_hour
    return penetration * air_changes * outdoor / removal


def indoor_estimates(outdoor_pm25: float, home: Home) -> IndoorEstimate:
    """Estimate the main room's PM2.5 with windows open, shut, and with the purifier on.

    Args:
        outdoor_pm25: Outdoor PM2.5 in µg/m³.
        home: The household's room size and purifier.

    Returns:
        The three estimates, rounded to whole µg/m³.
    """
    shut = indoor_pm25(outdoor_pm25, PENETRATION_WINDOWS_SHUT, AIR_CHANGES_WINDOWS_SHUT)
    opened = indoor_pm25(outdoor_pm25, PENETRATION_WINDOWS_OPEN, AIR_CHANGES_WINDOWS_OPEN)
    if not home.purifier_cadr_m3h:
        return IndoorEstimate(round(opened), round(shut), None, None)
    cleaning = home.purifier_cadr_m3h / room_volume_m3(home.room_sqft)
    purified = indoor_pm25(
        outdoor_pm25, PENETRATION_WINDOWS_SHUT, AIR_CHANGES_WINDOWS_SHUT, cleaning
    )
    return IndoorEstimate(round(opened), round(shut), round(purified), round(cleaning, 1))


def cigarettes(pm25: float, hours: float = 24) -> float:
    """Cigarettes that do about the same harm as breathing this air for this long.

    Args:
        pm25: PM2.5 in µg/m³.
        hours: Hours spent breathing it.

    Returns:
        Cigarettes, to one decimal place.

    >>> cigarettes(151)
    6.9
    """
    return round(pm25 * hours / 24 / CIGARETTE_PM25_DAY, 1)
