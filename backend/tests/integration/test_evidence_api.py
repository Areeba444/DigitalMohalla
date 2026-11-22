"""Evidence on the API (A5, A7, A10; FR-T-02, FR-T-08, FR-S-04, NFR-U-01; TC-310 to TC-312).

Uses the shared synthetic search community: nobody there has loan history, so every factor must say
"not enough verified history yet" (an absence of evidence, never a negative finding), no number is
returned for ranking, and a lender with no history is still listed. All data is synthetic.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.config.settings import get_settings
from app.main import create_app
from tests.integration.search_world import PASSWORD, S


@pytest.fixture
def client(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    get_settings.cache_clear()
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


def auth(client: TestClient) -> dict[str, str]:
    r = client.post(
        "/api/v1/auth/login", json={"email": "searcher@example.test", "password": PASSWORD}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_tc310_my_evidence_is_per_role_and_metric_never_one_number(
    client: TestClient, s: S
) -> None:
    """Input: a member with no loans. Expected: two roles, borrower with 3 factors and lender with
    2, each 'enough' false, no estimate, the not-a-negative-finding note, and no score field."""
    r = client.get("/api/v1/me/evidence", headers=auth(client))
    assert r.status_code == 200, r.text
    roles = {x["role"]: x["factors"] for x in r.json()["roles"]}
    assert [f["metric"] for f in roles["BORROWER"]] == [
        "ON_TIME_RETURN",
        "CONDITION_AGREED",
        "DISPUTE_FREE",
    ]
    assert [f["metric"] for f in roles["LENDER"]] == ["CONDITION_AGREED", "DISPUTE_FREE"]
    for f in roles["BORROWER"] + roles["LENDER"]:
        assert f["enough"] is False and f["estimate"] is None and f["verified_loans"] == 0
        assert "not a negative finding" in f["note"]
    assert not any(k in r.json() for k in ("score", "trust", "rating"))


def test_tc311_item_details_show_the_lenders_evidence_not_the_own_listing(
    client: TestClient, s: S
) -> None:
    """Input: open a lender's item. Expected: lender_evidence with has_history false and factors."""
    r = client.get(f"/api/v1/items/{s.items['drill']}", headers=auth(client))
    assert r.status_code == 200, r.text
    ev = r.json()["lender_evidence"]
    assert ev["has_history"] is False and len(ev["factors"]) == 2
    assert all(f["estimate"] is None for f in ev["factors"])


def test_tc312_search_lists_new_lenders_with_evidence_and_no_score(
    client: TestClient, s: S
) -> None:
    """Input: "drill". Expected: results still returned (a lender without history is not
    dropped, claim C5), each with lender_evidence and no rank score or part."""
    r = client.get("/api/v1/search", params={"q": "drill"}, headers=auth(client))
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    assert results and all(x["lender_evidence"]["has_history"] is False for x in results)
    assert not any(k in x for x in results for k in ("rank_score", "score_parts", "relevance"))
