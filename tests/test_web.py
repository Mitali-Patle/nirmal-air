import json
import re
from collections.abc import Iterator
from datetime import datetime
from typing import Any

import httpx2
import pytest
import respx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.ai.chain import AIChain
from app.ai.providers import LLMRequest
from app.air.cpcb import CPCB_URL, IST
from app.air.forecast import FORECAST_URL
from app.air.places import GEOCODING_URL
from app.config import Settings
from app.main import create_app
from tests.conftest import load_fixture

EVENING = datetime(2026, 11, 23, 18, 30, tzinfo=IST)  # one hour after the recorded reading


class Replies:
    """A model that returns canned JSON, one reply per call."""

    name = "fake:model"

    def __init__(self, *replies: dict[str, Any]) -> None:
        self.replies = [json.dumps(reply) for reply in replies]

    async def generate(self, request: LLMRequest) -> str:
        return self.replies.pop(0)


def make_client(*providers: Any) -> TestClient:
    settings = Settings(_env_file=None, app_env="test", data_gov_api_key=SecretStr("key"))
    app = create_app(settings)
    app.state.clock = lambda: EVENING
    app.state.ai = AIChain(list(providers))
    return TestClient(app)


def token(client: TestClient, path: str = "/") -> str:
    match = re.search(r'name="csrf" value="([^"]+)"', client.get(path).text)
    assert match is not None
    return match.group(1)


def load_sample(client: TestClient, sample: str = "delhi-family") -> httpx2.Response:
    return client.post(
        "/sample", data={"csrf": token(client), "sample": sample}, follow_redirects=False
    )


@pytest.fixture
def live() -> Iterator[respx.MockRouter]:
    with respx.mock(assert_all_called=False) as router:
        router.get(CPCB_URL).respond(json=load_fixture("cpcb_talkatora.json"))
        router.get(FORECAST_URL).respond(json=load_fixture("forecast_delhi.json"))
        router.get(GEOCODING_URL).respond(json=load_fixture("places_andheri.json"))
        yield router


def test_the_start_page_offers_samples_and_a_form() -> None:
    page = make_client().get("/").text
    assert page.count('name="sample"') == 3
    assert "Bengaluru cyclist" in page
    assert 'name="place_query"' in page
    assert "Continue to today" not in page


def test_posts_without_the_csrf_token_are_refused() -> None:
    client = make_client()
    assert client.post("/sample", data={"sample": "delhi-family"}).status_code == 403
    assert (
        client.post("/sample", data={"sample": "delhi-family", "csrf": "wrong"}).status_code == 403
    )


def test_a_sample_loads_and_unknown_samples_are_404() -> None:
    client = make_client()
    response = load_sample(client)
    assert (response.status_code, response.headers["location"]) == (303, "/today")
    assert "Continue to today in ITO, New Delhi" in client.get("/").text
    assert load_sample(client, "nope").status_code == 404


def test_today_needs_a_household_first() -> None:
    client = make_client()
    assert client.get("/today", follow_redirects=False).headers["location"] == "/"
    assert client.get("/today/plan").status_code == 204


def test_today_shows_the_measured_air_its_source_and_the_estimates(live: respx.MockRouter) -> None:
    client = make_client()
    load_sample(client)
    page = client.get("/today").text
    assert "AQI 324" in page and "Very Poor" in page
    assert "Measured 5 pm at" in page and "CPCB via data.gov.in" in page
    assert 'data-phase="dusk"' in page and 'data-haze="4"' in page
    assert page.count('class="hr ') == 24
    assert '<i class="key key-clean" aria-hidden="true"></i>Cleanest ' in page
    assert " the cleanest</li>" in page
    assert "With windows shut, the main room" in page
    assert "If Asha went by bus instead" in page
    assert 'hx-get="/today/plan?lang=en"' in page
    assert "Sample household: Delhi family" in page
    assert live.calls.last.request.headers["user-agent"] == "NirmalAir/0.1"


