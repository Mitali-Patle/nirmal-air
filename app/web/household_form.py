"""Reading the household form: fixed rows of people, routines and commutes, plus the home.

Empty rows are skipped. Everything else is validated by the `Household` model, and its
errors come back as short sentences naming the field, for the form to show.
"""

from collections.abc import Callable, Mapping
from typing import Any

from pydantic import ValidationError

from app.domain.household import Condition, Household

MEMBER_ROWS = 8
ROUTINE_ROWS = 6
COMMUTE_ROWS = 4
# Rows shown open; the rest sit behind "Add more…" so the usual household sees a short form.
SHOWN_ROWS = {"members": 4, "routines": 3, "commutes": 2}
ROW_PREFIX = {"members": ("m", "name"), "routines": ("r", "member"), "commutes": ("c", "member")}
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
        "members": _rows(form, "m", "name", MEMBER_ROWS, _member),
        "routines": _rows(form, "r", "member", ROUTINE_ROWS, _routine),
        "commutes": _rows(form, "c", "member", COMMUTE_ROWS, _commute),
        "home": _home(form),
    }
    unknown = _match_names(data)
    try:
        return Household.model_validate(data), []
    except ValidationError as error:
        problems = [_message(item) for item in error.errors()]
        # Our own sentence names the person; the model's general one adds nothing.
        return None, [problem for problem in problems if "must belong" not in problem] + unknown


def hidden_rows_in_use(form: Mapping[str, str]) -> dict[str, bool]:
    """Which "Add more…" sections hold something, so the form reopens them after an error.

    Args:
        form: Field names to submitted text.

    Returns:
        For people, routines and trips: whether any row past the shown ones is filled.
    """
    totals = {"members": MEMBER_ROWS, "routines": ROUTINE_ROWS, "commutes": COMMUTE_ROWS}
    return {
        kind: any(
            _filled(form, f"{ROW_PREFIX[kind][0]}{row}_{ROW_PREFIX[kind][1]}")
            for row in range(SHOWN_ROWS[kind], totals[kind])
        )
        for kind in totals
    }


def _key(name: object) -> str:
    return " ".join(str(name).split()).casefold()


def _match_names(data: dict[str, Any]) -> list[str]:
    """Point routines and trips at the person they name, ignoring capitals and extra spaces.

    Returns:
        One sentence per name that matches nobody, such as 'Routine 2: "Ravi" is not one of
        the people above.'
    """
    people = {
        _key(member["name"]): " ".join(str(member["name"]).split()) for member in data["members"]
    }
    problems = []
    for section, label in (("routines", "Routine"), ("commutes", "Trip")):
        for number, row in enumerate(data[section], start=1):
            match = people.get(_key(row["member"]))
            if match is None:
                problems.append(
                    f'{label} {number}: "{row["member"].strip()}" is not one of the people above.'
                )
            else:
                row["member"] = match
    return problems


def _rows(
    form: Mapping[str, str],
    prefix: str,
    key: str,
    count: int,
    read: Callable[[Mapping[str, str], int], dict[str, Any]],
) -> list[dict[str, Any]]:
    """The filled rows of one section: a row counts when its name or "who" field is filled."""
    return [read(form, row) for row in range(count) if _filled(form, f"{prefix}{row}_{key}")]


def _home(form: Mapping[str, str]) -> dict[str, Any]:
    return {
        "room_sqft": form.get("home_sqft") or 150,
        "purifier_cadr_m3h": form.get("home_cadr") or 0,
        "cooking_fuel": form.get("home_fuel", "LPG"),
        "incense_or_coils": "home_incense" in form,
        "smoking_indoors": "home_smoking" in form,
    }


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
