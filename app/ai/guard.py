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
# Words that state an amount without digits ("twice the PM2.5", "ten minutes", "दस मिनट")
# need a source too. "one" and Hindi "दो" are left out: they are also everyday words ("one
# window", "रहने दो") and would turn ordinary sentences away.
# Word edges are written out because Devanagari vowel signs are not "word" characters to \b.
_EDGE = r"[\w\u0900-\u097F]"
_ENGLISH_AMOUNTS = (
    "twice|thrice|double|triple|quadruple|half|dozen|hundred|thousand"
    "|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
    "|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety"
)
_HINDI_AMOUNTS = (
    "दोगुना|दोगुनी|दोगुने|दुगना|दुगनी|दुगुना|तिगुना|तिगुनी|आधा|आधी|आधे"
    "|तीन|चार|पाँच|पांच|छह|छः|सात|आठ|नौ|दस|बीस|तीस|चालीस|पचास|सौ|हज़ार|हजार"
)
_NUMBER_WORDS = re.compile(
    rf"(?<!{_EDGE})({_ENGLISH_AMOUNTS}|{_HINDI_AMOUNTS})(?!{_EDGE})", re.IGNORECASE
)


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


class FactGuard:
    """The amounts a set of facts allows, worked out once and used to check many sentences."""

    def __init__(self, allowed: Iterable[str]) -> None:
        sources = list(allowed)
        self._numbers = set().union(*(numbers_in(source) for source in sources))
        self._words = {
            word.casefold() for source in sources for word in _NUMBER_WORDS.findall(source)
        }

    def problems(self, text: str) -> list[str]:
        """Everything in `text` that states an amount the facts do not: digits and number words.

        Args:
            text: An AI-written sentence.

        Returns:
            Problems to send back to the model; empty when the sentence is clean.

        >>> FactGuard(["Worst time: 7 pm to 10 pm."]).problems("दोगुना खराब, 7 pm के बाद")
        ["number words not in the facts: ['दोगुना']"]
        """
        problems = []
        numbers = numbers_in(text) - self._numbers
        if numbers:
            problems.append(f"numbers not in the facts: {sorted(numbers)}")
        words = {word.casefold() for word in _NUMBER_WORDS.findall(text)} - self._words
        if words:
            problems.append(f"number words not in the facts: {sorted(words)}")
        return problems
