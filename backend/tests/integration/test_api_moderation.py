"""Moderation through the REST API (UC-I4, UC-D6; TC-54; NFR-S-02, NFR-PR-01).

The app here uses an engine that holds every request for a moderator, so the second synthetic
borrower's request lands in the queue. The request is cancelled at the end. The password is a
throwaway test value for this test database only. All data is synthetic.
"""

import json
import re
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.config.settings import get_settings
from app.domain.accounts.auth import hash_password
from app.main import create_app
from tests.integration.conftest import World
from tests.integration.test_api import TEST_PASSWORD, dates, login
from tests.integration.test_moderation import HighValueHold

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


@pytest.fixture
def holding_client(
    engine: Engine, world: World, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    get_settings.cache_clear()
    with engine.begin() as conn:
        for uid in (world.borrower2, world.lender, world.moderator):
            conn.execute(
                text("UPDATE app_user SET password_hash = :h WHERE id = :i"),
                {"h": hash_password(TEST_PASSWORD), "i": uid},
            )
    yield TestClient(create_app(engine=engine, assess=HighValueHold()))
    get_settings.cache_clear()


def test_moderator_queue_case_and_decision(holding_client: TestClient, world: World) -> None:
    client = holding_client
    borrower = login(client, "borrower2@example.test")
    lender = login(client, "lender@example.test")
    moderator = login(client, "moderator@example.test")
    created = client.post(
        "/api/v1/requests", json={"item_id": str(world.items[10]), **dates(70, 3)}, headers=borrower
    )
    assert created.json()["state"] == "HELD_FOR_REVIEW", created.text
    txn = created.json()["transaction_id"]

    queue = client.get("/api/v1/moderation/cases", headers=moderator)
    assert queue.status_code == 200
    [row] = [c for c in queue.json() if c["transaction_id"] == txn]
    assert (row["trigger_type"], row["hold_reason"]) == (
        "HIGH_VALUE_LOW_CONFIDENCE",
        "high_value_low_confidence",
    )
    assert client.get("/api/v1/moderation/cases", headers=borrower).json() == []

    case = client.get(f"/api/v1/moderation/cases/{row['id']}", headers=moderator)
    assert case.status_code == 200
    body = case.json()
    assert body["borrower_name"] == "Borrower2" and body["decisions"] == []
    assert set(UUID_RE.findall(json.dumps(body))) <= {row["id"], txn}  # no ids of people
    assert client.get(f"/api/v1/moderation/cases/{row['id']}", headers=borrower).status_code == 403

    decide = f"/api/v1/moderation/cases/{row['id']}/decision"
    assert (
        client.post(decide, json={"kind": "CLEARED", "reason": ""}, headers=moderator).status_code
        == 422
    )
    blank = client.post(decide, json={"kind": "CLEARED", "reason": "   "}, headers=moderator)
    assert blank.status_code == 422  # TC-54: refused by the decision rules
    assert (
        client.post(decide, json={"kind": "CLEARED", "reason": "x"}, headers=borrower).status_code
        == 403
    )
    done = client.post(
        decide,
        json={
            "kind": "SAFEGUARDS_IMPOSED",
            "reason": "Similar items returned well.",
            "safeguards": ["Deposit record"],
        },
        headers=moderator,
    )
    assert done.status_code == 200 and done.json()["state"] == "ASSESSED"
    seen = client.get(f"/api/v1/requests/{txn}", headers=lender).json()
    assert seen["moderator_safeguards"] == [{"label": "Deposit record"}]
    assert (
        client.post(
            decide, json={"kind": "CLEARED", "reason": "again"}, headers=moderator
        ).status_code
        == 409
    )
    client.post(f"/api/v1/requests/{txn}/cancel", headers=borrower)
