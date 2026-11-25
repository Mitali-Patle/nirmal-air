"""Sample households for evaluators and first-time visitors: one tap loads a whole family.

Each sample shows a different side of the app: a sensitive family in Delhi, a cyclist in
Bengaluru, and a car commuter with a heart condition in Mumbai who could take the metro.
"""

from dataclasses import dataclass
from types import MappingProxyType

from app.domain.household import Household
from app.services.today import PlaceChoice


@dataclass(frozen=True)
class Sample:
    """A ready-made household and where it lives."""

    title: str
    summary: str
    place: PlaceChoice
    household: Household


SAMPLES = MappingProxyType(
    {
        "delhi-family": Sample(
            "Delhi family",
            "A 6-year-old who plays outside, a grandmother with asthma, a car commute.",
            PlaceChoice("ITO, New Delhi", 28.6289, 77.2412),
            Household.model_validate(
                {
                    "members": [
                        {"name": "Asha", "role": "adult"},
                        {"name": "Aarav", "role": "child"},
                        {
                            "name": "Dadi",
                            "role": "senior",
                            "conditions": ["asthma or lung condition"],
                        },
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
            ),
        ),
        "bengaluru-cyclist": Sample(
            "Bengaluru cyclist",
            "One adult who cycles 6 km to work and runs in the morning.",
            PlaceChoice("Koramangala, Bengaluru", 12.9352, 77.6245),
            Household.model_validate(
                {
                    "members": [{"name": "Ravi", "role": "adult"}],
                    "commutes": [
                        {
                            "member": "Ravi",
                            "mode": "cycle",
                            "km_one_way": 6,
                            "days_per_week": 5,
                            "leaves_at_hour": 8,
                        }
                    ],
                    "routines": [
                        {
                            "member": "Ravi",
                            "activity": "sport or exercise",
                            "hour": 7,
                            "minutes": 40,
                        }
                    ],
                    "home": {"room_sqft": 120},
                }
            ),
        ),
        "mumbai-commuter": Sample(
            "Mumbai commuter",
            "A father with a heart condition who drives 14 km, and a daughter's school run.",
            PlaceChoice("Andheri East, Mumbai", 19.1136, 72.8697),
            Household.model_validate(
                {
                    "members": [
                        {"name": "Imran", "role": "adult", "conditions": ["heart condition"]},
                        {"name": "Zoya", "role": "child"},
                    ],
                    "commutes": [
                        {
                            "member": "Imran",
                            "mode": "car",
                            "km_one_way": 14,
                            "days_per_week": 6,
                            "leaves_at_hour": 8,
                            "metro_possible": True,
                        }
                    ],
                    "routines": [
                        {"member": "Zoya", "activity": "school run", "hour": 7, "minutes": 30}
                    ],
                    "home": {"room_sqft": 200, "cooking_fuel": "piped gas"},
                }
            ),
        ),
    }
)
