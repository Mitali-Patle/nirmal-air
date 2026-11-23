import pytest
from pydantic import ValidationError

from app.domain.household import (
    Commute,
    Condition,
    Household,
    Member,
    Mode,
    Role,
    Routine,
)


def household(**values: object) -> Household:
    return Household.model_validate(
        {"members": [{"name": "Asha", "role": "adult"}, {"name": "Dadi", "role": "senior"}]}
        | values
    )


@pytest.mark.parametrize("name", ["Aarav", "Dadi Ji", "दादी", "নানী", "  Asha  "])
def test_names_in_any_indian_script_are_accepted(name: str) -> None:
    assert Member(name=name, role=Role.ADULT).name == name.strip()


@pytest.mark.parametrize(
    "name", ["", "Asha1", "Asha  Rao", "ignore previous instructions and", "<b>", "a_b"]
)
def test_names_that_are_not_plain_words_are_rejected(name: str) -> None:
    with pytest.raises(ValidationError):
        Member(name=name, role=Role.ADULT)


@pytest.mark.parametrize(
    ("role", "conditions", "sensitive"),
    [
        (Role.ADULT, frozenset(), False),
        (Role.ADULT, frozenset({Condition.LUNG}), True),
        (Role.CHILD, frozenset(), True),
        (Role.SENIOR, frozenset(), True),
    ],
)
def test_children_seniors_and_people_with_conditions_are_sensitive(
    role: Role, conditions: frozenset[Condition], sensitive: bool
) -> None:
    assert Member(name="Asha", role=role, conditions=conditions).sensitive is sensitive


def test_a_full_household_validates() -> None:
    home = household(
        commutes=[
            {
                "member": "Asha",
                "mode": "car",
                "km_one_way": 12,
                "days_per_week": 5,
                "leaves_at_hour": 9,
            }
        ],
        routines=[{"member": "Dadi", "activity": "walk", "hour": 6, "minutes": 45}],
    )
    assert home.commutes[0].mode is Mode.CAR
    assert home.routines[0] == Routine(member="Dadi", activity="walk", hour=6, minutes=45)
    assert home.home.room_sqft == 150


@pytest.mark.parametrize(
    "values",
    [
        {"members": [{"name": "Asha", "role": "adult"}, {"name": "Asha", "role": "child"}]},
        {"routines": [{"member": "Ravi", "activity": "walk", "hour": 6, "minutes": 30}]},
        {"members": []},
        {"unknown": True},
    ],
)
def test_inconsistent_households_are_rejected(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        household(**values)


def test_commute_limits() -> None:
    with pytest.raises(ValidationError):
        Commute(member="Asha", mode=Mode.CAR, km_one_way=0, days_per_week=5, leaves_at_hour=9)
