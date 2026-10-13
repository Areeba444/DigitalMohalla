"""Disputes (UC-B12, UC-D6; FR-B-16, FR-B-17; suite 13: TC-50 to TC-52) against a real PostgreSQL.

A party raises a dispute while the loan is ACCEPTED, ACTIVE or RETURN_INITIATED: the loan becomes
DISPUTED with its previous state kept in the event, the database opens a case for a moderator, and
the loan is frozen. Only the raising party can withdraw it, which restores the previous state and
closes the case as WITHDRAWN. Each test runs in a rolled-back connection. All data is synthetic.
"""

from uuid import UUID

import pytest
from sqlalchemy import Connection, Engine, text

from app.domain.lifecycle.aggregate import BorrowingTransaction
from app.domain.lifecycle.errors import EventStoreError, InvalidTransition, NotAuthorised
from app.domain.lifecycle.service import Actor, BorrowingService
from app.domain.lifecycle.transition_table import TransitionTable
from app.infra.eventstore import store
from tests.integration.conftest import World, period
from tests.integration.test_borrowing_service import audit_count, borrower, lender, make_service


def loan_in(svc: BorrowingService, world: World, state: str, item: int = 3) -> UUID:
    """A loan driven through the real lifecycle to ACCEPTED, ACTIVE or RETURN_INITIATED."""
    txn = svc.create_request(borrower(world), world.items[item], period(2, 5)).transaction_id
    svc.accept(lender(world), txn)
    if state in ("ACTIVE", "RETURN_INITIATED"):
        svc.record_handover_checklist(
            lender(world), txn, checklist={"scratches": "none"}, deposit_received=True
        )
        svc.confirm_handover(borrower(world), txn)
    if state == "RETURN_INITIATED":
        svc.initiate_return(borrower(world), txn)
    assert svc.get_request(borrower(world), txn)["view"].state == state
    return txn


def case_rows(conn: Connection, txn: UUID) -> list[dict]:
    rows = conn.execute(
        text(
            "SELECT trigger_type::text AS trigger, dispute_reason::text AS reason, raised_by, "
            "status::text AS status, priority, reason AS text, closed_at FROM escalation_case "
            "WHERE transaction_id = :t ORDER BY opened_at"
        ),
        {"t": txn},
    ).mappings()
    return [dict(r) for r in rows]


def test_tc50_lender_raises_a_dispute_on_an_active_loan(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "ACTIVE")
    result = svc.raise_dispute(lender(world), txn, "DAMAGE", "Synthetic: a crack on the handle.")
    assert result.state == "DISPUTED"

    opened = store.load_stream(conn, txn)[-1]
    assert (opened["event_type"], opened["previous_state"], opened["new_state"]) == (
        "dispute_opened",
        "ACTIVE",
        "DISPUTED",
    )
    assert opened["payload"] == {
        "reason": "DAMAGE",
        "description": "Synthetic: a crack on the handle.",
    }
    [case] = case_rows(conn, txn)
    assert (case["trigger"], case["reason"], case["status"], case["priority"]) == (
        "DISPUTE",
        "DAMAGE",
        "OPEN",
        1,
    )
    assert case["raised_by"] == world.lender
    assert case["text"] == "Synthetic: a crack on the handle."

    # frozen: no further transitions and no changes to the handover (deposit) record
    with pytest.raises(InvalidTransition):
        svc.record_handover_checklist(lender(world), txn, deposit_received=False)
    with pytest.raises(InvalidTransition):
        svc.initiate_return(borrower(world), txn)
    assert svc.get_request(lender(world), txn)["actions"] == ["withdraw_dispute"]
    assert svc.get_request(borrower(world), txn)["actions"] == []


def test_a_second_dispute_shows_the_open_case(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "ACTIVE")
    svc.raise_dispute(lender(world), txn, "DAMAGE")
    again = svc.raise_dispute(borrower(world), txn, "OTHER", "Synthetic second claim.")
    assert (again.state, again.message) == ("DISPUTED", "a dispute is already open for this loan")
    assert len(case_rows(conn, txn)) == 1


def test_tc52_the_other_party_cannot_withdraw(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "ACTIVE")
    svc.raise_dispute(lender(world), txn, "DAMAGE")
    before = audit_count(engine, txn)
    with pytest.raises(NotAuthorised):
        svc.withdraw_dispute(borrower(world), txn)
    assert audit_count(engine, txn) == before + 1  # the refusal is logged
    assert svc.get_request(lender(world), txn)["view"].state == "DISPUTED"
    assert case_rows(conn, txn)[0]["status"] == "OPEN"


@pytest.mark.parametrize("state", ["ACCEPTED", "ACTIVE", "RETURN_INITIATED"])
def test_tc51_withdrawal_restores_the_previous_state(
    conn: Connection, engine: Engine, world: World, state: str
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, state)
    svc.raise_dispute(borrower(world), txn, "CONDITION_MISMATCH", "Synthetic.")
    result = svc.withdraw_dispute(borrower(world), txn)
    assert result.state == state

    last = store.load_stream(conn, txn)[-1]
    assert (last["event_type"], last["previous_state"], last["new_state"]) == (
        "dispute_withdrawn",
        "DISPUTED",
        state,
    )
    [case] = case_rows(conn, txn)
    assert case["status"] == "WITHDRAWN" and case["closed_at"] is not None
    # the database replay, the Python aggregate and the stored projection agree
    events = store.load_stream(conn, txn)
    assert store.replay_state(conn, txn) == store.stored_state(conn, txn) == state
    assert BorrowingTransaction.replay(events, TransitionTable.load()).state == state
    assert store.verify_chain(conn, txn) == []


def test_disputes_are_refused_outside_the_allowed_states_and_to_non_parties(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = svc.create_request(borrower(world), world.items[4], period(2, 5)).transaction_id
    with pytest.raises(InvalidTransition):  # ASSESSED: nothing has been lent yet
        svc.raise_dispute(borrower(world), txn, "OTHER")
    svc.accept(lender(world), txn)
    with pytest.raises(NotAuthorised):
        svc.raise_dispute(Actor(world.borrower2), txn, "OTHER")
    with pytest.raises(InvalidTransition):  # nothing to withdraw
        svc.withdraw_dispute(borrower(world), txn)


def test_an_unknown_reason_is_refused_by_the_database(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "ACCEPTED", item=5)
    with pytest.raises(EventStoreError):
        svc.raise_dispute(borrower(world), txn, "BOGUS")


def test_evidence_trail_for_the_parties_only(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "ACTIVE", item=6)
    svc.raise_dispute(lender(world), txn, "DAMAGE", "Synthetic: a crack on the handle.")
    trail = svc.dispute_case(borrower(world), txn)
    assert trail["case"]["raised_by_role"] == "LENDER"
    assert trail["case"]["status"] == "OPEN"
    assert [e["event_type"] for e in trail["events"]][-1] == "dispute_opened"
    assert ("HANDOVER", "LENDER") in trail["reports"]
    assert trail["assessment"] is not None
    with pytest.raises(NotAuthorised):
        svc.dispute_case(Actor(world.borrower2), txn)
    svc.withdraw_dispute(lender(world), txn)  # the trail stays readable after a withdrawal
    assert svc.dispute_case(lender(world), txn)["case"]["status"] == "WITHDRAWN"
