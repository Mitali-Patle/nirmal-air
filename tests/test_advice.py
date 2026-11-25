import pytest

from app.advice.ask import (
    Answer,
    AnswerKind,
    AskContext,
    ask_payload,
    check_answer,
    standard_answer,
)
from app.advice.bundle import build_facts
from app.advice.facts import Kind, Today
from app.advice.plan import Language, Plan, PlanItem, Slot, check_plan, plan_payload
from app.advice.standard import standard_plan
from app.ai.guard import unknown_numbers
from app.ai.task import OutputRejectedError
from app.domain.guidance import Decision, routine_decision
from app.domain.household import Activity, Household
from tests.builders import FAMILY, context, measured, timing, today


def facts_of(day: Today | None = None) -> dict[str, str]:
    return {fact.id: fact.text for fact in build_facts(day or today())}


def item(member: str, why: str, fact_ids: list[str], slot: Slot = Slot.MORNING) -> PlanItem:
    return PlanItem(slot=slot, member=member, action="Do this today.", why=why, fact_ids=fact_ids)


def good_plan() -> Plan:
    return Plan(
        headline="Very Poor air (AQI 326): keep windows shut.",
        items=[
            item("Dadi", "Her walk moves indoors.", ["routine_2"]),
            item(
                "Aarav", "Play indoors; 7 pm to 10 pm is 2.3 times worse.", ["routine_1", "worst"]
            ),
            item("Asha", "The bus saves 15 kg CO₂ a week.", ["swap_1_1"]),
            item("Everyone", "Shut windows keep the room near 103 µg/m³.", ["indoor_shut"]),
        ],
    )


def test_facts_carry_the_measured_air_and_every_estimate() -> None:
    facts = facts_of()
    assert facts["air_now"].startswith("AQI 326 (Very Poor) at ITO, Delhi - CPCB, under 1 km away")
    assert "about 154 µg/m³" in facts["pm25"]
    assert "2.6 times India's daily limit" in facts["pm25"]
    assert "about 7 cigarettes" in facts["cigarettes"]
    assert facts["cleanest"] == "Cleanest time: 1 pm to 4 pm today."
    assert "move it indoors today" in facts["routine_2"]
    assert "15 kg less CO₂ a week; 393% more polluted air" in facts["swap_1_1"]
    assert "no change in travel time" in facts["swap_1_2"]
    assert "about 17 µg/m³" in facts["indoor_purifier"]
    assert len(facts) == len(build_facts(today()))  # ids are unique


def test_each_fact_says_where_it_comes_from() -> None:
    kinds = {fact.id: fact.kind for fact in build_facts(today())}
    assert kinds["air_now"] is Kind.MEASURED
    assert kinds["cleanest"] is Kind.FORECAST
    assert kinds["indoor_shut"] is Kind.ESTIMATE
    assert kinds["member_1"] is Kind.HOUSEHOLD


def test_beyond_cpcbs_scale_figures_are_lower_bounds() -> None:
    facts = facts_of(today(measured(450, distance_km=40)))
    assert "at least 250 µg/m³" in facts["pm25"]
    assert "at least 11.4 cigarettes" in facts["cigarettes"]
    assert "at least" in facts["indoor_shut"]
    assert "far_station" in facts


def test_without_pm25_or_a_station_the_estimates_are_left_out() -> None:
    no_pm25 = facts_of(today(measured(250, pm25=False)))
    assert "pm25" not in no_pm25 and "indoor_shut" not in no_pm25
    assert "breathed in" not in no_pm25["commute_1"]
    no_air = facts_of(today(with_air=False))
    assert no_air["air_now"].startswith("No CPCB station near ITO, New Delhi")


def test_forecast_windows_for_tomorrow_say_so() -> None:
    day = today()
    late = type(day)(day.place, day.now, day.air, timing(day=25), day.household)
    assert facts_of(late)["cleanest"] == "Cleanest time: 1 pm to 4 pm tomorrow."


def test_the_payload_lists_members_and_facts_and_the_language() -> None:
    payload = plan_payload(context(language=Language.HINDI))
    assert payload["members"] == ["Asha", "Aarav", "Dadi"]
    assert payload["language"] == "Hindi (Devanagari script)"
    assert payload["now"] == "Tuesday 24 November, 8 am"
    assert payload["facts"][0]["id"] == "air_now"


def test_a_plan_that_follows_the_rules_passes() -> None:
    assert check_plan(good_plan(), context()) == good_plan()


def test_items_with_invented_numbers_or_people_are_dropped() -> None:
    plan = good_plan()
    extra = [
        item("Everyone", "Air the room at 11 am for 20 minutes.", ["cleanest"]),
        item("Ravi", "A stranger.", ["air_now"]),
        item("Asha", "Cites nothing real.", ["made_up"]),
    ]
    checked = check_plan(plan.model_copy(update={"items": plan.items + extra}), context())
    assert checked.items == plan.items


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"headline": "AQI 999 today"}, "headline: numbers not in the facts: [999.0]"),
        ({"items": good_plan().items[1:]}, "no item for Dadi"),
    ],
)
def test_bad_headlines_and_missing_members_are_sent_back(
    change: dict[str, object], problem: str
) -> None:
    with pytest.raises(OutputRejectedError) as caught:
        check_plan(good_plan().model_copy(update=change), context())
    assert problem in caught.value.problems


def test_too_few_items_are_sent_back() -> None:
    alone = Household.model_validate({"members": [{"name": "Asha", "role": "adult"}]})
    plan = Plan(headline="Fine.", items=[item("Asha", "Fine.", ["air_now"])])
    with pytest.raises(OutputRejectedError, match="only 1 items"):
        check_plan(plan, context(today(household=alone)))


