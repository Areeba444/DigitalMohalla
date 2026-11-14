"""Time-based lifecycle rules and extensions (plan item F5; FR-B-10, B-14, B-18; ES-08 workflow).

Request expiry (T15), handover, return and confirmation reminders (I01, I02, I06), overdue
escalation to a NON_RETURN dispute (T24, sequence (e)), and extensions (I03 to I05). TC-212 to
TC-219, input / expected / actual in each docstring. Time moves by passing `now` to the job runner;
synthetic loans only.
"""

from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.api.jobs import run_jobs
from tests.integration.conftest import World
from tests.integration.test_api import client, dates, login  # noqa: F401 - shared fixture


def day(n: float) -> datetime:
    return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=n)


def request(client: TestClient, world: World, item: int, start: int, length: int = 2) -> str:  # noqa: F811
    r = client.post(
        "/api/v1/requests",
        json={"item_id": str(world.items[item]), **dates(start, length)},
        headers=login(client, "borrower@example.test"),
    )
    assert r.status_code == 201 and r.json()["state"] == "ASSESSED", r.text
    return str(r.json()["transaction_id"])


def active_loan(client: TestClient, world: World, item: int, start: int, length: int = 2) -> str:  # noqa: F811
    txn = request(client, world, item, start, length)
    lender = login(client, "lender@example.test")
    borrower = login(client, "borrower@example.test")
    assert client.post(f"/api/v1/requests/{txn}/accept", headers=lender).status_code == 200
    client.post(
        f"/api/v1/transactions/{txn}/handover/checklist", json={"checklist": {}}, headers=lender
    )
    done = client.post(f"/api/v1/transactions/{txn}/handover/confirm", json={}, headers=borrower)
    assert done.json()["state"] == "ACTIVE", done.text
    return txn


def q(engine: Engine, sql: str, **kw: object) -> object:
    with engine.connect() as c:
        return c.execute(text(sql), kw).scalar_one()


def events(engine: Engine, txn: str, kind: str) -> int:
    return int(  # type: ignore[call-overload]
        q(
            engine,
            "SELECT count(*) FROM lifecycle_event WHERE stream_id = :t AND event_type = :k",
            t=txn,
            k=kind,
        )
    )


