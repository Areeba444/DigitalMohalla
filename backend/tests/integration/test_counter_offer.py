"""Counter-offer (plan item F6; ADR-0015, FR-B-10; lifecycle v3 I07, I08, T29).

TC-220 to TC-224, input / expected / actual in each docstring. Synthetic loans on PostgreSQL.
"""

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.integration.conftest import World
from tests.integration.test_api import client, dates, login  # noqa: F401 - shared fixture


def assessed(client: TestClient, world: World, item: int, start: int) -> str:  # noqa: F811
    r = client.post(
        "/api/v1/requests",
        json={"item_id": str(world.items[item]), **dates(start, 2)},
        headers=login(client, "borrower@example.test"),
    )
    assert r.json()["state"] == "ASSESSED", r.text
    return str(r.json()["transaction_id"])


def row(engine: Engine, sql: str, **kw: object) -> tuple:  # type: ignore[type-arg]
    with engine.connect() as c:
        return tuple(c.execute(text(sql), kw).one())


def test_tc220_lender_offers_other_dates_once(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: the lender offers days 172-174 for a request of days 170-172, then offers again; the
    borrower tries to offer. Expected: the request stays ASSESSED and the borrower is told; the
    second offer is 409; the borrower's is 403."""
    txn = assessed(client, world, item=15, start=170)
    lender, borrower = login(client, "lender@example.test"), login(client, "borrower@example.test")
    url = f"/api/v1/requests/{txn}/counter-offer"
    offer = {**dates(172, 2), "message": "Synthetic: weekend is busy"}
    ok = client.post(url, json=offer, headers=lender)
    assert ok.status_code == 200 and ok.json()["state"] == "ASSESSED", ok.text
    assert client.post(url, json={**dates(176, 2)}, headers=lender).status_code == 409
    assert client.post(url, json=offer, headers=borrower).status_code == 403
    (told,) = row(
        engine,
        "SELECT count(*) FROM notification WHERE user_id = :u AND type = 'counter_offered' "
        "AND payload->>'transaction_id' = :t",
        u=world.borrower,
        t=txn,
    )
    assert told == 1


def test_tc221_accepting_moves_the_dates_and_assesses_again(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: the borrower accepts the offer. Expected: the request has the offered dates, a second
    assessment exists (loan length feeds similarity, D17), it is ASSESSED again and the lender is
    told; the lender can then accept and the booking uses the new dates."""
    txn = assessed(client, world, item=15, start=180)
    lender, borrower = login(client, "lender@example.test"), login(client, "borrower@example.test")
    client.post(f"/api/v1/requests/{txn}/counter-offer", json=dates(183, 3), headers=lender)
    ok = client.post(f"/api/v1/requests/{txn}/counter-offer/accept", headers=borrower)
    assert ok.status_code == 200 and ok.json()["state"] == "ASSESSED", ok.text
    start, length, assessments = row(
        engine,
        "SELECT lower(requested_period)::date - current_date, "
        "upper(requested_period) - lower(requested_period), "
        "(SELECT count(*) FROM assessment a WHERE a.transaction_id = t.id) "
        "FROM borrowing_transaction t WHERE id = :t",
        t=txn,
    )
    assert (start, length.days, assessments) == (183, 3, 2)
    assert (
        client.post(f"/api/v1/requests/{txn}/accept", headers=lender).json()["state"] == "ACCEPTED"
    )
    (booked,) = row(
        engine,
        "SELECT lower(period)::date - current_date FROM booking WHERE transaction_id = :t",
        t=txn,
    )
    assert booked == 183


def test_tc222_declining_keeps_the_original_dates(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: the borrower declines the offer, then declines again. Expected: original dates kept,
    lender told; the second decline is 409 (nothing open); the lender may offer again."""
    txn = assessed(client, world, item=16, start=190)
    lender, borrower = login(client, "lender@example.test"), login(client, "borrower@example.test")
    client.post(f"/api/v1/requests/{txn}/counter-offer", json=dates(192, 2), headers=lender)
    url = f"/api/v1/requests/{txn}/counter-offer/decline"
    assert client.post(url, headers=borrower).status_code == 200
    assert client.post(url, headers=borrower).status_code == 409
    (start,) = row(
        engine,
        "SELECT lower(requested_period)::date - current_date FROM borrowing_transaction WHERE id = :t",
        t=txn,
    )
    assert start == 190
    again = client.post(f"/api/v1/requests/{txn}/counter-offer", json=dates(194, 2), headers=lender)
    assert again.status_code == 200


def test_tc223_offered_dates_taken_meanwhile_are_refused(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: the lender offers days 202-204, then accepts another request for days 203-205; the
    borrower accepts the offer. Expected: 409 and nothing changes (ADR-0002)."""
    txn = assessed(client, world, item=17, start=200)
    other = assessed(client, world, item=17, start=203)
    lender, borrower = login(client, "lender@example.test"), login(client, "borrower@example.test")
    client.post(f"/api/v1/requests/{txn}/counter-offer", json=dates(202, 2), headers=lender)
    client.post(f"/api/v1/requests/{other}/accept", headers=lender)
    refused = client.post(f"/api/v1/requests/{txn}/counter-offer/accept", headers=borrower)
    assert refused.status_code == 409
    (state,) = row(
        engine, "SELECT current_state::text FROM borrowing_transaction WHERE id = :t", t=txn
    )
    assert state == "ASSESSED"


def test_tc224_offers_must_be_other_future_dates(
    client: TestClient,  # noqa: F811
    world: World,
) -> None:
    """Expected 409: the same dates as the request, or dates in the past; 422 when end <= start."""
    txn = assessed(client, world, item=18, start=210)
    lender = login(client, "lender@example.test")
    url = f"/api/v1/requests/{txn}/counter-offer"
    assert client.post(url, json=dates(210, 2), headers=lender).status_code == 409
    assert client.post(url, json=dates(-3, 2), headers=lender).status_code == 409
    bad = {"start_date": "2030-01-05", "end_date": "2030-01-04"}
    assert client.post(url, json=bad, headers=lender).status_code == 422
