"""PostgreSQL adapter for SearchLogger (FR-S-05; tables search_query, search_impression, search_click)."""

import json
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text


class PostgresSearchLogStore:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def insert_query(
        self,
        *,
        user_id: UUID,
        community_id: UUID | None,
        query_text: str,
        filters: Mapping[str, Any],
        mode: str,
        config_version: str,
        result_count: int,
        latency_ms: int,
    ) -> UUID:
        value = self.conn.execute(
            text(
                "INSERT INTO search_query (user_id, community_id, query_text, filters, mode, "
                "config_version, result_count, latency_ms) VALUES (:u, :c, :q, CAST(:f AS jsonb), "
                "CAST(:m AS search_mode), :v, :n, :l) RETURNING id"
            ),
            {
                "u": user_id,
                "c": community_id,
                "q": query_text,
                "f": json.dumps(dict(filters), default=str),
                "m": mode,
                "v": config_version,
                "n": result_count,
                "l": latency_ms,
            },
        ).scalar_one()
        return UUID(str(value))

    def insert_impressions(
        self, query_id: UUID, shown: Sequence[tuple[int, UUID, Mapping[str, Any]]]
    ) -> None:
        if not shown:
            return
        self.conn.execute(
            text(
                "INSERT INTO search_impression (query_id, rank, item_id, score_parts) "
                "VALUES (:q, :r, :i, CAST(:s AS jsonb))"
            ),
            [
                {"q": query_id, "r": rank, "i": item, "s": json.dumps(dict(parts))}
                for rank, item, parts in shown
            ],
        )

    def query_owner(self, query_id: UUID) -> UUID | None:
        value = self.conn.execute(
            text("SELECT user_id FROM search_query WHERE id = :q"), {"q": query_id}
        ).scalar_one_or_none()
        return UUID(str(value)) if value else None

    def was_shown(self, query_id: UUID, item_id: UUID) -> bool:
        return (
            self.conn.execute(
                text("SELECT 1 FROM search_impression WHERE query_id = :q AND item_id = :i"),
                {"q": query_id, "i": item_id},
            ).first()
            is not None
        )

    def insert_click(self, query_id: UUID, item_id: UUID) -> UUID:
        value = self.conn.execute(
            text("INSERT INTO search_click (query_id, item_id) VALUES (:q, :i) RETURNING id"),
            {"q": query_id, "i": item_id},
        ).scalar_one()
        return UUID(str(value))

    def home_community(self, user_id: UUID) -> UUID | None:
        value = self.conn.execute(
            text(
                "SELECT community_id FROM membership WHERE user_id = :u AND status = 'APPROVED' "
                "ORDER BY decided_at NULLS LAST, requested_at, id LIMIT 1"
            ),
            {"u": user_id},
        ).scalar_one_or_none()
        return UUID(str(value)) if value else None
