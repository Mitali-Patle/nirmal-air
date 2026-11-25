"""The real pages in a browser: journeys, axe (WCAG 2.2 AA), phone widths, keyboard, console."""

from collections.abc import Callable
from datetime import datetime
from functools import cache
from importlib.resources import files
from typing import Any

import pytest
from playwright.sync_api import ConsoleMessage, Page, expect

from app.air.cpcb import IST
from tests.e2e.conftest import LiveApp, NewPage

pytestmark = pytest.mark.e2e

WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
MORNING = datetime(2026, 11, 23, 9, 30, tzinfo=IST)


def open_today(page: Page) -> None:
    page.goto("/")
    page.get_by_role("button", name="Delhi family").click()
    expect(page.locator("#how-slot .how")).to_be_attached(timeout=15_000)


def _start(page: Page) -> None:
    page.goto("/")


def open_form(page: Page) -> None:
    page.goto("/")
    page.get_by_text("Set up your household").click()


def _start_with_errors(page: Page) -> None:
    open_form(page)
    page.get_by_role("button", name="See today's plan").click()
    expect(page.get_by_role("alert")).to_contain_text("Choose a place from the list")


def _today_with_answer(page: Page) -> None:
    open_today(page)
    page.get_by_label("Your question").fill("Can Aarav play at 5 pm?")
    page.get_by_role("button", name="Ask", exact=True).click()
    expect(page.locator("#answer")).to_contain_text("The assistant is not available right now")


def _today_with_a_ticked_step(page: Page) -> None:
    open_today(page)
    button = page.locator("#log-swap-1")
    button.click()
    expect(page.locator("#week-status")).to_have_text("Logged: Asha went by bus.")
    expect(page.locator("#log-swap-1")).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#log-swap-1")).to_be_focused()


STATES: dict[str, Callable[[Page], None]] = {
    "start": _start,
    "start with errors": _start_with_errors,
    "today": open_today,
    "today with an answer": _today_with_answer,
    "today with a ticked step": _today_with_a_ticked_step,
}


@cache
def _axe_source() -> str:
    return (files("axe_playwright_python") / "axe.min.js").read_text(encoding="utf-8")


def axe_violations(page: Page) -> list[str]:
    """Run axe-core's WCAG 2.2 A/AA rules, with every collapsed panel opened first."""
    page.evaluate("document.querySelectorAll('details').forEach(d => { d.open = true; })")
    page.evaluate(_axe_source())
    results: dict[str, Any] = page.evaluate(
        "tags => axe.run(document, {runOnly: {type: 'tag', values: tags}})", WCAG_TAGS
    )
    return [
        f"{v['id']} ({v['impact']}): {v['help']} at {[n['target'] for n in v['nodes']][:3]}: "
        f"{v['nodes'][0]['any'][0]['message'] if v['nodes'][0]['any'] else ''}"
        for v in results["violations"]
    ]


@pytest.mark.parametrize("width", [375, 1280])
@pytest.mark.parametrize("scheme", ["light", "dark"])
@pytest.mark.parametrize("state", STATES)
def test_no_axe_violations(new_page: NewPage, state: str, scheme: str, width: int) -> None:
    page = new_page(color_scheme=scheme, viewport={"width": width, "height": 900})
    STATES[state](page)
    assert axe_violations(page) == []


def test_no_axe_violations_on_a_morning_sky(new_page: NewPage, live: LiveApp) -> None:
    live.at(MORNING)
    page = new_page(color_scheme="light")
    open_today(page)
    expect(page.locator("html")).to_have_attribute("data-phase", "morning")
    assert axe_violations(page) == []


@pytest.mark.parametrize("state", STATES)
def test_no_horizontal_scrolling_at_320px(new_page: NewPage, state: str) -> None:
    page = new_page(viewport={"width": 320, "height": 800})
    STATES[state](page)
    assert page.evaluate("document.documentElement.scrollWidth - window.innerWidth") <= 0


def test_the_plan_loads_as_signs_with_its_provenance(new_page: NewPage) -> None:
    page = new_page()
    open_today(page)
    expect(page.locator(".sign-big")).to_have_count(1)
    expect(page.get_by_text("Standard advice (not AI-generated)")).to_be_visible()
    expect(page.locator("#plan-status")).to_have_text("Today's plan is ready.")
    expect(page.get_by_text("Sample household: Delhi family")).to_be_visible()


def test_skip_link_is_first_and_moves_focus_to_main(new_page: NewPage) -> None:
    page = new_page()
    page.goto("/")
    page.keyboard.press("Tab")
    skip = page.get_by_role("link", name="Skip to content")
    expect(skip).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.locator("#main")).to_be_focused()


def test_console_is_clean_in_every_state(new_page: NewPage) -> None:
    """No script errors or CSP violations; the 422 page may log its status."""
    page = new_page()
    problems: list[str] = []

    def record(message: ConsoleMessage) -> None:
        if message.type in {"error", "warning"} and "Failed to load resource" not in message.text:
            problems.append(message.text)

    page.on("console", record)
    page.on("pageerror", lambda error: problems.append(str(error)))
    for build in STATES.values():
        build(page)
    assert problems == []


def test_use_my_location_names_the_place_found(new_page: NewPage) -> None:
    page = new_page(
        geolocation={"latitude": 28.6139, "longitude": 77.2090}, permissions=["geolocation"]
    )
    open_form(page)
    page.get_by_label("Town, city or locality").fill("Andheri")
    page.get_by_role("button", name="Use my location").click()
    expect(page.locator("#locate-status")).to_contain_text("Found: Your location, near Delhi")
    expect(page.get_by_label("Town, city or locality")).to_have_value("")
    page.get_by_label("Town, city or locality").fill("Lucknow")
    expect(page.locator("#locate-status")).to_contain_text("Using the place you type")


def test_a_refused_location_says_what_to_do(new_page: NewPage) -> None:
    page = new_page()
    open_form(page)
    page.get_by_role("button", name="Use my location").click()
    expect(page.locator("#locate-status")).to_contain_text("Location permission was not given")
    expect(page.get_by_role("button", name="Use my location")).to_be_enabled()
