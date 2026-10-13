"""PostgreSQL adapters for the lifecycle ports (PostgresEventStore, audit log).

`PostgresLifecycleStore` wraps one open connection, so a whole command runs in one DB transaction
(the caller commits or rolls back). `PostgresAuditLog` writes in its own short transaction, so a
rejected command is still recorded after the command's transaction rolls back (suite 1).
"""

import json
from contextlib import AbstractContextManager
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, Engine, text

from app.domain.lifecycle.ports import AssessmentResult, TransactionView
from app.infra.db import outcomes
from app.infra.eventstore import store


class PostgresLifecycleStore:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    # event store ----------------------------------------------------------------------------
    def create_request(
        self, *, item_id: UUID, borrower_id: UUID, lender_id: UUID, period: str, message: str | None
    ) -> UUID:
        return store.create_request(
            self.conn,
            item_id=item_id,
            borrower_id=borrower_id,
            lender_id=lender_id,
            period=period,
            message=message,
        )

    def append(
        self,
        stream_id: UUID,
        event_type: str,
        new_state: str,
        *,
        actor_id: UUID | None,
        authorisation: str,
        payload: dict[str, Any] | None = None,
        evidence_refs: dict[str, Any] | None = None,
        config_version: str | None = None,
    ) -> int:
        return store.append(
            self.conn,
            stream_id,
            event_type,
            new_state,
            actor_id=actor_id,
            authorisation=authorisation,
            payload=payload,
            evidence_refs=evidence_refs,
            config_version=config_version,
        )

    def savepoint(self) -> AbstractContextManager[Any]:
        return self.conn.begin_nested()

    def last_event(self, transaction_id: UUID, event_type: str) -> dict[str, Any] | None:
        row = (
            self.conn.execute(
                text(
                    "SELECT event_id, stream_seq, occurred_at FROM lifecycle_event "
                    "WHERE stream_id = :id AND event_type = CAST(:t AS event_type) "
                    "ORDER BY stream_seq DESC LIMIT 1"
                ),
                {"id": transaction_id, "t": event_type},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    # reads ------------------------------------------------------------------------------------
    def view(self, transaction_id: UUID) -> TransactionView:
        row = (
            self.conn.execute(
                text(
                    "SELECT t.id, t.item_id, t.borrower_id, t.lender_id, i.community_id, "
                    "i.value_band::text AS value_band, i.category_id, t.current_state::text AS state, "
                    "t.stream_version AS version, t.hold_reason::text AS hold_reason, t.due_at "
                    "FROM borrowing_transaction t JOIN item i ON i.id = t.item_id WHERE t.id = :id"
                ),
                {"id": transaction_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            raise store.StreamNotFound(str(transaction_id))
        return TransactionView(**row)

    def item(self, item_id: UUID) -> dict[str, Any]:
        row = (
            self.conn.execute(
                text(
                    "SELECT id, owner_id, community_id, status::text AS status, "
                    "value_band::text AS value_band, deposit_amount, title FROM item WHERE id = :id"
                ),
                {"id": item_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            raise store.StreamNotFound(f"item {item_id}")
        return dict(row)

    def locality_outcome(self, user_id: UUID, community_id: UUID) -> str:
        """The member's stored coarse result (A11); no coordinates are read here (NFR-PR-01)."""
        return self.conn.execute(
            text("SELECT locality_outcome_for(:u, :c)::text"), {"u": user_id, "c": community_id}
        ).scalar_one()

    def overlapping_pending(self, transaction_id: UUID) -> list[UUID]:
        rows = self.conn.execute(
            text(
                "SELECT o.id FROM borrowing_transaction t JOIN borrowing_transaction o "
                "ON o.item_id = t.item_id AND o.id <> t.id "
                "AND o.requested_period && t.requested_period "
                "WHERE t.id = :id AND o.current_state IS NOT NULL AND is_pending(o.current_state)"
            ),
            {"id": transaction_id},
        )
        return [r[0] for r in rows]

    def latest_assessment(self, transaction_id: UUID) -> dict[str, Any] | None:
        row = (
            self.conn.execute(
                text(
                    "SELECT id, generated_at, config_version, assurance_state::text AS assurance_state, "
                    "policy_decision::text AS policy_decision, rule_fired, posterior_mean, ci90_low, "
                    "ci90_high, effective_evidence, manipulation_risk, manipulation_level, safeguards, "
                    "explanation FROM assessment WHERE transaction_id = :id "
                    "ORDER BY generated_at DESC LIMIT 1"
                ),
                {"id": transaction_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def list_for_lender(self, lender_id: UUID, state: str | None) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            text(
                "SELECT t.id, t.item_id, i.title, t.borrower_id, t.current_state::text AS state, "
                "t.requested_period::text AS requested_period, t.created_at, "
                "(SELECT a.assurance_state::text FROM assessment a WHERE a.transaction_id = t.id "
                " ORDER BY a.generated_at DESC LIMIT 1) AS assurance_state "
                "FROM borrowing_transaction t JOIN item i ON i.id = t.item_id "
                "WHERE t.lender_id = :l AND (CAST(:s AS text) IS NULL OR t.current_state::text = :s) "
                "ORDER BY t.created_at DESC"
            ),
            {"l": lender_id, "s": state},
        ).mappings()
        return [dict(r) for r in rows]

    def booked_periods(self, item_id: UUID) -> list[str]:
        rows = self.conn.execute(
            text("SELECT period::text FROM v_item_calendar WHERE item_id = :i ORDER BY period"),
            {"i": item_id},
        )
        return [r[0] for r in rows]

    def events(self, transaction_id: UUID) -> list[dict[str, Any]]:
        return store.load_stream(self.conn, transaction_id)

    def list_items_for(self, user_id: UUID) -> list[dict[str, Any]]:
        """Published items in the member's communities, not owned by them (browse, seeded in it. 1)."""
        rows = self.conn.execute(
            text(
                "SELECT i.id, i.title, i.value_band::text AS value_band, i.deposit_amount, "
                "u.display_name AS owner_name FROM item i JOIN app_user u ON u.id = i.owner_id "
                "WHERE i.status = 'PUBLISHED' AND i.owner_id <> :u AND EXISTS ("
                " SELECT 1 FROM membership m WHERE m.user_id = :u AND m.community_id = i.community_id "
                " AND m.status = 'APPROVED') ORDER BY i.title"
            ),
            {"u": user_id},
        ).mappings()
        return [dict(r) for r in rows]

    def list_for_member(self, user_id: UUID) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            text(
                "SELECT t.id, t.item_id, i.title, t.current_state::text AS state, "
                "t.hold_reason::text AS hold_reason, t.requested_period::text AS requested_period, "
                "CASE WHEN t.borrower_id = :u THEN 'BORROWER' ELSE 'LENDER' END AS your_role, "
                "CASE WHEN t.borrower_id = :u THEN l.display_name ELSE b.display_name END "
                " AS counterpart_name, t.created_at, "
                "(SELECT a.assurance_state::text FROM assessment a WHERE a.transaction_id = t.id "
                " ORDER BY a.generated_at DESC LIMIT 1) AS assurance_state "
                "FROM borrowing_transaction t JOIN item i ON i.id = t.item_id "
                "JOIN app_user b ON b.id = t.borrower_id JOIN app_user l ON l.id = t.lender_id "
                "WHERE t.current_state IS NOT NULL AND :u IN (t.borrower_id, t.lender_id) "
                "ORDER BY t.created_at DESC"
            ),
            {"u": user_id},
        ).mappings()
        return [dict(r) for r in rows]

    def details(self, transaction_id: UUID) -> dict[str, Any]:
        row = (
            self.conn.execute(
                text(
                    "SELECT i.title AS item_title, i.deposit_amount, b.display_name AS borrower_name, "
                    "l.display_name AS lender_name, t.requested_period::text AS requested_period, "
                    "t.message, t.created_at FROM borrowing_transaction t "
                    "JOIN item i ON i.id = t.item_id JOIN app_user b ON b.id = t.borrower_id "
                    "JOIN app_user l ON l.id = t.lender_id WHERE t.id = :id"
                ),
                {"id": transaction_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            raise store.StreamNotFound(str(transaction_id))
        return dict(row)

    def latest_reports(self, transaction_id: UUID) -> dict[tuple[str, str], dict[str, Any]]:
        rows = self.conn.execute(
            text(
                "SELECT DISTINCT ON (phase, reporter_role) phase::text AS phase, "
                "reporter_role::text AS reporter_role, condition_agreed, checklist, "
                "deposit_received, notes, created_at FROM condition_report "
                "WHERE transaction_id = :id ORDER BY phase, reporter_role, created_at DESC, id DESC"
            ),
            {"id": transaction_id},
        ).mappings()
        return {(r["phase"], r["reporter_role"]): dict(r) for r in rows}

    # writes -----------------------------------------------------------------------------------
    def insert_assessment(self, transaction_id: UUID, result: AssessmentResult) -> UUID:
        return self.conn.execute(
            text(
                "INSERT INTO assessment (transaction_id, config_version, assurance_state, "
                "policy_decision, hold_reason, posterior_mean, ci90_low, ci90_high, "
                "effective_evidence, direct_evidence, indirect_evidence, manipulation_risk, "
                "manipulation_level, manipulation_corroborated, manipulation_signals, safeguards, "
                "explanation, rule_fired) VALUES (:t, :cv, CAST(:st AS assurance_state), "
                "CAST(:pd AS policy_decision), CAST(:hr AS hold_reason), :pm, :lo, :hi, :ee, "
                "CAST(:de AS jsonb), CAST(:ie AS jsonb), :mr, :ml, :mc, CAST(:ms AS jsonb), "
                "CAST(:sg AS jsonb), :ex, :rf) RETURNING id"
            ),
            {
                "t": transaction_id,
                "cv": result.config_version,
                "st": result.assurance_state,
                "pd": result.policy_decision,
                "hr": result.hold_reason,
                "pm": result.posterior_mean,
                "lo": result.ci90_low,
                "hi": result.ci90_high,
                "ee": result.effective_evidence,
                "de": json.dumps(result.direct_evidence),
                "ie": json.dumps(result.indirect_evidence),
                "mr": result.manipulation_risk,
                "ml": result.manipulation_level,
                "mc": result.manipulation_corroborated,
                "ms": json.dumps(result.manipulation_signals),
                "sg": json.dumps(result.safeguards),
                "ex": result.explanation,
                "rf": result.rule_fired,
            },
        ).scalar_one()

    def insert_condition_report(
        self,
        transaction_id: UUID,
        *,
        phase: str,
        reporter_id: UUID,
        reporter_role: str,
        condition_agreed: bool,
        checklist: dict[str, Any],
        deposit_received: bool | None,
        notes: str | None,
    ) -> UUID:
        return self.conn.execute(
            text(
                "INSERT INTO condition_report (transaction_id, phase, reporter_id, reporter_role, "
                "checklist, condition_agreed, deposit_received, notes) VALUES (:t, "
                "CAST(:ph AS condition_phase), :r, CAST(:rr AS party_role), CAST(:cl AS jsonb), "
                ":ag, :dep, :n) RETURNING id"
            ),
            {
                "t": transaction_id,
                "ph": phase,
                "r": reporter_id,
                "rr": reporter_role,
                "cl": json.dumps(checklist),
                "ag": condition_agreed,
                "dep": deposit_received,
                "n": notes,
            },
        ).scalar_one()

    # evidence -----------------------------------------------------------------------------------
    def record_outcomes(self, event_id: int) -> int:
        return outcomes.record_outcomes(self.conn, event_id)


class PostgresAuditLog:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def record_rejection(
        self,
        *,
        actor_id: UUID | None,
        authorisation: str,
        action: str,
        transaction_id: UUID,
        reason: str,
    ) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO audit_log (actor_id, authorisation, action, target_type, "
                    "target_id, outcome, reason) VALUES (:a, :auth, :act, 'borrowing_transaction', "
                    ":tid, 'REJECTED', :reason)"
                ),
                {
                    "a": actor_id,
                    "auth": authorisation,
                    "act": action,
                    "tid": str(transaction_id),
                    "reason": reason[:500],
                },
            )
