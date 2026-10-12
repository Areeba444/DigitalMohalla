"""BorrowingService against a real PostgreSQL: the Slice A loop and its failure paths.

Traces: UC-B5 to UC-B8, test plan suites 1 to 4 (TC-02, TC-07 to TC-10, TC-36, TC-37), NFR-R-01.
"""

import threading
import time
from uuid import UUID

import pytest
from sqlalchemy import Connection, Engine, text

from app.config.engine_config import load_engine_config
from app.domain.assurance.stub import StubAssuranceEngine
from app.domain.lifecycle.aggregate import BorrowingTransaction
from app.domain.lifecycle.errors import InvalidTransition, NotAuthorised
from app.domain.lifecycle.ports import AssessmentRequest, AssessmentResult
from app.domain.lifecycle.service import Actor, BorrowingService
from app.domain.lifecycle.transition_table import TransitionTable
from app.infra.eventstore import store
from app.infra.eventstore.postgres import PostgresAuditLog, PostgresLifecycleStore
from tests.integration.conftest import World, period

CONFIG = load_engine_config()


class SlowEngine:
    def assess(self, request: AssessmentRequest) -> AssessmentResult:
        time.sleep(0.5)
        return StubAssuranceEngine().assess(request)


class BrokenEngine:
    def assess(self, request: AssessmentRequest) -> AssessmentResult:
        raise RuntimeError("injected fault")


def make_service(
    conn: Connection, engine: Engine, assess: object | None = None, timeout_ms: int = 2000
) -> BorrowingService:
    return BorrowingService(
        PostgresLifecycleStore(conn),
        assess or StubAssuranceEngine(),  # type: ignore[arg-type]
        PostgresAuditLog(engine),
        config_version=CONFIG.config_version,
        engine_timeout_ms=timeout_ms,
    )


def borrower(world: World) -> Actor:
    return Actor(world.borrower)


def lender(world: World) -> Actor:
    return Actor(world.lender)


def audit_count(engine: Engine, txn: UUID) -> int:
    with engine.connect() as c:
        return c.execute(
            text("SELECT count(*) FROM audit_log WHERE target_id = :t AND outcome = 'REJECTED'"),
            {"t": str(txn)},
        ).scalar_one()


# ----------------------------------------------------------------------------- happy path
def test_full_loop_request_to_completed(conn: Connection, engine: Engine, world: World) -> None:
    svc = make_service(conn, engine)
    created = svc.create_request(borrower(world), world.items[7], period(1, 3), "synthetic")
    txn = created.transaction_id
    assert created.state == "ASSESSED"  # Slice A stub: INSUFFICIENT_EVIDENCE via R3
    assessment = svc.get_request(borrower(world), txn)["assessment"]
    assert assessment["assurance_state"] == "INSUFFICIENT_EVIDENCE"
    assert assessment["rule_fired"] == "R3"
    assert assessment["config_version"] == CONFIG.config_version  # NFR-D-01
    assert "Insufficient verified history" in assessment["explanation"]

    assert svc.accept(lender(world), txn).state == "ACCEPTED"
    svc.record_handover_checklist(lender(world), txn, checklist={"scratches": "none"})
    assert svc.confirm_handover(borrower(world), txn).state == "ACTIVE"
    assert svc.initiate_return(borrower(world), txn).state == "RETURN_INITIATED"
    assert svc.confirm_return(lender(world), txn).state == "RETURN_INITIATED"
    done = svc.confirm_return(borrower(world), txn)
    assert done.state == "COMPLETED"
    assert done.message == "returned on time"

    events = store.load_stream(conn, txn)
    assert [e["event_type"] for e in events] == [
        "request_created",
        "locality_checked",
        "assessment_generated",
        "request_accepted",
        "handover_confirmed",
        "return_initiated",
        "return_confirmed",
        "transaction_closed",
    ]
    # replay: database, Python aggregate and stored projection all agree (TC-07, NFR-R-03)
    assert store.replay_state(conn, txn) == store.stored_state(conn, txn) == "COMPLETED"
    assert BorrowingTransaction.replay(events, TransitionTable.load()).state == "COMPLETED"
    assert store.verify_chain(conn, txn) == []
    released = conn.execute(
        text("SELECT status::text FROM booking WHERE transaction_id = :t"), {"t": txn}
    ).scalar_one()
    assert released == "RELEASED"


