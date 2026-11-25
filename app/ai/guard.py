"""The number guard: an AI sentence may only use numbers that appear in the facts it was given.

Number words that state an amount ("twice", "half", "double") count too.

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
# Words that state an amount without digits ("twice the PM2.5") need a source too.
_NUMBER_WORDS = re.compile(r"\b(twice|thrice|double|triple|quadruple|half)\b", re.IGNORECASE)


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


def guard_problems(text: str, allowed: Iterable[str]) -> list[str]:
    """Everything in `text` that states an amount the facts do not: digits and number words.

    Args:
        text: An AI-written sentence.
        allowed: The fact texts it was given.

    Returns:
        Problems to send back to the model; empty when the sentence is clean.

    >>> guard_problems("Twice as bad after 7 pm", ["Worst time: 7 pm to 10 pm."])
    ["number words not in the facts: ['twice']"]
    """
    sources = list(allowed)
    problems = []
    numbers = unknown_numbers(text, sources)
    if numbers:
        problems.append(f"numbers not in the facts: {sorted(numbers)}")
    known_words = {word.casefold() for source in sources for word in _NUMBER_WORDS.findall(source)}
    words = {word.casefold() for word in _NUMBER_WORDS.findall(text)} - known_words
    if words:
        problems.append(f"number words not in the facts: {sorted(words)}")
    return problems
