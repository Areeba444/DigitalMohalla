"""Event store behaviour against a real PostgreSQL (test plan suites 1, 2, 4 and 5, in part)."""

from uuid import UUID

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.exc import DBAPIError

from app.infra.eventstore import store
from tests.integration.conftest import World, period

SYSTEM = "system:test-runner"
VERIFIED = {"locality_outcome": "VERIFIED"}


def new_request(conn: Connection, world: World, item: int) -> UUID:
    return store.create_request(
        conn,
        item_id=world.items[item],
        borrower_id=world.borrower,
        lender_id=world.lender,
        period=period(5, 8),
    )


def check_locality(conn: Connection, txn: UUID) -> None:
    store.append(
        conn,
        txn,
        "locality_checked",
        "LOCALITY_CHECKED",
        actor_id=None,
        authorisation=SYSTEM,
        payload=VERIFIED,
    )


def test_create_request_starts_stream(conn: Connection, world: World) -> None:
    txn = new_request(conn, world, 0)
    events = store.load_stream(conn, txn)
    assert [(e["stream_seq"], e["event_type"], e["new_state"]) for e in events] == [
        (1, "request_created", "REQUEST_CREATED")
    ]
    assert store.stored_state(conn, txn) == "REQUEST_CREATED"


def test_valid_move_then_replay_matches_stored_state(conn: Connection, world: World) -> None:
    txn = new_request(conn, world, 1)
    check_locality(conn, txn)
    assert store.stored_state(conn, txn) == "LOCALITY_CHECKED"
    assert store.replay_state(conn, txn) == store.stored_state(conn, txn)  # NFR-R-03


def test_invalid_transition_is_rejected(conn: Connection, world: World) -> None:
    txn = new_request(conn, world, 2)
    with pytest.raises(store.InvalidTransition), conn.begin_nested():
        store.append(
            conn,
            txn,
            "handover_confirmed",
            "ACTIVE",
            actor_id=world.borrower,
            authorisation="party:borrower",
        )
    assert store.stored_state(conn, txn) == "REQUEST_CREATED"  # nothing changed


def test_stale_command_is_rejected(conn: Connection, world: World) -> None:
    txn = new_request(conn, world, 3)
    with pytest.raises(store.StaleCommand), conn.begin_nested():
        store.append(
            conn,
            txn,
            "locality_checked",
            "LOCALITY_CHECKED",
            actor_id=None,
            authorisation=SYSTEM,
            payload=VERIFIED,
            expected_seq=5,
        )


def test_actor_who_is_not_a_party_is_rejected(conn: Connection, world: World) -> None:
    txn = new_request(conn, world, 4)
    check_locality(conn, txn)
    with pytest.raises((store.NotAuthorised, store.InvalidTransition)), conn.begin_nested():
        store.append(
            conn,
            txn,
            "request_cancelled",
            "CANCELLED",
            actor_id=world.borrower2,
            authorisation="party:borrower",
        )
    assert store.stored_state(conn, txn) == "LOCALITY_CHECKED"


def test_events_cannot_be_updated_or_deleted(conn: Connection, world: World) -> None:
    txn = new_request(conn, world, 5)
    with pytest.raises(DBAPIError), conn.begin_nested():
        conn.execute(
            text("UPDATE lifecycle_event SET authorisation = 'role:admin' WHERE stream_id = :i"),
            {"i": txn},
        )
    with pytest.raises(DBAPIError), conn.begin_nested():
        conn.execute(text("DELETE FROM lifecycle_event WHERE stream_id = :i"), {"i": txn})


def test_untouched_chain_verifies_and_tampering_is_detected(conn: Connection, world: World) -> None:
    txn = new_request(conn, world, 6)
    assert store.verify_chain(conn, txn) == []
    # a superuser can switch the append-only trigger off; the hash chain must still show the edit
    conn.execute(text("ALTER TABLE lifecycle_event DISABLE TRIGGER lifecycle_event_append_only"))
    conn.execute(
        text("UPDATE lifecycle_event SET authorisation = 'role:admin' WHERE stream_id = :i"),
        {"i": txn},
    )
    conn.execute(text("ALTER TABLE lifecycle_event ENABLE TRIGGER lifecycle_event_append_only"))
    assert store.verify_chain(conn, txn) != []
