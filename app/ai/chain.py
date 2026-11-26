"""The fallback chain: a cached answer, else each model in turn, else labelled standard advice.

Every answer is parsed against the task's schema and checked against the facts it was given.
A rejected answer gets one repair attempt on the same model, with the problems listed. A
rate-limited model sits out until it may be asked again. The chain never raises for model
problems, and every result records how it was produced.
"""

import asyncio
import hashlib
import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Any

from pydantic import BaseModel, ValidationError

from app.ai.providers import LLMRequest, Provider, ProviderError, RateLimitedError
from app.ai.repair import MAX_REPLY_CHARS, rejection_reasons, repair_request
from app.ai.task import AIResult, AITask, Attempt, Outcome, OutputRejectedError, Provenance
from app.cache import TtlCache

CALL_TIMEOUT_S = 10.0
TOTAL_BUDGET_S = 20.0
MIN_CALL_S = 2.0
DEFAULT_RETRY_AFTER_S = 60.0
ANSWER_TTL_S = 60 * 60


@dataclass(frozen=True)
class _Asked:
    """One request to the chain: the payload, its JSON text and its cache key."""

    payload: dict[str, Any]
    user: str
    key: str


@dataclass
class _Run:
    """State of one chain run."""

    started: float
    deadline: float
    attempts: list[Attempt]


class AIChain:
    """Runs AI tasks across models in order of preference."""

    def __init__(
        self,
        providers: Sequence[Provider],
        cache: TtlCache[AIResult[Any]] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._providers = tuple(providers)
        self._cache = cache or TtlCache(ANSWER_TTL_S, ANSWER_TTL_S)
        self._clock = clock
        self._resting_until: dict[str, float] = {}
        self._in_flight: dict[str, asyncio.Lock] = {}

    async def run[C, T: BaseModel](
        self, task: AITask[C, T], context: C, allow: Callable[[], bool] | None = None
    ) -> AIResult[T]:
        """Produce a checked answer, or the task's standard advice if every model fails.

        Identical requests that arrive together wait for one model call instead of each making
        their own; a cached answer is reused without asking `allow`.

        Args:
            task: What to ask.
            context: The facts and household the answer must rest on.
            allow: Asked before any model is called; False means standard advice (a rate limit).

        Returns:
            The answer and its provenance.
        """
        payload = task.payload(context)
        user = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        key = f"{task.name}:{task.version}:{hashlib.sha256(user.encode()).hexdigest()}"
        asked = _Asked(payload, user, key)
        lock = self._in_flight.setdefault(key, asyncio.Lock())
        try:
            async with lock:
                return await self._answer(task, context, asked, allow)
        finally:
            if not lock.locked():
                self._in_flight.pop(key, None)

    async def _answer[C, T: BaseModel](
        self,
        task: AITask[C, T],
        context: C,
        asked: _Asked,
        allow: Callable[[], bool] | None,
    ) -> AIResult[T]:
        payload, user, key = asked.payload, asked.user, asked.key
        cached = self._cache.get(key)
        if cached is not None and not cached.stale:
            hit: AIResult[T] = cached.value
            return replace(hit, provenance=hit.provenance.model_copy(update={"cached": True}))
        started = self._clock()
        run = _Run(started, started + TOTAL_BUDGET_S, [])
        if allow is not None and not allow():
            run.attempts.append(
                Attempt(provider="all models", outcome=Outcome.LIMITED, latency_ms=0)
            )
            return self._fallback(task, context, payload, run)
        request = LLMRequest(
            system=task.system,
            user=user,
            schema=task.output,
            temperature=task.temperature,
            max_output_tokens=task.max_output_tokens,
            timeout_s=CALL_TIMEOUT_S,
        )
        for provider in self._providers:
            answer = await self._ask(provider, task, context, request, run)
            if answer is not None:
                result = AIResult(
                    answer[0], self._provenance(task, payload, run, provider.name, answer[1])
                )
                self._cache.put(key, result)
                return result
        return self._fallback(task, context, payload, run)

    async def _ask[C, T: BaseModel](
        self,
        provider: Provider,
        task: AITask[C, T],
        context: C,
        request: LLMRequest,
        run: _Run,
    ) -> tuple[T, str] | None:
        """One model's answer and its raw text, allowing one repair, or None."""
        if self._resting_until.get(provider.name, 0.0) > self._clock():
            run.attempts.append(
                Attempt(provider=provider.name, outcome=Outcome.RESTING, latency_ms=0)
            )
            return None
        for _ in range(2):
            remaining = run.deadline - self._clock()
            if remaining < MIN_CALL_S:
                run.attempts.append(
                    Attempt(provider=provider.name, outcome=Outcome.NO_TIME, latency_ms=0)
                )
                return None
            started = self._clock()
            try:
                text = await provider.generate(
                    replace(request, timeout_s=min(CALL_TIMEOUT_S, remaining))
                )
            except RateLimitedError as error:
                wait = error.retry_after_s or DEFAULT_RETRY_AFTER_S
                self._resting_until[provider.name] = self._clock() + wait
                self._record(run, provider, Outcome.RATE_LIMITED, started)
                return None
            except ProviderError as error:
                self._record(run, provider, Outcome.FAILED, started, [str(error)])
                return None
            try:
                answer = task.check(task.output.model_validate_json(text), context)
            except (ValidationError, OutputRejectedError) as error:
                problems = rejection_reasons(error)
                self._record(run, provider, Outcome.REJECTED, started, problems)
                request = replace(request, user=repair_request(request.user, text, problems))
                continue
            self._record(run, provider, Outcome.OK, started)
            return answer, text
        return None

    def _record(
        self,
        run: _Run,
        provider: Provider,
        outcome: Outcome,
        started: float,
        problems: Sequence[str] = (),
    ) -> None:
        latency_ms = round((self._clock() - started) * 1000)
        run.attempts.append(
            Attempt(
                provider=provider.name,
                outcome=outcome,
                latency_ms=latency_ms,
                problems=tuple(problems),
            )
        )

    def _fallback[C, T: BaseModel](
        self, task: AITask[C, T], context: C, payload: dict[str, Any], run: _Run
    ) -> AIResult[T]:
        """The task's standard advice, with the attempts that led to it."""
        return AIResult(task.fallback(context), self._provenance(task, payload, run, None, None))

    def _provenance(
        self,
        task: AITask[Any, Any],
        payload: dict[str, Any],
        run: _Run,
        provider: str | None,
        reply: str | None,
    ) -> Provenance:
        return Provenance(
            task=task.name,
            prompt_version=task.version,
            provider=provider,
            cached=False,
            latency_ms=round((self._clock() - run.started) * 1000),
            attempts=tuple(run.attempts),
            request=payload,
            reply=reply[:MAX_REPLY_CHARS] if reply else None,
        )
