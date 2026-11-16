"""Embedding backfill on the scheduler (ADR-0016, ADR-0012; plan item A9).

Every published listing whose text has no embedding for the configured model, or whose text
changed since it was embedded (the stored SHA-256 differs), is embedded and stored. The claim key
carries the text hash, so an unchanged listing is never embedded twice and an edited one is. With
no model configured, or no pgvector table, the job has nothing to do.
"""

from datetime import datetime
from typing import Any

from app.domain.scheduler.runner import DueItem
from app.domain.search.embedding import IEmbed, listing_text, text_hash, to_pgvector
from app.infra.db.embeddings import PostgresEmbeddingStore, table_exists


class EmbeddingBackfill:
    name = "embedding_backfill"

    def __init__(self, embedder: IEmbed | None) -> None:
        self.embedder = embedder

    def due(self, uow: Any, now: datetime) -> list[DueItem]:
        if self.embedder is None or not table_exists(uow.conn):
            return []
        items = []
        store = PostgresEmbeddingStore(uow.conn)
        for row in store.published_with_hash(self.embedder.model_name):
            digest = text_hash(listing_text(row))
            if row["stored"] is None or bytes(row["stored"]) != digest:
                items.append(
                    DueItem(
                        f"{row['id']}:{self.embedder.model_name}:{digest.hex()[:16]}",
                        {"item": row["id"]},
                    )
                )
        return items

    def run(self, uow: Any, item: DueItem, now: datetime) -> None:
        if self.embedder is None:  # due() returns nothing without a model; refuse rather than guess
            raise RuntimeError("no embedding model is configured")
        store = PostgresEmbeddingStore(uow.conn)
        row = store.item(item.ref["item"])
        if row is None:
            raise RuntimeError("listing no longer exists")
        body = listing_text(row)
        [vector] = self.embedder.embed([body])
        store.upsert(row["id"], self.embedder.model_name, text_hash(body), to_pgvector(vector))
