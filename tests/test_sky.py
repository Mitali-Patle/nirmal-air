from datetime import datetime

import pytest

from app.domain.aqi import Category
from app.domain.readings import IST
from app.domain.sky import Phase, haze_level, phase_at, sun_times

DELHI = (28.61, 77.21)


@pytest.mark.parametrize(
    ("place", "when", "expected"),
    [
        ((28.61, 77.21), (6, 21), "05:23 19:21"),  # Delhi, longest day
        ((13.08, 80.27), (11, 25), "06:12 17:39"),  # Chennai
        ((22.57, 88.36), (11, 25), "05:55 16:51"),  # Kolkata sets an hour before Mumbai
        ((19.08, 72.88), (11, 25), "06:51 17:59"),  # Mumbai
    ],
)
def test_sun_times_across_india(
    place: tuple[float, float], when: tuple[int, int], expected: str
) -> None:
    times = sun_times(*place, datetime(2026, *when, 12, tzinfo=IST))
    assert f"{times.sunrise:%H:%M} {times.sunset:%H:%M}" == expected


@pytest.mark.parametrize(
    ("hour", "minute", "phase"),
    [
        (5, 30, Phase.NIGHT),
        (7, 0, Phase.MORNING),
        (11, 0, Phase.AFTERNOON),
        (15, 30, Phase.EVENING),
        (17, 30, Phase.DUSK),
        (21, 0, Phase.NIGHT),
    ],
)
def test_phases_follow_the_sun(hour: int, minute: int, phase: Phase) -> None:
    now = datetime(2026, 11, 25, hour, minute, tzinfo=IST)
    assert phase_at(now, sun_times(*DELHI, now)) is phase


def test_haze_follows_the_measured_band_and_stays_clear_without_data() -> None:
    assert [haze_level(category) for category in Category] == [0, 1, 2, 3, 4, 5]
    assert haze_level(None) == 0
