import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.aqi import Category, category_for, pm25_from_sub_index, station_aqi
from app.domain.readings import Pollutant


@pytest.mark.parametrize(
    ("aqi", "label"),
    [
        (0, "Good"),
        (50, "Good"),
        (51, "Satisfactory"),
        (100, "Satisfactory"),
        (101, "Moderate"),
        (200, "Moderate"),
        (201, "Poor"),
        (300, "Poor"),
        (301, "Very Poor"),
        (400, "Very Poor"),
        (401, "Severe"),
        (500, "Severe"),
    ],
)
def test_band_edges_follow_cpcb(aqi: int, label: str) -> None:
    assert category_for(aqi).label == label


def test_station_aqi_is_the_highest_sub_index() -> None:
    result = station_aqi({Pollutant.PM25: 324, Pollutant.PM10: 226, Pollutant.NO2: 21})
    assert result is not None
    assert (result.value, result.dominant, result.category) == (
        324,
        Pollutant.PM25,
        Category.VERY_POOR,
    )


@pytest.mark.parametrize(
    "sub_indices",
    [
        {Pollutant.OZONE: 56, Pollutant.CO: 24, Pollutant.NO2: 30},  # no particles
        {Pollutant.PM25: 120, Pollutant.CO: 24},  # fewer than three pollutants
    ],
)
def test_station_aqi_needs_three_pollutants_including_particles(
    sub_indices: dict[Pollutant, int],
) -> None:
    assert station_aqi(sub_indices) is None


@pytest.mark.parametrize(
    ("sub_index", "pm25"),
    [(0, 0.0), (50, 30.0), (100, 60.0), (150, 75.0), (300, 120.0), (400, 250.0), (480, 250.0)],
)
def test_pm25_reverses_the_breakpoints(sub_index: int, pm25: float) -> None:
    assert pm25_from_sub_index(sub_index) == pm25


@given(st.integers(min_value=0, max_value=499))
def test_pm25_never_falls_as_the_index_rises(sub_index: int) -> None:
    assert pm25_from_sub_index(sub_index) <= pm25_from_sub_index(sub_index + 1)
