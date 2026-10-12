"""The Slice A loop through the REST API, with real login (Architecture_Design.md section 4).

Traces: FR-A-04 (part), NFR-S-01, NFR-S-02, NFR-PR-01, test plan suites 1, 4 and 14 (in part).
All users are synthetic. The password below is a throwaway test value for this test database only.
"""

from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.config.settings import get_settings
from app.domain.accounts.auth import hash_password
from app.main import create_app
from tests.integration.conftest import World

TEST_PASSWORD = "synthetic-test-password"  # noqa: S105 - test value, not a real credential
FORBIDDEN_KEYS = ("latitude", "longitude", "address", "cnic", "password", "coordinates")


@pytest.fixture
def client(engine: Engine, world: World, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    get_settings.cache_clear()
    with engine.begin() as conn:
        for uid in (world.borrower, world.lender, world.borrower2):
            conn.execute(
                text("UPDATE app_user SET password_hash = :h WHERE id = :i"),
                {"h": hash_password(TEST_PASSWORD), "i": uid},
            )
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


def login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def dates(start_in: int, length: int) -> dict[str, str]:
    start = date.today() + timedelta(days=start_in)
    return {
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=length)).isoformat(),
    }


def test_full_loop_through_the_api(client: TestClient, world: World) -> None:
    borrower = login(client, "borrower@example.test")
    lender = login(client, "lender@example.test")
    item = str(world.items[18])

    created = client.post(
        "/api/v1/requests", json={"item_id": item, **dates(3, 3)}, headers=borrower
    )
    assert created.status_code == 201, created.text
    txn = created.json()["transaction_id"]
    assert created.json()["state"] == "ASSESSED"

    detail = client.get(f"/api/v1/requests/{txn}", headers=lender).json()
    assert detail["assessment"]["assurance_state"] == "INSUFFICIENT_EVIDENCE"
    assert "Insufficient verified history" in detail["assessment"]["explanation"]
    queue = client.get("/api/v1/lender/requests?state=ASSESSED", headers=lender).json()
    assert txn in [row["id"] for row in queue]

    assert (
        client.post(f"/api/v1/requests/{txn}/accept", headers=lender).json()["state"] == "ACCEPTED"
    )
    assert (
        client.post(
            f"/api/v1/transactions/{txn}/handover/checklist", json={}, headers=lender
        ).status_code
        == 200
    )
    handover = client.post(f"/api/v1/transactions/{txn}/handover/confirm", headers=borrower)
    assert handover.json()["state"] == "ACTIVE"
    assert client.post(f"/api/v1/transactions/{txn}/return", headers=borrower).json()["state"] == (
        "RETURN_INITIATED"
    )
    client.post(f"/api/v1/transactions/{txn}/return/confirm", headers=lender)
    done = client.post(f"/api/v1/transactions/{txn}/return/confirm", headers=borrower)
    assert done.json()["state"] == "COMPLETED"

    events = client.get(f"/api/v1/transactions/{txn}/events", headers=borrower).json()
    assert [e["new_state"] for e in events][-1] == "COMPLETED"
    assert len(events) == 8


def test_requests_need_a_login(client: TestClient, world: World) -> None:
    body = {"item_id": str(world.items[18]), **dates(3, 3)}
    assert client.post("/api/v1/requests", json=body).status_code == 401
    bad = {"Authorization": "Bearer not-a-real-token"}
    assert client.post("/api/v1/requests", json=body, headers=bad).status_code == 401


def test_wrong_password_gives_a_generic_error(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": "borrower@example.test", "password": "wrong"}
    )
    unknown = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.test", "password": "wrong"}
    )
    assert response.status_code == unknown.status_code == 401
    assert response.json() == unknown.json()  # does not reveal which emails exist


