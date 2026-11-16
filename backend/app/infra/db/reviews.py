"""PostgreSQL adapter for ReviewService (Module 5, UC-D1; plan item A3)."""

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

from app.domain.assurance.detection.manipulation import ReviewSnapshot


class PostgresReviewStore:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def loan(self, txn_id: UUID) -> dict[str, Any] | None:
        """The loan's parties, its completion time (the event that made it COMPLETED) and whether
        both parties confirmed the return without disagreeing."""
        row = (
            self.conn.execute(
                text(
                    "SELECT t.current_state::text AS state, t.borrower_id, t.lender_id, "
                    "(SELECT max(e.occurred_at) FROM lifecycle_event e WHERE e.stream_id = t.id "
                    " AND e.new_state = 'COMPLETED') AS completed_at, "
                    "EXISTS (SELECT 1 FROM lifecycle_event e WHERE e.stream_id = t.id "
                    " AND e.event_type = 'return_confirmed') AND NOT EXISTS (SELECT 1 FROM "
                    " condition_report cr WHERE cr.transaction_id = t.id AND cr.phase = 'RETURN' "
                    " AND NOT cr.condition_agreed) AS return_confirmed "
                    "FROM borrowing_transaction t WHERE t.id = :t"
                ),
                {"t": txn_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def review_by(self, txn_id: UUID, reviewer_id: UUID) -> dict[str, Any] | None:
        row = (
            self.conn.execute(
                text(
                    "SELECT id, created_at FROM review WHERE transaction_id = :t "
                    "AND reviewer_id = :r FOR UPDATE"
                ),
                {"t": txn_id, "r": reviewer_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def reviews_received(self, user_id: UUID, since: datetime) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            text(
                "SELECT reviewer_id, comment, created_at FROM review "
                "WHERE reviewee_id = :u AND created_at >= :s"
            ),
            {"u": user_id, "s": since},
        ).mappings()
        return [dict(r) for r in rows]

    def reviews_given(self, user_id: UUID, since: datetime) -> list[ReviewSnapshot]:
        rows = self.conn.execute(
            text(
                "SELECT r.id::text, r.reviewer_id::text, r.reviewee_id::text, "
                "(SELECT min(v::int) FROM jsonb_each_text(r.ratings) AS e(k, v)), r.comment, "
                "r.created_at FROM review r WHERE r.reviewer_id = :u AND r.created_at >= :s"
            ),
            {"u": user_id, "s": since},
        ).all()
        return [ReviewSnapshot(r[0], r[1], r[2], r[3], r[4], r[5], True) for r in rows]

    def disputes_raised(self, by: UUID, against: UUID, since: datetime) -> list[datetime]:
        return list(
            self.conn.execute(
                text(
                    "SELECT ec.opened_at FROM escalation_case ec JOIN borrowing_transaction t "
                    "ON t.id = ec.transaction_id WHERE ec.trigger_type = 'DISPUTE' "
                    "AND ec.raised_by = :b AND :a IN (t.borrower_id, t.lender_id) "
                    "AND ec.opened_at >= :s"
                ),
                {"b": by, "a": against, "s": since},
            ).scalars()
        )

    def insert(
        self,
        txn_id: UUID,
        reviewer: UUID,
        reviewee: UUID,
        role: str,
        ratings: Mapping[str, int],
        comment: str | None,
        retaliation: bool,
        similar: bool,
    ) -> UUID:
        value = self.conn.execute(
            text(
                "INSERT INTO review (transaction_id, reviewer_id, reviewee_id, reviewee_role, "
                "ratings, comment, retaliation_flag, similarity_flag) VALUES (:t, :r, :e, "
                "CAST(:role AS party_role), CAST(:g AS jsonb), :c, :rf, :sf) RETURNING id"
            ),
            {
                "t": txn_id,
                "r": reviewer,
                "e": reviewee,
                "role": role,
                "g": json.dumps(dict(ratings)),
                "c": comment,
                "rf": retaliation,
                "sf": similar,
            },
        ).scalar_one()
        return UUID(str(value))

    def update(
        self,
        review_id: UUID,
        ratings: Mapping[str, int],
        comment: str | None,
        retaliation: bool,
        similar: bool,
    ) -> None:
        self.conn.execute(
            text(
                "UPDATE review SET ratings = CAST(:g AS jsonb), comment = :c, "
                "retaliation_flag = :rf, similarity_flag = :sf WHERE id = :i"
            ),
            {
                "i": review_id,
                "g": json.dumps(dict(ratings)),
                "c": comment,
                "rf": retaliation,
                "sf": similar,
            },
        )
