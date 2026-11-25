from types import SimpleNamespace
from typing import Any

from app.web.limits import MAX_CLIENTS, AILimits, RateLimiter, client_key


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def request(ip: str = "", forwarded: str = "") -> Any:
    headers = {"x-forwarded-for": forwarded} if forwarded else {}
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=ip) if ip else None)


def test_a_sliding_window_allows_the_limit_then_recovers() -> None:
    clock = Clock()
    limiter = RateLimiter(2, 60, clock=clock)
    assert [limiter.allow("a") for _ in range(3)] == [True, True, False]
    assert limiter.allow("b")
    clock.now = 60
    assert limiter.allow("a")


def test_only_a_bounded_number_of_clients_is_remembered() -> None:
    limiter = RateLimiter(1, 60)
    for index in range(MAX_CLIENTS + 1):
        limiter.allow(f"client-{index}")
    assert limiter.allow("client-0")  # forgotten, so allowed again


def test_the_client_is_the_first_forwarded_address() -> None:
    assert client_key(request(forwarded="1.2.3.4, 10.0.0.1")) == "1.2.3.4"
    assert client_key(request(ip="5.6.7.8")) == "5.6.7.8"
    assert client_key(request()) == "unknown"


def test_both_limits_apply() -> None:
    limits = AILimits(clock=Clock())
    allowed = [limits.allow(request(ip="9.9.9.9")) for _ in range(21)]
    assert allowed.count(True) == 20
