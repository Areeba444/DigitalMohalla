"""Trust edges follow the outcomes when a loan closes through the service (ADR-0006, FR-T-04).

Uses the shared integration world (synthetic users and items) and rolls back after each test.
"""

from sqlalchemy import Connection, Engine, text

from app.domain.lifecycle.service import Actor
from tests.integration.conftest import World, period
from tests.integration.test_borrowing_service import make_service


def edges_between(
    conn: Connection, a: object, b: object
) -> dict[tuple[str, str], tuple[float, int]]:
    rows = conn.execute(
        text(
            "SELECT role::text, metric::text, weight, evidence_count FROM trust_edge "
            "WHERE source_id = :a AND target_id = :b"
        ),
        {"a": a, "b": b},
    ).all()
    return {(r[0], r[1]): (float(r[2]), r[3]) for r in rows}


def test_closing_a_loan_creates_the_edges_both_ways(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    borrower, lender = Actor(world.borrower), Actor(world.lender)
    txn = svc.create_request(borrower, world.items[12], period(2, 4), "synthetic").transaction_id
    svc.accept(lender, txn)
    svc.record_handover_checklist(lender, txn, checklist={"scratches": "none"})
    svc.confirm_handover(borrower, txn)
    svc.initiate_return(borrower, txn)
    svc.confirm_return(lender, txn)
    before = edges_between(conn, world.lender, world.borrower)
    svc.confirm_return(borrower, txn)

    lender_about_borrower = edges_between(conn, world.lender, world.borrower)
    borrower_about_lender = edges_between(conn, world.borrower, world.lender)
    assert set(lender_about_borrower) == {
        ("BORROWER", "ON_TIME_RETURN"),
        ("BORROWER", "CONDITION_AGREED"),
        ("BORROWER", "DISPUTE_FREE"),
    }
    assert set(borrower_about_lender) == {
        ("LENDER", "CONDITION_AGREED"),
        ("LENDER", "DISPUTE_FREE"),
    }
    # one more confirmed success than before for each edge; a single fresh success alone gives 0.667
    for key, (weight, count) in lender_about_borrower.items():
        assert count == before.get(key, (0.0, 0))[1] + 1
        assert 0.5 < weight <= 1.0
