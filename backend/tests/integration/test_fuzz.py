"""TC-84 (suite 17, NFR-S-02): malformed and hostile input never causes a 500 or leaks internals.

Hypothesis generates injection strings, control and NUL characters, odd Unicode, oversized text,
malformed dates and identifiers for the request body, the path ids and the checklist body. Every
answer must be a client error or a success, and no response may contain database or traceback text.
Requests that do get created are cancelled again. Uses Hypothesis (already a test dependency) in
place of Schemathesis. All data is synthetic.
"""

from typing import Any
from urllib.parse import quote

from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests.integration.conftest import World
from tests.integration.test_api import client, dates, login  # noqa: F401 - shared fixture

NUL = chr(0)
HOSTILE = [
    "'; DROP TABLE item; --",
    "' OR '1'='1",
    "<script>alert(1)</script>",
    "../../../etc/passwd",
    "%00",
    NUL,
    "a" + NUL + "b",
    "{{7*7}}${7*7}",
    chr(0x202E) + "evil",
    "x" * 5000,
    "",
]
LEAKS = ("psycopg", "sqlalchemy", "traceback", "select ", "insert ", 'relation "', "syntax error")
FUZZ = settings(
    max_examples=60, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
texts = st.one_of(st.sampled_from(HOSTILE), st.text(max_size=300))
weird_dates: st.SearchStrategy[Any] = st.one_of(
    st.dates().map(str), st.text(max_size=12), st.integers(), st.none()
)


def check(response: Any) -> None:
    assert response.status_code < 500, (response.status_code, response.text[:300])
    lowered = response.text.lower()
    assert not [w for w in LEAKS if w in lowered], response.text[:300]


@FUZZ
@given(
    message=texts, start=weird_dates, end=weird_dates, item=st.one_of(texts, st.uuids().map(str))
)
def test_request_body_fuzz(
    client: TestClient,  # noqa: F811
    world: World,
    message: str,
    start: Any,
    end: Any,
    item: str,
) -> None:
    borrower = login(client, "borrower2@example.test")
    for item_id in (item, str(world.items[13])):
        r = client.post(
            "/api/v1/requests",
            json={"item_id": item_id, "start_date": start, "end_date": end, "message": message},
            headers=borrower,
        )
        check(r)
        if r.status_code == 201:
            client.post(f"/api/v1/requests/{r.json()['transaction_id']}/cancel", headers=borrower)


@FUZZ
@given(message=texts)
def test_hostile_message_on_a_valid_request(
    client: TestClient,  # noqa: F811
    world: World,
    message: str,
) -> None:
    borrower = login(client, "borrower2@example.test")
    r = client.post(
        "/api/v1/requests",
        json={"item_id": str(world.items[14]), **dates(120, 2), "message": message},
        headers=borrower,
    )
    check(r)
    if r.status_code == 201:
        detail = client.get(f"/api/v1/requests/{r.json()['transaction_id']}", headers=borrower)
        check(detail)
        assert detail.json()["message"] == message  # stored as plain text, never interpreted
        client.post(f"/api/v1/requests/{r.json()['transaction_id']}/cancel", headers=borrower)


@FUZZ
@given(raw=texts)
def test_path_id_fuzz(client: TestClient, raw: str) -> None:  # noqa: F811
    borrower = login(client, "borrower2@example.test")
    part = quote(raw, safe="")
    for url in (
        f"/api/v1/requests/{part}",
        f"/api/v1/transactions/{part}/events",
        f"/api/v1/items/{part}",
    ):
        check(client.get(url, headers=borrower))
    check(client.post(f"/api/v1/requests/{part}/accept", headers=borrower))


json_values = st.recursive(
    st.one_of(st.none(), st.booleans(), st.integers(), st.floats(allow_nan=False), texts),
    lambda inner: st.one_of(
        st.lists(inner, max_size=4), st.dictionaries(st.text(max_size=10), inner, max_size=4)
    ),
    max_leaves=12,
)


@FUZZ
@given(
    body=st.dictionaries(
        st.sampled_from(["checklist", "deposit_received", "notes", "x"]), json_values
    )
)
def test_checklist_body_fuzz(client: TestClient, world: World, body: dict) -> None:  # noqa: F811
    lender = login(client, "lender@example.test")
    # an unknown transaction: the body is validated first, and nothing may crash either way
    txn = "00000000-0000-0000-0000-000000000000"
    check(client.post(f"/api/v1/transactions/{txn}/handover/checklist", json=body, headers=lender))
