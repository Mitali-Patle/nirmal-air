"""Reading the household form: fixed rows of people, routines and commutes, plus the home.

Empty rows are skipped. Everything else is validated by the `Household` model, and its
errors come back as short sentences naming the field, each linked to the form field it is
about, for the form to show.
"""

from collections.abc import Callable, Mapping, Sequence
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
# The form field (row suffix, or the home's own field) that each model field is typed into.
FORM_FIELDS = {
    "name": "name",
    "role": "role",
    "member": "member",
    "activity": "activity",
    "hour": "hour",
    "minutes": "minutes",
    "mode": "mode",
    "km_one_way": "km",
    "days_per_week": "days",
    "leaves_at_hour": "hour",
    "people_in_vehicle": "people",
}
HOME_FIELDS = {
    "room_sqft": "home_sqft",
    "purifier_cadr_m3h": "home_cadr",
    "cooking_fuel": "home_fuel",
}
Field = Callable[[str], str]
# For each section, the form rows that were filled in, in order.
FilledRows = Mapping[str, list[int]]


@dataclass(frozen=True)
class FormError:
    """One problem to show, and the id of the form field it is about (None for the whole form)."""

    message: str
    field: str | None = None


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

    def filled_rows(self, form: Mapping[str, str]) -> list[int]:
        """The rows that hold something, in form order."""
        return [row for row in range(self.rows) if self.filled(form, row)]

    def values(self, form: Mapping[str, str], rows: Sequence[int]) -> list[dict[str, Any]]:
        """The given rows, read into the shape the `Household` model takes."""
        return [self.read(form, partial(self.field, row)) for row in rows]


def parse_household(form: Mapping[str, str]) -> tuple[Household | None, list[FormError]]:
    """Build a household from the submitted form.

    Args:
        form: Field names to submitted text.

    Returns:
        The household and no errors, or None and the problems to show.
    """
    rows = {section.name: section.filled_rows(form) for section in SECTIONS}
    data: dict[str, Any] = {
        section.name: section.values(form, rows[section.name]) for section in SECTIONS
    }
    data["home"] = _home(form)
    unknown = _match_names(data, rows) + _unnamed_trips(form)
    try:
        household = Household.model_validate(data)
    except ValidationError as error:
        problems = [_message(item, rows) for item in error.errors()]
        # Our own sentence names the person; the model's general one adds nothing.
        kept = [problem for problem in problems if "must belong" not in problem.message]
        return None, kept + unknown
    return (None, unknown) if unknown else (household, [])


def described_by(errors: Sequence[FormError]) -> dict[str, str]:
    """For each field with a problem, the ids of the messages about it, such as "error-2".

    The summary numbers its messages `error-1`, `error-2`…; a field points at its own with
    `aria-describedby`, so a screen reader reads the problem with the field.

    >>> described_by([FormError("Pick a place", "place_query"), FormError("Odd")])
    {'place_query': 'error-1'}
    """
    ids: dict[str, list[str]] = {}
    for number, error in enumerate(errors, start=1):
        if error.field:
            ids.setdefault(error.field, []).append(f"error-{number}")
    return {field: " ".join(found) for field, found in ids.items()}


def _unnamed_trips(form: Mapping[str, str]) -> list[FormError]:
    """A trip with its distance filled but nobody named would otherwise vanish silently."""
    return [
        FormError(
            f"{COMMUTES.label} {row + 1}: who makes this trip?", COMMUTES.field(row, "member")
        )
        for row in range(COMMUTES.rows)
        if not COMMUTES.filled(form, row) and form.get(COMMUTES.field(row, "km"), "").strip()
    ]


