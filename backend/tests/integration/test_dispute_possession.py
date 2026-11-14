"""Dispute closure by item possession on a real PostgreSQL (ADR-0009, review DM14; suite 26).

TC-140 to TC-144. A dispute raised before handover ends NO_SHOW and frees the dates; one raised while
the borrower has the item goes back to ACTIVE with the dates still held, so nobody else can book
them; RETURNED and LOST end COMPLETED, and LOST also pauses the item. A possession that does not
fit the stage is refused by the service, and the database's event_validate_v3 trigger refuses it
too. Each test runs in a rolled-back connection. All data is synthetic.
"""

from uuid import UUID

import pytest
from sqlalchemy import Connection, Engine, text

from app.domain.lifecycle.errors import DatesTaken, EventStoreError
from app.domain.lifecycle.service import BorrowingService, CommandResult
from app.domain.moderation.decisions import Decision, InvalidDecision
from app.infra.eventstore import store
from tests.integration.conftest import World, period
from tests.integration.test_borrowing_service import borrower, lender, make_service
from tests.integration.test_disputes import loan_in
from tests.integration.test_moderation import case_of, decisions_of, moderator


def resolve(
    svc: BorrowingService,
    world: World,
    conn: Connection,
    txn: UUID,
    possession: str,
    fault: str = "none",
) -> CommandResult:
    case = case_of(conn, txn)
    return svc.decide(
        moderator(world),
        case["id"],
        Decision(
            "DISPUTE_RESOLVED", "Synthetic: photos and statements checked.", (), fault, possession
        ),
    )


def booking_status(conn: Connection, txn: UUID) -> str:
    return str(
        conn.execute(
            text("SELECT status::text FROM booking WHERE transaction_id = :t"), {"t": txn}
        ).scalar_one()
    )


def item_status(conn: Connection, txn: UUID) -> str:
    return str(
        conn.execute(
            text(
                "SELECT i.status::text FROM item i JOIN borrowing_transaction t "
                "ON t.item_id = i.id WHERE t.id = :t"
            ),
            {"t": txn},
        ).scalar_one()
    )


def metrics(conn: Connection, txn: UUID) -> dict[str, bool]:
    rows = conn.execute(
        text(
            "SELECT subject_role::text || ':' || metric::text, success FROM outcome "
            "WHERE transaction_id = :t"
        ),
        {"t": txn},
    ).all()
    return {str(k): bool(v) for k, v in rows}


def test_tc140_not_handed_over_ends_no_show_and_releases_the_dates(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "ACCEPTED", item=6)
    svc.raise_dispute(borrower(world), txn, "NO_SHOW", "Synthetic: lender never came.")
    result = resolve(svc, world, conn, txn, "NOT_HANDED_OVER", fault="lender")
    assert result.state == "NO_SHOW"
    last = store.load_stream(conn, txn)[-1]
    assert (last["event_type"], last["new_state"], last["payload"]["possession"]) == (
        "dispute_resolved",
        "NO_SHOW",
        "NOT_HANDED_OVER",
    )
    assert booking_status(conn, txn) == "RELEASED"
    assert "BORROWER:ON_TIME_RETURN" not in metrics(conn, txn)  # the item never changed hands
    assert metrics(conn, txn)["LENDER:DISPUTE_FREE"] is False
    assert store.verify_chain(conn, txn) == []


@pytest.mark.parametrize("stage", ["ACTIVE", "RETURN_INITIATED"])
def test_tc141_item_still_with_the_borrower_goes_back_to_active_with_dates_held(
    conn: Connection, engine: Engine, world: World, stage: str
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, stage, item=7)
    svc.raise_dispute(lender(world), txn, "CONDITION_MISMATCH", "Synthetic: checklist differs.")
    result = resolve(svc, world, conn, txn, "WITH_BORROWER")
    assert result.state == "ACTIVE"
    assert booking_status(conn, txn) == "HELD"  # the occupied item is not released (DM14)
    assert "BORROWER:ON_TIME_RETURN" not in metrics(conn, txn)  # judged when it is returned
    # nobody can even request the same dates while the borrower still has the item (guard G1)
    with pytest.raises(DatesTaken):
        svc.create_request(borrower(world), world.items[7], period(2, 5))


