"""Property-based checks of the posterior with Hypothesis (Test Plan §3: unit, property-based)."""

from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.config.engine_config import load_engine_config
from app.domain.assurance.estimation.posterior import EstimatorParams, WeightedOutcome, estimate

NOW = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
P = EstimatorParams.from_config(load_engine_config().section("trust_estimation_alg1"))

outcome = st.builds(
    lambda age, ok, sim: WeightedOutcome(NOW - timedelta(days=age), ok, sim),
    st.floats(0, 1000),
    st.booleans(),
    st.floats(0.5, 1.0),
)


@given(st.lists(outcome, max_size=40))
def test_estimate_is_a_proper_probability_with_the_mean_inside_its_interval(
    xs: list[WeightedOutcome],
) -> None:
    e = estimate(xs, P, NOW)
    assert 0.0 < e.lower_90 <= e.mean <= e.upper_90 < 1.0
    assert e.n_raw == len(xs)
    # every weight lands on exactly one side (floating-point tolerance)
    assert e.alpha + e.beta == pytest.approx(P.alpha0 + P.beta0 + e.n_eff)


@given(st.lists(outcome, max_size=30), st.floats(0, 1000))
def test_another_success_never_lowers_the_mean(xs: list[WeightedOutcome], age: float) -> None:
    before = estimate(xs, P, NOW).mean
    after = estimate([*xs, WeightedOutcome(NOW - timedelta(days=age), True)], P, NOW).mean
    assert after >= before


@given(st.integers(0, 40))
def test_interval_narrows_as_consistent_evidence_grows(n: int) -> None:
    def width(k: int) -> float:
        e = estimate([WeightedOutcome(NOW, True)] * k, P, NOW)
        return e.upper_90 - e.lower_90

    assert width(n + 1) < width(n)


@given(st.floats(0, 1000), st.floats(0, 1000))
def test_older_evidence_weighs_less(a: float, b: float) -> None:
    young, old = sorted((a, b))
    w_young = estimate([WeightedOutcome(NOW - timedelta(days=young), True)], P, NOW).n_eff
    w_old = estimate([WeightedOutcome(NOW - timedelta(days=old), True)], P, NOW).n_eff
    assert w_old <= w_young