def test_without_a_station_or_forecast_the_page_says_so() -> None:
    client = make_client()
    load_sample(client)
    with respx.mock:
        respx.get(CPCB_URL).respond(json={"records": []})
        respx.get(FORECAST_URL).respond(503)
        page = client.get("/today").text
    assert "No CPCB station near ITO, New Delhi has reported" in page
    assert "The forecast is not available right now" in page
    assert 'data-haze="0"' in page


def test_the_plan_falls_back_to_labelled_standard_advice(live: respx.MockRouter) -> None:
    client = make_client()
    load_sample(client)
    fragment = client.get("/today/plan").text
    assert "Standard advice (not AI-generated)" in fragment
    assert "Keep today&#39;s walk indoors." in fragment
    assert "How this was generated" in fragment
    assert 'hx-swap-oob="true"' in fragment


def test_an_ai_plan_is_drawn_as_signs_with_its_provenance(live: respx.MockRouter) -> None:
    plan = {
        "items": [
            {
                "slot": "evening",
                "member": "Aarav",
                "action": "Play indoors.",
                "why": "Very Poor air.",
                "fact_ids": ["routine_1"],
            },
            {
                "slot": "morning",
                "member": "Dadi",
                "action": "Walk indoors.",
                "why": "Asthma.",
                "fact_ids": ["routine_2"],
            },
            {
                "slot": "morning",
                "member": "Asha",
                "action": "Try the bus.",
                "why": "Less CO₂.",
                "fact_ids": ["swap_1_1"],
            },
            {
                "slot": "evening",
                "member": "Everyone",
                "action": "Keep windows shut.",
                "why": "The worst time.",
                "fact_ids": ["windows"],
            },
        ],
    }
    client = make_client(Replies(plan))
    load_sample(client)
    fragment = client.get("/today/plan?lang=hi").text
    assert "Standard advice" not in fragment
    assert fragment.index("Play indoors.") < fragment.index("Earlier today (2)")
    assert "sign-big" in fragment and "fake:model" in fragment and "plan-v4" in fragment
    assert "Hindi (Devanagari script)" not in fragment  # the payload is not echoed raw


def test_ask_answers_from_the_facts_and_checks_the_token(live: respx.MockRouter) -> None:
    answer = {"kind": "answer", "text": "Not today: the air is Very Poor.", "fact_ids": ["air_now"]}
    client = make_client(Replies(answer))
    load_sample(client)
    csrf = token(client, "/today")
    assert client.post("/ask", data={"question": "Can Aarav play?"}).status_code == 403
    fragment = client.post(
        "/ask", data={"question": "Can Aarav play?"}, headers={"X-CSRF-Token": csrf}
    ).text
    assert "Not today: the air is Very Poor." in fragment and "Can Aarav play?" in fragment
    assert client.post("/ask", data={"question": "x", "csrf": csrf}).status_code == 422


def test_ask_without_a_household_is_empty() -> None:
    client = make_client()
    assert (
        client.post("/ask", data={"question": "Hello there", "csrf": token(client)}).status_code
        == 204
    )


def test_the_ask_fallback_repeats_the_measured_air(live: respx.MockRouter) -> None:
    client = make_client()
    load_sample(client)
    fragment = client.post("/ask", data={"question": "Can Aarav play?", "csrf": token(client)}).text
    assert "The assistant is not available right now. AQI 324" in fragment


def test_place_suggestions(live: respx.MockRouter) -> None:
    client = make_client()
    assert client.get("/places?q=a").text.strip() == ""
    assert 'name="place_index" value="0" checked' in client.get("/places?q=Andheri").text
    live.get(GEOCODING_URL).respond(json={"results": []})
    assert "No place in India matches" in client.get("/places?q=Zzz").text
    live.get(GEOCODING_URL).respond(500)
    assert "Place search is not answering" in client.get("/places?q=Powai").text
    assert 'value="0" checked' in client.get("/places?q=Andheri").text  # cached earlier


