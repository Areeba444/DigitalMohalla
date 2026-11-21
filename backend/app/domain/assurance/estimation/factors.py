"""Evidence factors per role and metric, and the population baseline (A5; FR-T-02, FR-T-08, FR-S-04;
Algorithm doc iteration 2 §2 and §3). Pure, no I/O.

Plain-language rules:
- A member's evidence is kept per role (BORROWER, LENDER) and per metric (ON_TIME_RETURN,
  CONDITION_AGREED, DISPUTE_FREE). They are never averaged into one number (NFR-U-01); each factor is
  shown on its own with the number of verified loans and a confidence in words.
- Each factor is the recency-weighted Beta posterior of Algorithm 1 over that role's and metric's
  VALID outcomes. Outcomes under re-evaluation are not counted (ES-11).
- When the effective evidence n_eff is below the minimum, the detail is suppressed: only "too few
  loans to show" and the count are given, so small samples cannot identify a person or be misread
  (FR-T-08). Zero history is "not enough verified history yet", an absence of evidence, never a
  negative finding (FR-T-02).
- The population baseline is the recency-weighted mean of all VALID outcomes of a role and metric in
  a community. Below `min_weighted_outcomes` the fixed fallback 0.5 is kept, so a small community is
  not pulled to a noisy mean. It stands in for a lender with too little history in search, so a new
  lender is never penalised (claim C5).
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from app.domain.assurance.estimation.posterior import (
    EstimatorParams,
    WeightedOutcome,
    estimate,
    recency_weight,
)

ROLE_METRICS: dict[str, tuple[str, ...]] = {
    "BORROWER": ("ON_TIME_RETURN", "CONDITION_AGREED", "DISPUTE_FREE"),
    "LENDER": ("CONDITION_AGREED", "DISPUTE_FREE"),
}
METRIC_WORDS = {
    "ON_TIME_RETURN": "Returns on time",
    "CONDITION_AGREED": "Item as described and returned in agreed condition",
    "DISPUTE_FREE": "Loans without a dispute",
}
ROLE_METRIC_WORDS = {
    ("LENDER", "CONDITION_AGREED"): "Items are as described",
}
NOT_ENOUGH = "Not enough verified history yet. That is not a negative finding."
TOO_FEW = "Too few loans to show detail."


@dataclass(frozen=True)
class OutcomeRow:
    """One stored outcome of the member, as read from the database."""

    role: str
    metric: str
    success: bool
    occurred_at: datetime
    status: str = "VALID"


@dataclass(frozen=True)
class Factor:
    role: str
    metric: str
    label: str
    verified_loans: int  # VALID outcomes counted
    effective: float  # sum of recency weights (a diagnostic, never shown as a score)
    enough: bool  # effective evidence reaches the minimum
    mean: float | None  # only when enough
    lower_90: float | None
    upper_90: float | None
    confidence: str  # words
    note: str


def confidence_word(lower: float, upper: float) -> str:
    """The 90% interval's width in words: narrow means well supported."""
    width = upper - lower
    if width <= 0.25:
        return "high confidence"
    if width <= 0.5:
        return "moderate confidence"
    return "low confidence"


def factor(
    rows: Iterable[OutcomeRow],
    role: str,
    metric: str,
    params: EstimatorParams,
    n_min: float,
    now: datetime,
) -> Factor:
    mine = [r for r in rows if r.role == role and r.metric == metric and r.status == "VALID"]
    label = ROLE_METRIC_WORDS.get((role, metric), METRIC_WORDS[metric])
    if not mine:
        return Factor(
            role, metric, label, 0, 0.0, False, None, None, None, "no evidence yet", NOT_ENOUGH
        )
    est = estimate([WeightedOutcome(r.occurred_at, r.success) for r in mine], params, now)
    if est.n_eff < n_min:
        return Factor(
            role, metric, label, est.n_raw, round(est.n_eff, 2), False, None, None, None,
            "too little evidence", TOO_FEW,
        )  # fmt: skip
    return Factor(
        role, metric, label, est.n_raw, round(est.n_eff, 2), True, round(est.mean, 3),
        round(est.lower_90, 3), round(est.upper_90, 3), confidence_word(est.lower_90, est.upper_90), "",
    )  # fmt: skip


def role_factors(
    rows: list[OutcomeRow], role: str, params: EstimatorParams, n_min: float, now: datetime
) -> list[Factor]:
    return [factor(rows, role, m, params, n_min, now) for m in ROLE_METRICS[role]]


def population_baseline(
    rows: Iterable[tuple[bool, datetime]],
    half_life_days: float,
    now: datetime,
    min_weighted: float,
    fallback: float = 0.5,
) -> float:
    """Recency-weighted mean of (success, time) pairs, or `fallback` below `min_weighted` weight."""
    total = good = 0.0
    for success, at in rows:
        w = recency_weight(max(0.0, (now - at).total_seconds() / 86400.0), half_life_days)
        total += w
        good += w if success else 0.0
    if total < min_weighted or total == 0:
        return fallback
    return round(good / total, 4)


def ranking_value(lender_factor: Factor, baseline: float) -> float:
    """The lender's value for ranking (Algorithm 5): the posterior mean when there is enough
    evidence, otherwise the population baseline, so a new lender is never ranked down for having no
    history. Internal only: never returned to clients (FR-S-04, NFR-U-01)."""
    if lender_factor.enough and lender_factor.mean is not None:
        return lender_factor.mean
    return baseline
