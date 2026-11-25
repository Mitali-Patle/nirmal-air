"""Rate limits for the routes that call AI models, so one client cannot spend the free quota.

Counts live in memory per server instance, like the caches: enough to stop a loop or a
script, without adding a shared store to every request.
"""

import time
from collections import OrderedDict, deque
from collections.abc import Callable

from fastapi import Request

PER_CLIENT = (20, 10 * 60)  # 20 AI requests per client in 10 minutes
OVERALL = (60, 60)  # 60 AI requests per instance per minute
MAX_CLIENTS = 2048
PROXY_HEADERS = ("x-vercel-forwarded-for", "x-real-ip", "x-forwarded-for")


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


class AILimits:
    """The per-client and overall limits together.

    Args:
        behind_proxy: True on Vercel, where the platform sets the client's address in a header
            it does not let clients override; elsewhere the socket peer is used.
        clock: Monotonic clock (tests pass a fake one).
    """

    def __init__(
        self, *, behind_proxy: bool = False, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._per_client = RateLimiter(*PER_CLIENT, clock=clock)
        self._overall = RateLimiter(*OVERALL, clock=clock)
        self._behind_proxy = behind_proxy

    def allow(self, request: Request) -> bool:
        """Whether this request may call a model now.

        Args:
            request: The incoming request.

        Returns:
            True when both the client's and the overall limit allow it.
        """
        key = client_key(request, behind_proxy=self._behind_proxy)
        return self._per_client.allow(key) and self._overall.allow("all")


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
