"""SearchService: keyword retrieval, filters and sorts for item search (Module 4; F10; ADR-0016).

UC-B3, FR-S-02 (keyword search that works without the model), FR-S-03 (server filters and sorts).
Retrieval, the eligibility rules and the filters are one SQL query (the store), so a filter never
thins a result list after the fact (issue I-5):

- eligible: PUBLISHED, in one of the member's APPROVED communities, not the member's own item, and
  not from a lender who has blocked the member (the request guard G1 would refuse it anyway);
- filters: category, community, dates (no held booking overlaps them), maximum deposit, condition.
  "Distance" is same community or not, because no coordinates are stored, and the filter is on the
  deposit because lending has no price (FR-S-01, S-03 as changed in FR/NFR v1.4);
- keyword score: full-text rank on `search_tsv` (title, description, other names such as Roman
  Urdu, configuration 'simple', so words are matched as typed) plus trigram similarity on the title
  for typos. Words are OR-ed, so "drill machine" also finds "drill".

Relevance in keyword mode is the keyword score divided by the best one in this result set (Algorithm
5's keyword-only relevance); results below `ranking_alg5.retrieval.min_relevance` are dropped. Sorts:
relevance (then newest), evidence (the lender's verified loans as a lender, then relevance), newest.
Each result carries a short reason line in plain words, never a number (FR-S-01, NFR-U-01).

A9 adds the meaning-based half (HYBRID mode): the same eligibility and filters with the exact cosine
similarity to the query vector; candidates are the top N by meaning, relevance is
0.7 * meaning + 0.3 * keywords (config), and an item found by meaning alone gets the reason "Similar
in meaning to your search". With no model, no pgvector or a failing model, search stays
KEYWORD_ONLY (FR-S-02). A10 adds the re-ranking of Algorithm 5 on top.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

SORTS = ("relevance", "evidence", "newest")
PAGE_SIZE = 20
_WORD = re.compile(r"\w+", re.UNICODE)


class InvalidSearch(ValueError):
    """Bad filters or sort (422)."""


@dataclass(frozen=True)
class SearchFilters:
    category_id: int | None = None
    community_id: UUID | None = None
    start: datetime | None = None
    end: datetime | None = None
    max_deposit: float | None = None
    condition: str | None = None


@dataclass
class SearchResult:
    mode: str
    results: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0


class SearchStore(Protocol):
    def candidates(
        self,
        member: UUID,
        words: list[str],
        text_query: str,
        f: SearchFilters,
        limit: int,
        vector: str | None = None,
        model: str | None = None,
    ) -> list[dict[str, Any]]:
        """Eligible, filtered items with: keyword (raw score), in_title, in_terms, in_description,
        fuzzy (title similarity), lender_loans, same_community, created_at and listing fields. With
        a query vector (A9): the top `limit` by meaning, with `semantic` (cosine similarity, 0 for
        an item not embedded yet) and `keyword_match`."""
        ...


def query_words(q: str) -> list[str]:
    """Lower-case word tokens, at most 10, for an OR-ed full-text query. Only letters and digits
    reach PostgreSQL's to_tsquery, so no query syntax can be injected."""
    return [w.lower() for w in _WORD.findall(q or "")][:10]


def reason_line(c: dict[str, Any], words: list[str]) -> str:
    """Where the words matched, in plain words. No score is ever shown."""
    if not words:
        return "Listed in your community"
    if c.get("keyword_match") is False:
        reason = "Similar in meaning to your search"
    elif c["in_title"]:
        reason = "Matches your words in the title"
    elif c["in_terms"]:
        reason = "Matches another name for this item"
    elif c["in_description"]:
        reason = "Matches your words in the description"
    else:
        reason = "Close spelling of a word in the title"
    return reason + (" · in your community" if c["same_community"] else "")


class SearchService:
    def __init__(
        self,
        store: SearchStore,
        *,
        min_relevance: float,
        candidate_pool: int,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> None:
        self.store = store
        self.min_relevance = min_relevance
        self.pool = candidate_pool
        self.w_sem = semantic_weight
        self.w_kw = keyword_weight

    def search(
        self,
        member: UUID,
        q: str,
        filters: SearchFilters,
        sort: str = "relevance",
        page: int = 1,
        query_vector: str | None = None,
        model: str | None = None,
    ) -> SearchResult:
        """Keyword-only, or HYBRID when a query vector (pgvector text form) and its model are given
        (A9): candidates are the top N by meaning and relevance mixes meaning and keywords
        (ranking_alg5.retrieval.relevance_mix)."""
        if sort not in SORTS:
            raise InvalidSearch(f"sort must be one of {', '.join(SORTS)}")
        if (filters.start is None) != (filters.end is None):
            raise InvalidSearch("give both dates or neither")
        if filters.start and filters.end and filters.end <= filters.start:
            raise InvalidSearch("the end date must be after the start date")
        if page < 1:
            raise InvalidSearch("page starts at 1")
        words = query_words(q)
        hybrid = bool(words and query_vector and model)
        rows = self.store.candidates(
            member,
            words,
            " | ".join(words),
            filters,
            self.pool,
            query_vector if hybrid else None,
            model if hybrid else None,
        )
        best = max((r["keyword"] for r in rows if r.get("keyword_match", True)), default=0.0)
        results = []
        for r in rows:
            matched = r.get("keyword_match", True)
            kw = (r["keyword"] / best) if words and best > 0 and matched else 0.0
            if hybrid:
                sem = min(1.0, max(0.0, r["semantic"]))
                relevance = self.w_sem * sem + self.w_kw * kw
                parts = {"semantic": round(sem, 4), "keyword": round(kw, 4)}
            else:
                relevance = kw if words else 1.0
                parts = {"keyword": round(kw, 4)}
            if words and relevance < self.min_relevance:
                continue
            parts["relevance"] = round(relevance, 4)
            results.append(
                {
                    **r,
                    "relevance": relevance,
                    "reason": reason_line(r, words),
                    "available": True if filters.start else None,
                    "score_parts": parts,
                }
            )
        key = {
            "relevance": lambda x: (-x["relevance"], -x["created_at"].timestamp()),
            "evidence": lambda x: (-x["lender_loans"], -x["relevance"]),
            "newest": lambda x: (-x["created_at"].timestamp(),),
        }[sort]
        results.sort(key=key)
        start = (page - 1) * PAGE_SIZE
        mode = "HYBRID" if hybrid else "KEYWORD_ONLY"
        return SearchResult(mode, results[start : start + PAGE_SIZE], len(results))
