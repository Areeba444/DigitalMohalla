"""Trust-edge projection in PostgreSQL (ADR-0006; rules in domain/assurance/indirect/edges).

`refresh_trust_edges` recomputes edges from the VALID outcomes, as of a given time, either for
everything or for a set of (observer, subject) pairs. The rows of a refreshed pair are replaced in
one transaction, so an edge whose outcomes were all flagged disappears. `updated_at` is the time
the weight was computed: weights decay with age, so a later refresh gives a slightly lower weight
(a scheduled refresh for that drift comes with the scheduler in iteration 2, ADR-0006 question 5).
"""

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import Connection, text

from app.config.engine_config import load_engine_config
from app.domain.assurance.estimation.posterior import EstimatorParams
from app.domain.assurance.indirect.edges import ConfirmedOutcome, build_edges

_OUTCOMES = (
    "SELECT observer_id::text, subject_id::text, subject_role::text, metric::text, success, "
    "occurred_at, status::text FROM outcome"
)


def refresh_trust_edges(
    conn: Connection, as_of: datetime, pairs: Iterable[tuple[str, str]] | None = None
) -> int:
    """Recompute edges (all of them, or only the given observer -> subject pairs); returns rows written."""
    params = EstimatorParams.from_config(load_engine_config().section("trust_estimation_alg1"))
    if pairs is None:
        rows = conn.execute(text(_OUTCOMES)).all()
        conn.execute(text("DELETE FROM trust_edge"))
    else:
        wanted = sorted(set(pairs))
        if not wanted:
            return 0
        rows = []
        for src, dst in wanted:
            rows += conn.execute(
                text(
                    _OUTCOMES
                    + " WHERE observer_id = CAST(:s AS uuid) AND subject_id = CAST(:d AS uuid)"
                ),
                {"s": src, "d": dst},
            ).all()
            conn.execute(
                text(
                    "DELETE FROM trust_edge WHERE source_id = CAST(:s AS uuid) AND target_id = CAST(:d AS uuid)"
                ),
                {"s": src, "d": dst},
            )
    edges = build_edges((ConfirmedOutcome(*r) for r in rows), params, as_of)
    for e in edges:
        conn.execute(
            text(
                "INSERT INTO trust_edge (source_id, target_id, role, metric, weight, evidence_count, updated_at) "
                "VALUES (CAST(:s AS uuid), CAST(:t AS uuid), CAST(:r AS party_role), "
                "CAST(:m AS outcome_metric), :w, :n, :at)"
            ),
            {
                "s": e.source_id,
                "t": e.target_id,
                "r": e.role,
                "m": e.metric,
                "w": e.weight,
                "n": e.evidence_count,
                "at": as_of,
            },
        )
    return len(edges)
