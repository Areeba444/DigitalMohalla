"""Recency-weighted Beta posterior: known values and boundaries (Test Plan suite 6, TC-20 to TC-24)."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.config.engine_config import load_engine_config
from app.domain.assurance.estimation.posterior import (
    EstimatorParams,
    WeightedOutcome,
    credible_interval,
    estimate,
    recency_weight,
)

NOW = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
P = EstimatorParams.from_config(load_engine_config().section("trust_estimation_alg1"))
FIXTURES = (
    Path(__file__).resolve().parents[3] / "docs/design/14_testing/scenario_fixtures_iteration1.json"
)


def ago(days: float, success: bool = True, **kw: object) -> WeightedOutcome:
    return WeightedOutcome(NOW - timedelta(days=days), success, **kw)  # type: ignore[arg-type]


def test_parameters_come_from_the_config() -> None:
    assert (P.alpha0, P.beta0, P.half_life_days, P.level) == (1.0, 1.0, 180.0, 0.9)


def test_tc20_no_history_is_the_uniform_prior_not_a_bad_score() -> None:
    e = estimate([], P, NOW)
    assert (e.alpha, e.beta, e.n_eff, e.n_raw) == (1.0, 1.0, 0.0, 0)
    assert e.mean == 0.5
    assert e.lower_90 == pytest.approx(0.05) and e.upper_90 == pytest.approx(0.95)


def test_tc21_eighteen_successes_and_two_failures_today() -> None:
    e = estimate([ago(0)] * 18 + [ago(0, False)] * 2, P, NOW)
    assert (e.alpha, e.beta) == (19.0, 3.0)
    assert e.mean == pytest.approx(0.8636, abs=1e-4)
    assert e.lower_90 < e.mean < e.upper_90


def test_tc22_recency_weights_at_10_and_360_days() -> None:
    assert recency_weight(10, 180) == pytest.approx(0.962, abs=5e-4)
    assert recency_weight(360, 180) == pytest.approx(0.25)
    assert recency_weight(180, 180) == pytest.approx(0.5)


def test_design_example_one_success_is_very_wide() -> None:
    e = estimate([ago(0)], P, NOW)
    assert (e.alpha, e.beta) == (2.0, 1.0)
    # Beta(2, 1) quantiles are square roots: sqrt(0.05) and sqrt(0.95)
    assert e.lower_90 == pytest.approx(0.05**0.5, abs=1e-6)
    assert e.upper_90 == pytest.approx(0.95**0.5, abs=1e-6)


def test_design_example_decay() -> None:
    e = estimate([ago(0), ago(180), ago(360, False)], P, NOW)
    assert e.alpha == pytest.approx(2.5) and e.beta == pytest.approx(1.25)
    assert e.mean == pytest.approx(2 / 3) and e.n_eff == pytest.approx(1.75)


def test_tc23_flagged_outcomes_do_not_count() -> None:
    e = estimate([ago(0), ago(0, False, status="FLAGGED_FOR_REEVALUATION")], P, NOW)
    assert (e.alpha, e.beta, e.n_raw) == (2.0, 1.0, 1)


def test_similarity_scales_the_weight() -> None:
    e = estimate([ago(0, similarity=0.5)], P, NOW)
    assert e.alpha == pytest.approx(1.5) and e.n_eff == pytest.approx(0.5)


@pytest.mark.parametrize(
    "fid",
    ["ES-01", "ES-02", "ES-03", "ES-04", "ES-05", "ES-06", "ES-13"],
)
def test_tc24_fixture_intervals_are_the_beta_quantiles(fid: str) -> None:
    fx = {f["scenario_id"]: f for f in json.loads(FIXTURES.read_text(encoding="utf-8"))["fixtures"]}
    de = fx[fid]["direct_evidence"]
    lo, hi = credible_interval(de["alpha"], de["beta"], P.level)
    assert lo == pytest.approx(de["lower_90"], abs=6e-4)
    assert hi == pytest.approx(de["upper_90"], abs=6e-4)
    assert de["alpha"] / (de["alpha"] + de["beta"]) == pytest.approx(de["mean"], abs=6e-4)


def test_es13_posterior_from_its_outcome_ages() -> None:
    fx = {f["scenario_id"]: f for f in json.loads(FIXTURES.read_text(encoding="utf-8"))["fixtures"]}
    de = fx["ES-13"]["direct_evidence"]
    e = estimate([ago(o["age_days"], o["success"]) for o in de["outcomes"]], P, NOW)
    assert e.alpha == pytest.approx(de["alpha"], abs=1e-4)
    assert e.n_eff == pytest.approx(de["n_eff"], abs=1e-4)
    assert e.lower_90 == pytest.approx(de["lower_90"], abs=6e-4)


@pytest.mark.parametrize(
    "bad",
    [
        lambda: estimate([ago(-1)], P, NOW),  # an outcome in the future
        lambda: estimate([WeightedOutcome(datetime(2026, 1, 1), True)], P, NOW),  # naive time
        lambda: estimate([], P, datetime(2026, 1, 1)),  # naive as_of
        lambda: estimate([ago(1, similarity=0.0)], P, NOW),  # similarity outside (0, 1]
        lambda: estimate([ago(1, similarity=1.5)], P, NOW),
        lambda: recency_weight(1, 0),  # half-life must be positive
    ],
)
def test_invalid_inputs_are_refused(bad: object) -> None:
    with pytest.raises(ValueError):
        bad()  # type: ignore[operator]
