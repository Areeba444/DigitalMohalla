"""Keyword search, eligibility, filters and sorts (suite 29, keyword part; plan item F10).

FR-S-02, FR-S-03, issue I-5. A dedicated synthetic community with a searcher, two lenders, a
lender who blocked the searcher, and items in another community, so eligibility can be checked
exactly. TC-280 to TC-286, input / expected / actual in each docstring.
"""

from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.config.settings import get_settings
from app.domain.search.service import query_words
from app.main import create_app
from tests.integration.search_world import PASSWORD, S  # the shared fixture `s` is in conftest


@pytest.fixture
def client(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    get_settings.cache_clear()
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


def login(client: TestClient, email: str) -> dict[str, str]:
    token = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {token.json()['access_token']}"}


def find(client: TestClient, **params: object) -> dict:
    token = client.post(
        "/api/v1/auth/login", json={"email": "searcher@example.test", "password": PASSWORD}
    )
    r = client.get(
        "/api/v1/search",
        params=params,
        headers={"Authorization": f"Bearer {token.json()['access_token']}"},
    )
    assert r.status_code == 200, r.text
    return r.json()


def ids(s: S, body: dict) -> list[str]:
    names = {str(v): k for k, v in s.items.items()}
    return [names.get(r["item_id"], "?") for r in body["results"]]


def test_tc280_keyword_search_ranks_title_matches_with_a_reason(client: TestClient, s: S) -> None:
    """Input: "drill". Expected: KEYWORD_ONLY; the drill (title) first, the screwdriver set
    (description) after it; reason lines in words; no score field in any result."""
    body = find(client, q="drill")
    assert body["mode"] == "KEYWORD_ONLY" and body["query_id"] is not None  # logged (M9)
    assert ids(s, body) == ["drill", "screw"]
    assert body["results"][0]["reason"].startswith("Matches your words in the title")
    assert body["results"][1]["reason"].startswith("Matches your words in the description")
    assert not any(
        k in r for r in body["results"] for k in ("score", "keyword", "relevance", "score_parts")
    )


def test_tc281_other_names_and_typos(client: TestClient, s: S) -> None:
    """Input: "seedhi" (Roman Urdu for ladder) and "ladr" (typo). Expected: the ladder both times."""
    assert ids(s, find(client, q="seedhi")) == ["ladder"]
    assert "ladder" in ids(s, find(client, q="aluminum ladr"))


def test_tc282_eligibility_is_inside_the_query(client: TestClient, s: S) -> None:
    """I-5, suite 29. Input: "drill", then no words. Expected: never the other community's,
    the draft, the searcher's own, or the blocking lender's drill."""
    for body in (find(client, q="drill"), find(client)):
        found = set(ids(s, body))
        assert not found & {"elsewhere", "draft", "mine", "blocked"}
    assert set(ids(s, find(client))) == {"drill", "ladder", "mixer", "screw"}


def test_tc283_filters(client: TestClient, s: S, engine: Engine) -> None:
    """Expected: category, maximum deposit and condition narrow the list; dates leave out an item
    with a held booking in them."""
    with engine.connect() as c:
        kitchen = c.execute(
            text("SELECT id FROM category WHERE name = 'Search kitchen'")
        ).scalar_one()
    assert ids(s, find(client, category=kitchen)) == ["mixer"]
    assert set(ids(s, find(client, max_deposit=300))) == {"ladder", "screw"}
    assert ids(s, find(client, condition="WORN")) == ["screw"]
    start = date.today() + timedelta(days=400)
    period = {"from": str(start), "to": str(start + timedelta(days=2))}
    searcher, lender = (
        login(client, "searcher@example.test"),
        login(client, "slender1@example.test"),
    )
    asked = client.post(
        "/api/v1/requests",
        json={
            "item_id": str(s.items["drill"]),
            "start_date": period["from"],
            "end_date": period["to"],
        },
        headers=searcher,
    )
    assert asked.status_code == 201, asked.text
    # a pending request blocks nothing (ADR-0001): the drill is still available on those dates
    assert "drill" in ids(s, find(client, q="drill", **period))
    txn = asked.json()["transaction_id"]
    accepted = client.post(f"/api/v1/requests/{txn}/accept", headers=lender)
    assert accepted.status_code == 200, (asked.json(), accepted.text)
    assert accepted.json()["state"] == "ACCEPTED"
    body = find(client, q="drill", **period)
    assert "drill" not in ids(s, body) and all(r["available"] for r in body["results"])


def test_tc284_sorts(client: TestClient, s: S) -> None:
    """Expected: newest puts the last inserted listing first; evidence and relevance return the
    same set; same_community is true for the home community."""
    newest = ids(s, find(client, sort="newest"))
    assert newest[0] == "screw" and set(newest) == {"drill", "ladder", "mixer", "screw"}
    assert set(ids(s, find(client, sort="evidence"))) == set(newest)
    assert all(r["same_community"] for r in find(client)["results"])


def test_tc285_bad_input(client: TestClient) -> None:
    token = client.post(
        "/api/v1/auth/login", json={"email": "searcher@example.test", "password": PASSWORD}
    )
    h = {"Authorization": f"Bearer {token.json()['access_token']}"}
    assert client.get("/api/v1/search", params={"from": "2030-01-01"}, headers=h).status_code == 422
    assert client.get("/api/v1/search", params={"sort": "price"}, headers=h).status_code == 422
    assert client.get("/api/v1/search").status_code == 401


def test_tc286_query_syntax_cannot_reach_postgres() -> None:
    assert query_words("drill & | !:* (x)") == ["drill", "x"]
    assert query_words("SEEDHI") == ["seedhi"]
    assert query_words("") == []
