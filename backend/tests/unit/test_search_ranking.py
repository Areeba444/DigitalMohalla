"""Algorithm 5 re-ranking (A10; FR-S-04; claim C5). Fake store, no database. All data is synthetic.

Hand check: weights 0.4 / 0.3 / 0.15 / 0.1 / 0.05. Two equally relevant fresh items, same community,
no dates (availability 0.5): the one whose lender has value 0.9 beats value 0.5 by 0.3 * 0.4 = 0.12.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.domain.search.service import SearchFilters, SearchService

NOW = datetime.now(UTC)
WEIGHTS = {
    "relevance": 0.4,
    "lender_evidence": 0.3,
    "availability": 0.15,
    "same_community": 0.1,
    "freshness": 0.05,
}


class FakeStore:
    def __init__(self, rows: list[dict]) -> None:  # type: ignore[type-arg]
        self.rows = rows

    def candidates(self, *args: object) -> list[dict]:  # type: ignore[type-arg]
        return self.rows


def row(owner: UUID, age_days: float = 0, same: bool = True) -> dict:  # type: ignore[type-arg]
    return {
        "id": uuid4(), "owner_id": owner, "keyword": 1.0, "title": "Drill", "same_community": same,
        "created_at": NOW - timedelta(days=age_days), "lender_loans": 0, "in_title": True, "in_terms": False, "in_description": False,
    }  # fmt: skip


def service(rows: list[dict], values: dict[UUID, float]) -> SearchService:  # type: ignore[type-arg]
    return SearchService(
        FakeStore(rows),  # type: ignore[arg-type]
        min_relevance=0.25, candidate_pool=100,
        weights=WEIGHTS, lender_value=lambda owners: values,
    )  # fmt: skip


def test_better_lender_evidence_ranks_higher_all_else_equal() -> None:
    a, b = uuid4(), uuid4()
    rows = [row(b), row(a)]
    out = service(rows, {a: 0.9, b: 0.5}).search(uuid4(), "drill", SearchFilters())
    assert [r["owner_id"] for r in out.results] == [a, b]
    gap = out.results[0]["rank_score"] - out.results[1]["rank_score"]
    assert gap == pytest.approx(0.12, abs=1e-6)


def test_a_new_lender_at_the_baseline_is_not_below_a_lender_with_that_value() -> None:  # C5
    new, seasoned = uuid4(), uuid4()
    out = service([row(new), row(seasoned)], {new: 0.7, seasoned: 0.7}).search(
        uuid4(), "drill", SearchFilters()
    )
    assert out.results[0]["rank_score"] == pytest.approx(out.results[1]["rank_score"])


def test_freshness_halves_every_half_life_and_same_community_adds_a_tenth() -> None:
    o = uuid4()
    out = service([row(o, 30), row(o, 0, same=False)], {o: 0.5}).search(
        uuid4(), "drill", SearchFilters()
    )
    by_fresh = {round(r["score_parts"]["freshness"], 2): r for r in out.results}
    assert set(by_fresh) == {0.5, 1.0}
    # 0.1 from same community outweighs 0.05 * 0.5 freshness lost: old same-community item first
    assert out.results[0]["same_community"] is True


def test_scores_are_not_part_of_the_api_model() -> None:  # NFR-U-01
    from app.api.schemas import SearchResultOut

    assert "rank_score" not in SearchResultOut.model_fields
    assert "score_parts" not in SearchResultOut.model_fields
