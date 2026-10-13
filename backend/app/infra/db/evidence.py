"""PostgreSQL evidence for the assurance engine (EvidenceSource in domain/assurance/engine).

Each read uses its own short connection: the engine runs in a worker thread with a timeout, apart
from the command's own transaction, and reads only committed history.
"""

from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, text

from app.domain.assurance.engine import OutcomeSnapshot
from app.infra.db.trust_graph import load_graph


class PostgresEvidenceSource:
    def __init__(self, db: Callable[[], Engine]) -> None:
        self.db = db

    def borrower_outcomes(self, borrower_id: UUID) -> list[OutcomeSnapshot]:
        with self.db().connect() as c:
            rows = c.execute(
                text(
                    "SELECT occurred_at, success, status::text, category_id, value_band::text, "
                    "EXTRACT(EPOCH FROM loan_duration) / 86400.0 FROM outcome WHERE subject_id = :b "
                    "AND subject_role = 'BORROWER' AND metric = 'ON_TIME_RETURN'"
                ),
                {"b": borrower_id},
            ).all()
        return [OutcomeSnapshot(r[0], r[1], r[2], r[3], r[4], float(r[5])) for r in rows]

    def trust_graph(self) -> dict[str, dict[str, float]]:
        with self.db().connect() as c:
            return load_graph(c, "BORROWER", "ON_TIME_RETURN")

    def open_dispute(self, borrower_id: UUID) -> bool:
        """A live dispute on any loan where the borrower is a party, in either role."""
        with self.db().connect() as c:
            return bool(
                c.execute(
                    text(
                        "SELECT EXISTS (SELECT 1 FROM escalation_case ec JOIN borrowing_transaction t "
                        "ON t.id = ec.transaction_id WHERE ec.trigger_type = 'DISPUTE' "
                        "AND ec.status IN ('OPEN', 'AWAITING_INFORMATION') "
                        "AND :b IN (t.borrower_id, t.lender_id))"
                    ),
                    {"b": borrower_id},
                ).scalar_one()
            )

    def resolved_disputes_since(self, borrower_id: UUID, since: datetime) -> int:
        """Disputes raised against the borrower on their loans and closed by a moderator since
        `since`. A dispute the borrower raised (a complaint, as in ES-05) is not held against them."""
        with self.db().connect() as c:
            return int(
                c.execute(
                    text(
                        "SELECT count(*) FROM escalation_case ec JOIN borrowing_transaction t "
                        "ON t.id = ec.transaction_id WHERE ec.trigger_type = 'DISPUTE' "
                        "AND ec.status IN ('DECIDED', 'REVERSED') AND ec.closed_at >= :since "
                        "AND t.borrower_id = :b AND ec.raised_by <> :b"
                    ),
                    {"b": borrower_id, "since": since},
                ).scalar_one()
            )

    def verification_ok(self, borrower_id: UUID, item_id: UUID) -> bool:
        with self.db().connect() as c:
            return bool(
                c.execute(
                    text(
                        "SELECT u.verification_level >= i.required_verification FROM app_user u, item i "
                        "WHERE u.id = :b AND i.id = :i"
                    ),
                    {"b": borrower_id, "i": item_id},
                ).scalar_one_or_none()
            )

    def display_names(self, user_ids: list[str]) -> dict[str, str]:
        if not user_ids:
            return {}
        with self.db().connect() as c:
            rows = c.execute(
                text("SELECT id::text, display_name FROM app_user WHERE id::text = ANY(:ids)"),
                {"ids": user_ids},
            ).all()
        return {r[0]: r[1] for r in rows}
