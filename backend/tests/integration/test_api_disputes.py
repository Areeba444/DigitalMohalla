"""Disputes through the REST API (UC-B12, UC-D6; TC-50 to TC-52; NFR-S-02, NFR-PR-01).

Uses the second synthetic borrower, so the open dispute never touches the assessments other API
tests expect for the first one. The dispute is withdrawn at the end. All data is synthetic.
"""

import json
import re

from fastapi.testclient import TestClient

from tests.integration.conftest import World
from tests.integration.test_api import client, dates, login  # noqa: F401 - shared fixture

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def test_raise_read_and_withdraw_a_dispute(client: TestClient, world: World) -> None:  # noqa: F811
    borrower = login(client, "borrower2@example.test")
    lender = login(client, "lender@example.test")
    created = client.post(
        "/api/v1/requests",
        json={"item_id": str(world.items[2]), **dates(40, 3)},
        headers=borrower,
    )
    assert created.status_code == 201, created.text
    txn = created.json()["transaction_id"]
    client.post(f"/api/v1/requests/{txn}/accept", headers=lender)
    client.post(f"/api/v1/transactions/{txn}/handover/checklist", json={}, headers=lender)
    assert (
        client.post(f"/api/v1/transactions/{txn}/handover/confirm", headers=borrower).json()[
            "state"
        ]
        == "ACTIVE"
    )
    detail = client.get(f"/api/v1/requests/{txn}", headers=lender).json()
    assert "raise_dispute" in detail["available_actions"]

    bad = client.post(
        f"/api/v1/transactions/{txn}/dispute", json={"reason": "BOGUS"}, headers=lender
    )
    assert bad.status_code == 422
    raised = client.post(
        f"/api/v1/transactions/{txn}/dispute",
        json={"reason": "DAMAGE", "description": "Synthetic: a dent on the side."},
        headers=lender,
    )
    assert raised.status_code == 200 and raised.json()["state"] == "DISPUTED"

    trail = client.get(f"/api/v1/transactions/{txn}/dispute", headers=borrower)
    assert trail.status_code == 200
    body = trail.json()
    assert body["case"]["raised_by_role"] == "LENDER"
    assert (body["case"]["dispute_reason"], body["case"]["status"]) == ("DAMAGE", "OPEN")
    assert body["available_actions"] == []  # the borrower did not raise it
    # ids in the response: only the case, the request and nothing about the people
    assert set(UUID_RE.findall(json.dumps(body))) <= {body["case"]["id"], txn}

    other = client.post(f"/api/v1/transactions/{txn}/dispute/withdraw", headers=borrower)
    assert other.status_code == 403  # TC-52
    frozen = client.post(f"/api/v1/transactions/{txn}/return", headers=borrower)
    assert frozen.status_code == 409  # the loan is frozen
    withdrawn = client.post(f"/api/v1/transactions/{txn}/dispute/withdraw", headers=lender)
    assert withdrawn.status_code == 200 and withdrawn.json()["state"] == "ACTIVE"  # TC-51
    assert (
        client.get(f"/api/v1/transactions/{txn}/dispute", headers=lender).json()["case"]["status"]
        == "WITHDRAWN"
    )


def test_no_case_is_404_and_strangers_are_403(client: TestClient, world: World) -> None:  # noqa: F811
    borrower = login(client, "borrower2@example.test")
    created = client.post(
        "/api/v1/requests", json={"item_id": str(world.items[1]), **dates(50, 2)}, headers=borrower
    )
    txn = created.json()["transaction_id"]
    assert client.get(f"/api/v1/transactions/{txn}/dispute", headers=borrower).status_code == 404
    stranger = login(client, "borrower@example.test")
    assert client.get(f"/api/v1/transactions/{txn}/dispute", headers=stranger).status_code == 403
    client.post(f"/api/v1/requests/{txn}/cancel", headers=borrower)