def household_form(csrf: str, **extra: str) -> dict[str, str]:
    return {
        "csrf": csrf,
        "m0_name": "Meera",
        "m0_role": "senior",
        "m0_lung": "on",
        "r0_member": "Meera",
        "r0_activity": "walk",
        "r0_hour": "6",
        "r0_minutes": "30",
        "home_sqft": "120",
        "home_fuel": "LPG",
        **extra,
    }


def test_a_household_form_saves_with_a_searched_place(live: respx.MockRouter) -> None:
    client = make_client()
    form = household_form(token(client), place_query="Andheri", place_index="1")
    response = client.post("/household", data=form, follow_redirects=False)
    assert response.status_code == 303
    assert "Continue to today in Andheri" in client.get("/").text
    assert "Sample household" not in client.get("/today").text


def test_a_household_form_saves_with_the_browsers_location() -> None:
    client = make_client()
    form = household_form(token(client), geo_lat="28.61", geo_lon="77.21")
    assert client.post("/household", data=form, follow_redirects=False).status_code == 303
    assert "Your location, near Delhi" in client.get("/").text


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ({"geo_lat": "51.5", "geo_lon": "-0.1"}, "Choose a place from the list"),
        ({"geo_lat": "north", "geo_lon": "77"}, "Choose a place from the list"),
        ({}, "Choose a place from the list"),
        ({"place_query": "Andheri", "place_index": "9"}, "Choose a place from the list"),
        (
            {"geo_lat": "28.6", "geo_lon": "77.2", "m0_name": "M3era"},
            "Person 1 name: use letters only",
        ),
    ],
)
def test_household_form_problems_are_shown(
    live: respx.MockRouter, extra: dict[str, str], message: str
) -> None:
    client = make_client()
    response = client.post("/household", data=household_form(token(client), **extra))
    assert response.status_code == 422
    assert message in response.text
    assert 'role="alert"' in response.text


def test_place_search_failure_on_save_asks_for_a_place(live: respx.MockRouter) -> None:
    live.get(GEOCODING_URL).respond(500)
    client = make_client()
    form = household_form(token(client), place_query="Andheri")
    assert client.post("/household", data=form).status_code == 422


def test_the_theme_choice_is_remembered(live: respx.MockRouter) -> None:
    client = make_client()
    load_sample(client)
    client.post("/theme", data={"csrf": token(client), "theme": "light"})
    page = client.get("/today").text
    assert 'data-theme="light"' in page and 'data-phase="morning"' in page
    client.post("/theme", data={"csrf": token(client), "theme": "dark"})
    assert 'data-phase="night"' in client.get("/today").text


def test_ticking_a_step_updates_this_week(live: respx.MockRouter) -> None:
    client = make_client()
    load_sample(client)
    page = client.get("/today").text
    assert "This week" in page and 'name="step" value="swap-1"' in page
    csrf = token(client, "/today")
    fragment = client.post("/log", data={"csrf": csrf, "step": "swap-1"}).text
    assert 'aria-pressed="true"' in fragment
    assert "Logged: Asha went by bus." in fragment
    assert "3 kg</span> CO₂ avoided" in fragment
    client.post("/log", data={"csrf": csrf, "step": "swap-1"})
    assert "1 step logged in the last 7 days" in client.get("/today").text


def test_logging_needs_a_real_step_a_token_and_a_household(live: respx.MockRouter) -> None:
    client = make_client()
    assert client.post("/log", data={"csrf": token(client), "step": "swap-1"}).status_code == 204
    load_sample(client)
    csrf = token(client, "/today")
    assert client.post("/log", data={"step": "swap-1"}).status_code == 403
    assert client.post("/log", data={"csrf": csrf, "step": "fly-1"}).status_code == 404


