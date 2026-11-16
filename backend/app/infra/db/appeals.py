"""PostgreSQL adapter for AppealService (Module 9, plan item M3; sequence (h))."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.infra.db import trust_edges
from app.infra.db.cases import PostgresCaseStore

_DECISION = (
    "SELECT d.id, d.case_id, d.decided_by, d.kind::text AS kind, d.reason, d.decided_at, "
    "d.reverses_decision_id FROM moderator_decision d "
)


class PostgresAppealStore(PostgresCaseStore):
    """Reuses the case store (case lookup, moderators, admins, audit) and adds decisions."""

    def _one(self, sql: str, **params: Any) -> dict[str, Any] | None:
        row = self.conn.execute(text(sql), params).mappings().first()
        return dict(row) if row else None

    def decision(self, decision_id: UUID) -> dict[str, Any] | None:
        return self._one(_DECISION + "WHERE d.id = :d", d=decision_id)

    def appealed_decision(self, case_id: UUID) -> dict[str, Any] | None:
        return self._one(
            _DECISION + "WHERE d.case_id = :c AND d.kind IN ('CLEARED', 'SAFEGUARDS_IMPOSED', "
            "'RESTRICTED', 'DISPUTE_RESOLVED') ORDER BY d.decided_at DESC, d.id LIMIT 1",
            c=case_id,
        )

    def latest_decision(self, case_id: UUID) -> dict[str, Any] | None:
        return self._one(
            _DECISION + "WHERE d.case_id = :c ORDER BY d.decided_at DESC, d.id LIMIT 1", c=case_id
        )

    def appeal_count(self, case_id: UUID) -> int:
        return int(
            self.conn.execute(
                text(
                    "SELECT count(*) FROM audit_log WHERE target_type = 'escalation_case' "
                    "AND target_id = :c AND action = 'appeal_filed' AND outcome = 'SUCCESS'"
                ),
                {"c": str(case_id)},
            ).scalar_one()
        )

    def set_status(self, case_id: UUID, status: str, assigned_to: UUID | None = None) -> None:
        self.conn.execute(
            text(
                "UPDATE escalation_case SET status = CAST(:s AS case_status), "
                "assigned_to = coalesce(:a, assigned_to) WHERE id = :c"
            ),
            {"s": status, "a": assigned_to, "c": case_id},
        )

    def insert_decision(
        self,
        case_id: UUID,
        decided_by: UUID,
        role: str,
        kind: str,
        reason: str,
        reverses: UUID | None,
    ) -> UUID:
        value = self.conn.execute(
            text(
                "INSERT INTO moderator_decision (case_id, decided_by, decider_role, kind, reason, "
                "reverses_decision_id) VALUES (:c, :d, CAST(:r AS actor_role), "
                "CAST(:k AS decision_kind), :reason, :rev) RETURNING id"
            ),
            {
                "c": case_id,
                "d": decided_by,
                "r": role,
                "k": kind,
                "reason": reason,
                "rev": reverses,
            },
        ).scalar_one()
        return UUID(str(value))

    def flag_outcomes(self, decision_id: UUID, flagged_by: UUID) -> int:
        """Outcomes written by the event that applied `decision_id` become
        FLAGGED_FOR_REEVALUATION, with the overturning decision as the reason (ES-11)."""
        rows = self.conn.execute(
            text(
                "UPDATE outcome SET status = 'FLAGGED_FOR_REEVALUATION', flagged_by_decision_id = :f "
                "WHERE status = 'VALID' AND source_event_id IN (SELECT event_id FROM lifecycle_event "
                " WHERE evidence_refs ->> 'decision_id' = :d) RETURNING id"
            ),
            {"f": flagged_by, "d": str(decision_id)},
        ).all()
        return len(rows)

    def refresh_trust_edges(self, transaction_id: UUID) -> int:
        b, lnd = self.conn.execute(
            text(
                "SELECT borrower_id::text, lender_id::text FROM borrowing_transaction WHERE id = :t"
            ),
            {"t": transaction_id},
        ).one()
        return trust_edges.refresh_trust_edges(self.conn, datetime.now(UTC), [(lnd, b), (b, lnd)])
