"""Outcomes are written when a loan closes through the service (Test Plan TC-67, FR-B-15).

Uses the shared integration world (synthetic users and items) and rolls back after each test.
"""

from sqlalchemy import Connection, Engine, text

from app.domain.lifecycle.service import Actor
from tests.integration.conftest import World, period
from tests.integration.test_borrowing_service import make_service


def outcomes_of(conn: Connection, txn: object) -> dict[tuple[str, str], tuple[bool, str, str]]:
    rows = conn.execute(
        text(
            "SELECT subject_role::text, metric::text, success, subject_id::text, observer_id::text "
            "FROM outcome WHERE transaction_id = :t"
        ),
        {"t": txn},
    ).all()
    return {(r[0], r[1]): (r[2], r[3], r[4]) for r in rows}


def test_closing_a_loan_writes_its_outcomes_in_the_same_transaction(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    borrower, lender = Actor(world.borrower), Actor(world.lender)
    txn = svc.create_request(borrower, world.items[11], period(2, 4), "synthetic").transaction_id
    svc.accept(lender, txn)
    svc.record_handover_checklist(lender, txn, checklist={"scratches": "none"})
    svc.confirm_handover(borrower, txn)
    svc.initiate_return(borrower, txn)
    svc.confirm_return(lender, txn)
    assert outcomes_of(conn, txn) == {}, "nothing counts before the loan is closed"

    assert svc.confirm_return(borrower, txn).state == "COMPLETED"
    got = outcomes_of(conn, txn)
    b, lnd = str(world.borrower), str(world.lender)
    assert got == {
        ("BORROWER", "ON_TIME_RETURN"): (True, b, lnd),
        ("BORROWER", "CONDITION_AGREED"): (True, b, lnd),
        ("BORROWER", "DISPUTE_FREE"): (True, b, lnd),
        ("LENDER", "CONDITION_AGREED"): (True, lnd, b),
        ("LENDER", "DISPUTE_FREE"): (True, lnd, b),
    }
    snapshot = conn.execute(
        text(
            "SELECT DISTINCT o.value_band::text = i.value_band::text, o.category_id = i.category_id, "
            "o.loan_duration = interval '2 days', o.status::text, "
            "o.source_event_id = (SELECT max(event_id) FROM lifecycle_event WHERE stream_id = :t "
            "AND event_type = 'transaction_closed') "
            "FROM outcome o JOIN borrowing_transaction t ON t.id = o.transaction_id "
            "JOIN item i ON i.id = t.item_id WHERE o.transaction_id = :t"
        ),
        {"t": txn},
    ).all()
    assert snapshot == [(True, True, True, "VALID", True)]
    pending = conn.execute(
        text("SELECT count(*) FROM v_pending_outcomes WHERE stream_id = :t"), {"t": txn}
    ).scalar_one()
    assert pending == 0