@pytest.mark.parametrize(
    ("aqi", "activity", "sensitive", "forecast", "decision"),
    [
        (326, Activity.WALK, True, True, Decision.INDOORS),
        (250, Activity.WALK, False, True, Decision.CLEANEST_TIME),
        (350, Activity.SCHOOL_RUN, False, True, Decision.SHORT_WITH_MASK),
        (150, Activity.ERRANDS, True, True, Decision.AS_USUAL),
        (80, Activity.PLAY, True, True, Decision.AS_USUAL),
        (None, Activity.PLAY, True, True, Decision.CLEANEST_TIME),
        (None, Activity.PLAY, True, False, Decision.SHORTER),
    ],
)
def test_routine_rules_follow_cpcb_bands(
    aqi: int | None, activity: Activity, sensitive: bool, forecast: bool, decision: Decision
) -> None:
    assert routine_decision(aqi, activity, sensitive=sensitive, has_forecast=forecast) is decision


def test_standard_advice_on_very_poor_air() -> None:
    plan = standard_plan(context())
    actions = {(entry.member, entry.action) for entry in plan.items}
    assert ("Dadi", "Keep today's walk indoors.") in actions
    assert ("Everyone", "Run the purifier in the main room with doors shut.") in actions
    assert ("Dadi", "Keep usual medicines handy; see a doctor if breathing gets worse.") in actions
    assert plan.headline.startswith("Very Poor air today")
    assert check_plan(plan, context()) == plan  # it would pass the AI's own checks


def test_standard_advice_on_clean_air() -> None:
    plan = standard_plan(context(today(measured(80))))
    actions = [entry.action for entry in plan.items]
    assert actions[0] == "Open the windows to air the house."
    assert "Run the purifier in the main room with doors shut." not in actions
    assert plan.headline == "Satisfactory air today: normal routines are fine."


@pytest.mark.parametrize(
    ("aqi", "headline"),
    [
        (150, "Moderate air today: keep windows shut at the worst times"),
        (None, "Unknown air today: no recent measurement nearby, so use the cleanest time"),
    ],
)
def test_standard_headlines(aqi: int | None, headline: str) -> None:
    day = today(measured(aqi)) if aqi else today(with_air=False)
    assert standard_plan(context(day)).headline.startswith(headline)


def test_standard_advice_without_any_data() -> None:
    plan = standard_plan(context(today(with_air=False, with_timing=False)))
    assert plan.items[0].action == "Keep windows mostly shut until a nearby reading is available."
    assert "Keep today's walk short." in [entry.action for entry in plan.items]


def test_standard_advice_covers_smoke_at_home_and_zero_emission_commutes() -> None:
    data = FAMILY.model_dump(mode="json")
    data["home"] |= {
        "smoking_indoors": True,
        "cooking_fuel": "wood, coal or kerosene",
        "incense_or_coils": False,
    }
    data["commutes"][0] |= {"mode": "cycle", "km_one_way": 5}
    household = Household.model_validate(data)
    facts = facts_of(today(household=household))
    assert "someone smokes indoors" in facts["home"]
    actions = [entry.action for entry in standard_plan(context(today(household=household))).items]
    assert "Keep smoking out of the house." in actions
    assert any(action.startswith("Cook with a window") for action in actions)
    assert "Try the lower-CO₂ way for this trip." not in actions
    assert not any("incense" in action for action in actions)


def test_standard_reasons_never_invent_numbers() -> None:
    facts = facts_of()
    for entry in standard_plan(context()).items:
        assert unknown_numbers(entry.why, facts.values()) == set()


def test_answers_are_checked_like_plans() -> None:
    ask = AskContext("Can Aarav play at 5 pm?", context())
    good = Answer(kind=AnswerKind.ANSWER, text="Not today: AQI 326.", fact_ids=["air_now"])
    assert check_answer(good, ask) == good
    assert ask_payload(ask)["question"] == "Can Aarav play at 5 pm?"
    off_topic = Answer(kind=AnswerKind.OFF_TOPIC, text="I can only help with air quality.")
    assert check_answer(off_topic, ask) == off_topic


@pytest.mark.parametrize(
    ("answer", "problem"),
    [
        (Answer(kind=AnswerKind.ANSWER, text="Yes, AQI is 50.", fact_ids=["air_now"]), "[50.0]"),
        (Answer(kind=AnswerKind.ANSWER, text="Yes.", fact_ids=["nope"]), "unknown fact ids"),
        (Answer(kind=AnswerKind.ANSWER, text="Yes."), "at least one fact id"),
    ],
)
def test_bad_answers_are_sent_back(answer: Answer, problem: str) -> None:
    with pytest.raises(OutputRejectedError, match=problem.replace("[", r"\[").replace("]", r"\]")):
        check_answer(answer, AskContext("Can Aarav play?", context()))


def test_the_standard_answer_repeats_the_measured_air() -> None:
    answer = standard_answer(AskContext("Can Aarav play?", context()))
    assert answer.text.startswith("The assistant is not available right now. AQI 326")
    assert answer.fact_ids == ["air_now", "health"]


def test_sensitive_commuters_are_offered_swaps_that_do_not_add_exposure() -> None:
    data = FAMILY.model_dump(mode="json")
    data["members"][0]["conditions"] = ["heart condition"]
    facts = facts_of(today(household=Household.model_validate(data)))
    assert facts["swap_1_1"].startswith("If Asha went by car shared by 3 people")
    assert facts_of()["swap_1_1"].startswith("If Asha went by bus")
