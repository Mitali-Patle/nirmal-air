import pytest

from app.ai.guard import FactGuard, numbers_in


@pytest.mark.parametrize(
    ("text", "numbers"),
    [
        ("AQI 326 at 8 am", {326.0, 8.0}),
        ("PM2.5, PM10, NO2, CO2 and an N95 mask", set()),
        ("1,200 m and 1,20,000 people", {1200.0, 120000.0}),
        ("about 6.9 cigarettes.", {6.9}),
        ("AQI ३२६", {326.0}),
        ("CO₂ in µg/m³", set()),
    ],
)
def test_numbers_are_found_and_pollutant_names_ignored(text: str, numbers: set[float]) -> None:
    assert numbers_in(text) == numbers


def test_numbers_must_come_from_the_facts() -> None:
    facts = ["Cleanest time: 1 pm to 4 pm today.", "AQI 326 (Very Poor)."]
    guard = FactGuard(facts)
    assert guard.problems("Play between 1 pm and 4 pm; AQI is 326.") == []
    assert guard.problems("Play at 2 pm for 30 minutes.") == [
        "numbers not in the facts: [2.0, 30.0]"
    ]
    assert FactGuard([]).problems("Nothing to check.") == []


def test_number_words_need_a_source_too() -> None:
    facts = ["Worst time: 7 pm to 10 pm, with about 2.3 times the PM2.5 of the cleanest time."]
    guard = FactGuard(facts)
    assert guard.problems("Air is twice as bad at 7 pm.") == [
        "number words not in the facts: ['twice']"
    ]
    assert guard.problems("Half the purifier time at 9 pm.") == [
        "numbers not in the facts: [9.0]",
        "number words not in the facts: ['half']",
    ]
    assert FactGuard([*facts, "Double the cost."]).problems("Double-check windows at 7 pm.") == []
