"""PostgreSQL adapter for CaseService (Module 9, plan item M2; sequence (g))."""

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, Engine, text

_CASE = (
    "SELECT ec.id, ec.transaction_id, ec.status::text AS status, ec.info_deadline, "
    "ec.trigger_type::text AS trigger_type, ec.raised_by, t.borrower_id, t.lender_id, "
    "i.community_id FROM escalation_case ec "
    "JOIN borrowing_transaction t ON t.id = ec.transaction_id JOIN item i ON i.id = t.item_id "
)


class PostgresCaseStore:
    def __init__(self, conn: Connection, audit_engine: Engine | None = None) -> None:
        self.conn = conn
        self.audit_engine = audit_engine

    def case_for_update(self, case_id: UUID) -> dict[str, Any] | None:
        row = (
            self.conn.execute(text(_CASE + "WHERE ec.id = :c FOR UPDATE OF ec"), {"c": case_id})
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def is_moderator(self, user_id: UUID, community_id: UUID) -> bool:
        return (
            self.conn.execute(
                text(
                    "SELECT 1 FROM membership WHERE user_id = :u AND community_id = :c "
                    "AND role = 'MODERATOR' AND status = 'APPROVED'"
                ),
                {"u": user_id, "c": community_id},
            ).first()
            is not None
        )

    def set_awaiting(self, case_id: UUID, deadline: datetime) -> None:
        self.conn.execute(
            text(
                "UPDATE escalation_case SET status = 'AWAITING_INFORMATION', info_deadline = :d "
                "WHERE id = :c AND status = 'OPEN'"
            ),
            {"c": case_id, "d": deadline},
        )

    def reopen(self, case_id: UUID) -> None:
        self.conn.execute(
            text(
                "UPDATE escalation_case SET status = 'OPEN' "
                "WHERE id = :c AND status = 'AWAITING_INFORMATION'"
            ),
            {"c": case_id},
        )

    def insert_statement(self, case_id: UUID, author_id: UUID, role: str, text_: str) -> UUID:
        value = self.conn.execute(
            text(
                "INSERT INTO case_statement (case_id, author_id, author_role, statement) "
                "VALUES (:c, :a, CAST(:r AS party_role), :s) RETURNING id"
            ),
            {"c": case_id, "a": author_id, "r": role, "s": text_},
        ).scalar_one()
        return UUID(str(value))

    def statements(self, case_id: UUID) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            text(
                "SELECT s.id, s.author_role::text AS author_role, u.display_name AS author_name, "
                "s.statement, s.created_at FROM case_statement s "
                "JOIN app_user u ON u.id = s.author_id WHERE s.case_id = :c "
                "ORDER BY s.created_at, s.id"
            ),
            {"c": case_id},
        ).mappings()
        return [dict(r) for r in rows]

    def overdue_information(self, now: datetime) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            text(
                _CASE + "WHERE ec.status = 'AWAITING_INFORMATION' AND ec.info_deadline <= :now "
                "ORDER BY ec.info_deadline FOR UPDATE OF ec SKIP LOCKED"
            ),
            {"now": now},
        ).mappings()
        return [dict(r) for r in rows]

    def information_request(self, case_id: UUID) -> dict[str, Any] | None:
        value = self.conn.execute(
            text(
                "SELECT new_value FROM audit_log WHERE target_type = 'escalation_case' "
                "AND target_id = :c AND action = 'info_requested' AND outcome = 'SUCCESS' "
                "ORDER BY id DESC LIMIT 1"
            ),
            {"c": str(case_id)},
        ).scalar_one_or_none()
        return dict(value) if value else None

    def moderators_of(self, community_id: UUID) -> list[UUID]:
        return list(
            self.conn.execute(
                text(
                    "SELECT user_id FROM membership WHERE community_id = :c AND role = 'MODERATOR' "
                    "AND status = 'APPROVED' ORDER BY user_id"
                ),
                {"c": community_id},
            ).scalars()
        )

    def admins(self) -> list[UUID]:
        return list(
            self.conn.execute(
                text(
                    "SELECT id FROM app_user WHERE platform_role = 'ADMIN' AND status = 'ACTIVE' "
                    "ORDER BY id"
                )
            ).scalars()
        )

    def audit(
        self,
        *,
        actor_id: UUID | None,
        authorisation: str,
        action: str,
        case_id: UUID,
        new_value: Mapping[str, Any],
    ) -> None:
        self.conn.execute(
            text(
                "INSERT INTO audit_log (actor_id, authorisation, action, target_type, target_id, "
                "new_value, outcome) VALUES (:a, :auth, :act, 'escalation_case', :t, "
                "CAST(:v AS jsonb), 'SUCCESS')"
            ),
            {
                "a": actor_id,
                "auth": authorisation,
                "act": action,
                "t": str(case_id),
                "v": json.dumps(dict(new_value)),
            },
        )

    def audit_rejection(self, *, actor_id: UUID, action: str, case_id: UUID, reason: str) -> None:
        if self.audit_engine is None:
            return
        with self.audit_engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO audit_log (actor_id, authorisation, action, target_type, "
                    "target_id, outcome, reason) VALUES (:a, 'member', :act, 'escalation_case', "
                    ":t, 'REJECTED', :r)"
                ),
                {"a": actor_id, "act": action, "t": str(case_id), "r": reason[:500]},
            )
