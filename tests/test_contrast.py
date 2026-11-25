"""WCAG AA contrast for every sky phase and haze level, read from the real stylesheet."""

import re
from pathlib import Path

import pytest

TOKENS = (Path(__file__).parent.parent / "public/static/css/tokens.css").read_text()
PHASES = ("morning", "afternoon", "evening", "dusk", "night")
AA_TEXT = 4.5
COLOUR_RULE = r"--([\w-]+): (#[0-9A-Fa-f]{6})"


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def luminance(rgb: tuple[float, float, float]) -> float:
    def channel(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def mix(
    smog: tuple[int, int, int], sky: tuple[int, int, int], share: float
) -> tuple[float, float, float]:
    """CSS color-mix(in srgb, smog share, sky): a straight blend of the encoded channels."""
    r, g, b = (s * share + k * (1 - share) for s, k in zip(smog, sky, strict=True))
    return r, g, b


def phase_tokens(phase: str) -> dict[str, tuple[int, int, int]]:
    block = re.search(rf'html\[data-phase="{phase}"\] \{{(.*?)\}}', TOKENS, re.S)
    assert block is not None
    pairs = re.findall(COLOUR_RULE, block.group(1))
    return {name: hex_rgb(value) for name, value in pairs}


HAZES = [0.0] + [float(v) / 100 for v in re.findall(r'data-haze="\d"\] \{ --haze: (\d+)%', TOKENS)]
ROOT = {name: hex_rgb(value) for name, value in re.findall(COLOUR_RULE, TOKENS)}


@pytest.mark.parametrize("phase", PHASES)
@pytest.mark.parametrize("haze", HAZES)
def test_text_is_readable_on_the_sky_at_every_haze(phase: str, haze: float) -> None:
    tokens = phase_tokens(phase)
    for ground in ("sky", "bar-sky"):
        background = mix(tokens["smog"], tokens[ground], haze)
        for text in ("ink", "muted"):
            assert contrast(tokens[text], background) >= AA_TEXT, (phase, haze, ground, text)


@pytest.mark.parametrize("phase", PHASES)
def test_text_is_readable_on_panels(phase: str) -> None:
    tokens = phase_tokens(phase)
    for text in ("ink", "muted"):
        assert contrast(tokens[text], tokens["panel"]) >= AA_TEXT, (phase, text)


@pytest.mark.parametrize("board", ["sign-green", "sign-green-deep", "sign-blue", "sign-blue-deep"])
def test_sign_legends_are_readable(board: str) -> None:
    assert contrast(ROOT["sign-legend"], ROOT[board]) >= AA_TEXT


@pytest.mark.parametrize("kind", ["measured", "forecast", "estimate", "guidance", "household"])
def test_fact_chips_are_readable(kind: str) -> None:
    assert contrast(ROOT[f"kind-{kind}-fg"], ROOT[f"kind-{kind}-bg"]) >= AA_TEXT


def test_all_six_haze_levels_are_defined() -> None:
    assert len(HAZES) == 6
