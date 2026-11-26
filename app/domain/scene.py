"""The sky drawn at the top of the Today page: sun or moon, stars, clouds and rain.

Positions are worked out here and drawn by the template in a 1200 x 120 SVG. The sun follows
its real path for the place, from sunrise on the left to sunset on the right. Clouds come
from the real cloud cover, rain from the real rain, and smog hides stars.
"""

import math
from dataclasses import dataclass
from datetime import datetime

from app.domain.sky import Phase, SunTimes

WIDTH, HEIGHT = 1200, 120
# The arc stays in the lower part of the drawing: the band crops its top on wide screens.
HORIZON_Y, ARC_HEIGHT = 112, 52
MAX_STARS = 24
MAX_HAZE = 5
# Cloud cover thresholds (percent) for one, two and three clouds on each side.
CLOUD_STEPS = (20, 50, 80)
# Fixed star positions, so the sky does not change on every page load.
STARS = tuple(
    ((index * 487 + 61) % WIDTH, 10 + (index * 37) % 70, 1.2 + (index % 3) * 0.5)
    for index in range(MAX_STARS)
)
CLOUD_SLOTS = ((90, 38, 1.0), (300, 62, 0.8), (500, 30, 0.7))


@dataclass(frozen=True)
class Body:
    """The sun or the moon, placed in the SVG."""

    kind: str
    x: int
    y: int


@dataclass(frozen=True)
class Cloud:
    """One cloud: its place, size, and the side it drifts in from."""

    x: int
    y: int
    scale: float
    side: str


@dataclass(frozen=True)
class Scene:
    """Everything the sky band draws."""

    body: Body | None
    stars: tuple[tuple[int, int, float], ...]
    clouds: tuple[Cloud, ...]
    rain: bool


def sun_position(now: datetime, sun: SunTimes) -> Body | None:
    """Where the sun is on its arc between sunrise and sunset, if it is up.

    Args:
        now: The current time at the place.
        sun: That day's sunrise and sunset.

    Returns:
        The sun, or None when it has set or not yet risen.

    >>> from app.domain.readings import IST
    >>> rise, noon, dusk = (datetime(2026, 11, 25, h, tzinfo=IST) for h in (7, 12, 17))
    >>> sun_position(noon, SunTimes(rise, dusk))
    Body(kind='sun', x=600, y=60)
    """
    if not sun.sunrise <= now < sun.sunset:
        return None
    share = (now - sun.sunrise) / (sun.sunset - sun.sunrise)
    return Body(
        "sun", round(WIDTH * share), round(HORIZON_Y - ARC_HEIGHT * math.sin(math.pi * share))
    )


def scene(
    now: datetime, sun: SunTimes, phase: Phase, haze: int, weather: tuple[int, bool] | None
) -> Scene:
    """The sky to draw right now.

    Args:
        now: The current time at the place.
        sun: That day's sunrise and sunset.
        phase: The page's phase of day (a forced light or dark theme changes it).
        haze: The haze level from the AQI band, 0 to 5.
        weather: Cloud cover in percent and whether it is raining, if known.

    Returns:
        The scene.
    """
    dark = phase in {Phase.DUSK, Phase.NIGHT}
    cover, raining = weather if weather is not None else (0, False)
    overcast = cover >= CLOUD_STEPS[-1]  # no sun or moon shows through
    body = None if overcast else _body(now, sun, dark=dark)
    visible_stars = round(MAX_STARS * (1 - haze / (MAX_HAZE + 1))) if dark else 0
    return Scene(body, STARS[:visible_stars], _clouds(cover, raining=raining), raining)


def _body(now: datetime, sun: SunTimes, *, dark: bool) -> Body:
    """The sun on its arc while it is up and the page is light, else the moon.

    A light theme chosen at night still shows the moon: a sun at 8 pm would be untrue.
    """
    moon = Body("moon", 1040, HORIZON_Y - ARC_HEIGHT)
    if dark:
        return moon
    return sun_position(now, sun) or moon


def _clouds(cover: int, *, raining: bool) -> tuple[Cloud, ...]:
    """One, two or three clouds on each side for the cloud cover; at least one when raining."""
    count = sum(cover >= step for step in CLOUD_STEPS) or (1 if raining else 0)
    return tuple(
        Cloud(x if side == "left" else WIDTH - x - 120, y, scale, side)
        for side in ("left", "right")
        for x, y, scale in CLOUD_SLOTS[:count]
    )
