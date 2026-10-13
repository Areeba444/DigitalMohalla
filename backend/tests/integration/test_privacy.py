"""Privacy (suite 14; NFR-PR-01, NFR-PR-02, NFR-S-07; TC-58, TC-60).

- Every response model in the OpenAPI spec, followed through every nested model, has no field for
  an address, coordinates, a CNIC, a phone number, an email or a password, and identifies only the
  request, the item or a case, never a person. New endpoints are covered automatically.
- A whole loan through the API: no response contains such a key, and no value looks like an email,
  a CNIC or a pair of coordinates.
- A request payload cannot carry a location: unknown fields are refused; locality comes from the
  stored A11 result (TC-60).
- Log lines and audit rows written during the loop carry none of it either.
Uploads (TC-59, TC-85) are deferred to iteration 2 (decision D20). All data is synthetic.
"""

import json
import logging
import re
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.main import create_app
from tests.integration.conftest import World
from tests.integration.test_api import client, dates, login  # noqa: F401 - shared fixture

FORBIDDEN_FIELD = re.compile(
    r"address|street|latitude|longitude|^lat$|^lng$|^lon$|coordinat|geo|gps|cnic|national"
    r"|phone|email|password",
    re.IGNORECASE,
)
ALLOWED_IDS = {"id", "item_id", "transaction_id"}  # the request, the item, a case; never a person
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
CNIC = re.compile(r"\b\d{5}-?\d{7}-?\d\b")
COORDINATES = re.compile(r"-?\d{1,3}\.\d{4,}\s*,\s*-?\d{1,3}\.\d{4,}")


def response_models() -> dict[str, dict[str, Any]]:
    spec = create_app().openapi()
    schemas = spec["components"]["schemas"]

    def refs(node: Any) -> set[str]:
        found: set[str] = set()
        if isinstance(node, dict):
            if "$ref" in node:
                found.add(node["$ref"].split("/")[-1])
            for v in node.values():
                found |= refs(v)
        elif isinstance(node, list):
            for v in node:
                found |= refs(v)
        return found

    todo = {
        name
        for ops in spec["paths"].values()
        for op in ops.values()
        for code, r in op.get("responses", {}).items()
        if code.startswith("2")
        for name in refs(r)
    }
    seen: dict[str, dict[str, Any]] = {}
    while todo:
        name = todo.pop()
        if name not in seen:
            seen[name] = schemas[name]
            todo |= refs(schemas[name]) - set(seen)
    return seen


def test_tc58_no_response_model_has_a_location_or_identity_field() -> None:
    models = response_models()
    assert len(models) >= 10  # the scan really walks the spec
    for name, schema in models.items():
        for field in schema.get("properties", {}):
            assert not FORBIDDEN_FIELD.search(field), f"{name}.{field}"
            if field.endswith("_id") or field == "id":
                assert field in ALLOWED_IDS, f"{name}.{field} identifies a person?"


def test_tc60_every_request_body_refuses_unknown_fields() -> None:
    """Guards future endpoints: a body model that silently ignores extra fields fails here."""
    spec = create_app().openapi()
    schemas = spec["components"]["schemas"]
    bodies = {
        content["schema"]["$ref"].split("/")[-1]
        for ops in spec["paths"].values()
        for op in ops.values()
        for content in op.get("requestBody", {}).get("content", {}).values()
        if "$ref" in content.get("schema", {})
    }
    assert bodies, "no request bodies found"
    for name in bodies:
        assert schemas[name].get("additionalProperties") is False, f"{name} accepts unknown fields"


def keys_and_strings(node: Any) -> tuple[set[str], list[str]]:
    keys: set[str] = set()
    strings: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            keys.add(k)
            sub_k, sub_s = keys_and_strings(v)
            keys |= sub_k
            strings += sub_s
    elif isinstance(node, list):
        for v in node:
            sub_k, sub_s = keys_and_strings(v)
            keys |= sub_k
            strings += sub_s
    elif isinstance(node, str):
        strings.append(node)
    return keys, strings


