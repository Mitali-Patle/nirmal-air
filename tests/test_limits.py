from types import SimpleNamespace
from typing import Any

from app.web.limits import (
    AI_OVERALL,
    AI_PER_CLIENT,
    MAX_CLIENTS,
    PAGE_PER_CLIENT,
    Budget,
    ClientLimits,
    RateLimiter,
    client_key,
)


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def request(ip: str = "", headers: dict[str, str] | None = None) -> Any:
    return SimpleNamespace(headers=headers or {}, client=SimpleNamespace(host=ip) if ip else None)


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


def test_forwarded_addresses_are_trusted_only_behind_vercels_proxy() -> None:
    spoofed = request(ip="5.6.7.8", headers={"x-forwarded-for": "1.1.1.1"})
    assert client_key(spoofed, behind_proxy=False) == "5.6.7.8"
    vercel = request(ip="10.0.0.1", headers={"x-vercel-forwarded-for": "1.2.3.4, 10.0.0.2"})
    assert client_key(vercel, behind_proxy=True) == "1.2.3.4"
    real_ip = request(ip="10.0.0.1", headers={"x-real-ip": "9.8.7.6"})
    assert client_key(real_ip, behind_proxy=True) == "9.8.7.6"
    assert client_key(request(ip="10.0.0.1"), behind_proxy=True) == "10.0.0.1"
    assert client_key(request(), behind_proxy=False) == "unknown"


def test_both_limits_apply() -> None:
    limits = ClientLimits(AI_PER_CLIENT, AI_OVERALL, clock=Clock())
    allowed = [limits.allow(request(ip="9.9.9.9")) for _ in range(21)]
    assert allowed.count(True) == 20


def test_the_overall_budget_stops_many_clients_together() -> None:
    limits = ClientLimits(Budget(5, 60), Budget(3, 60), clock=Clock())
    allowed = [limits.allow(request(ip=f"10.0.0.{index}")) for index in range(5)]
    assert allowed == [True, True, True, False, False]


def test_the_page_budget_has_no_overall_cap() -> None:
    limits = ClientLimits(PAGE_PER_CLIENT, clock=Clock())
    allowed = [limits.allow(request(ip="7.7.7.7")) for _ in range(PAGE_PER_CLIENT.limit + 1)]
    assert allowed.count(True) == PAGE_PER_CLIENT.limit
    assert limits.allow(request(ip="8.8.8.8"))