def test_handover_waits_for_lender_checklist(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = svc.create_request(borrower(world), world.items[8], period(1, 3)).transaction_id
    svc.accept(lender(world), txn)
    result = svc.confirm_handover(borrower(world), txn)  # lender has not recorded a checklist
    assert result.state == "ACCEPTED"
    assert result.message and "checklist" in result.message


# ----------------------------------------------------------------------------- holds
def test_inconclusive_locality_holds_the_request(
    conn: Connection, engine: Engine, world: World
) -> None:
    uid = conn.execute(
        text(
            "INSERT INTO app_user (display_name, email, verification_level, status, is_synthetic) "
            "VALUES ('Refuser', 'refuser@example.test', 'COMMUNITY_VERIFIED', 'ACTIVE', true) "
            "RETURNING id"
        )
    ).scalar_one()
    mid = conn.execute(
        text(
            "INSERT INTO membership (user_id, community_id, role, status, decided_at) "
            "VALUES (:u, :c, 'MEMBER', 'APPROVED', now()) RETURNING id"
        ),
        {"u": uid, "c": world.community},
    ).scalar_one()
    conn.execute(
        text(
            "INSERT INTO locality_verification (membership_id, method, outcome, geofence_signal, "
            "permission_refused, valid_until) VALUES (:m, 'GEOFENCE_INVITATION', 'INCONCLUSIVE', "
            "'UNAVAILABLE', true, now() + interval '30 days')"
        ),
        {"m": mid},
    )
    svc = make_service(conn, engine)
    result = svc.create_request(Actor(uid), world.items[9], period(1, 3))
    assert result.state == "HELD_FOR_REVIEW"
    assert result.hold_reason == "locality_inconclusive"  # ES-10; never an automatic rejection
    case = conn.execute(
        text("SELECT trigger_type::text FROM escalation_case WHERE transaction_id = :t"),
        {"t": result.transaction_id},
    ).scalar_one()
    assert case == "LOCALITY_HOLD"


@pytest.mark.parametrize("assess", [SlowEngine(), BrokenEngine()], ids=["timeout", "exception"])
def test_engine_failure_holds_without_assigning_a_state(
    conn: Connection, engine: Engine, world: World, assess: object
) -> None:
    svc = make_service(conn, engine, assess, timeout_ms=100)
    result = svc.create_request(borrower(world), world.items[10], period(1, 3))
    assert result.state == "HELD_FOR_REVIEW"
    assert result.hold_reason == "engine_failure"  # TC-36, TC-37 (FR-T-07)
    n = conn.execute(
        text("SELECT count(*) FROM assessment WHERE transaction_id = :t"),
        {"t": result.transaction_id},
    ).scalar_one()
    assert n == 0  # no default assurance state


# ----------------------------------------------------------------------------- calendar
def test_second_acceptance_for_overlapping_dates_ends_declined(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    first = svc.create_request(borrower(world), world.items[11], period(5, 8)).transaction_id
    second = svc.create_request(
        Actor(world.borrower2), world.items[11], period(6, 9)
    ).transaction_id
    assert (
        svc.accept(lender(world), first).state == "ACCEPTED"
    )  # soft hold: both were created (TC-09)
    refused = svc.accept(lender(world), second)
    assert refused.state == "DECLINED"
    assert refused.message == "dates taken"
    assert store.stored_state(conn, second) == "DECLINED"


def test_acceptance_declines_overlapping_pending_requests(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    winner = svc.create_request(borrower(world), world.items[12], period(5, 8)).transaction_id
    other = svc.create_request(
        Actor(world.borrower2), world.items[12], period(7, 10)
    ).transaction_id
    svc.accept(lender(world), winner)
    assert svc.decline_overlapping(winner) == [other]
    assert store.stored_state(conn, other) == "DECLINED"


# ----------------------------------------------------------------------------- authorisation
def test_wrong_party_is_refused_and_audited(conn: Connection, engine: Engine, world: World) -> None:
    svc = make_service(conn, engine)
    txn = svc.create_request(borrower(world), world.items[13], period(1, 3)).transaction_id
    before = audit_count(engine, txn)
    with pytest.raises(NotAuthorised):
        svc.accept(Actor(world.borrower2), txn)  # not the lender (TC-10)
    with pytest.raises(NotAuthorised):
        svc.get_request(Actor(world.borrower2), txn)
    assert audit_count(engine, txn) == before + 1
    assert store.stored_state(conn, txn) == "ASSESSED"


def test_invalid_transition_is_refused_and_audited(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = svc.create_request(borrower(world), world.items[14], period(1, 3)).transaction_id
    svc.cancel(borrower(world), txn)
    before = audit_count(engine, txn)
    with pytest.raises(InvalidTransition):
        svc.cancel(borrower(world), txn)  # CANCELLED is terminal
    assert audit_count(engine, txn) == before + 1
    assert len(store.load_stream(conn, txn)) == 4  # nothing was appended by the refused command


# ----------------------------------------------------------------------------- schema drift
def test_domain_table_equals_database_table(conn: Connection) -> None:
    rows = conn.execute(
        text(
            "SELECT from_state::text, event_type::text, to_state::text, "
            "(SELECT string_agg(r::text, '|' ORDER BY r::text) FROM unnest(allowed_roles) r) "
            "FROM allowed_transition"
        )
    ).all()
    database = {(f, e, t, roles) for f, e, t, roles in rows}
    domain = {
        (t.from_state, t.event_type, t.to_state, "|".join(sorted(t.allowed_roles)))
        for t in TransitionTable.load().transitions
    }
    assert database == domain


# ----------------------------------------------------------------------------- concurrency
def test_simultaneous_acceptances_exactly_one_wins(engine: Engine, world: World) -> None:
    """Suite 3 (NFR-R-01): N parallel acceptances for overlapping dates; exactly one commits."""
    n_requests, rounds = 5, 3
    for round_no in range(rounds):
        item = world.items[15 + round_no]
        requests: list[UUID] = []
        for k in range(n_requests):
            with engine.begin() as c:
                svc = make_service(c, engine)
                who = Actor(world.borrower if k % 2 == 0 else world.borrower2)
                requests.append(svc.create_request(who, item, period(10 + k, 20)).transaction_id)

        results: list[str | None] = [None] * n_requests
        errors: list[BaseException] = []
        barrier = threading.Barrier(n_requests)

        def accept(
            index: int,
            txn: UUID,
            barrier: threading.Barrier = barrier,
            results: list[str | None] = results,
            errors: list[BaseException] = errors,
        ) -> None:
            try:
                barrier.wait()
                with engine.begin() as c:
                    results[index] = make_service(c, engine).accept(lender(world), txn).state
            except BaseException as exc:  # noqa: BLE001 - surfaced by the assertion below
                errors.append(exc)

        threads = [threading.Thread(target=accept, args=(i, t)) for i, t in enumerate(requests)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, errors
        assert results.count("ACCEPTED") == 1, results
        assert results.count("DECLINED") == n_requests - 1, results
        with engine.connect() as c:
            held = c.execute(
                text(
                    "SELECT count(*) FROM booking "
                    "WHERE transaction_id = ANY(:ids) AND status = 'HELD'"
                ),
                {"ids": requests},
            ).scalar_one()
        assert held == 1
