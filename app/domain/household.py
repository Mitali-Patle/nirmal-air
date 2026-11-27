"""The household profile: who lives here, how they travel, what they do outdoors, the home.

Every field is a choice from a fixed list or a bounded number, except member names, which are
up to 20 letters and spaces. That keeps the profile small enough for a cookie and leaves
little room in what reaches the AI; the prompts still treat names as data, never as
instructions, and the number guard checks every figure the AI writes.
"""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# Letters in any script, plus the vowel signs of Indian scripts (U+0900 to U+0DFF); a hyphen
# or apostrophe may join letters and a word may end in a full stop; single spaces between
# words: "Aarav", "Dadi Ji", "नानी माँ", "Mary-Jane", "O'Brien", "Dr. Rao".
_LETTERS = r"(?:[^\W\d_]|[\u0900-\u0DFF])+"
_WORD = rf"{_LETTERS}(?:[-'\u2019]{_LETTERS})*\.?"
Name = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=20, pattern=rf"^{_WORD}( {_WORD})*$"
    ),
]


MAX_MEMBERS = 8
MAX_COMMUTES = 4
MAX_ROUTINES = 6


class Role(StrEnum):
    """Age group, which changes how sensitive someone is to polluted air."""

    ADULT = "adult"
    CHILD = "child"
    SENIOR = "senior"


class Condition(StrEnum):
    """Conditions CPCB's health statements single out."""

    LUNG = "asthma or lung condition"
    HEART = "heart condition"
    PREGNANT = "pregnant"


class Mode(StrEnum):
    """Ways to make a trip."""

    WALK = "walk"
    CYCLE = "cycle"
    TWO_WHEELER = "scooter or motorbike"
    AUTO = "auto-rickshaw"
    BUS = "bus"
    METRO = "metro"
    CAR = "car"
    SUV = "SUV"


class Activity(StrEnum):
    """Regular outdoor routines."""

    WALK = "walk"
    PLAY = "outdoor play"
    SPORT = "sport or exercise"
    SCHOOL_RUN = "school run"
    ERRANDS = "market and errands"


class CookingFuel(StrEnum):
    """Main cooking fuel at home."""

    LPG = "LPG"
    PIPED_GAS = "piped gas"
    ELECTRIC = "electric"
    SOLID = "wood, coal or kerosene"


class _Strict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Member(_Strict):
    """One person in the household."""

    name: Name
    role: Role
    conditions: frozenset[Condition] = frozenset()

    @property
    def sensitive(self) -> bool:
        """Whether CPCB's advice for sensitive groups applies to this person."""
        return self.role is not Role.ADULT or bool(self.conditions)


class Commute(_Strict):
    """A regular trip one member makes."""

    member: Name
    mode: Mode
    km_one_way: float = Field(ge=0.5, le=60)
    days_per_week: int = Field(ge=1, le=7)
    leaves_at_hour: int = Field(ge=0, le=23)
    people_in_vehicle: int = Field(default=1, ge=1, le=4)
    metro_possible: bool = False


class Routine(_Strict):
    """A regular outdoor activity."""

    member: Name
    activity: Activity
    hour: int = Field(ge=0, le=23)
    minutes: int = Field(ge=10, le=180)


class Home(_Strict):
    """The main living room and what happens in it."""

    room_sqft: int = Field(default=150, ge=50, le=1000)
    purifier_cadr_m3h: int = Field(default=0, ge=0, le=1500)
    cooking_fuel: CookingFuel = CookingFuel.LPG
    incense_or_coils: bool = False
    smoking_indoors: bool = False


class Household(_Strict):
    """Everything the app knows about one household."""

    members: tuple[Member, ...] = Field(min_length=1, max_length=MAX_MEMBERS)
    commutes: tuple[Commute, ...] = Field(default=(), max_length=MAX_COMMUTES)
    routines: tuple[Routine, ...] = Field(default=(), max_length=MAX_ROUTINES)
    home: Home = Home()

    @property
    def sensitive_names(self) -> frozenset[str]:
        """Names of the members CPCB's advice for sensitive groups applies to."""
        return frozenset(member.name for member in self.members if member.sensitive)

    @model_validator(mode="after")
    def _names_refer_to_members(self) -> Self:
        names = [member.name for member in self.members]
        # "Asha" and "asha" are the same person to a reader, so they are not allowed together.
        if len({name.casefold() for name in names}) != len(names):
            raise ValueError("Each member needs a different name")
        used = {trip.member for trip in self.commutes} | {item.member for item in self.routines}
        if not used <= set(names):
            raise ValueError("Commutes and routines must belong to a household member")
        return self
