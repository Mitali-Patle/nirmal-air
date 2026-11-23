from dataclasses import dataclass, field

from pydantic import BaseModel

from app.ai.chain import AIChain
from app.ai.providers import LLMRequest, ProviderError, RateLimitedError
from app.ai.task import AITask, Attempt, Outcome, OutputRejectedError


class Echo(BaseModel):
    text: str


def check(answer: Echo, context: str) -> Echo:
    if answer.text == "bad":
        raise OutputRejectedError(["text: bad is not allowed"])
    return answer


TASK: AITask[str, Echo] = AITask(
    name="echo",
    version="echo-v1",
    system="Echo the request.",
    output=Echo,
    payload=lambda context: {"say": context},
    check=check,
    fallback=lambda context: Echo(text="standard"),
)


@dataclass
class Scripted:
    """A provider that answers from a script: text to return or an error to raise."""

    name: str
    script: list[str | Exception]
    requests: list[LLMRequest] = field(default_factory=list)

    async def generate(self, request: LLMRequest) -> str:
        self.requests.append(request)
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def outcomes(attempts: tuple[Attempt, ...]) -> list[str]:
    return [attempt.outcome.value for attempt in attempts]


async def test_the_first_good_answer_wins_and_is_cached() -> None:
    first = Scripted("a", ['{"text": "hello"}'])
    chain = AIChain([first, Scripted("b", [])])
    result = await chain.run(TASK, "hello")
    assert result.value.text == "hello"
    assert (result.provenance.provider, result.provenance.cached) == ("a", False)
    assert result.provenance.request == {"say": "hello"}
    assert result.provenance.reply == '{"text": "hello"}'
    again = await chain.run(TASK, "hello")
    assert again.provenance.cached is True
    assert len(first.requests) == 1


async def test_a_rejected_answer_gets_one_repair_with_the_problems() -> None:
    provider = Scripted("a", ['{"text": "bad"}', '{"text": "good"}'])
    result = await AIChain([provider]).run(TASK, "x")
    assert result.value.text == "good"
    assert outcomes(result.provenance.attempts) == ["answer rejected", "ok"]
    assert "bad is not allowed" in provider.requests[1].user


async def test_two_bad_answers_move_on_to_the_next_model() -> None:
    chain = AIChain(
        [Scripted("a", ["not json", '{"wrong": 1}']), Scripted("b", ['{"text": "ok"}'])]
    )
    result = await chain.run(TASK, "x")
    assert result.provenance.provider == "b"
    assert outcomes(result.provenance.attempts) == ["answer rejected", "answer rejected", "ok"]
    assert result.provenance.attempts[0].problems


async def test_every_model_failing_gives_labelled_standard_advice() -> None:
    chain = AIChain([Scripted("a", [ProviderError("a: HTTP 503")])])
    result = await chain.run(TASK, "x")
    assert result.value.text == "standard"
    assert result.provenance.fallback is True
    assert result.provenance.attempts[0].problems == ("a: HTTP 503",)


async def test_a_rate_limited_model_rests_until_it_may_be_asked_again() -> None:
    clock = Clock()
    limited = Scripted("a", [RateLimitedError("a: rate limited", 30), '{"text": "back"}'])
    chain = AIChain([limited, Scripted("b", ['{"text": "b1"}', '{"text": "b2"}'])], clock=clock)
    assert (await chain.run(TASK, "one")).provenance.provider == "b"
    second = await chain.run(TASK, "two")
    assert outcomes(second.provenance.attempts) == [Outcome.RESTING.value, "ok"]
    clock.now = 31
    assert (await chain.run(TASK, "three")).provenance.provider == "a"


async def test_a_rate_limit_without_a_delay_rests_a_minute() -> None:
    clock = Clock()
    chain = AIChain([Scripted("a", [RateLimitedError("a: rate limited", None)])], clock=clock)
    await chain.run(TASK, "one")
    clock.now = 59
    result = await chain.run(TASK, "two")
    assert outcomes(result.provenance.attempts) == [Outcome.RESTING.value]


async def test_models_are_skipped_once_the_time_budget_is_spent() -> None:
    clock = Clock()

    class Slow(Scripted):
        async def generate(self, request: LLMRequest) -> str:
            clock.now += 19
            raise ProviderError("slow: ReadTimeout")

    chain = AIChain([Slow("slow", []), Scripted("b", [])], clock=clock)
    result = await chain.run(TASK, "x")
    assert outcomes(result.provenance.attempts) == ["no answer", Outcome.NO_TIME.value]
    assert result.provenance.latency_ms == 19000
