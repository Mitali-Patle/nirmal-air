"""Reading the household form: fixed rows of people, routines and commutes, plus the home.

Empty rows are skipped. Everything else is validated by the `Household` model, and its
errors come back as short sentences naming the field, for the form to show.
"""

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from app.domain.household import Condition, Household

MEMBER_ROWS = 4
ROUTINE_ROWS = 3
COMMUTE_ROWS = 2
CONDITION_FIELDS = {
    "lung": Condition.LUNG,
    "heart": Condition.HEART,
    "pregnant": Condition.PREGNANT,
}
SECTION_LABELS = {"members": "Person", "routines": "Routine", "commutes": "Commute", "home": "Home"}


def parse_household(form: Mapping[str, str]) -> tuple[Household | None, list[str]]:
    """Build a household from the submitted form.

    Args:
        form: Field names to submitted text.

    Returns:
        The household and no errors, or None and the problems to show.
    """
    data: dict[str, Any] = {
        "members": [
            _member(form, row) for row in range(MEMBER_ROWS) if _filled(form, f"m{row}_name")
        ],
        "routines": [
            _routine(form, row) for row in range(ROUTINE_ROWS) if _filled(form, f"r{row}_member")
        ],
        "commutes": [
            _commute(form, row) for row in range(COMMUTE_ROWS) if _filled(form, f"c{row}_member")
        ],
        "home": {
            "room_sqft": form.get("home_sqft") or 150,
            "purifier_cadr_m3h": form.get("home_cadr") or 0,
            "cooking_fuel": form.get("home_fuel", "LPG"),
            "incense_or_coils": "home_incense" in form,
            "smoking_indoors": "home_smoking" in form,
        },
    }
    try:
        return Household.model_validate(data), []
    except ValidationError as error:
        return None, [_message(item) for item in error.errors()]


def _filled(form: Mapping[str, str], key: str) -> bool:
    return bool(form.get(key, "").strip())


def _member(form: Mapping[str, str], row: int) -> dict[str, Any]:
    return {
        "name": form.get(f"m{row}_name", ""),
        "role": form.get(f"m{row}_role", "adult"),
        "conditions": [
            condition for field, condition in CONDITION_FIELDS.items() if f"m{row}_{field}" in form
        ],
    }


def _routine(form: Mapping[str, str], row: int) -> dict[str, Any]:
    return {
        "member": form.get(f"r{row}_member", ""),
        "activity": form.get(f"r{row}_activity", ""),
        "hour": form.get(f"r{row}_hour", ""),
        "minutes": form.get(f"r{row}_minutes", ""),
    }


def _commute(form: Mapping[str, str], row: int) -> dict[str, Any]:
    return {
        "member": form.get(f"c{row}_member", ""),
        "mode": form.get(f"c{row}_mode", ""),
        "km_one_way": form.get(f"c{row}_km", ""),
        "days_per_week": form.get(f"c{row}_days", ""),
        "leaves_at_hour": form.get(f"c{row}_hour", ""),
        "people_in_vehicle": form.get(f"c{row}_people") or 1,
        "metro_possible": f"c{row}_metro" in form,
    }


def _message(error: Mapping[str, Any]) -> str:
    """A short sentence for one validation error, such as "Person 2 name: letters only"."""
    location = [part for part in error["loc"] if part not in {"__root__"}]
    if location == ["members"]:
        return "Add at least one person, with a name."
    if not location:
        return str(error["msg"]).removeprefix("Value error, ")
    section = SECTION_LABELS.get(str(location[0]), str(location[0]))
    where = (
        f"{section} {int(location[1]) + 1}"
        if len(location) > 1 and isinstance(location[1], int)
        else section
    )
    field = str(location[-1]).replace("_", " ")
    if error["type"] == "string_pattern_mismatch":
        return f"{where} {field}: use letters only, one space between words."
    return f"{where} {field}: {str(error['msg']).removeprefix('Value error, ').lower()}."