def form_from_household(household: Household) -> dict[str, str]:
    """The form's fields for a saved household, so it can be edited instead of retyped.

    The saved place is kept by the server (`place_keep`), not written into the form.

    Args:
        household: The saved household.

    Returns:
        Field names to values, as the form would send them.
    """
    form = {"place_keep": "1"}
    for row, member in enumerate(household.members):
        form |= {MEMBERS.field(row, "name"): member.name, MEMBERS.field(row, "role"): member.role}
        form |= {
            MEMBERS.field(row, name): "on"
            for name, condition in CONDITION_FIELDS.items()
            if condition in member.conditions
        }
    for row, routine in enumerate(household.routines):
        form |= {
            ROUTINES.field(row, "member"): routine.member,
            ROUTINES.field(row, "activity"): routine.activity,
            ROUTINES.field(row, "hour"): str(routine.hour),
            ROUTINES.field(row, "minutes"): str(routine.minutes),
        }
    for row, trip in enumerate(household.commutes):
        form |= {
            COMMUTES.field(row, "member"): trip.member,
            COMMUTES.field(row, "mode"): trip.mode,
            COMMUTES.field(row, "km"): f"{trip.km_one_way:g}",
            COMMUTES.field(row, "days"): str(trip.days_per_week),
            COMMUTES.field(row, "hour"): str(trip.leaves_at_hour),
            COMMUTES.field(row, "people"): str(trip.people_in_vehicle),
        }
        if trip.metro_possible:
            form[COMMUTES.field(row, "metro")] = "on"
    home = household.home
    form |= {
        "home_sqft": str(home.room_sqft),
        "home_cadr": str(home.purifier_cadr_m3h),
        "home_fuel": home.cooking_fuel,
    }
    form |= {"home_incense": "on"} if home.incense_or_coils else {}
    form |= {"home_smoking": "on"} if home.smoking_indoors else {}
    return form


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


def _match_names(data: dict[str, Any], rows: FilledRows) -> list[FormError]:
    """Point routines and trips at the person they name, ignoring capitals and extra spaces.

    Returns:
        One problem per name that matches nobody, such as 'Routine 2: "Ravi" is not one of
        the people above.', linked to that row's "Who" field.
    """
    people = {
        _key(member["name"]): " ".join(str(member["name"]).split()) for member in data["members"]
    }
    problems = []
    for section in (ROUTINES, COMMUTES):
        for values, row in zip(data[section.name], rows[section.name], strict=True):
            match = people.get(_key(values["member"]))
            if match is None:
                name = values["member"].strip()
                problems.append(
                    FormError(
                        f'{section.label} {row + 1}: "{name}" is not one of the people above.',
                        section.field(row, "member"),
                    )
                )
            else:
                values["member"] = match
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
SECTIONS_BY_NAME = {section.name: section for section in SECTIONS}
SECTION_LABELS = {section.name: section.label for section in SECTIONS} | {"home": HOME_LABEL}


def _message(error: Mapping[str, Any], rows: FilledRows) -> FormError:
    """A short sentence for one validation error, such as "Person 2 name: letters only"."""
    location = [part for part in error["loc"] if part not in {"__root__"}]
    if location == ["members"]:
        return FormError("Add at least one person, with a name.", MEMBERS.field(0, "name"))
    if not location:
        return FormError(str(error["msg"]).removeprefix("Value error, "))
    row = _form_row(location, rows)
    section = SECTION_LABELS.get(str(location[0]), str(location[0]))
    where = section if row is None else f"{section} {row + 1}"
    field = FIELD_LABELS.get(str(location[-1]), str(location[-1]).replace("_", " "))
    if error["type"] == "string_pattern_mismatch":
        text = f"{where} {field}: use letters, with one space between words."
    else:
        text = f"{where} {field}: {str(error['msg']).removeprefix('Value error, ').lower()}."
    return FormError(text, _field_id(location, row))


def _form_row(location: Sequence[Any], rows: FilledRows) -> int | None:
    """The form row an error is in: the model counts filled rows only, the form counts all."""
    if len(location) <= 1 or not isinstance(location[1], int):
        return None
    return rows[str(location[0])][location[1]]


def _field_id(location: Sequence[Any], row: int | None) -> str | None:
    """The id of the form field an error is about, when there is one to point at.

    >>> _field_id(["commutes", 1, "km_one_way"], 2), _field_id(["home", "room_sqft"], None)
    ('c2_km', 'home_sqft')
    >>> _field_id(["members", 0, "conditions", 0], 0) is None
    True
    """
    name = str(location[-1])
    section = SECTIONS_BY_NAME.get(str(location[0]))
    if section is None:
        return HOME_FIELDS.get(name)
    if row is None or name not in FORM_FIELDS:
        return None
    return section.field(row, FORM_FIELDS[name])