def assert_private(body: Any, where: str) -> None:
    keys, strings = keys_and_strings(body)
    assert not [k for k in keys if FORBIDDEN_FIELD.search(k)], where
    for s in strings:
        assert not EMAIL.search(s), (where, s)
        assert not CNIC.search(s), (where, s)
        assert not COORDINATES.search(s), (where, s)


def test_tc58_a_whole_loan_through_the_api_reveals_nothing_personal(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    borrower = login(client, "borrower2@example.test")
    lender = login(client, "lender@example.test")
    item = str(world.items[11])
    seen: list[tuple[str, Any]] = []

    def call(method: str, url: str, headers: dict[str, str], **kw: Any) -> Any:
        r = client.request(method, url, headers=headers, **kw)
        assert r.status_code < 500, (url, r.text)
        seen.append((f"{method} {url} -> {r.status_code}", r.json()))
        return r.json()

    txn = call("POST", "/api/v1/requests", borrower, json={"item_id": item, **dates(90, 3)})[
        "transaction_id"
    ]
    for who in (borrower, lender):
        call("GET", f"/api/v1/requests/{txn}", who)
        call("GET", f"/api/v1/transactions/{txn}/events", who)
        call("GET", "/api/v1/requests", who)
        call("GET", "/api/v1/items", who)
        call("GET", f"/api/v1/items/{item}", who)
    call("GET", "/api/v1/lender/requests", lender)
    call("POST", f"/api/v1/requests/{txn}/accept", borrower)  # refused: audited
    call("POST", f"/api/v1/requests/{txn}/accept", lender)
    call("POST", f"/api/v1/transactions/{txn}/handover/checklist", lender, json={"notes": "ok"})
    call("POST", f"/api/v1/transactions/{txn}/handover/confirm", borrower)
    call("POST", f"/api/v1/transactions/{txn}/return", borrower)
    call("POST", f"/api/v1/transactions/{txn}/return/confirm", lender)
    done = call("POST", f"/api/v1/transactions/{txn}/return/confirm", borrower)
    assert done["state"] == "COMPLETED"
    call("GET", f"/api/v1/requests/{txn}", lender)

    for where, body in seen:
        assert_private(body, where)
    for record in caplog.records:  # NFR-PR-01: nothing personal in log lines
        line = record.getMessage()
        assert not EMAIL.search(line) and not CNIC.search(line), line
        assert not COORDINATES.search(line), line
    with engine.connect() as c:  # audit rows of the refused command
        rows = c.execute(
            text("SELECT row_to_json(a)::text FROM audit_log a WHERE target_id = :t"), {"t": txn}
        ).scalars()
        audited = list(rows)
    assert audited, "the refused accept should be audited"
    for row in audited:
        assert not EMAIL.search(row) and not CNIC.search(row) and not COORDINATES.search(row), row


def test_tc60_a_request_cannot_carry_a_location(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    borrower = login(client, "borrower2@example.test")
    body = {"item_id": str(world.items[12]), **dates(95, 2)}
    for extra in ({"latitude": 33.6844}, {"location": "Sector F-7"}, {"address": "House 1"}):
        r = client.post("/api/v1/requests", json={**body, **extra}, headers=borrower)
        assert r.status_code == 422, (extra, r.text)  # unknown fields are refused
    created = client.post("/api/v1/requests", json=body, headers=borrower)
    assert created.status_code == 201
    txn = created.json()["transaction_id"]
    with engine.connect() as c:
        payload = c.execute(
            text(
                "SELECT payload FROM lifecycle_event WHERE stream_id = :t "
                "AND event_type = 'request_created'"
            ),
            {"t": txn},
        ).scalar_one()
    assert not [k for k in payload if FORBIDDEN_FIELD.search(k) or "locat" in k], payload
    assert json.dumps(payload).find("locality") == -1  # read from the stored A11 result instead
    client.post(f"/api/v1/requests/{txn}/cancel", headers=borrower)
