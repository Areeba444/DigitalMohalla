"""Recency-weighted Beta posterior (Algorithm 1 of the algorithm design; FR-T-02, FR-T-03).

Plain-language note: every verified outcome is a success or a failure. Starting from the prior
Beta(1, 1) ("no evidence yet"), each outcome adds its weight to the successes (alpha) or failures
(beta). The weight halves every `half_life_days` (180) and is multiplied by how similar the past
loan is to the request. The mean alpha / (alpha + beta) is the estimate; the 90% credible interval
from the Beta quantiles shows how sure it is: wide with little evidence, narrow with a lot.
n_eff, the sum of the weights, is reported as a diagnostic only, never as a trust number.
Pure functions, no I/O (A8 layer rules).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from scipy.stats import beta as beta_distribution  # type: ignore[import-untyped]  # SciPy ships no type stubs


@dataclass(frozen=True)
class WeightedOutcome:
    """One verified outcome of the subject in the role and metric being estimated.

    similarity: the (already floored) similarity to the request, in (0, 1]; 1.0 when unused.
    status: only VALID outcomes count; FLAGGED_FOR_REEVALUATION ones are skipped (ES-11).
    """

    occurred_at: datetime
    success: bool
    similarity: float = 1.0
    status: str = "VALID"


@dataclass(frozen=True)
class EstimatorParams:
    alpha0: float
    beta0: float
    half_life_days: float
    level: float

    @classmethod
    def from_config(cls, section: Mapping[str, Any]) -> "EstimatorParams":
        """`section` is trust_estimation_alg1 of engine.json."""
        return cls(
            alpha0=float(section["prior"]["alpha_0"]),
            beta0=float(section["prior"]["beta_0"]),
            half_life_days=float(section["recency_decay"]["half_life_days"]),
            level=float(section["credible_interval"]["confidence_level"]),
        )


@dataclass(frozen=True)
class TrustEstimate:
    alpha: float
    beta: float
    mean: float
    lower_90: float
    upper_90: float
    n_eff: float
    n_raw: int


def recency_weight(age_days: float, half_life_days: float) -> float:
    """2^(-age / half-life): 1.0 today, 0.5 after one half-life."""
    if half_life_days <= 0:
        raise ValueError("half-life must be positive")
    if age_days < 0:
        raise ValueError("an outcome cannot be in the future")
    return float(2.0 ** (-age_days / half_life_days))


def credible_interval(alpha: float, beta: float, level: float) -> tuple[float, float]:
    """Equal-tailed interval: the (1 - level)/2 and (1 + level)/2 quantiles of Beta(alpha, beta)."""
    tail = (1.0 - level) / 2.0
    lo = float(beta_distribution.ppf(tail, alpha, beta))
    hi = float(beta_distribution.ppf(1.0 - tail, alpha, beta))
    return lo, hi


def estimate(
    outcomes: Iterable[WeightedOutcome], params: EstimatorParams, as_of: datetime
) -> TrustEstimate:
    """Posterior for one subject, role and metric, as seen at `as_of` (timezone-aware)."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    alpha, beta, n_eff, n_raw = params.alpha0, params.beta0, 0.0, 0
    for o in outcomes:
        if o.status != "VALID":
            continue
        if o.occurred_at.tzinfo is None:
            raise ValueError("outcome times must be timezone-aware")
        if not 0.0 < o.similarity <= 1.0:
            raise ValueError("similarity must be in (0, 1]")
        age = (as_of - o.occurred_at).total_seconds() / 86400.0
        w = recency_weight(age, params.half_life_days) * o.similarity
        if o.success:
            alpha += w
        else:
            beta += w
        n_eff += w
        n_raw += 1
    lo, hi = credible_interval(alpha, beta, params.level)
    return TrustEstimate(alpha, beta, alpha / (alpha + beta), lo, hi, n_eff, n_raw)
