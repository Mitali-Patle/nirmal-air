"""Rate limits, so one client cannot spend the free AI quota or hammer the data services.

Two budgets: AI calls (tight, per client and per instance) and every page or lookup that
reads an outside service (generous, per client). Counts live in memory per server instance,
like the caches: enough to stop a loop or a script, without a shared store on every request.
"""

import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class Budget:
    """At most `limit` requests in any `window_s` seconds."""

    limit: int
    window_s: float


AI_PER_CLIENT = Budget(20, 10 * 60)
AI_OVERALL = Budget(60, 60)
# Pages, place search, location and colour changes: a person clicking around stays far below.
PAGE_PER_CLIENT = Budget(60, 60)
MAX_CLIENTS = 2048
# Only headers Vercel's proxy sets itself; the generic X-Forwarded-For is never read.
PROXY_HEADERS = ("x-vercel-forwarded-for", "x-real-ip")


class RateLimiter:
    """A sliding-window limit per key, remembering a bounded number of keys."""

    def __init__(
        self, limit: int, window_s: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._limit = limit
        self._window_s = window_s
        self._clock = clock
        self._events: OrderedDict[str, deque[float]] = OrderedDict()

    def allow(self, key: str) -> bool:
        """Record one request for `key` if it is within the limit.

        Args:
            key: Who is asking.

        Returns:
            Whether the request may go ahead.
        """
        now = self._clock()
        events = self._events.pop(key, deque())
        while events and now - events[0] >= self._window_s:
            events.popleft()
        allowed = len(events) < self._limit
        if allowed:
            events.append(now)
        self._events[key] = events
        if len(self._events) > MAX_CLIENTS:
            self._events.popitem(last=False)
        return allowed


class ClientLimits:
    """A per-client budget, and optionally one for the whole instance.

    Args:
        per_client: The budget for each client address.
        overall: The budget for all clients together, if any.
        behind_proxy: True on Vercel, where the platform sets the client's address in a header
            it does not let clients override; elsewhere the socket peer is used.
        clock: Monotonic clock (tests pass a fake one).
    """

    def __init__(
        self,
        per_client: Budget,
        overall: Budget | None = None,
        *,
        behind_proxy: bool = False,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._per_client = RateLimiter(per_client.limit, per_client.window_s, clock=clock)
        self._overall = (
            RateLimiter(overall.limit, overall.window_s, clock=clock) if overall else None
        )
        self._behind_proxy = behind_proxy

    def allow(self, request: Request) -> bool:
        """Whether this request may go ahead now.

        Args:
            request: The incoming request.

        Returns:
            True when the client's budget (and the overall one, if set) allows it.
        """
        key = client_key(request, behind_proxy=self._behind_proxy)
        if not self._per_client.allow(key):
            return False
        return self._overall is None or self._overall.allow("all")


def client_key(request: Request, *, behind_proxy: bool) -> str:
    """The client's address.

    Behind Vercel's proxy the platform writes these headers itself (it overwrites any a client
    sends), so they can be trusted there. Elsewhere they are ignored, because anyone can send
    them.

    Args:
        request: The incoming request.
        behind_proxy: Whether the app runs behind Vercel's proxy.

    Returns:
        An address string.
    """
    if behind_proxy:
        for header in PROXY_HEADERS:
            forwarded = request.headers.get(header, "")
            if forwarded:
                return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
