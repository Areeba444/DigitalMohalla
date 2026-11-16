"""Meaning-based search and its fallback (suite 29, meaning part; plan item A9; ADR-0016).

Needs PostgreSQL with pgvector (CI's pgvector/pgvector:pg16 image); skipped where migration 0004
found no pgvector. The model is a TEST DOUBLE: a tiny deterministic "concept" embedder that maps a
few words to shared directions, so "bore into masonry" and "hammer drill" point the same way. It
tests the plumbing (backfill, exact cosine search, HYBRID mode, fallback), not language quality;
search quality is measured on the frozen query set with the real model (M11).
TC-300 to TC-304, input / expected / actual in each docstring.
"""

import math
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.api import search as search_api
from app.config.engine_config import load_engine_config
from app.domain.scheduler.runner import JobRunner
from app.domain.search.embedding import DIMS, ModelUnavailable
from app.infra.db.embeddings import table_exists
from app.infra.db.jobs import unit_of_work_factory
from app.infra.jobs.embeddings import EmbeddingBackfill
from tests.integration.search_world import S
from tests.integration.test_search import client, login  # noqa: F401 - shared fixture

CONCEPTS = {
    0: {"drill", "hole", "holes", "bore", "masonry", "brick", "wall", "walls"},
    1: {"ladder", "step", "high", "reach", "seerhi", "climb", "aluminium"},
    2: {"mixer", "cake", "cakes", "dough", "bake", "baking"},
    3: {"screwdriver", "screw", "bits", "fix", "repair"},
}


class ConceptEmbedder:
    """Test double for IEmbed: a word counts towards its concept's direction; other words are
    ignored. Unit length, DIMS numbers, deterministic."""

    model_name = "test-concepts-v1"
    dims = DIMS

    def __init__(self, broken: bool = False) -> None:
        self.broken = broken
        self.calls = 0

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if self.broken:
            raise ModelUnavailable("test: model down")
        out = []
        for t in texts:
            self.calls += 1
            v = [0.0] * DIMS
            for word in t.lower().replace(".", " ").replace(",", " ").split():
                for dim, words in CONCEPTS.items():
                    if word in words:
                        v[dim] += 1.0
            if not any(v):
                v[DIMS - 1] = 1.0
            norm = math.sqrt(sum(x * x for x in v))
            out.append([x / norm for x in v])
        return out


@pytest.fixture
def pgvector(engine: Engine) -> None:
    with engine.connect() as c:
        if not table_exists(c):
            pytest.skip("pgvector is not available on this test database (migration 0004)")


def backfill(engine: Engine, embedder: ConceptEmbedder) -> int:
    runner = JobRunner(
        _NoLock(),
        unit_of_work_factory(engine, load_engine_config(), datetime.now(UTC)),
        [EmbeddingBackfill(embedder)],
        max_attempts=3,
    )
    return runner.run_due_jobs(datetime.now(UTC)).jobs["embedding_backfill"].ran


class _NoLock:
    @contextmanager
    def lock(self) -> Iterator[bool]:
        yield True


def find(client: TestClient, **params: object) -> dict:  # noqa: F811
    r = client.get("/api/v1/search", params=params, headers=login(client, "searcher@example.test"))
    assert r.status_code == 200, r.text
    return r.json()


def names(s: S, body: dict) -> list[str]:
    by_id = {str(v): k for k, v in s.items.items()}
    return [by_id.get(r["item_id"], "?") for r in body["results"]]


def test_tc300_backfill_embeds_each_listing_once_and_again_after_an_edit(
    pgvector: None, s: S, engine: Engine
) -> None:
    """Input: run the backfill twice, edit the ladder's description, run again. Expected: every
    published listing embedded once; the rerun embeds nothing; only the edited one again."""
    model = ConceptEmbedder()
    first = backfill(engine, model)
    assert first >= 4 and backfill(engine, model) == 0
    with engine.begin() as c:
        c.execute(
            text(
                "UPDATE item SET description = 'Folds flat, reaches the ceiling fan.' WHERE id = :i"
            ),
            {"i": s.items["ladder"]},
        )
    assert backfill(engine, model) == 1
    with engine.connect() as c:
        n = c.execute(
            text(
                "SELECT count(*) FROM item_embedding WHERE model = 'test-concepts-v1' AND item_id = :i"
            ),
            {"i": s.items["ladder"]},
        ).scalar_one()
    assert n == 1  # updated in place, never duplicated


def test_tc301_meaning_finds_an_item_without_shared_words(
    pgvector: None,
    s: S,
    engine: Engine,
    client: TestClient,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Input: "bore into masonry" (no word in common with "Bosch hammer drill"). Expected: HYBRID
    mode, the drill first with the reason "Similar in meaning to your search"; the log records
    HYBRID with semantic and keyword parts."""
    model = ConceptEmbedder()
    backfill(engine, model)
    monkeypatch.setattr(search_api, "get_embedder", lambda: model)
    body = find(client, q="bore into masonry")
    assert body["mode"] == "HYBRID"
    assert names(s, body)[0] == "drill"
    assert body["results"][0]["reason"].startswith("Similar in meaning")
    with engine.connect() as c:
        mode, parts = c.execute(
            text(
                "SELECT q.mode::text, i.score_parts FROM search_query q JOIN search_impression i "
                "ON i.query_id = q.id AND i.rank = 1 WHERE q.id = :q"
            ),
            {"q": body["query_id"]},
        ).one()
    assert mode == "HYBRID" and {"semantic", "keyword", "relevance"} <= set(parts)


def test_tc302_eligibility_holds_in_hybrid_mode(
    pgvector: None,
    s: S,
    engine: Engine,
    client: TestClient,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I-5 in HYBRID mode. Input: "drill", which every decoy is close to in meaning. Expected: no
    other-community, draft, own or blocking-lender item; still drill and screwdriver set."""
    model = ConceptEmbedder()
    backfill(engine, model)
    monkeypatch.setattr(search_api, "get_embedder", lambda: model)
    body = find(client, q="drill")
    assert body["mode"] == "HYBRID"
    found = set(names(s, body))
    assert not found & {"elsewhere", "draft", "mine", "blocked"}
    assert {"drill", "screw"} <= found


def test_tc303_a_failing_model_falls_back_to_keywords(
    pgvector: None,
    s: S,
    client: TestClient,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-S-02. Input: the model raises. Expected: 200, KEYWORD_ONLY, the keyword results."""
    monkeypatch.setattr(search_api, "get_embedder", lambda: ConceptEmbedder(broken=True))
    body = find(client, q="drill")
    assert body["mode"] == "KEYWORD_ONLY" and names(s, body)[0] == "drill"


def test_tc304_no_model_configured_is_keyword_only(
    s: S,
    client: TestClient,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(search_api, "get_embedder", lambda: None)
    assert find(client, q="drill")["mode"] == "KEYWORD_ONLY"
