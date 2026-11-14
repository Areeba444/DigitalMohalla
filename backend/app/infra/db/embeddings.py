"""item_embedding reads and writes for A9 (ADR-0016; migration 0004)."""

from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text


def table_exists(conn: Connection) -> bool:
    """False where the server has no pgvector, so the table was not created: keyword-only."""
    return conn.execute(text("SELECT to_regclass('dm.item_embedding') IS NOT NULL")).scalar_one()


class PostgresEmbeddingStore:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def published_with_hash(self, model: str) -> list[dict[str, Any]]:
        """Published listings with their text fields and the hash of their current embedding."""
        rows = self.conn.execute(
            text(
                "SELECT i.id, i.title, i.description, i.search_terms, e.content_sha256 AS stored "
                "FROM item i LEFT JOIN item_embedding e ON e.item_id = i.id AND e.model = :m "
                "WHERE i.status = 'PUBLISHED' ORDER BY i.id"
            ),
            {"m": model},
        ).mappings()
        return [dict(r) for r in rows]

    def item(self, item_id: UUID) -> dict[str, Any] | None:
        row = (
            self.conn.execute(
                text("SELECT id, title, description, search_terms FROM item WHERE id = :i"),
                {"i": item_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def upsert(self, item_id: UUID, model: str, sha256: bytes, vector: str) -> None:
        self.conn.execute(
            text(
                "INSERT INTO item_embedding (item_id, model, content_sha256, embedding) "
                "VALUES (:i, :m, :h, CAST(:v AS public.vector)) "
                "ON CONFLICT (item_id, model) DO UPDATE SET embedding = EXCLUDED.embedding, "
                "content_sha256 = EXCLUDED.content_sha256, created_at = now()"
            ),
            {"i": item_id, "m": model, "h": sha256, "v": vector},
        )