def test_tc212_unanswered_request_expires_after_the_response_window(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: an ASSESSED request; jobs at +71 h, then +73 h twice. Expected: still ASSESSED at 71 h;
    EXPIRED once at 73 h with both parties told; the rerun does nothing (T15)."""
    txn = request(client, world, item=8, start=120)
    now = datetime.now(UTC)
    run_jobs(engine, now + timedelta(hours=71))
    assert (
        q(engine, "SELECT current_state::text FROM borrowing_transaction WHERE id = :t", t=txn)
        == "ASSESSED"
    )
    run_jobs(engine, now + timedelta(hours=73))
    run_jobs(engine, now + timedelta(hours=73))
    assert (
        q(engine, "SELECT current_state::text FROM borrowing_transaction WHERE id = :t", t=txn)
        == "EXPIRED"
    )
    assert events(engine, txn, "request_expired") == 1
    assert (
        q(
            engine,
            "SELECT count(*) FROM notification WHERE dedupe_key = :k",
            k=f"{txn}:request_expired",
        )
        == 2
    )


def test_tc213_to_tc215_reminders_then_overdue_dispute(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """ES-08 workflow. Input: an ACTIVE loan due at the start of day 126; jobs at due - 23 h,
    due + 1 h, due + 71 h and due + 73 h (twice). Expected: reminder 1 to the borrower (TC-213);
    reminder 2 at the due date to both (TC-214); no dispute before the 72 h limit; then one system
    NON_RETURN dispute, routed to the moderator; a rerun adds nothing (TC-215, T24)."""
    txn = active_loan(client, world, item=9, start=124, length=2)
    due = day(126)
    assert q(engine, "SELECT due_at FROM borrowing_transaction WHERE id = :t", t=txn) == due
    run_jobs(engine, due - timedelta(hours=23))
    assert events(engine, txn, "reminder_sent") == 1
    run_jobs(engine, due + timedelta(hours=1))
    assert events(engine, txn, "reminder_sent") == 2
    assert (
        q(
            engine,
            "SELECT count(*) FROM notification WHERE type = 'return_due_today' "
            "AND payload->>'transaction_id' = :t",
            t=txn,
        )
        == 1
    )
    run_jobs(engine, due + timedelta(hours=71))
    assert events(engine, txn, "dispute_opened") == 0
    run_jobs(engine, due + timedelta(hours=73))
    run_jobs(engine, due + timedelta(hours=73))
    assert events(engine, txn, "dispute_opened") == 1
    with engine.connect() as c:
        reason, raised_by, state = c.execute(
            text(
                "SELECT ec.dispute_reason::text, ec.raised_by, t.current_state::text "
                "FROM escalation_case ec JOIN borrowing_transaction t ON t.id = ec.transaction_id "
                "WHERE ec.transaction_id = :t"
            ),
            {"t": txn},
        ).one()
        told = c.execute(
            text(
                "SELECT count(*) FROM notification WHERE user_id = :m AND type = 'case_opened' "
                "AND payload->>'transaction_id' = :t"
            ),
            {"m": world.moderator, "t": txn},
        ).scalar_one()
    assert (reason, raised_by, state, told) == ("NON_RETURN", None, "DISPUTED", 1)


def test_tc216_extension_moves_the_due_date_and_the_booking(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: the borrower asks for 3 more days, asks again, the lender approves. Expected: the
    second ask is refused (one pending); due date and booking end move together; the borrower is
    told; reminders then key on the new due date (I03, I04)."""
    txn = active_loan(client, world, item=10, start=130, length=2)
    borrower, lender = login(client, "borrower@example.test"), login(client, "lender@example.test")
    url = f"/api/v1/transactions/{txn}/extension"
    new_due = (date.today() + timedelta(days=135)).isoformat()
    asked = client.post(
        url, json={"new_due_date": new_due, "reason": "Synthetic"}, headers=borrower
    )
    assert asked.status_code == 200, asked.text
    assert client.post(url, json={"new_due_date": new_due}, headers=borrower).status_code == 409
    assert client.post(f"{url}/approve", headers=borrower).status_code == 403
    ok = client.post(f"{url}/approve", headers=lender)
    assert ok.status_code == 200, ok.text
    assert q(engine, "SELECT due_at FROM borrowing_transaction WHERE id = :t", t=txn) == day(135)
    assert q(engine, "SELECT upper(period) FROM booking WHERE transaction_id = :t", t=txn) == day(
        135
    )
    assert client.post(f"{url}/approve", headers=lender).status_code == 409  # nothing pending
    run_jobs(engine, day(132) + timedelta(hours=1))  # the old due date: no reminder for it now
    assert events(engine, txn, "reminder_sent") == 0


def test_tc217_extension_into_a_booked_period_changes_nothing(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: loan A on days 140-142; loan B on the same item accepted for days 142-144; A asks to
    keep it until day 144 and the lender approves. Expected: 409; A's due date and booking unchanged."""
    a = active_loan(client, world, item=11, start=140, length=2)
    b = request(client, world, item=11, start=142, length=2)
    lender, borrower = login(client, "lender@example.test"), login(client, "borrower@example.test")
    assert client.post(f"/api/v1/requests/{b}/accept", headers=lender).status_code == 200
    new_due = (date.today() + timedelta(days=144)).isoformat()
    client.post(
        f"/api/v1/transactions/{a}/extension", json={"new_due_date": new_due}, headers=borrower
    )
    refused = client.post(f"/api/v1/transactions/{a}/extension/approve", headers=lender)
    assert refused.status_code == 409
    assert q(engine, "SELECT due_at FROM borrowing_transaction WHERE id = :t", t=a) == day(142)


def test_tc218_declined_extension_keeps_the_due_date(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: ask, then decline with a reason; ask for an earlier date. Expected: due date unchanged,
    borrower told; an earlier or equal date is refused (I05)."""
    txn = active_loan(client, world, item=12, start=150, length=2)
    borrower, lender = login(client, "borrower@example.test"), login(client, "lender@example.test")
    url = f"/api/v1/transactions/{txn}/extension"
    early = (date.today() + timedelta(days=151)).isoformat()
    assert client.post(url, json={"new_due_date": early}, headers=borrower).status_code == 409
    later = (date.today() + timedelta(days=155)).isoformat()
    client.post(url, json={"new_due_date": later}, headers=borrower)
    no = client.post(f"{url}/decline", json={"reason": "Needed back"}, headers=lender)
    assert no.status_code == 200
    assert q(engine, "SELECT due_at FROM borrowing_transaction WHERE id = :t", t=txn) == day(152)
    assert (
        q(
            engine,
            "SELECT count(*) FROM notification WHERE type = 'extension_decided' "
            "AND payload->>'transaction_id' = :t",
            t=txn,
        )
        == 1
    )


def test_tc219_handover_and_confirmation_reminders(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: an ACCEPTED loan on its start day; an ACTIVE loan whose return was started and not
    confirmed for 25 h. Expected: one handover reminder (I01); one confirmation reminder (I06)."""
    lender = login(client, "lender@example.test")
    accepted = request(client, world, item=13, start=160)
    client.post(f"/api/v1/requests/{accepted}/accept", headers=lender)
    run_jobs(engine, day(160) + timedelta(hours=1))
    run_jobs(engine, day(160) + timedelta(hours=2))
    assert events(engine, accepted, "reminder_sent") == 1

    returning = active_loan(client, world, item=14, start=165)
    client.post(
        f"/api/v1/transactions/{returning}/return", headers=login(client, "borrower@example.test")
    )
    run_jobs(engine, datetime.now(UTC) + timedelta(hours=25))
    run_jobs(engine, datetime.now(UTC) + timedelta(hours=26))
    assert events(engine, returning, "reminder_sent") == 1
