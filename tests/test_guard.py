import pytest

from app.ai.guard import numbers_in, unknown_numbers


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
    assert unknown_numbers("Play between 1 pm and 4 pm; AQI is 326.", facts) == set()
    assert unknown_numbers("Play at 2 pm for 30 minutes.", facts) == {2.0, 30.0}
    assert unknown_numbers("Nothing to check.", []) == set()
