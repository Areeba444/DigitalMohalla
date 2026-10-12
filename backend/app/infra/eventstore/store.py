"""Event store: append, read, replay and verify lifecycle events (Module 3, FR-B-08, FR-B-09).

Plain-language note. The rules of the borrowing lifecycle (which move is allowed from which state,
who may make it, the no-double-booking calendar, the append-only hash chain) are enforced by
PostgreSQL triggers in the frozen schema (docs/design/06_data_model/schema.sql, rules R1 to R5).
This module does not copy those rules into Python. It only (a) reads the current state and version
so the caller's event carries the right `previous_state` and `stream_seq`, (b) inserts the event,
and (c) turns the database's refusals into named Python errors. One place enforces the rules, so
they cannot drift apart.
"""

import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text
from sqlalchemy.exc import DBAPIError

from app.domain.lifecycle.errors import (
    DatesTaken,
    EventStoreError,
    InvalidTransition,
    NotAuthorised,
    StaleCommand,
    StreamNotFound,
)

# PostgreSQL SQLSTATE -> named error (codes are raised by the triggers in schema.sql)
_SQLSTATE_TO_ERROR: dict[str, type[EventStoreError]] = {
    "40001": StaleCommand,  # serialization_failure
    "42501": NotAuthorised,  # insufficient_privilege
    "23514": InvalidTransition,  # check_violation (invalid transition, failed guard)
    "23503": InvalidTransition,  # foreign_key_violation (event_transition_fk)
    "23P01": DatesTaken,  # exclusion_violation
}


def _translate(exc: DBAPIError) -> EventStoreError | None:
    cls = _SQLSTATE_TO_ERROR.get(getattr(exc.orig, "sqlstate", None) or "")
    if cls is None:
        return None
    return cls(str(exc.orig).splitlines()[0])


def _json(value: Mapping[str, Any] | None) -> str:
    return json.dumps(dict(value or {}))


def create_request(
    conn: Connection,
    *,
    item_id: UUID,
    borrower_id: UUID,
    lender_id: UUID,
    period: str,
    message: str | None = None,
) -> UUID:
    """Create the transaction and its first event (`request_created`) in the caller's transaction.

    `period` is a bounded timestamptz range literal such as "[2026-11-01,2026-11-04)". The request
    guards (published item, active verified member, no block, no past dates, dates not already
    booked) run in the database and surface as InvalidTransition / DatesTaken.
    """
    try:
        txn_id: UUID = conn.execute(
            text(
                "INSERT INTO borrowing_transaction "
                "(item_id, borrower_id, lender_id, requested_period, message) "
                "VALUES (:item, :borrower, :lender, CAST(:period AS tstzrange), :message) "
                "RETURNING id"
            ),
            {
                "item": item_id,
                "borrower": borrower_id,
                "lender": lender_id,
                "period": period,
                "message": message,
            },
        ).scalar_one()
        conn.execute(
            text(
                "INSERT INTO lifecycle_event (stream_id, stream_seq, event_type, actor_id, "
                "new_state, authorisation, payload) "
                "SELECT t.id, 1, 'request_created', t.borrower_id, 'REQUEST_CREATED', "
                "'party:borrower', jsonb_build_object('item_id', t.item_id::text, "
                "'requested_period', t.requested_period::text) "
                "FROM borrowing_transaction t WHERE t.id = :id"
            ),
            {"id": txn_id},
        )
    except DBAPIError as exc:
        translated = _translate(exc)
        if translated is None:
            raise
        raise translated from exc
    return txn_id


def append(
    conn: Connection,
    stream_id: UUID,
    event_type: str,
    new_state: str,
    *,
    actor_id: UUID | None,
    authorisation: str,
    payload: Mapping[str, Any] | None = None,
    evidence_refs: Mapping[str, Any] | None = None,
    config_version: str | None = None,
    expected_seq: int | None = None,
) -> int:
    """Append one event to a stream and return its event_id.

    `expected_seq` is the stream_seq the caller believes comes next. Pass it when the command was
    built from an earlier read, so a concurrent writer makes this call fail with StaleCommand.
    """
    row = conn.execute(
        text("SELECT current_state, stream_version FROM borrowing_transaction WHERE id = :id"),
        {"id": stream_id},
    ).first()
    if row is None:
        raise StreamNotFound(str(stream_id))
    previous_state, version = row
    seq = expected_seq if expected_seq is not None else version + 1
    try:
        event_id: int = conn.execute(
            text(
                "INSERT INTO lifecycle_event (stream_id, stream_seq, event_type, actor_id, "
                "previous_state, new_state, evidence_refs, authorisation, config_version, payload) "
                "VALUES (:stream, :seq, CAST(:etype AS event_type), :actor, "
                "CAST(:prev AS lifecycle_state), CAST(:new AS lifecycle_state), "
                "CAST(:evidence AS jsonb), :auth, :config, CAST(:payload AS jsonb)) "
                "RETURNING event_id"
            ),
            {
                "stream": stream_id,
                "seq": seq,
                "etype": event_type,
                "actor": actor_id,
                "prev": previous_state,
                "new": new_state,
                "evidence": _json(evidence_refs),
                "auth": authorisation,
                "config": config_version,
                "payload": _json(payload),
            },
        ).scalar_one()
    except DBAPIError as exc:
        translated = _translate(exc)
        if translated is None:
            raise
        raise translated from exc
    return event_id


def load_stream(conn: Connection, stream_id: UUID) -> list[dict[str, Any]]:
    """All events of one transaction in stream_seq order (IEventQuery.load_stream)."""
    rows = conn.execute(
        text(
            "SELECT event_id, stream_seq, event_type::text AS event_type, actor_id, occurred_at, "
            "previous_state::text AS previous_state, new_state::text AS new_state, evidence_refs, "
            "authorisation, config_version, payload FROM lifecycle_event "
            "WHERE stream_id = :id ORDER BY stream_seq"
        ),
        {"id": stream_id},
    ).mappings()
    return [dict(r) for r in rows]


def replay_state(conn: Connection, stream_id: UUID) -> str | None:
    """State rebuilt by replaying the events from scratch (NFR-R-03); compare with stored_state."""
    return conn.execute(text("SELECT replay_state(:id)::text"), {"id": stream_id}).scalar_one()


def stored_state(conn: Connection, stream_id: UUID) -> str | None:
    return conn.execute(
        text("SELECT current_state::text FROM borrowing_transaction WHERE id = :id"),
        {"id": stream_id},
    ).scalar_one_or_none()


def verify_chain(conn: Connection, stream_id: UUID) -> list[tuple[int, str]]:
    """Problems found in the hash chain of one stream; empty means untouched (NFR-S-05)."""
    rows = conn.execute(
        text("SELECT stream_seq, problem FROM verify_event_chain(:id)"), {"id": stream_id}
    )
    return [(r[0], r[1]) for r in rows]
