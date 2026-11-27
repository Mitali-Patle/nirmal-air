"""Reading the household form: fixed rows of people, routines and commutes, plus the home.

Empty rows are skipped. Everything else is validated by the `Household` model, and its
errors come back as short sentences naming the field, for the form to show.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import partial
from typing import Any

from pydantic import ValidationError

from app.domain.household import Condition, Household

CONDITION_FIELDS = {
    "lung": Condition.LUNG,
    "heart": Condition.HEART,
    "pregnant": Condition.PREGNANT,
}
HOME_LABEL = "Home"
# How the model's field names read in an error, matching the form's own labels.
FIELD_LABELS = {
    "member": "who",
    "minutes": "minutes",
    "hour": "time",
    "km_one_way": "km one way",
    "days_per_week": "days a week",
    "leaves_at_hour": "leaves at",
    "people_in_vehicle": "people in the car",
    "room_sqft": "main room size",
    "purifier_cadr_m3h": "air purifier CADR",
    "cooking_fuel": "cooking fuel",
}
Field = Callable[[str], str]


@dataclass(frozen=True)
class Section:
    """One repeating part of the form, such as the people or the trips.

    A row's fields are named `{prefix}{row}_{field}` ("c1_km"), and a row counts as filled when
    its `key` field is. The first `shown` rows are open; the rest sit behind "Add more…", so
    the usual household sees a short form.
    """

    name: str
    prefix: str
    key: str
    label: str
    rows: int
    shown: int
    read: Callable[[Mapping[str, str], Field], dict[str, Any]]

    def field(self, row: int, name: str) -> str:
        """The form field name for one field of one row.

        >>> COMMUTES.field(1, "km")
        'c1_km'
        """
        return f"{self.prefix}{row}_{name}"

    def filled(self, form: Mapping[str, str], row: int) -> bool:
        """Whether a row holds something (its name or "who" field is filled)."""
        return bool(form.get(self.field(row, self.key), "").strip())

    def values(self, form: Mapping[str, str]) -> list[dict[str, Any]]:
        """The filled rows, read into the shape the `Household` model takes."""
        return [
            self.read(form, partial(self.field, row))
            for row in range(self.rows)
            if self.filled(form, row)
        ]


def parse_household(form: Mapping[str, str]) -> tuple[Household | None, list[str]]:
    """Build a household from the submitted form.

    Args:
        form: Field names to submitted text.

    Returns:
        The household and no errors, or None and the problems to show.
    """
    data: dict[str, Any] = {section.name: section.values(form) for section in SECTIONS}
    data["home"] = _home(form)
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
    return {
        section.name: any(section.filled(form, row) for row in range(section.shown, section.rows))
        for section in SECTIONS
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
    for section in (ROUTINES, COMMUTES):
        for number, row in enumerate(data[section.name], start=1):
            match = people.get(_key(row["member"]))
            if match is None:
                name = row["member"].strip()
                problems.append(
                    f'{section.label} {number}: "{name}" is not one of the people above.'
                )
            else:
                row["member"] = match
    return problems


def _home(form: Mapping[str, str]) -> dict[str, Any]:
    """The home's fields; ones left empty fall back to the `Home` model's defaults."""
    given = {
        "room_sqft": form.get("home_sqft"),
        "purifier_cadr_m3h": form.get("home_cadr"),
        "cooking_fuel": form.get("home_fuel"),
    }
    return {key: value for key, value in given.items() if value} | {
        "incense_or_coils": "home_incense" in form,
        "smoking_indoors": "home_smoking" in form,
    }


def _member(form: Mapping[str, str], field: Field) -> dict[str, Any]:
    return {
        "name": form.get(field("name"), ""),
        "role": form.get(field("role"), "adult"),
        "conditions": [
            condition for name, condition in CONDITION_FIELDS.items() if field(name) in form
        ],
    }


def _routine(form: Mapping[str, str], field: Field) -> dict[str, Any]:
    return {
        "member": form.get(field("member"), ""),
        "activity": form.get(field("activity"), ""),
        "hour": form.get(field("hour"), ""),
        "minutes": form.get(field("minutes"), ""),
    }


def _commute(form: Mapping[str, str], field: Field) -> dict[str, Any]:
    return {
        "member": form.get(field("member"), ""),
        "mode": form.get(field("mode"), ""),
        "km_one_way": form.get(field("km"), ""),
        "days_per_week": form.get(field("days"), ""),
        "leaves_at_hour": form.get(field("hour"), ""),
        "people_in_vehicle": form.get(field("people")) or 1,
        "metro_possible": field("metro") in form,
    }


MEMBERS = Section("members", "m", "name", "Person", rows=8, shown=4, read=_member)
ROUTINES = Section("routines", "r", "member", "Routine", rows=6, shown=3, read=_routine)
COMMUTES = Section("commutes", "c", "member", "Trip", rows=4, shown=2, read=_commute)
SECTIONS = (MEMBERS, ROUTINES, COMMUTES)
SECTION_LABELS = {section.name: section.label for section in SECTIONS} | {"home": HOME_LABEL}


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
    field = FIELD_LABELS.get(str(location[-1]), str(location[-1]).replace("_", " "))
    if error["type"] == "string_pattern_mismatch":
        return f"{where} {field}: use letters, with one space between words."
    return f"{where} {field}: {str(error['msg']).removeprefix('Value error, ').lower()}."
