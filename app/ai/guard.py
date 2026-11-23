"""The number guard: an AI sentence may only use numbers that appear in the facts it was given.

Names that contain digits, such as PM2.5, PM10, CO₂ or N95, are not numbers and are ignored.
Digits in any script count, so Hindi answers written with Devanagari digits are checked too.

The guard proves a number came from the facts, not that it is used for the right thing: "2 pm"
passes if any fact contains a 2. Citing fact ids and showing those facts beside each item is
what lets a reader check the meaning.
"""

import re
from collections.abc import Iterable

# A word that starts with letters and ends in digits: PM2.5, PM10, NO2, N95, FFP2.
_NAMED = re.compile(r"\b[^\W\d_]+\d+(?:\.\d+)?\b")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def numbers_in(text: str) -> set[float]:
    """Every number written in a piece of text.

    Args:
        text: Any text.

    Returns:
        The numbers, with thousands separators removed.

    >>> sorted(numbers_in("PM2.5 is 151 µg/m³, 1,200 m away, about 6.9 cigarettes"))
    [6.9, 151.0, 1200.0]
    """
    plain = _NAMED.sub(" ", text)
    found = set()
    for match in _NUMBER.findall(plain):
        digits = match.replace(",", "")
        found.add(float(digits.rstrip(".")))
    return found


def unknown_numbers(text: str, allowed: Iterable[str]) -> set[float]:
    """Numbers in `text` that appear in none of the allowed texts.

    Args:
        text: An AI-written sentence.
        allowed: The fact texts it was given.

    Returns:
        The numbers that have no source; empty when the sentence is clean.

    >>> unknown_numbers("Walk after 1 pm; the air is 3 times cleaner", ["Cleanest: 1 pm to 4 pm"])
    {3.0}
    """
    known = set().union(*(numbers_in(item) for item in allowed))
    return numbers_in(text) - known
