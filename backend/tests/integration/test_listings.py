"""Listings (plan item F9, FR-B-01, UC-B1): create, draft, edit, publish and pause.

TC-180 to TC-186, input / expected / actual in each docstring. Also shows the same member lending
and borrowing: the borrower of the iteration 1 loop lists an item that another member requests.
All users and items are synthetic.
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.integration.conftest import World
from tests.integration.test_api import client, dates, login  # noqa: F401 - shared fixture


def category(engine: Engine) -> int:
    with engine.connect() as c:
        return int(c.execute(text("SELECT id FROM category WHERE name = 'Tools'")).scalar_one())


def body(world: World, engine: Engine, **extra: object) -> dict:
    return {
        "community_id": str(world.community),
        "title": "Synthetic ladder 3 m",
        "category_id": category(engine),
        "value_band": "MEDIUM",
        "deposit_amount": 500,
        **extra,
    }


def test_tc180_draft_then_publish_needs_description_and_condition(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: a draft with only title, category and value; publish it; add description and
    condition; publish again. Expected: DRAFT; 422 naming what is missing; PUBLISHED."""
    h = login(client, "borrower@example.test")
    draft = client.post("/api/v1/items", json=body(world, engine), headers=h)
    assert draft.status_code == 201, draft.text
    item = draft.json()
    assert (item["status"], item["is_yours"], item["owner_name"]) == ("DRAFT", True, "Borrower")
    url = f"/api/v1/items/{item['id']}"
    early = client.patch(url, json={"status": "PUBLISHED"}, headers=h)
    assert early.status_code == 422 and "description and condition" in early.json()["detail"]
    done = client.patch(
        url,
        json={
            "status": "PUBLISHED",
            "description": "Aluminium step ladder, folds flat.",
            "condition": "GOOD",
            "search_terms": "seedhi",
            "usage_terms": "Indoor use only",
        },
        headers=h,
    )
    assert done.status_code == 200, done.text
    assert (done.json()["status"], done.json()["search_terms"]) == ("PUBLISHED", "seedhi")
    with engine.connect() as c:
        tsv = c.execute(
            text(
                "SELECT search_tsv @@ plainto_tsquery('simple', 'seedhi') FROM item WHERE id = :i"
            ),
            {"i": item["id"]},
        ).scalar_one()
    assert tsv is True  # the Roman Urdu name is searchable by keyword (DA-23)


def test_tc181_only_members_list_and_only_owners_edit(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: a member of another community lists here; another member edits the listing.
    Expected: 403 both times."""
    h = login(client, "borrower@example.test")
    with engine.begin() as c:
        other = c.execute(
            text(
                "INSERT INTO community (name, join_code) VALUES ('Synthetic F9', 'SF9') RETURNING id"
            )
        ).scalar_one()
    outside = client.post(
        "/api/v1/items", json={**body(world, engine), "community_id": str(other)}, headers=h
    )
    assert outside.status_code == 403
    mine = client.post("/api/v1/items", json=body(world, engine), headers=h).json()
    stranger = login(client, "borrower2@example.test")
    edit = client.patch(f"/api/v1/items/{mine['id']}", json={"title": "x"}, headers=stranger)
    assert edit.status_code == 403


def test_tc182_drafts_are_private_and_published_items_are_not(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: another member opens a draft, then the same listing published. Expected: 404, then
    200 with the condition and terms, and booked dates."""
    owner = login(client, "borrower@example.test")
    other = login(client, "borrower2@example.test")
    item = client.post("/api/v1/items", json=body(world, engine), headers=owner).json()
    url = f"/api/v1/items/{item['id']}"
    assert client.get(url, headers=other).status_code == 404
    assert client.get(url, headers=owner).status_code == 200
    client.patch(
        url,
        json={"status": "PUBLISHED", "description": "Synthetic.", "condition": "FAIR"},
        headers=owner,
    )
    seen = client.get(url, headers=other).json()
    assert (seen["condition"], seen["is_yours"], seen["booked_periods"]) == ("FAIR", False, [])
    mine = client.get("/api/v1/me/items", headers=owner).json()
    assert item["id"] in {m["id"] for m in mine}


def test_tc183_pause_and_republish(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: publish, pause, then try DRAFT. Expected: PAUSED stops new requests (G1); a published
    listing cannot go back to DRAFT (409)."""
    h = login(client, "borrower@example.test")
    item = client.post(
        "/api/v1/items",
        json=body(world, engine, publish=True, description="Synthetic.", condition="NEW"),
        headers=h,
    ).json()
    url = f"/api/v1/items/{item['id']}"
    assert client.patch(url, json={"status": "PAUSED"}, headers=h).json()["status"] == "PAUSED"
    req = client.post(
        "/api/v1/requests",
        json={"item_id": item["id"], **dates(5, 2)},
        headers=login(client, "borrower2@example.test"),
    )
    assert req.status_code == 409 and "not published" in req.json()["detail"]
    assert client.patch(url, json={"status": "DRAFT"}, headers=h).status_code == 409
    assert (
        client.patch(url, json={"status": "PUBLISHED"}, headers=h).json()["status"] == "PUBLISHED"
    )


def test_tc184_one_member_lends_and_borrows(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: "Borrower" publishes an item; "Borrower2" requests it. Expected: the request reaches
    the new lender, whose role on that loan is LENDER while they stay BORROWER on their own loans."""
    lender = login(client, "borrower@example.test")
    item = client.post(
        "/api/v1/items",
        json=body(world, engine, publish=True, description="Synthetic drill.", condition="GOOD"),
        headers=lender,
    ).json()
    req = client.post(
        "/api/v1/requests",
        json={"item_id": item["id"], **dates(60, 2)},
        headers=login(client, "borrower2@example.test"),
    )
    assert req.status_code == 201, req.text
    txn = req.json()["transaction_id"]
    seen = client.get(f"/api/v1/requests/{txn}", headers=lender).json()
    assert seen["your_role"] == "LENDER"
    roles = {r["your_role"] for r in client.get("/api/v1/requests", headers=lender).json()}
    assert "LENDER" in roles


def test_tc185_bad_input_is_refused(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Expected 422: negative deposit, unknown condition, unknown category, past end date, stray
    field (no location may be smuggled in)."""
    h = login(client, "borrower@example.test")
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    cases = [
        {"deposit_amount": -1},
        {"condition": "BROKEN"},
        {"category_id": 9999},
        {"publish": True, "description": "x", "condition": "GOOD", "expires_at": past},
        {"address": "somewhere"},
    ]
    for extra in cases:
        r = client.post("/api/v1/items", json=body(world, engine, **extra), headers=h)
        assert r.status_code == 422, (extra, r.text)


def test_tc186_categories_listed(client: TestClient, world: World) -> None:  # noqa: F811
    h = login(client, "borrower@example.test")
    names = [c["name"] for c in client.get("/api/v1/categories", headers=h).json()]
    assert "Tools" in names
