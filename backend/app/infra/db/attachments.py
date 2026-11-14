"""PostgreSQL adapter for AttachmentService (plan item M4; table `attachment`, ADR-0014)."""

from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text


class PostgresAttachmentStore:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def _one(self, sql: str, **params: Any) -> dict[str, Any] | None:
        row = self.conn.execute(text(sql), params).mappings().first()
        return dict(row) if row else None

    def item(self, item_id: UUID) -> dict[str, Any] | None:
        return self._one("SELECT id, owner_id, community_id FROM item WHERE id = :i", i=item_id)

    def loan(self, txn_id: UUID) -> dict[str, Any] | None:
        return self._one(
            "SELECT t.id, t.borrower_id, t.lender_id, t.current_state::text AS state, "
            "i.community_id FROM borrowing_transaction t JOIN item i ON i.id = t.item_id "
            "WHERE t.id = :t",
            t=txn_id,
        )

    def latest_report(self, txn_id: UUID, phase: str, role: str) -> UUID | None:
        value = self.conn.execute(
            text(
                "SELECT id FROM condition_report WHERE transaction_id = :t "
                "AND phase = CAST(:p AS condition_phase) AND reporter_role = CAST(:r AS party_role) "
                "ORDER BY created_at DESC LIMIT 1"
            ),
            {"t": txn_id, "p": phase, "r": role},
        ).scalar_one_or_none()
        return UUID(str(value)) if value else None

    def insert(
        self,
        *,
        uploaded_by: UUID,
        key: str,
        sha256: bytes,
        mime: str,
        item_id: UUID | None = None,
        transaction_id: UUID | None = None,
        condition_report_id: UUID | None = None,
    ) -> UUID:
        value = self.conn.execute(
            text(
                "INSERT INTO attachment (transaction_id, item_id, condition_report_id, uploaded_by, "
                "storage_key, content_sha256, mime_type, metadata_stripped) "
                "VALUES (:t, :i, :r, :u, :k, :h, :m, true) RETURNING id"
            ),
            {
                "t": transaction_id,
                "i": item_id,
                "r": condition_report_id,
                "u": uploaded_by,
                "k": key,
                "h": sha256,
                "m": mime,
            },
        ).scalar_one()
        return UUID(str(value))

    def attachment(self, attachment_id: UUID) -> dict[str, Any] | None:
        return self._one(
            "SELECT a.id, a.storage_key, a.item_id, a.transaction_id, "
            "coalesce(i.owner_id, NULL) AS owner_id, t.borrower_id, t.lender_id, "
            "coalesce(i.community_id, ti.community_id) AS community_id FROM attachment a "
            "LEFT JOIN item i ON i.id = a.item_id "
            "LEFT JOIN borrowing_transaction t ON t.id = a.transaction_id "
            "LEFT JOIN item ti ON ti.id = t.item_id WHERE a.id = :a",
            a=attachment_id,
        )

    def is_member(self, user_id: UUID, community_id: UUID) -> bool:
        return (
            self.conn.execute(
                text(
                    "SELECT 1 FROM membership WHERE user_id = :u AND community_id = :c "
                    "AND status = 'APPROVED'"
                ),
                {"u": user_id, "c": community_id},
            ).first()
            is not None
        )

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

    def photos_for(self, *, item_id: UUID | None = None, txn_id: UUID | None = None) -> list[Any]:
        """Attachment ids of a listing or a loan, oldest first."""
        return list(
            self.conn.execute(
                text(
                    "SELECT id FROM attachment WHERE (CAST(:i AS uuid) IS NULL OR item_id = :i) "
                    "AND (CAST(:t AS uuid) IS NULL OR transaction_id = :t) ORDER BY created_at, id"
                ),
                {"i": item_id, "t": txn_id},
            ).scalars()
        )
