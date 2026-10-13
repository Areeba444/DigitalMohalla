"""Trust-edge weights from verified outcomes (ADR-0006, accepted as experimental: team decision D10).

Plain-language note: an edge A -> B (for one role and metric) says "A has confirmed outcomes about
B". Its weight is the recency-weighted Beta posterior mean of those outcomes, computed with the same
estimator and configuration as direct evidence (Algorithm 1): (1 + s) / (2 + s + f), where s and f
are the recency-weighted successes and failures. One success gives 0.667, five give about 0.857,
one failure 0.333. No similarity weighting on edges: path decay in the k-hop search discounts them
instead. An edge exists only when at least one VALID outcome supports it; flagged ones do not count.
Pure functions, no I/O (A8 layer rules).
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from app.domain.assurance.estimation.posterior import EstimatorParams, WeightedOutcome, estimate


@dataclass(frozen=True)
class ConfirmedOutcome:
    """One outcome row as the edge projection needs it: who observed whom, and how it went."""

    observer_id: str
    subject_id: str
    subject_role: str
    metric: str
    success: bool
    occurred_at: datetime
    status: str = "VALID"


@dataclass(frozen=True)
class TrustEdge:
    source_id: str
    target_id: str
    role: str
    metric: str
    weight: float  # rounded to 3 decimals, as stored (numeric(4, 3))
    evidence_count: int


def edge_weight(
    outcomes: Iterable[WeightedOutcome], params: EstimatorParams, as_of: datetime
) -> float:
    """Posterior mean of what the source confirmed about the target (similarity is not applied)."""
    plain = [WeightedOutcome(o.occurred_at, o.success, 1.0, o.status) for o in outcomes]
    return estimate(plain, params, as_of).mean


def build_edges(
    outcomes: Iterable[ConfirmedOutcome], params: EstimatorParams, as_of: datetime
) -> list[TrustEdge]:
    """All edges supported by at least one VALID outcome, sorted by key."""
    groups: dict[tuple[str, str, str, str], list[WeightedOutcome]] = {}
    for o in outcomes:
        if o.status != "VALID":
            continue
        if o.observer_id == o.subject_id:
            raise ValueError("an outcome cannot be observed by its own subject")
        key = (o.observer_id, o.subject_id, o.subject_role, o.metric)
        groups.setdefault(key, []).append(WeightedOutcome(o.occurred_at, o.success))
    return [
        TrustEdge(src, tgt, role, metric, round(edge_weight(ws, params, as_of), 3), len(ws))
        for (src, tgt, role, metric), ws in sorted(groups.items())
    ]
