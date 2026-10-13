"""Write verified outcomes from closing events (FR-B-15; rules in domain/assurance/estimation/outcomes).

`record_outcomes` reads one `transaction_closed` or `dispute_resolved` event, gathers the facts the
rules need (return time against the due date, the stage and reason of the dispute, the moderator's
finding), and inserts one row per subject and metric. It is idempotent: the unique constraint
(source_event_id, subject_id, metric) makes a second call insert nothing, so the catch-up
`record_pending_outcomes` (over the view `v_pending_outcomes`) is always safe to run.
"""

from typing import Any

from sqlalchemy import Connection, text

from app.domain.assurance.estimation.outcomes import (
    ClosedLoan,
    OutcomeRecord,
    ResolvedDispute,
    outcomes_for_closed_loan,
    outcomes_for_resolved_dispute,
)


class MissingFinding(Exception):
    """A resolved dispute whose moderator decision does not say who was at fault."""


def _event(conn: Connection, event_id: int) -> dict[str, Any] | None:
    row = (
        conn.execute(
            text(
                "SELECT event_id, stream_id, stream_seq, event_type::text AS event_type, occurred_at, "
                "payload, evidence_refs FROM lifecycle_event WHERE event_id = :id"
            ),
            {"id": event_id},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


def _last_before(
    conn: Connection, stream_id: Any, seq: int, event_type: str
) -> dict[str, Any] | None:
    row = (
        conn.execute(
            text(
                "SELECT stream_seq, occurred_at, previous_state::text AS previous_state, payload "
                "FROM lifecycle_event WHERE stream_id = :s AND stream_seq < :seq "
                "AND event_type = CAST(:t AS event_type) ORDER BY stream_seq DESC LIMIT 1"
            ),
            {"s": stream_id, "seq": seq, "t": event_type},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


def outcomes_for_event(conn: Connection, event_id: int) -> list[OutcomeRecord]:
    """The outcome rows one closing event should produce (empty for any other event)."""
    e = _event(conn, event_id)
    if e is None:
        return []
    if e["event_type"] == "transaction_closed":
        return outcomes_for_closed_loan(
            ClosedLoan(returned_on_time=e["payload"].get("outcome") == "on_time")
        )
    if e["event_type"] != "dispute_resolved":
        return []
    opened = _last_before(conn, e["stream_id"], e["stream_seq"], "dispute_opened")
    if opened is None:
        raise MissingFinding(f"event {event_id}: dispute_resolved without dispute_opened")
    decision_id = (e["evidence_refs"] or {}).get("decision_id")
    at_fault = conn.execute(
        text("SELECT resolved_outcome ->> 'at_fault' FROM moderator_decision WHERE id::text = :d"),
        {"d": decision_id},
    ).scalar_one_or_none()
    if at_fault is None:
        raise MissingFinding(f"event {event_id}: the decision does not record who was at fault")
    on_time: bool | None = None
    if opened["previous_state"] == "RETURN_INITIATED":
        ri = _last_before(conn, e["stream_id"], opened["stream_seq"], "return_initiated")
        due = conn.execute(
            text("SELECT upper(requested_period) FROM borrowing_transaction WHERE id = :t"),
            {"t": e["stream_id"]},
        ).scalar_one()
        on_time = ri is not None and ri["occurred_at"] <= due
    return outcomes_for_resolved_dispute(
        ResolvedDispute(
            stage=opened["previous_state"],
            reason=(opened["payload"] or {}).get("reason", ""),
            at_fault=at_fault,
            returned_on_time=on_time,
        )
    )


def record_outcomes(conn: Connection, event_id: int) -> int:
    """Insert the outcomes of one closing event; returns how many rows were new."""
    records = outcomes_for_event(conn, event_id)
    if not records:
        return 0
    e = _event(conn, event_id)
    if e is None:  # cannot happen: outcomes_for_event found the event a moment ago
        return 0
    inserted = 0
    for r in records:
        inserted += conn.execute(
            text(
                "INSERT INTO outcome (transaction_id, source_event_id, subject_id, observer_id, "
                "subject_role, metric, success, occurred_at, category_id, value_band, loan_duration) "
                "SELECT t.id, :eid, "
                "CASE CAST(:role AS party_role) WHEN 'BORROWER' THEN t.borrower_id ELSE t.lender_id END, "
                "CASE CAST(:role AS party_role) WHEN 'BORROWER' THEN t.lender_id ELSE t.borrower_id END, "
                "CAST(:role AS party_role), CAST(:metric AS outcome_metric), :ok, :at, "
                "i.category_id, i.value_band, upper(t.requested_period) - lower(t.requested_period) "
                "FROM borrowing_transaction t JOIN item i ON i.id = t.item_id WHERE t.id = :txn "
                "ON CONFLICT (source_event_id, subject_id, metric) DO NOTHING"
            ),
            {
                "eid": event_id,
                "role": r.subject_role,
                "metric": r.metric,
                "ok": r.success,
                "at": e["occurred_at"],
                "txn": e["stream_id"],
            },
        ).rowcount
    return inserted


def record_pending_outcomes(conn: Connection) -> int:
    """Catch up every closing event that has no outcomes yet (view v_pending_outcomes)."""
    ids = (
        conn.execute(text("SELECT event_id FROM v_pending_outcomes ORDER BY event_id"))
        .scalars()
        .all()
    )
    return sum(record_outcomes(conn, int(i)) for i in ids)
