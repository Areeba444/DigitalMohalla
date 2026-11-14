"""PostgreSQL adapter for ListingService (Module 3, FR-B-01; plan item F9)."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

_CASTS = {
    "condition": "CAST(:condition AS item_condition)",
    "value_band": "CAST(:value_band AS value_band)",
    "required_verification": "CAST(:required_verification AS verification_level)",
}


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
        names = list(fields)
        values = [_CASTS.get(n, f":{n}") for n in names]
        sql = (
            f"INSERT INTO item (owner_id, community_id, status, {', '.join(names)}) "
            f"VALUES (:owner, :community, CAST(:status AS item_status), {', '.join(values)}) "
            "RETURNING id"
        )
        params = {**fields, "owner": owner_id, "community": community_id, "status": status}
        return UUID(str(self.conn.execute(text(sql), params).scalar_one()))

    def update(self, item_id: UUID, status: str, fields: Mapping[str, Any]) -> None:
        sets = [f"{n} = {_CASTS.get(n, f':{n}')}" for n in fields]
        sets += ["status = CAST(:status AS item_status)", "updated_at = now()"]
        self.conn.execute(
            text(f"UPDATE item SET {', '.join(sets)} WHERE id = :id"),
            {**fields, "status": status, "id": item_id},
        )

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
