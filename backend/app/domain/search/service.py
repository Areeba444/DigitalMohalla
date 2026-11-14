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

A9 adds the meaning-based half: the same query with a vector distance, and HYBRID mode. A10 adds the
re-ranking of Algorithm 5. Until then the mode is KEYWORD_ONLY.
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
        self, member: UUID, words: list[str], text_query: str, f: SearchFilters, limit: int
    ) -> list[dict[str, Any]]:
        """Eligible, filtered items with: keyword (raw score), in_title, in_terms, in_description,
        fuzzy (title similarity), lender_loans, same_community, created_at and listing fields."""
        ...


def query_words(q: str) -> list[str]:
    """Lower-case word tokens, at most 10, for an OR-ed full-text query. Only letters and digits
    reach PostgreSQL's to_tsquery, so no query syntax can be injected."""
    return [w.lower() for w in _WORD.findall(q or "")][:10]


def reason_line(c: dict[str, Any], words: list[str]) -> str:
    """Where the words matched, in plain words. No score is ever shown."""
    if not words:
        return "Listed in your community"
    if c["in_title"]:
        reason = "Matches your words in the title"
    elif c["in_terms"]:
        reason = "Matches another name for this item"
    elif c["in_description"]:
        reason = "Matches your words in the description"
    else:
        reason = "Close spelling of a word in the title"
    return reason + (" · in your community" if c["same_community"] else "")


class SearchService:
    def __init__(self, store: SearchStore, *, min_relevance: float, candidate_pool: int) -> None:
        self.store = store
        self.min_relevance = min_relevance
        self.pool = candidate_pool

    def search(
        self, member: UUID, q: str, filters: SearchFilters, sort: str = "relevance", page: int = 1
    ) -> SearchResult:
        if sort not in SORTS:
            raise InvalidSearch(f"sort must be one of {', '.join(SORTS)}")
        if (filters.start is None) != (filters.end is None):
            raise InvalidSearch("give both dates or neither")
        if filters.start and filters.end and filters.end <= filters.start:
            raise InvalidSearch("the end date must be after the start date")
        if page < 1:
            raise InvalidSearch("page starts at 1")
        words = query_words(q)
        rows = self.store.candidates(member, words, " | ".join(words), filters, self.pool)
        best = max((r["keyword"] for r in rows), default=0.0)
        results = []
        for r in rows:
            relevance = (r["keyword"] / best) if words and best > 0 else 1.0
            if words and relevance < self.min_relevance:
                continue
            results.append(
                {
                    **r,
                    "relevance": relevance,
                    "reason": reason_line(r, words),
                    "available": True if filters.start else None,
                    "score_parts": {"keyword": round(relevance, 4)},
                }
            )
        key = {
            "relevance": lambda x: (-x["relevance"], -x["created_at"].timestamp()),
            "evidence": lambda x: (-x["lender_loans"], -x["relevance"]),
            "newest": lambda x: (-x["created_at"].timestamp(),),
        }[sort]
        results.sort(key=key)
        start = (page - 1) * PAGE_SIZE
        return SearchResult("KEYWORD_ONLY", results[start : start + PAGE_SIZE], len(results))
