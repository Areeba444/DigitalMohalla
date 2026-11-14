"""PostgreSQL adapter for ListingService (Module 3, FR-B-01; plan item F9)."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

# The listing columns an owner sets. Both statements are fixed text with bound parameters only.
_COLUMNS = (
    "title",
    "description",
    "category_id",
    "condition",
    "value_band",
    "deposit_amount",
    "usage_terms",
    "handover_method",
    "search_terms",
    "expires_at",
    "required_verification",
)
_INSERT = text(
    "INSERT INTO item (owner_id, community_id, status, title, description, category_id, "
    "condition, value_band, deposit_amount, usage_terms, handover_method, search_terms, "
    "expires_at, required_verification) VALUES (:owner, :community, "
    "CAST(:status AS item_status), :title, :description, :category_id, "
    "CAST(:condition AS item_condition), CAST(:value_band AS value_band), "
    "coalesce(:deposit_amount, 0), :usage_terms, :handover_method, :search_terms, :expires_at, "
    "CAST(:required_verification AS verification_level)) RETURNING id"
)
_UPDATE = text(
    "UPDATE item SET "
    "title = CASE WHEN :set_title THEN :title ELSE title END, "
    "description = CASE WHEN :set_description THEN :description ELSE description END, "
    "category_id = CASE WHEN :set_category_id THEN :category_id ELSE category_id END, "
    "condition = CASE WHEN :set_condition THEN CAST(:condition AS item_condition) "
    " ELSE condition END, "
    "value_band = CASE WHEN :set_value_band THEN CAST(:value_band AS value_band) "
    " ELSE value_band END, "
    "deposit_amount = CASE WHEN :set_deposit_amount THEN :deposit_amount "
    " ELSE deposit_amount END, "
    "usage_terms = CASE WHEN :set_usage_terms THEN :usage_terms ELSE usage_terms END, "
    "handover_method = CASE WHEN :set_handover_method THEN :handover_method "
    " ELSE handover_method END, "
    "search_terms = CASE WHEN :set_search_terms THEN :search_terms ELSE search_terms END, "
    "expires_at = CASE WHEN :set_expires_at THEN :expires_at ELSE expires_at END, "
    "required_verification = CASE WHEN :set_required_verification "
    " THEN CAST(:required_verification AS verification_level) ELSE required_verification END, "
    "status = CAST(:status AS item_status), updated_at = now() WHERE id = :id"
)


class PostgresListingStore:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def is_approved_member(self, user_id: UUID, community_id: UUID) -> bool:
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

    def category(self, category_id: int) -> dict[str, Any] | None:
        row = (
            self.conn.execute(
                text(
                    "SELECT id, name, is_restricted, min_verification::text AS min_verification "
                    "FROM category WHERE id = :c"
                ),
                {"c": category_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def categories(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            text(
                "SELECT id, name, is_restricted, min_verification::text AS min_verification "
                "FROM category ORDER BY name"
            )
        ).mappings()
        return [dict(r) for r in rows]

    def insert(
        self, owner_id: UUID, community_id: UUID, status: str, fields: Mapping[str, Any]
    ) -> UUID:
        params = {n: fields.get(n) for n in _COLUMNS}
        params.update(owner=owner_id, community=community_id, status=status)
        return UUID(str(self.conn.execute(_INSERT, params).scalar_one()))

    def update(self, item_id: UUID, status: str, fields: Mapping[str, Any]) -> None:
        """Only the given fields change: each column has a `set_<name>` flag (static SQL)."""
        params: dict[str, Any] = {n: fields.get(n) for n in _COLUMNS}
        params.update({f"set_{n}": n in fields for n in _COLUMNS})
        params.update(status=status, id=item_id)
        self.conn.execute(_UPDATE, params)

    def listing(self, item_id: UUID) -> dict[str, Any] | None:
        row = (
            self.conn.execute(
                text(
                    "SELECT i.id, i.owner_id, i.community_id, c.name AS community_name, "
                    "i.category_id, k.name AS category_name, i.title, i.description, "
                    "i.condition::text AS condition, i.value_band::text AS value_band, "
                    "i.deposit_amount, i.usage_terms, i.handover_method, i.search_terms, "
                    "i.required_verification::text AS required_verification, "
                    "i.status::text AS status, i.expires_at, i.created_at, i.updated_at, "
                    "u.display_name AS owner_name "
                    "FROM item i JOIN community c ON c.id = i.community_id "
                    "JOIN category k ON k.id = i.category_id JOIN app_user u ON u.id = i.owner_id "
                    "WHERE i.id = :id"
                ),
                {"id": item_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def owned_by(self, owner_id: UUID) -> list[dict[str, Any]]:
        """The member's own listings in every status, for "My listings" (drafts included)."""
        rows = self.conn.execute(
            text(
                "SELECT i.id, i.title, i.value_band::text AS value_band, i.deposit_amount, "
                "i.status::text AS status, i.condition::text AS condition, i.updated_at "
                "FROM item i WHERE i.owner_id = :u AND i.status <> 'REMOVED' "
                "ORDER BY i.updated_at DESC, i.id"
            ),
            {"u": owner_id},
        ).mappings()
        return [dict(r) for r in rows]
