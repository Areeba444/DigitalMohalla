"""PostgreSQL adapter for SearchService: one query for retrieval, eligibility and filters (F10).

Uses the generated `search_tsv` column (GIN index) and the `pg_trgm` index on titles from migration
0003. All values are bound parameters; the OR-ed full-text query is built only from letter and digit
tokens (search.service.query_words).
"""

from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

from app.domain.search.service import SearchFilters

_CANDIDATES = text(
    """
WITH q AS (SELECT CASE WHEN :tsq = '' THEN NULL ELSE to_tsquery('simple', :tsq) END AS tsq),
home AS (SELECT community_id FROM membership WHERE user_id = :m AND status = 'APPROVED'),
first_home AS (SELECT community_id FROM membership WHERE user_id = :m AND status = 'APPROVED'
                ORDER BY decided_at NULLS LAST, requested_at, id LIMIT 1)  -- the member's home community
SELECT i.id, i.title, i.condition::text AS condition, i.value_band::text AS value_band,
       i.deposit_amount, i.created_at, c.name AS community_name, k.name AS category_name,
       u.display_name AS owner_name,
       coalesce(ts_rank_cd(i.search_tsv, q.tsq), 0) + 0.5 * similarity(i.title, :raw) AS keyword,
       coalesce(to_tsvector('simple', i.title) @@ q.tsq, false) AS in_title,
       coalesce(to_tsvector('simple', coalesce(i.search_terms, '')) @@ q.tsq, false) AS in_terms,
       coalesce(to_tsvector('simple', coalesce(i.description, '')) @@ q.tsq, false) AS in_description,
       similarity(i.title, :raw) AS fuzzy,
       i.community_id = (SELECT community_id FROM first_home) AS same_community,
       (SELECT count(*) FROM outcome o WHERE o.subject_id = i.owner_id AND o.subject_role = 'LENDER'
          AND o.metric = 'CONDITION_AGREED' AND o.status = 'VALID') AS lender_loans
  FROM item i CROSS JOIN q
  JOIN community c ON c.id = i.community_id
  JOIN category k ON k.id = i.category_id
  JOIN app_user u ON u.id = i.owner_id
 WHERE i.status = 'PUBLISHED' AND i.owner_id <> :m
   AND i.community_id IN (SELECT community_id FROM home)
   AND NOT EXISTS (SELECT 1 FROM user_block b WHERE b.blocker_id = i.owner_id AND b.blocked_id = :m)
   AND (q.tsq IS NULL OR i.search_tsv @@ q.tsq OR similarity(i.title, :raw) >= 0.3)
   AND (CAST(:category AS smallint) IS NULL OR i.category_id = :category)
   AND (CAST(:community AS uuid) IS NULL OR i.community_id = :community)
   AND (CAST(:max_deposit AS numeric) IS NULL OR i.deposit_amount <= :max_deposit)
   AND (CAST(:condition AS text) IS NULL OR i.condition = CAST(:condition AS item_condition))
   AND (CAST(:start AS timestamptz) IS NULL OR NOT EXISTS (
        SELECT 1 FROM booking bk WHERE bk.item_id = i.id AND bk.status = 'HELD'
           AND bk.period && tstzrange(CAST(:start AS timestamptz), CAST(:end AS timestamptz))))
 ORDER BY keyword DESC, i.created_at DESC, i.id
 LIMIT :limit
"""
)


class PostgresSearchStore:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def candidates(
        self, member: UUID, words: list[str], text_query: str, f: SearchFilters, limit: int
    ) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            _CANDIDATES,
            {
                "m": member,
                "tsq": text_query,
                "raw": " ".join(words),
                "category": f.category_id,
                "community": f.community_id,
                "max_deposit": f.max_deposit,
                "condition": f.condition,
                "start": f.start,
                "end": f.end,
                "limit": limit,
            },
        ).mappings()
        out = []
        for r in rows:
            d = dict(r)
            d["keyword"] = float(d["keyword"])
            d["deposit_amount"] = float(d["deposit_amount"])
            d["lender_loans"] = int(d["lender_loans"])
            out.append(d)
        return out
