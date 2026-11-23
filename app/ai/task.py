"""What an AI task is, and the record of how each answer was produced."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class OutputRejectedError(Exception):
    """A well-formed answer that breaks a rule, such as a number not among the facts.

    Attributes:
        problems: Short descriptions, sent back to the model for its one repair attempt.
    """

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class AITask[C, T: BaseModel]:
    """Everything one kind of AI call needs.

    Attributes:
        name: Task name, used in cache keys and provenance.
        version: Prompt version; changing it retires cached answers.
        system: System prompt.
        output: Schema the answer must match.
        payload: Builds the JSON user message from the context.
        check: Checks an answer against the context. It may drop bad parts and return the
            rest, or raise `OutputRejectedError`.
        fallback: Non-AI answer used when every model fails.
        temperature: Sampling temperature.
        max_output_tokens: Upper bound on answer length.
    """

    name: str
    version: str
    system: str
    output: type[T]
    payload: Callable[[C], dict[str, Any]]
    check: Callable[[T, C], T]
    fallback: Callable[[C], T]
    temperature: float = 0.3
    max_output_tokens: int = 2000


class Outcome(StrEnum):
    """What happened when a model was tried."""

    OK = "ok"
    REJECTED = "answer rejected"
    FAILED = "no answer"
    RATE_LIMITED = "rate limited"
    RESTING = "skipped: rate limited earlier"
    NO_TIME = "skipped: out of time"


class Attempt(BaseModel):
    """One try against one model."""

    model_config = ConfigDict(frozen=True)

    provider: str
    outcome: Outcome
    latency_ms: int
    problems: tuple[str, ...] = ()


class Provenance(BaseModel):
    """How a result was produced, for the "How this was generated" panel."""

    model_config = ConfigDict(frozen=True)

    task: str
    prompt_version: str
    provider: str | None
    cached: bool
    latency_ms: int
    attempts: tuple[Attempt, ...]
    request: dict[str, Any]
    reply: str | None

    @property
    def fallback(self) -> bool:
        """Whether this is standard advice rather than an AI answer."""
        return self.provider is None


@dataclass(frozen=True)
class AIResult[T: BaseModel]:
    """A checked answer and how it was produced."""

    value: T
    provenance: Provenance
