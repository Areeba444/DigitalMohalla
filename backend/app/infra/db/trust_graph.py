"""Read the trust graph from PostgreSQL for the k-hop search (FR-T-04; rules in domain/assurance/indirect/khop).

The graph for one role and metric is small at neighbourhood scale, so it is read whole; the search
itself is bounded by k (see the k sweep, test suite 8, for latency at larger scale).
"""

from sqlalchemy import Connection, text

from app.domain.assurance.indirect.khop import Graph, IndirectResult, KHopParams, indirect_trust


def load_graph(conn: Connection, role: str, metric: str) -> dict[str, dict[str, float]]:
    rows = conn.execute(
        text(
            "SELECT source_id::text, target_id::text, weight FROM trust_edge "
            "WHERE role = CAST(:r AS party_role) AND metric = CAST(:m AS outcome_metric)"
        ),
        {"r": role, "m": metric},
    ).all()
    graph: dict[str, dict[str, float]] = {}
    for src, dst, w in rows:
        graph.setdefault(src, {})[dst] = float(w)
    return graph


def indirect_for(
    conn: Connection,
    lender_id: str,
    borrower_id: str,
    params: KHopParams,
    target_mean: float | None,
    role: str = "BORROWER",
    metric: str = "ON_TIME_RETURN",
    graph: Graph | None = None,
) -> IndirectResult:
    """Indirect evidence the lender can draw on about the borrower, through community paths."""
    g = graph if graph is not None else load_graph(conn, role, metric)
    return indirect_trust(g, lender_id, borrower_id, params, target_mean)
