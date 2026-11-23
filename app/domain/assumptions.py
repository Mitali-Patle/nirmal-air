"""Every constant behind the app's estimates, with where it comes from.

`docs/ASSUMPTIONS.md` lists the same values for readers. These are typical published values,
not measurements of any one home or trip, so every result built on them is shown as an
estimate.
"""

from dataclasses import dataclass
from types import MappingProxyType

from app.domain.household import Mode

# Berkeley Earth, "Air Pollution and Cigarette Equivalence" (Muller and Muller, 2015):
# breathing 22 µg/m³ of PM2.5 for 24 hours does about as much harm as smoking one cigarette.
CIGARETTE_PM25_DAY = 22.0

# Indoor air from outdoor air, steady-state mass balance (the model reviewed by Chen and Zhao,
# Atmospheric Environment 45, 2011): indoor = P · a · outdoor / (a + k + CADR / V).
# The values are assumptions taken from the middle of published ranges.
PENETRATION_WINDOWS_SHUT = 0.8  # P: share of fine particles that get through cracks.
PENETRATION_WINDOWS_OPEN = 1.0  # An open window filters nothing.
DEPOSITION_PER_HOUR = 0.2  # k: particles settling onto indoor surfaces.
AIR_CHANGES_WINDOWS_SHUT = 1.0  # a: a typical, not airtight, Indian home with windows shut.
AIR_CHANGES_WINDOWS_OPEN = 5.0  # a: windows open on one side of the room.
CEILING_HEIGHT_M = 3.0  # Ten feet, common in Indian homes.
SQ_M_PER_SQ_FT = 0.092903


@dataclass(frozen=True)
class ModeFacts:
    """What one way of travelling means for time, the air you breathe and CO₂.

    Attributes:
        speed_kmh: Average speed in city traffic.
        exposure_ratio: PM2.5 met on the way, as a multiple of the outdoor level.
        breathing_l_per_min: Air breathed per minute while travelling this way.
        co2_kg_per_km: Tailpipe or power-station CO₂ per kilometre.
        co2_shared: Whether the CO₂ is per vehicle, so it is split between the people in it.
    """

    speed_kmh: float
    exposure_ratio: float
    breathing_l_per_min: float
    co2_kg_per_km: float
    co2_shared: bool


# Speed, exposure ratio and breathing rate: Goel et al., "On-road PM2.5 pollution exposure in
# multiple transport microenvironments in Delhi", Atmospheric Environment 123 (2015), the
# abstract and Table 3 (cars with AC on recirculation, open-windowed buses).
# CO₂: India GHG Program, "India Specific Road Transport Emission Factors" (2015), values with
# the uplift for real-world driving: scooter under 110 cc, CNG auto, petrol hatchback under
# 1400 cc, diesel SUV under 2500 cc, intracity bus per passenger-km.
# Metro CO₂: Goel and Tiwari, "Case Study of Metro Rails in Indian Cities", UNEP DTU (2014):
# 61 g per passenger-km for the Delhi Metro, from its electricity use.
MODES = MappingProxyType(
    {
        Mode.WALK: ModeFacts(4, 1.4, 15, 0.0, co2_shared=False),
        Mode.CYCLE: ModeFacts(17, 1.1, 35, 0.0, co2_shared=False),
        Mode.TWO_WHEELER: ModeFacts(24, 1.3, 10, 0.0368, co2_shared=True),
        Mode.AUTO: ModeFacts(22, 1.3, 10, 0.10768, co2_shared=True),
        Mode.BUS: ModeFacts(14, 1.2, 10, 0.015161, co2_shared=False),
        Mode.METRO: ModeFacts(32, 0.8, 10, 0.061, co2_shared=False),
        Mode.CAR: ModeFacts(20, 0.5, 10, 0.140, co2_shared=True),
        Mode.SUV: ModeFacts(20, 0.5, 10, 0.210, co2_shared=True),
    }
)

# Public transport also means walking to the stop and waiting there (Goel et al. 2015
# assumed ten minutes of walking and five of waiting; a bus stop measured 1.2 times the
# outdoor level, an underground metro station 1.3 times).
ACCESS_WALK_MIN = 10
WAIT_MIN = 5
WAIT_EXPOSURE_RATIO = MappingProxyType({Mode.BUS: 1.2, Mode.METRO: 1.3})
WAIT_BREATHING_L_PER_MIN = 10

# Walking and cycling are only offered as swaps for trips up to these distances.
WALKABLE_KM = 2.0
CYCLABLE_KM = 8.0
CARPOOL_PEOPLE = 3
