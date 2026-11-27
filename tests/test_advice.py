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
from app.advice.facts import FactId, Kind, Today
from app.advice.plan import (
    Language,
    Plan,
    PlanItem,
    Slot,
    _cleanest_time_issues,
    check_plan,
    plan_payload,
)
from app.advice.standard import standard_plan
from app.ai.guard import FactGuard
from app.ai.task import OutputRejectedError
from app.domain.guidance import Decision, routine_decision
from app.domain.household import Activity, Household
from app.services.samples import SAMPLES
from tests.builders import FAMILY, NOW, context, measured, timing, today


def facts_of(day: Today | None = None) -> dict[str, str]:
    return {fact.id: fact.text for fact in build_facts(day or today())}


def item(member: str, why: str, fact_ids: list[str], slot: Slot = Slot.MORNING) -> PlanItem:
    return PlanItem(slot=slot, member=member, action="Do this today.", why=why, fact_ids=fact_ids)


def good_plan() -> Plan:
    return Plan(
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


def test_a_plan_that_leaves_out_a_sensitive_member_is_sent_back() -> None:
    with pytest.raises(OutputRejectedError) as caught:
        check_plan(good_plan().model_copy(update={"items": good_plan().items[1:]}), context())
    assert "no item for Dadi" in caught.value.problems


def test_too_few_items_are_sent_back() -> None:
    alone = Household.model_validate({"members": [{"name": "Asha", "role": "adult"}]})
    plan = Plan(items=[item("Asha", "Fine.", ["air_now"])])
    with pytest.raises(OutputRejectedError, match="only 1 usable items"):
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
    assert check_plan(plan, context()) == plan  # it would pass the AI's own checks


def test_standard_advice_on_clean_air() -> None:
    plan = standard_plan(context(today(measured(80))))
    actions = [entry.action for entry in plan.items]
    assert actions[0] == "Open the windows to air the house."
    assert "Run the purifier in the main room with doors shut." not in actions


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
    guard = FactGuard(facts.values())
    for entry in standard_plan(context()).items:
        assert guard.problems(entry.why) == []


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


def test_a_home_without_a_purifier_sees_what_one_would_change() -> None:
    data = FAMILY.model_dump(mode="json")
    data["home"]["purifier_cadr_m3h"] = 0
    facts = facts_of(today(household=Household.model_validate(data)))
    assert "indoor_purifier" not in facts
    assert facts["indoor_purifier_if"].startswith("A typical air purifier (250 m³/h)")
    assert "about 17 µg/m³" in facts["indoor_purifier_if"]


def test_different_households_in_the_same_air_get_different_advice() -> None:
    plans = {
        key: standard_plan(context(today(household=sample.household)))
        for key, sample in SAMPLES.items()
    }
    members = {key: {entry.member for entry in plan.items} for key, plan in plans.items()}
    assert members["delhi-family"] >= {"Aarav", "Dadi", "Asha"}
    assert "Ravi" in members["bengaluru-cyclist"]
    assert "Imran" in members["mumbai-commuter"]
    delhi_swap = facts_of(today(household=SAMPLES["delhi-family"].household))["swap_1_1"]
    mumbai_swap = facts_of(today(household=SAMPLES["mumbai-commuter"].household))["swap_1_1"]
    assert delhi_swap.startswith("If Asha went by bus")  # healthy adult: biggest CO2 saving
    assert mumbai_swap.startswith(
        "If Imran went by car shared"
    )  # heart condition: no added exposure


def test_houseplants_are_never_offered_as_a_fix() -> None:
    facts = {fact.id: fact for fact in build_facts(today())}
    plants = facts[FactId.PLANTS]
    assert plants.figure == "0.023 m³/h" and "do not measurably clean" in plants.text
    assert (
        FactGuard([plants.text]).problems("One plant cleans 0.023 m³ an hour; 10 to 1,000 per m².")
        == []
    )


def test_a_plan_must_offer_each_commutes_chosen_swap() -> None:
    without_swap = Plan(items=[entry for entry in good_plan().items if entry.member != "Asha"])
    asha = item("Asha", "Drive as usual.", ["commute_1"])
    with pytest.raises(OutputRejectedError) as rejected:
        check_plan(
            without_swap.model_copy(update={"items": [*without_swap.items, asha]}), context()
        )
    assert "offer swap_1_1 for its commute" in rejected.value.problems


def test_english_steps_quote_the_cleanest_time_whole() -> None:
    point = item("Everyone", "Air the house at 1 pm.", ["cleanest"])
    whole = item("Everyone", "Air the house from 1 pm to 4 pm.", ["cleanest"])
    checked = check_plan(
        good_plan().model_copy(update={"items": [*good_plan().items, point, whole]}), context()
    )
    assert point not in checked.items and whole in checked.items
    hindi = context(language=Language.HINDI)
    hindi_point = item("Everyone", "दोपहर 1 pm पर हवा दें", ["cleanest"])
    assert not _cleanest_time_issues(hindi_point, hindi)


def test_a_cleanest_time_tomorrow_must_say_tomorrow() -> None:
    day = today()
    late = Today(day.place, NOW.replace(hour=21), day.air, timing(day=25), day.household)
    step = item("Everyone", "Air the house from 1 pm to 4 pm.", ["cleanest"])
    assert _cleanest_time_issues(step, context(late)) == ["say the cleanest time is tomorrow"]
    tomorrow = item("Everyone", "Air the house from 1 pm to 4 pm tomorrow.", ["cleanest"])
    assert _cleanest_time_issues(tomorrow, context(late)) == []


def test_standard_advice_covers_pregnancy_and_combines_errands() -> None:
    household = Household.model_validate(
        {
            "members": [
                {"name": "Meera", "role": "adult", "conditions": ["pregnant"]},
                {"name": "Ravi", "role": "adult"},
            ],
            "routines": [
                {"member": "Ravi", "activity": "market and errands", "hour": 18, "minutes": 40}
            ],
        }
    )
    actions = {
        entry.member: entry.action
        for entry in standard_plan(context(today(household=household))).items
    }
    assert actions["Meera"] == "Keep time outdoors short; see a doctor if breathing gets hard."
    assert actions["Ravi"].endswith("Do them in one outing.")
