"""PostgreSQL reads for evidence factors and the population baseline (A5, A7, A10)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Connection, text

from app.domain.assurance.estimation.factors import OutcomeRow


def outcome_rows(conn: Connection, user_id: UUID) -> list[OutcomeRow]:
    """Every stored outcome of one member, in both roles."""
    rows = conn.execute(
        text(
            "SELECT subject_role::text, metric::text, success, occurred_at, status::text "
            "FROM outcome WHERE subject_id = :u"
        ),
        {"u": user_id},
    ).all()
    return [OutcomeRow(r[0], r[1], bool(r[2]), r[3], r[4]) for r in rows]


def lender_rows(conn: Connection, owner_ids: list[UUID]) -> dict[UUID, list[OutcomeRow]]:
    """LENDER outcomes of several lenders at once (search results, item details)."""
    out: dict[UUID, list[OutcomeRow]] = {o: [] for o in owner_ids}
    if not owner_ids:
        return out
    rows = conn.execute(
        text(
            "SELECT subject_id, subject_role::text, metric::text, success, occurred_at, status::text "
            "FROM outcome WHERE subject_role = 'LENDER' AND subject_id = ANY(:ids)"
        ),
        {"ids": owner_ids},
    ).all()
    for r in rows:
        out[r[0]].append(OutcomeRow(r[1], r[2], bool(r[3]), r[4], r[5]))
    return out


def baseline_rows(
    conn: Connection, community_id: UUID | None, role: str, metric: str
) -> list[tuple[bool, datetime]]:
    """VALID outcomes of one role and metric across a community's loans (the population baseline).

    With no community, all communities."""
    rows = conn.execute(
        text(
            "SELECT o.success, o.occurred_at FROM outcome o "
            "JOIN borrowing_transaction t ON t.id = o.transaction_id "
            "JOIN item i ON i.id = t.item_id "
            "WHERE o.subject_role = CAST(:role AS party_role) AND o.metric = CAST(:metric AS outcome_metric) "
            "AND o.status = 'VALID' AND (CAST(:c AS uuid) IS NULL OR i.community_id = CAST(:c AS uuid))"
        ),
        {"role": role, "metric": metric, "c": community_id},
    ).all()
    return [(bool(r[0]), r[1]) for r in rows]


def member_communities(conn: Connection, user_id: UUID) -> list[UUID]:
    rows = conn.execute(
        text("SELECT community_id FROM membership WHERE user_id = :u AND status = 'APPROVED'"),
        {"u": user_id},
    ).scalars()
    return list(rows)