def test_non_lender_cannot_accept_and_invalid_move_is_409(client: TestClient, world: World) -> None:
    borrower = login(client, "borrower@example.test")
    other = login(client, "borrower2@example.test")
    created = client.post(
        "/api/v1/requests", json={"item_id": str(world.items[19]), **dates(3, 3)}, headers=borrower
    )
    txn = created.json()["transaction_id"]
    assert client.post(f"/api/v1/requests/{txn}/accept", headers=other).status_code == 403
    assert client.post(f"/api/v1/requests/{txn}/cancel", headers=borrower).status_code == 200
    assert client.post(f"/api/v1/requests/{txn}/cancel", headers=borrower).status_code == 409


def test_dates_must_be_in_order(client: TestClient, world: World) -> None:
    borrower = login(client, "borrower@example.test")
    today = date.today().isoformat()
    response = client.post(
        "/api/v1/requests",
        json={"item_id": str(world.items[0]), "start_date": today, "end_date": today},
        headers=borrower,
    )
    assert response.status_code == 422


def test_responses_carry_no_location_or_secret_fields(client: TestClient, world: World) -> None:
    """Suite 14 (in part): no address, coordinates, CNIC or password field in what the API returns."""
    borrower = login(client, "borrower@example.test")
    created = client.post(
        "/api/v1/requests", json={"item_id": str(world.items[17]), **dates(20, 2)}, headers=borrower
    )
    txn = created.json()["transaction_id"]
    bodies = [
        created.text,
        client.get(f"/api/v1/requests/{txn}", headers=borrower).text,
        client.get(f"/api/v1/transactions/{txn}/events", headers=borrower).text,
        client.get(f"/api/v1/items/{world.items[17]}", headers=borrower).text,
    ]
    for body in bodies:
        for key in FORBIDDEN_KEYS:
            assert key not in body.lower(), f"{key!r} found in a response"


def test_ui_endpoints_names_actions_and_lists(client: TestClient, world: World) -> None:
    """What the screens need: browse, my requests, names, evidence with a separate risk band."""
    borrower = login(client, "borrower@example.test")
    lender = login(client, "lender@example.test")
    item = str(world.items[16])

    browse = client.get("/api/v1/items", headers=borrower).json()
    assert item in [i["id"] for i in browse]
    assert not client.get("/api/v1/items", headers=lender).json()  # owner sees none of own items

    txn = client.post(
        "/api/v1/requests",
        json={"item_id": item, **dates(30, 3), "message": "for a shelf"},
        headers=borrower,
    ).json()["transaction_id"]
    mine = client.get("/api/v1/requests", headers=borrower).json()
    row = next(r for r in mine if r["id"] == txn)
    assert (row["your_role"], row["counterpart_name"]) == ("BORROWER", "Lender")

    as_lender = client.get(f"/api/v1/requests/{txn}", headers=lender).json()
    assert as_lender["available_actions"] == ["accept", "decline"]
    assert as_lender["borrower_name"] == "Borrower"
    assert as_lender["message"] == "for a shelf"
    assert as_lender["assessment"]["manipulation_level"] == 1  # shown apart from reliability
    as_borrower = client.get(f"/api/v1/requests/{txn}", headers=borrower).json()
    assert as_borrower["available_actions"] == ["cancel"]

    client.post(f"/api/v1/requests/{txn}/accept", headers=lender)
    after = client.get(f"/api/v1/requests/{txn}", headers=borrower).json()
    assert after["available_actions"] == []  # nothing to do until the lender's checklist
    client.post(
        f"/api/v1/transactions/{txn}/handover/checklist", json={"notes": "ok"}, headers=lender
    )
    after = client.get(f"/api/v1/requests/{txn}", headers=borrower).json()
    assert after["available_actions"] == ["handover_confirm"]
    assert [r["reporter_role"] for r in after["reports"]] == ["LENDER"]


def test_cors_allows_the_expo_web_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/requests",
        headers={"Origin": "http://localhost:8081", "Access-Control-Request-Method": "POST"},
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8081"


def test_cors_allows_any_localhost_port_in_development(client: TestClient) -> None:
    """Expo picks another port when 8081 is busy, so any localhost port must work (and nothing else)."""
    ok = client.options(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:8082", "Access-Control-Request-Method": "POST"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:8082"
    other = client.options(
        "/api/v1/auth/login",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in other.headers
