"""Search log (suite 30, logging part; plan item M9; FR-S-05, NFR-PR-01).

Each search writes one query row and one impression per shown result, in rank order; a click is
recorded only for a shown result of the member's own search; the log holds no location and cannot be
edited. TC-290 to TC-294, input / expected / actual in each docstring. Uses the synthetic community
of the search tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError

from tests.integration.search_world import S
from tests.integration.test_search import client, login  # noqa: F401 - shared fixture


def search(client: TestClient, who: str = "searcher", **params: object) -> dict:  # noqa: F811
    r = client.get("/api/v1/search", params=params, headers=login(client, f"{who}@example.test"))
    assert r.status_code == 200, r.text
    return r.json()


def test_tc290_a_search_is_logged_with_its_impressions(
    client: TestClient,  # noqa: F811
    s: S,  # noqa: F811
    engine: Engine,
) -> None:
    """Input: "drill" with a deposit filter. Expected: a query_id; one query row with the text,
    mode, config version, result count and latency; impressions in rank order with score parts;
    no location key anywhere in the row."""
    body = search(client, q="drill", max_deposit=5000)
    qid = body["query_id"]
    assert qid is not None
    with engine.connect() as c:
        row = (
            c.execute(
                text(
                    "SELECT query_text, mode::text, config_version, result_count, latency_ms, filters "
                    "FROM search_query WHERE id = :q"
                ),
                {"q": qid},
            )
            .mappings()
            .one()
        )
        shown = c.execute(
            text(
                "SELECT rank, item_id::text, score_parts FROM search_impression WHERE query_id = :q ORDER BY rank"
            ),
            {"q": qid},
        ).all()
    assert (row["query_text"], row["mode"], row["result_count"]) == (
        "drill",
        "KEYWORD_ONLY",
        len(body["results"]),
    )
    assert row["config_version"].startswith("1.") and row["latency_ms"] >= 0
    assert row["filters"]["max_deposit"] == "5000.0" and row["filters"]["sort"] == "relevance"
    assert not {"lat", "lng", "latitude", "longitude", "location", "address"} & set(row["filters"])
    assert [r[1] for r in shown] == [x["item_id"] for x in body["results"]]
    assert [r[0] for r in shown] == list(range(1, len(shown) + 1))
    assert all("keyword" in r[2] for r in shown)


def test_tc291_clicks_only_on_shown_results_of_your_own_search(
    client: TestClient,  # noqa: F811
    s: S,  # noqa: F811
    engine: Engine,
) -> None:
    """Input: click the first result; click an item that was not shown; another member clicks this
    search. Expected: 202; 404; 404. The other shown result counts as ignored."""
    body = search(client, q="drill")
    qid, first = body["query_id"], body["results"][0]["item_id"]
    h = login(client, "searcher@example.test")
    ok = client.post(f"/api/v1/search/{qid}/clicks", json={"item_id": first}, headers=h)
    assert ok.status_code == 202, ok.text
    not_shown = str(s.items["mixer"])
    assert (
        client.post(
            f"/api/v1/search/{qid}/clicks", json={"item_id": not_shown}, headers=h
        ).status_code
        == 404
    )
    other = login(client, "slender1@example.test")
    assert (
        client.post(
            f"/api/v1/search/{qid}/clicks", json={"item_id": first}, headers=other
        ).status_code
        == 404
    )
    with engine.connect() as c:
        ignored = c.execute(
            text(
                "SELECT count(*) FROM search_impression i WHERE i.query_id = :q AND NOT EXISTS "
                "(SELECT 1 FROM search_click k WHERE k.query_id = i.query_id AND k.item_id = i.item_id)"
            ),
            {"q": qid},
        ).scalar_one()
    assert ignored == len(body["results"]) - 1


def test_tc292_browsing_without_words_is_not_logged(
    client: TestClient,  # noqa: F811
    s: S,  # noqa: F811
) -> None:
    assert search(client)["query_id"] is None


def test_tc293_the_log_is_append_only(
    client: TestClient,  # noqa: F811
    s: S,  # noqa: F811
    engine: Engine,
) -> None:
    """Expected: updating or deleting a logged query is refused by the database."""
    qid = search(client, q="ladder")["query_id"]
    for sql in (
        "UPDATE search_query SET query_text = 'x' WHERE id = :q",
        "DELETE FROM search_query WHERE id = :q",
    ):
        with pytest.raises(DBAPIError), engine.begin() as c:
            c.execute(text(sql), {"q": qid})


def test_tc294_paging_continues_the_rank(
    client: TestClient,  # noqa: F811
    s: S,  # noqa: F811
    engine: Engine,
) -> None:
    """Input: page 2 of a short result list. Expected: no results and no impressions, but the
    query is still logged (result count 0)."""
    body = search(client, q="drill", page=2)
    with engine.connect() as c:
        n = c.execute(
            text("SELECT result_count FROM search_query WHERE id = :q"), {"q": body["query_id"]}
        ).scalar_one()
    assert body["results"] == [] and n == 0
