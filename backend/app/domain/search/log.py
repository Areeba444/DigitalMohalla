"""SearchLogger: queries, shown results and clicks for evaluation (Module 4; FR-S-05; plan item M9).

What is kept, per DA-23 and sequence (i): the member, their community, the query text, the filters,
the mode (HYBRID or KEYWORD_ONLY), the config version that ranked it, the result count and the
latency; then one impression row per shown result, in rank order, with its score parts; then a click
row when a shown result is opened. "Ignored" results are impressions with no click. No location is
ever logged: the schema refuses location keys in the filters (`has_location_keys`), and the API has
no location input for search.

The log is append-only evidence (triggers forbid updates and deletes). A logging failure must never
block the member's search, so the API logs after it has the results and drops the log on error.
An empty query (browsing with filters only) is not a search and is not logged.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol
from uuid import UUID

from app.domain.lifecycle.errors import StreamNotFound


class SearchLogStore(Protocol):
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
    ) -> UUID: ...

    def insert_impressions(
        self, query_id: UUID, shown: Sequence[tuple[int, UUID, Mapping[str, Any]]]
    ) -> None: ...

    def query_owner(self, query_id: UUID) -> UUID | None: ...

    def was_shown(self, query_id: UUID, item_id: UUID) -> bool: ...

    def insert_click(self, query_id: UUID, item_id: UUID) -> UUID: ...

    def home_community(self, user_id: UUID) -> UUID | None: ...


class SearchLogger:
    def __init__(self, store: SearchLogStore, config_version: str) -> None:
        self.store = store
        self.config_version = config_version

    def log_search(
        self,
        user_id: UUID,
        query_text: str,
        filters: Mapping[str, Any],
        mode: str,
        results: Sequence[Mapping[str, Any]],
        latency_ms: int,
        offset: int = 0,
    ) -> UUID | None:
        """One query row and an impression per shown result. `offset` is the rank of the first
        shown result minus one (paging). Returns the query id, or None for an empty query."""
        text = query_text.strip()
        if not text:
            return None
        query_id = self.store.insert_query(
            user_id=user_id,
            community_id=self.store.home_community(user_id),
            query_text=text[:200],
            filters={k: v for k, v in filters.items() if v is not None},
            mode=mode,
            config_version=self.config_version,
            result_count=len(results),
            latency_ms=max(0, latency_ms),
        )
        self.store.insert_impressions(
            query_id,
            [
                (offset + rank, r["id"], r.get("score_parts", {}))
                for rank, r in enumerate(results, start=1)
            ],
        )
        return query_id

    def log_click(self, user_id: UUID, query_id: UUID, item_id: UUID) -> UUID:
        """A member opened a result of their own search. Clicks on someone else's query, or on an
        item that was not shown, are refused (404), so the log stays honest."""
        if self.store.query_owner(query_id) != user_id:
            raise StreamNotFound(f"search {query_id}")
        if not self.store.was_shown(query_id, item_id):
            raise StreamNotFound(f"item {item_id} was not shown for this search")
        return self.store.insert_click(query_id, item_id)