def test_a_new_household_starts_a_new_week(live: respx.MockRouter) -> None:
    client = make_client()
    load_sample(client)
    client.post("/log", data={"csrf": token(client, "/today"), "step": "swap-1"})
    load_sample(client, "mumbai-commuter")
    assert "0 steps logged" in client.get("/today").text


def test_the_browsers_location_is_named_with_its_station() -> None:
    client = make_client()
    found = client.get("/near?lat=28.6139&lon=77.2090").text
    assert found.startswith("Found: Your location, near Delhi. Nearest CPCB station:")
    assert "outside India" in client.get("/near?lat=51.5&lon=-0.12").text
    assert "outside India" in client.get("/near").text


JOINT_FAMILY = {
    **{
        f"m{row}_name": name
        for row, name in enumerate(
            ["Dada", "Dadi", "Ravi", "Meena", "Kabir", "Ishita", "Anya", "Chachi"]
        )
    },
    "m0_role": "senior",
    "m0_heart": "on",
    "m1_role": "senior",
    "m1_lung": "on",
    "m4_role": "child",
    "m5_role": "child",
    "m6_role": "child",
    "m7_pregnant": "on",
    **{
        f"r{row}_member": name
        for row, name in enumerate(["dada", " DADI ", "kabir", "Ishita", "Anya", "Ravi"])
    },
    **{f"r{row}_activity": "walk" for row in range(6)},
    **{f"r{row}_hour": "7" for row in range(6)},
    **{f"r{row}_minutes": "30" for row in range(6)},
    **{f"c{row}_member": name for row, name in enumerate(["ravi", "Meena", "Chachi", "Ravi"])},
    **{f"c{row}_mode": "car" for row in range(4)},
    **{f"c{row}_km": "8" for row in range(4)},
    **{f"c{row}_days": "5" for row in range(4)},
    **{f"c{row}_hour": "9" for row in range(4)},
    "home_sqft": "300",
    "home_fuel": "LPG",
    "place_query": "Andheri",
}


def test_an_eight_person_joint_family_with_loose_name_typing_is_saved(
    live: respx.MockRouter,
) -> None:
    client = make_client()
    response = client.post(
        "/household", data={"csrf": token(client), **JOINT_FAMILY}, follow_redirects=False
    )
    assert response.status_code == 303
    page = client.get("/today").text
    assert page.count("I did this") >= 4  # trips and routines moved indoors
    fragment = client.get("/today/plan").text
    assert "Standard advice" in fragment
    assert fragment.count('class="sign ') <= 12


def test_names_that_match_nobody_are_named_and_extra_rows_reopen() -> None:
    client = make_client()
    form = {**JOINT_FAMILY, "r5_member": "Ravindra", "geo_lat": "28.6", "geo_lon": "77.2"}
    response = client.post("/household", data={"csrf": token(client), **form})
    assert response.status_code == 422
    assert "Routine 6: &#34;Ravindra&#34; is not one of the people above." in response.text
    assert response.text.count('class="more-rows" open') == 3


def test_a_household_of_just_people_works(live: respx.MockRouter) -> None:
    client = make_client()
    form = {"csrf": token(client), "m0_name": "Asha", "geo_lat": "28.6", "geo_lon": "77.2"}
    assert client.post("/household", data=form, follow_redirects=False).status_code == 303
    page = client.get("/today").text
    assert "Getting around" not in page
    assert "Nothing to tick today" in page
    assert "Standard advice" in client.get("/today/plan").text


def test_errors_are_readable_pages_and_htmx_fragments() -> None:
    client = make_client()
    missing = client.get("/nowhere")
    assert (
        missing.status_code == 404 and "Page not found" in missing.text and "<html" in missing.text
    )
    invalid = client.get("/today?lang=xx")
    assert invalid.status_code == 422 and "Some of that could not be read" in invalid.text
    expired = client.post(
        "/sample", data={"sample": "delhi-family"}, headers={"HX-Request": "true"}
    )
    assert expired.status_code == 403 and expired.text.startswith(
        '<p class="note" role="alert">The form expired'
    )
