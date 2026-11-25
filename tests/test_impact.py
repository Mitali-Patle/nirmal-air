import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.commute import offered_swaps, swaps, trip_impact
from app.domain.household import Commute, Home, Mode
from app.domain.indoor import cigarettes, indoor_estimates, indoor_pm25


def commute(**values: object) -> Commute:
    defaults: dict[str, object] = {
        "member": "Asha",
        "mode": Mode.CAR,
        "km_one_way": 12,
        "days_per_week": 5,
        "leaves_at_hour": 9,
    }
    return Commute.model_validate(defaults | values)


def test_a_car_trip_uses_the_india_ghg_programme_factor() -> None:
    trip = trip_impact(Mode.CAR, 12)
    assert (trip.minutes, trip.co2_kg, trip.air_m3) == (36, 1.68, 0.18)
    assert trip.inhaled_ug(150) == 27


def test_public_transport_adds_the_walk_and_the_wait() -> None:
    trip = trip_impact(Mode.METRO, 12)
    # 22.5 min riding + 10 walking + 5 waiting; air 0.18 + 0.21 + 0.065 m³.
    assert (trip.minutes, trip.co2_kg, trip.air_m3) == (38, 0.73, 0.455)


def test_shared_vehicles_split_co2_but_buses_do_not() -> None:
    assert trip_impact(Mode.CAR, 10, people_in_vehicle=2).co2_kg == 0.7
    assert trip_impact(Mode.BUS, 10, people_in_vehicle=2).co2_kg == 0.15


def test_car_swaps_rank_by_co2_and_show_the_exposure_trade_off() -> None:
    found = swaps(commute(metro_possible=True))
    assert [(swap.mode, swap.people_in_vehicle) for swap in found] == [
        (Mode.BUS, 1),
        (Mode.CAR, 3),
        (Mode.METRO, 1),
    ]
    bus = found[0]
    assert (bus.co2_saved_kg_week, bus.minutes_change) == (15.0, 30)
    assert bus.air_change_pct > 0  # an AC car keeps out more PM2.5 than an open bus


def test_short_trips_offer_walking_and_cycling() -> None:
    modes = {swap.mode for swap in swaps(commute(mode=Mode.TWO_WHEELER, km_one_way=2))}
    assert modes == {Mode.BUS, Mode.WALK, Mode.CYCLE}


def test_zero_emission_trips_have_no_swaps() -> None:
    assert swaps(commute(mode=Mode.CYCLE, km_one_way=5)) == []


def test_a_full_carpool_is_not_offered_again() -> None:
    found = swaps(commute(people_in_vehicle=3))
    assert all(swap.mode is not Mode.CAR for swap in found)


def test_indoor_estimates_with_and_without_a_purifier() -> None:
    assert indoor_estimates(151.2, Home()).with_purifier is None
    estimate = indoor_estimates(151.2, Home(room_sqft=150, purifier_cadr_m3h=250))
    assert (estimate.windows_open, estimate.windows_shut, estimate.with_purifier) == (145, 101, 17)
    assert estimate.purifier_air_changes == 6.0


@given(
    outdoor=st.floats(min_value=1, max_value=999),
    cadr=st.integers(min_value=1, max_value=1500),
    sqft=st.integers(min_value=50, max_value=1000),
)
def test_shutting_windows_and_purifying_never_make_the_room_worse(
    outdoor: float, cadr: int, sqft: int
) -> None:
    estimate = indoor_estimates(outdoor, Home(room_sqft=sqft, purifier_cadr_m3h=cadr))
    assert estimate.with_purifier is not None
    assert (
        estimate.with_purifier <= estimate.windows_shut <= estimate.windows_open <= round(outdoor)
    )


def test_indoor_air_is_never_dirtier_than_outdoor_air() -> None:
    assert indoor_pm25(100, 1.0, 50) < 100


@pytest.mark.parametrize(
    ("pm25", "hours", "expected"), [(22, 24, 1.0), (151.2, 24, 6.9), (88, 6, 1.0)]
)
def test_cigarette_equivalence(pm25: float, hours: float, expected: float) -> None:
    assert cigarettes(pm25, hours) == expected


def test_a_sensitive_commuter_with_no_safe_swap_is_offered_none() -> None:
    full_car = commute(people_in_vehicle=3)  # carpool already; only the bus is left
    assert [swap.mode for swap in offered_swaps(full_car, sensitive=False)] == [Mode.BUS]
    assert offered_swaps(full_car, sensitive=True) == []