def test_tc141_the_continued_loan_closes_normally_and_counts_the_finding_once(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "ACTIVE", item=8)
    svc.raise_dispute(lender(world), txn, "OTHER", "Synthetic: question about the charger.")
    resolve(svc, world, conn, txn, "WITH_BORROWER")
    svc.initiate_return(borrower(world), txn)
    svc.confirm_return(lender(world), txn, checklist={"scratches": "none"}, condition_agreed=True)
    svc.confirm_return(borrower(world), txn)
    assert svc.get_request(borrower(world), txn)["view"].state == "COMPLETED"
    assert metrics(conn, txn)["BORROWER:ON_TIME_RETURN"] is True  # recorded at the real return
    dispute_free = conn.execute(
        text(
            "SELECT count(*) FROM outcome WHERE transaction_id = :t "
            "AND metric = 'DISPUTE_FREE' AND subject_role = 'BORROWER'"
        ),
        {"t": txn},
    ).scalar_one()
    assert dispute_free == 1  # from the dispute only, not again at the close


def test_tc142_returned_completes_the_loan_and_releases_the_dates(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "RETURN_INITIATED", item=9)
    svc.raise_dispute(lender(world), txn, "DAMAGE", "Synthetic: dent on the lid.")
    result = resolve(svc, world, conn, txn, "RETURNED", fault="borrower")
    assert result.state == "COMPLETED"
    assert booking_status(conn, txn) == "RELEASED"
    assert item_status(conn, txn) == "PUBLISHED"
    assert metrics(conn, txn)["BORROWER:CONDITION_AGREED"] is False


def test_tc143_lost_completes_the_loan_pauses_the_item_and_fails_the_return(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "ACTIVE", item=10)
    svc.raise_dispute(lender(world), txn, "NON_RETURN", "Synthetic: item not returned.")
    result = resolve(svc, world, conn, txn, "LOST", fault="borrower")
    assert result.state == "COMPLETED"
    assert item_status(conn, txn) == "PAUSED"  # not lendable until the lender acts
    m = metrics(conn, txn)
    assert (m["BORROWER:ON_TIME_RETURN"], m["BORROWER:CONDITION_AGREED"]) == (False, False)


@pytest.mark.parametrize(
    ("stage", "possession"),
    [("ACCEPTED", "RETURNED"), ("ACCEPTED", "WITH_BORROWER"), ("ACTIVE", "NOT_HANDED_OVER")],
)
def test_tc144_a_possession_that_does_not_fit_is_refused_and_nothing_is_stored(
    conn: Connection, engine: Engine, world: World, stage: str, possession: str
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, stage, item=11)
    svc.raise_dispute(borrower(world), txn, "OTHER", "Synthetic: disagreement.")
    with pytest.raises(InvalidDecision, match="does not fit"):
        resolve(svc, world, conn, txn, possession)
    assert decisions_of(conn, txn) == 0
    assert store.load_stream(conn, txn)[-1]["new_state"] == "DISPUTED"


def test_tc144_the_database_refuses_a_mismatched_possession_on_its_own(
    conn: Connection, engine: Engine, world: World
) -> None:
    """Defence in depth: an insert that skips the service is refused by event_validate_v3."""
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "ACCEPTED", item=12)
    svc.raise_dispute(borrower(world), txn, "NO_SHOW", "Synthetic: no handover.")
    case = case_of(conn, txn)
    decision_id = conn.execute(
        text(
            "INSERT INTO moderator_decision (case_id, decided_by, decider_role, kind, reason, "
            "resolved_outcome) VALUES (:c, :m, 'MODERATOR', 'DISPUTE_RESOLVED', 'x', "
            "CAST(:o AS jsonb)) RETURNING id"
        ),
        {
            "c": case["id"],
            "m": world.moderator,
            "o": '{"at_fault": "none", "possession": "RETURNED"}',
        },
    ).scalar_one()
    community = conn.execute(
        text(
            "SELECT i.community_id FROM item i JOIN borrowing_transaction t ON t.item_id = i.id "
            "WHERE t.id = :t"
        ),
        {"t": txn},
    ).scalar_one()
    with pytest.raises(EventStoreError, match="possession"):
        store.append(
            conn,
            txn,
            "dispute_resolved",
            "COMPLETED",
            actor_id=world.moderator,
            authorisation=f"role:moderator@{community}",
            payload={"decision": "DISPUTE_RESOLVED", "possession": "RETURNED"},
            evidence_refs={"decision_id": str(decision_id)},
        )
