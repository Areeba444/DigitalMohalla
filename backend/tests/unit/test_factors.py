"""Evidence factors and the population baseline (A5; FR-T-02, FR-T-08, FR-S-04; suite 6 and 30).

Numbers are hand-checked: ten on-time returns of the same age have weights 2^(-age/half-life), and the
posterior is Beta(1 + sum of weights, 1) when all succeed. All data is synthetic.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.assurance.estimation.factors import (
    NOT_ENOUGH,
    TOO_FEW,
    OutcomeRow,
    confidence_word,
    factor,
    population_baseline,
    ranking_value,
    role_factors,
)
from app.domain.assurance.estimation.posterior import EstimatorParams

NOW = datetime(2026, 11, 21, 8, 0, tzinfo=UTC)
PARAMS = EstimatorParams(alpha0=1.0, beta0=1.0, half_life_days=180.0, level=0.9)


def rows(n: int, age_days: float = 0, ok: bool = True, role: str = "BORROWER",
         metric: str = "ON_TIME_RETURN", status: str = "VALID") -> list[OutcomeRow]:  # fmt: skip
    return [OutcomeRow(role, metric, ok, NOW - timedelta(days=age_days), status) for _ in range(n)]


def test_no_history_is_an_absence_of_evidence_not_a_negative_finding() -> None:  # FR-T-02
    f = factor([], "LENDER", "CONDITION_AGREED", PARAMS, 3.0, NOW)
    assert (f.verified_loans, f.enough, f.mean) == (0, False, None)
    assert f.note == NOT_ENOUGH and "not a negative finding" in f.note


def test_too_few_loans_are_suppressed() -> None:  # FR-T-08
    f = factor(rows(2), "BORROWER", "ON_TIME_RETURN", PARAMS, 3.0, NOW)
    assert (f.verified_loans, f.enough) == (2, False)
    assert f.mean is None and f.lower_90 is None and f.upper_90 is None  # no detail shown
    assert f.note == TOO_FEW


def test_enough_loans_give_the_posterior_and_an_interval() -> None:
    f = factor(rows(10), "BORROWER", "ON_TIME_RETURN", PARAMS, 3.0, NOW)
    # ten fresh successes: Beta(11, 1), mean 11/12 = 0.917, 5% quantile 0.05^(1/11) = 0.762
    assert f.enough and f.verified_loans == 10
    assert f.mean == pytest.approx(0.917, abs=1e-3)
    assert f.lower_90 == pytest.approx(0.762, abs=1e-3)
    assert f.upper_90 is not None and f.upper_90 - f.lower_90 < 0.25  # hand check: 0.99 - 0.76
    assert f.confidence == "high confidence"


def test_only_valid_outcomes_of_the_asked_role_and_metric_count() -> None:
    mixed = (
        rows(5)
        + rows(5, ok=False, role="LENDER", metric="CONDITION_AGREED")
        + rows(5, status="FLAGGED_FOR_REEVALUATION", ok=False)  # ES-11: under review, not counted
    )
    f = factor(mixed, "BORROWER", "ON_TIME_RETURN", PARAMS, 3.0, NOW)
    assert f.verified_loans == 5 and f.mean is not None and f.mean > 0.8


def test_old_evidence_counts_for_less() -> None:  # FR-T-03
    recent = factor(rows(4, age_days=10), "BORROWER", "ON_TIME_RETURN", PARAMS, 3.0, NOW)
    old = factor(rows(4, age_days=720), "BORROWER", "ON_TIME_RETURN", PARAMS, 3.0, NOW)
    assert recent.effective > 3.0 > old.effective  # 4 * 2^(-720/180) = 0.25
    assert recent.enough and not old.enough


def test_role_factors_keep_roles_and_metrics_apart() -> None:
    data = rows(6, metric="ON_TIME_RETURN") + rows(6, ok=False, metric="DISPUTE_FREE")
    fs = {f.metric: f for f in role_factors(data, "BORROWER", PARAMS, 3.0, NOW)}
    assert set(fs) == {"ON_TIME_RETURN", "CONDITION_AGREED", "DISPUTE_FREE"}
    assert fs["ON_TIME_RETURN"].mean is not None and fs["ON_TIME_RETURN"].mean > 0.8
    assert fs["DISPUTE_FREE"].mean is not None and fs["DISPUTE_FREE"].mean < 0.2  # kept separate
    assert fs["CONDITION_AGREED"].verified_loans == 0
    assert {f.metric for f in role_factors(data, "LENDER", PARAMS, 3.0, NOW)} == {
        "CONDITION_AGREED",
        "DISPUTE_FREE",
    }


def test_lender_condition_factor_is_worded_as_described() -> None:
    f = factor([], "LENDER", "CONDITION_AGREED", PARAMS, 3.0, NOW)
    assert f.label == "Items are as described"


@pytest.mark.parametrize(
    ("lower", "upper", "word"),
    [
        (0.8, 0.95, "high confidence"),
        (0.6, 0.95, "moderate confidence"),
        (0.05, 0.95, "low confidence"),
    ],
)
def test_confidence_in_words(lower: float, upper: float, word: str) -> None:
    assert confidence_word(lower, upper) == word


def test_baseline_keeps_the_fallback_until_enough_weight() -> None:
    few = [(True, NOW)] * 10
    assert population_baseline(few, 180.0, NOW, min_weighted=30.0) == 0.5
    assert population_baseline([], 180.0, NOW, min_weighted=30.0, fallback=0.5) == 0.5


def test_baseline_is_the_recency_weighted_mean_once_there_is_enough() -> None:
    data = [(True, NOW)] * 30 + [(False, NOW)] * 10  # fresh: weights 1, so 30 / 40
    assert population_baseline(data, 180.0, NOW, min_weighted=30.0) == 0.75


def test_a_new_lender_is_ranked_at_the_baseline_never_below_it() -> None:  # claim C5
    new = factor([], "LENDER", "CONDITION_AGREED", PARAMS, 3.0, NOW)
    assert ranking_value(new, 0.8) == 0.8
    seasoned = factor(rows(10, role="LENDER", metric="CONDITION_AGREED"), "LENDER",
                      "CONDITION_AGREED", PARAMS, 3.0, NOW)  # fmt: skip
    assert ranking_value(seasoned, 0.8) == seasoned.mean
