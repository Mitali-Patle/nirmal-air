"""The whole session must fit in one cookie: browsers silently drop cookies over 4 KB."""

import base64
import json
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

from app.domain.household import Household
from app.domain.week import MAX_ENTRIES, DayImpact, LogEntry
from app.services.today import PlaceChoice
from app.web.session import load_household, save_household, save_log

COOKIE_LIMIT = 4096
SIGNATURE_AND_ATTRIBUTES = 160  # itsdangerous timestamp and signature, name, path, flags
NAMES = [
    "नानी माँ जी बड़ी",
    "दादाजी साहब",
    "बड़ी मौसी जी",
    "छोटी बुआ जी",
    "भैया जी बड़े",
    "दीदी रानी जी",
    "मुन्ना राजा जी",
    "गुड़िया रानी",
]
EVERY_CONDITION = ["asthma or lung condition", "heart condition", "pregnant"]


def largest_household() -> Household:
    return Household.model_validate(
        {
            "members": [
                {"name": n, "role": "senior", "conditions": EVERY_CONDITION} for n in NAMES
            ],
            "routines": [
                {"member": NAMES[i], "activity": "sport or exercise", "hour": 17, "minutes": 120}
                for i in range(6)
            ],
            "commutes": [
                {
                    "member": NAMES[i],
                    "mode": "scooter or motorbike",
                    "km_one_way": 12.5,
                    "days_per_week": 6,
                    "leaves_at_hour": 9,
                    "people_in_vehicle": 2,
                    "metro_possible": True,
                }
                for i in range(4)
            ],
            "home": {
                "room_sqft": 300,
                "purifier_cadr_m3h": 450,
                "cooking_fuel": "wood, coal or kerosene",
                "incense_or_coils": True,
                "smoking_indoors": True,
            },
        }
    )


def test_the_largest_household_and_a_full_week_fit_in_one_cookie() -> None:
    request: Any = SimpleNamespace(session={"csrf": "x" * 43, "theme": "auto"})
    place = PlaceChoice("Koramangala, Bengaluru Urban, Karnataka", 12.9352, 77.6245)
    save_household(request, place, largest_household(), "Mumbai commuter")
    today = date(2026, 11, 25)
    entries = [
        LogEntry(
            today - timedelta(days=i // (MAX_ENTRIES // 7)),
            f"indoors-{i}",
            f"{NAMES[i % 8]}'s sport or exercise moved indoors",
            DayImpact(-12345, -6789),
        )
        for i in range(MAX_ENTRIES)
    ]
    save_log(request, entries)
    cookie = base64.b64encode(json.dumps(request.session).encode())  # as Starlette writes it
    assert len(cookie) + SIGNATURE_AND_ATTRIBUTES < COOKIE_LIMIT
    assert load_household(request) == (place, largest_household())
