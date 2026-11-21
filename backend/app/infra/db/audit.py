"""PostgreSQL reads for the audit view (UC-I6; FR-M-05; plan item M5).

Lifecycle events and audit_log rows are read together (the schema's v_audit_trail idea), newest
first, each with its own hash-chain check. A row is valid when its stored hash equals the hash
recomputed from its content and its predecessor, and its prev_hash is really the previous row's hash.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

from app.domain.audit.view import AuditRow


@dataclass(frozen=True)
class AuditFilter:
    actor: UUID | None = None
    target: str | None = None  # a transaction, case or membership id
    action: str | None = None
    outcome: str | None = None  # SUCCESS or REJECTED
    since: datetime | None = None
    until: datetime | None = None


_SQL = """
SELECT * FROM (
  SELECT 'event' AS source, e.event_id AS id, e.occurred_at, e.actor_id, e.authorisation,
         e.event_type::text AS action, 'borrowing_transaction' AS target_type,
         e.stream_id::text AS target_id, to_jsonb(e.previous_state) AS previous_value,
         to_jsonb(e.new_state) AS new_value, e.evidence_refs, 'SUCCESS' AS outcome,
         NULL::text AS reason,
         (e.row_hash = event_hash(e.prev_hash, e) AND e.prev_hash IS NOT DISTINCT FROM
            (SELECT p.row_hash FROM lifecycle_event p
              WHERE p.stream_id = e.stream_id AND p.stream_seq < e.stream_seq
              ORDER BY p.stream_seq DESC LIMIT 1)) AS hash_valid
    FROM lifecycle_event e
  UNION ALL
  SELECT 'audit', a.id, a.occurred_at, a.actor_id, a.authorisation, a.action, a.target_type,
         a.target_id, a.previous_value, a.new_value, a.evidence_refs, a.outcome, a.reason,
         (a.row_hash = audit_hash(a.prev_hash, a) AND a.prev_hash IS NOT DISTINCT FROM
            (SELECT p.row_hash FROM audit_log p WHERE p.id < a.id ORDER BY p.id DESC LIMIT 1))
    FROM audit_log a
) t
WHERE (CAST(:actor AS uuid) IS NULL OR t.actor_id = CAST(:actor AS uuid))
  AND (CAST(:target AS text) IS NULL OR t.target_id = CAST(:target AS text)
       OR t.evidence_refs::text LIKE '%' || CAST(:target AS text) || '%')
  AND (CAST(:action AS text) IS NULL OR t.action = CAST(:action AS text))
  AND (CAST(:outcome AS text) IS NULL OR t.outcome = CAST(:outcome AS text))
  AND (CAST(:since AS timestamptz) IS NULL OR t.occurred_at >= CAST(:since AS timestamptz))
  AND (CAST(:until AS timestamptz) IS NULL OR t.occurred_at < CAST(:until AS timestamptz))
ORDER BY t.occurred_at DESC, t.id DESC
LIMIT :limit OFFSET :offset
"""


def search(conn: Connection, f: AuditFilter, limit: int, offset: int) -> list[AuditRow]:
    rows = conn.execute(
        text(_SQL),
        {
            "actor": f.actor,
            "target": f.target,
            "action": f.action,
            "outcome": f.outcome,
            "since": f.since,
            "until": f.until,
            "limit": limit,
            "offset": offset,
        },
    ).mappings()
    return [
        AuditRow(
            source=r["source"],
            id=int(r["id"]),
            occurred_at=r["occurred_at"].isoformat(),
            actor_id=str(r["actor_id"]) if r["actor_id"] else None,
            authorisation=r["authorisation"],
            action=r["action"],
            target_type=r["target_type"],
            target_id=r["target_id"],
            previous_value=r["previous_value"],
            new_value=r["new_value"],
            evidence_refs=r["evidence_refs"],
            outcome=r["outcome"],
            reason=r["reason"],
            hash_valid=bool(r["hash_valid"]),
        )
        for r in rows
    ]


def get_entry(conn: Connection, source: str, entry_id: int) -> AuditRow | None:
    """One entry by (source, id), found through the same query so its hash check is included."""
    sql = _SQL.replace(
        "WHERE (CAST(:actor",
        "WHERE t.source = CAST(:src AS text) AND t.id = CAST(:eid AS bigint) AND (CAST(:actor",
    )
    row = (
        conn.execute(
            text(sql),
            {
                "actor": None,
                "target": None,
                "action": None,
                "outcome": None,
                "since": None,
                "until": None,
                "limit": 1,
                "offset": 0,
                "src": source,
                "eid": entry_id,
            },
        )
        .mappings()
        .first()
    )
    if row is None:
        return None
    return AuditRow(
        source=row["source"],
        id=int(row["id"]),
        occurred_at=row["occurred_at"].isoformat(),
        actor_id=str(row["actor_id"]) if row["actor_id"] else None,
        authorisation=row["authorisation"],
        action=row["action"],
        target_type=row["target_type"],
        target_id=row["target_id"],
        previous_value=row["previous_value"],
        new_value=row["new_value"],
        evidence_refs=row["evidence_refs"],
        outcome=row["outcome"],
        reason=row["reason"],
        hash_valid=bool(row["hash_valid"]),
    )


def log_view(
    conn: Connection, actor_id: UUID, action: str, target_id: str, detail: dict[str, Any]
) -> None:
    """The view (or an unmasking) is itself an audit entry (UC-I6 step 4, ext 3d)."""
    conn.execute(
        text(
            "INSERT INTO audit_log (actor_id, authorisation, action, target_type, target_id, "
            "new_value, outcome) VALUES (:a, 'role:admin', :act, 'audit_log', :t, "
            "CAST(:v AS jsonb), 'SUCCESS')"
        ),
        {"a": actor_id, "act": action, "t": target_id, "v": json.dumps(detail)},
    )


def moderator_member_pairs(conn: Connection, since: datetime) -> list[tuple[str, str]]:
    """(moderator, member) per decision since `since`: the borrower and the lender of the loan."""
    rows = conn.execute(
        text(
            "SELECT d.decided_by::text, m::text FROM moderator_decision d "
            "JOIN escalation_case c ON c.id = d.case_id "
            "JOIN borrowing_transaction t ON t.id = c.transaction_id "
            "CROSS JOIN LATERAL (VALUES (t.borrower_id), (t.lender_id)) AS p(m) "
            "WHERE d.decided_at >= :since"
        ),
        {"since": since},
    ).all()
    return [(a, b) for a, b in rows]
