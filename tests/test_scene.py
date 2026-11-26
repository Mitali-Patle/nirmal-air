from datetime import datetime

import httpx
import pytest
import respx

from app.air.errors import WeatherUnavailableError
from app.air.weather import WEATHER_URL, Weather, fetch_weather
from app.domain.readings import IST
from app.domain.scene import MAX_STARS, Body, scene, sun_position
from app.domain.sky import Phase, SunTimes

RISE = datetime(2026, 11, 25, 7, tzinfo=IST)
SET = datetime(2026, 11, 25, 17, tzinfo=IST)
SUN = SunTimes(RISE, SET)


def at(hour: int) -> datetime:
    return RISE.replace(hour=hour)


def test_the_sun_rises_left_and_sets_right_and_is_gone_at_night() -> None:
    morning, evening = sun_position(at(8), SUN), sun_position(at(16), SUN)
    assert morning is not None and evening is not None
    assert morning.x < 600 < evening.x
    assert sun_position(at(18), SUN) is None
    assert sun_position(at(6), SUN) is None


def test_night_has_a_moon_and_smog_hides_stars() -> None:
    clear = scene(at(23), SUN, Phase.NIGHT, 0, None)
    smoggy = scene(at(23), SUN, Phase.NIGHT, 5, None)
    assert clear.body == Body("moon", 1040, 34)
    assert len(clear.stars) == MAX_STARS > len(smoggy.stars) > 0
    assert scene(at(12), SUN, Phase.AFTERNOON, 0, None).stars == ()


@pytest.mark.parametrize(
    ("weather", "clouds", "rain", "body"),
    [
        (None, 0, False, True),
        ((10, False), 0, False, True),
        ((55, False), 4, False, True),
        ((95, True), 6, True, False),  # overcast: no sun
        ((5, True), 2, True, True),  # rain from a mostly clear sky still shows a cloud each side
    ],
)
def test_clouds_and_rain_follow_the_weather(
    weather: tuple[int, bool] | None, clouds: int, rain: bool, body: bool
) -> None:
    drawn = scene(at(12), SUN, Phase.AFTERNOON, 0, weather)
    assert (len(drawn.clouds), drawn.rain, drawn.body is not None) == (clouds, rain, body)
    assert {cloud.side for cloud in drawn.clouds} <= {"left", "right"}


def test_a_light_theme_before_sunrise_still_shows_a_sun() -> None:
    drawn = scene(at(5), SUN, Phase.MORNING, 0, None)
    assert drawn.body == Body("sun", 1040, 40)


@respx.mock
async def test_weather_is_fetched_and_failures_raise(client: httpx.AsyncClient) -> None:
    route = respx.get(WEATHER_URL).respond(
        json={"current": {"cloud_cover": 82.6, "precipitation": 0}}
    )
    assert await fetch_weather(client, 28.6, 77.2) == Weather(83, raining=False)
    assert route.calls.last.request.url.params["current"] == "cloud_cover,precipitation"
    respx.get(WEATHER_URL).respond(200, json={"current": {}})
    with pytest.raises(WeatherUnavailableError):
        await fetch_weather(client, 28.6, 77.2)
