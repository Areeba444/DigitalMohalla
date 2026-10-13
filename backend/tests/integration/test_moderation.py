"""Moderator decisions on a real PostgreSQL (UC-I4, UC-D6; suite 13: TC-53 to TC-57).

Holds are produced by the real lifecycle: an engine fault (engine_failure), an engine answer that
holds a high-value request (rule R4), or an inconclusive locality check. Disputes are raised by a
party. The synthetic world's moderator and admin decide. Each test runs in a rolled-back
connection. All data is synthetic.
"""

from uuid import UUID

import pytest
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import IntegrityError

from app.domain.lifecycle.errors import InvalidTransition, NotAuthorised
from app.domain.lifecycle.ports import AssessmentRequest, AssessmentResult
from app.domain.lifecycle.service import Actor
from app.domain.moderation.decisions import Decision, InvalidDecision
from app.infra.eventstore import store
from tests.integration.conftest import World, period
from tests.integration.test_borrowing_service import (
    CONFIG,
    BrokenEngine,
    audit_count,
    borrower,
    lender,
    make_service,
)
from tests.integration.test_disputes import loan_in


class HighValueHold:
    """An engine answer holding the request for a moderator (rule R4)."""

    def assess(self, request: AssessmentRequest) -> AssessmentResult:
        return AssessmentResult(
            assurance_state="REVIEW_RECOMMENDED",
            policy_decision="RESTRICT_HIGH_VALUE",
            rule_fired="R4",
            hold_reason="high_value_low_confidence",
            explanation="Synthetic hold for a moderator.",
            config_version=CONFIG.config_version,
            posterior_mean=0.5,
            ci90_low=0.05,
            ci90_high=0.95,
            effective_evidence=0.0,
        )


def moderator(world: World) -> Actor:
    return Actor(world.moderator)


def admin(world: World) -> Actor:
    return Actor(world.admin, "ADMIN")


def case_of(conn: Connection, txn: UUID) -> dict:
    row = (
        conn.execute(
            text(
                "SELECT id, status::text AS status FROM escalation_case WHERE transaction_id = :t "
                "ORDER BY opened_at DESC LIMIT 1"
            ),
            {"t": txn},
        )
        .mappings()
        .one()
    )
    return dict(row)


def decisions_of(conn: Connection, txn: UUID) -> int:
    return conn.execute(
        text(
            "SELECT count(*) FROM moderator_decision d JOIN escalation_case ec ON ec.id = d.case_id "
            "WHERE ec.transaction_id = :t"
        ),
        {"t": txn},
    ).scalar_one()


def held(conn: Connection, engine: Engine, world: World, assess: object, item: int) -> UUID:
    result = make_service(conn, engine, assess).create_request(
        borrower(world), world.items[item], period(3, 6)
    )
    assert result.state == "HELD_FOR_REVIEW"
    return result.transaction_id


# ----------------------------------------------------------------------------- disputes
def test_tc53_resolved_dispute_completes_the_loan_and_becomes_evidence(
    conn: Connection, engine: Engine, world: World
) -> None:
    svc = make_service(conn, engine)
    txn = loan_in(svc, world, "ACTIVE")
    svc.raise_dispute(lender(world), txn, "DAMAGE", "Synthetic: a crack on the handle.")
    case = case_of(conn, txn)
    result = svc.decide(
        moderator(world),
        case["id"],
        Decision(
            "DISPUTE_RESOLVED",
            "Handover photos show no crack; the return photos do.",
            (),
            "borrower",
        ),
    )
    assert result.state == "COMPLETED"
    last = store.load_stream(conn, txn)[-1]
    assert (last["event_type"], last["previous_state"], last["new_state"]) == (
        "dispute_resolved",
        "DISPUTED",
        "COMPLETED",
    )
    assert case_of(conn, txn)["status"] == "DECIDED"
    [decision] = svc.moderator_case(moderator(world), case["id"])["decisions"]
    assert decision["kind"] == "DISPUTE_RESOLVED" and decision["resolved_outcome"] == {
        "at_fault": "borrower"
    }
    outcomes = dict(
        conn.execute(
            text(
                "SELECT subject_role::text || ':' || metric::text, success FROM outcome "
                "WHERE transaction_id = :t AND metric = 'DISPUTE_FREE'"
            ),
            {"t": txn},
        ).all()
    )
    assert outcomes == {"BORROWER:DISPUTE_FREE": False, "LENDER:DISPUTE_FREE": True}
    assert store.verify_chain(conn, txn) == []


# ----------------------------------------------------------------------------- holds
def test_tc54_a_decision_without_a_reason_is_refused_and_nothing_is_stored(
    conn: Connection, engine: Engine, world: World
) -> None:
    txn = held(conn, engine, world, HighValueHold(), 1)
    before = audit_count(engine, txn)
    with pytest.raises(InvalidDecision):
        make_service(conn, engine).decide(
            moderator(world), case_of(conn, txn)["id"], Decision("CLEARED", "  ")
        )
    assert decisions_of(conn, txn) == 0
    assert audit_count(engine, txn) == before + 1
    with (
        pytest.raises(IntegrityError, match="check constraint"),
        conn.begin_nested(),
    ):
        conn.execute(  # the database refuses it as well (FR-T-11)
            text(
                "INSERT INTO moderator_decision (case_id, decided_by, decider_role, kind, reason) "
                "VALUES (:c, :u, 'MODERATOR', 'CLEARED', '   ')"
            ),
            {"c": case_of(conn, txn)["id"], "u": world.moderator},
        )


def test_tc55_engine_failure_hold_refuses_safeguards_and_clearing_reassesses(
    conn: Connection, engine: Engine, world: World
) -> None:
    txn = held(conn, engine, world, BrokenEngine(), 2)
    case_id = case_of(conn, txn)["id"]
    svc = make_service(conn, engine)  # the engine works again
    with pytest.raises(InvalidDecision, match="engine failure"):
        svc.decide(
            moderator(world), case_id, Decision("SAFEGUARDS_IMPOSED", "Photos.", ("Photos",))
        )
    result = svc.decide(moderator(world), case_id, Decision("CLEARED", "The engine is back."))
    assert result.state == "ASSESSED"
    tail = [(e["event_type"], e["new_state"]) for e in store.load_stream(conn, txn)][-2:]
    assert tail == [("hold_cleared", "LOCALITY_CHECKED"), ("assessment_generated", "ASSESSED")]
    assert svc.get_request(lender(world), txn)["assessment"] is not None


def test_high_value_hold_cleared_with_safeguards_reaches_the_lender_with_them(
    conn: Connection, engine: Engine, world: World
) -> None:
    txn = held(conn, engine, world, HighValueHold(), 3)
    svc = make_service(conn, engine)
    result = svc.decide(
        admin(world),
        case_of(conn, txn)["id"],
        Decision(
            "SAFEGUARDS_IMPOSED",
            "Good history with similar items.",
            ("Deposit record", "Handover photos"),
        ),
    )
    assert result.state == "ASSESSED"
    seen = svc.get_request(lender(world), txn)
    assert seen["moderator_safeguards"] == [
        {"label": "Deposit record"},
        {"label": "Handover photos"},
    ]
    assert seen["actions"] == ["accept", "decline"]


def test_restricting_a_hold_declines_the_request(
    conn: Connection, engine: Engine, world: World
) -> None:
    txn = held(conn, engine, world, HighValueHold(), 4)
    result = make_service(conn, engine).decide(
        moderator(world),
        case_of(conn, txn)["id"],
        Decision("RESTRICTED", "Ring confirmed on review."),
    )
    assert result.state == "DECLINED"
    assert case_of(conn, txn)["status"] == "DECIDED"


def test_cleared_locality_hold_goes_on_to_the_assessment(
    conn: Connection, engine: Engine, world: World
) -> None:
    uid = conn.execute(
        text(
            "INSERT INTO app_user (display_name, email, verification_level, status, is_synthetic) "
            "VALUES ('Newcomer', 'newcomer-mod@example.test', 'COMMUNITY_VERIFIED', 'ACTIVE', true) "
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
    txn = svc.create_request(Actor(uid), world.items[5], period(3, 6)).transaction_id
    result = svc.decide(
        moderator(world), case_of(conn, txn)["id"], Decision("CLEARED", "Known to me.")
    )
    assert result.state == "ASSESSED"


def test_tc56_cancelling_while_held_withdraws_the_case_without_a_decision(
    conn: Connection, engine: Engine, world: World
) -> None:
    txn = held(conn, engine, world, HighValueHold(), 6)
    svc = make_service(conn, engine)
    assert svc.cancel(borrower(world), txn).state == "CANCELLED"
    assert case_of(conn, txn)["status"] == "WITHDRAWN"
    assert decisions_of(conn, txn) == 0


def test_tc57_a_second_decision_on_the_same_case_is_refused(
    conn: Connection, engine: Engine, world: World
) -> None:
    """Sequential form of TC-57: the second moderator sees the current state and nothing is
    applied. A truly simultaneous second write fails on the stream's sequence number instead."""
    txn = held(conn, engine, world, HighValueHold(), 7)
    case_id = case_of(conn, txn)["id"]
    svc = make_service(conn, engine)
    svc.decide(moderator(world), case_id, Decision("CLEARED", "Fine."))
    with pytest.raises(InvalidTransition, match="already decided"):
        svc.decide(admin(world), case_id, Decision("RESTRICTED", "Too late."))
    assert decisions_of(conn, txn) == 1
    assert svc.get_request(lender(world), txn)["view"].state == "ASSESSED"


# ----------------------------------------------------------------------------- who may decide
def test_only_community_moderators_and_admins_decide_never_a_party(
    conn: Connection, engine: Engine, world: World
) -> None:
    txn = held(conn, engine, world, HighValueHold(), 8)
    case_id = case_of(conn, txn)["id"]
    svc = make_service(conn, engine)
    for outsider in (Actor(world.borrower2), lender(world), Actor(world.lender, "ADMIN")):
        with pytest.raises(NotAuthorised):
            svc.decide(outsider, case_id, Decision("CLEARED", "x"))
    assert decisions_of(conn, txn) == 0


def test_moderation_queue_lists_live_cases_for_moderators_only(
    conn: Connection, engine: Engine, world: World
) -> None:
    txn = held(conn, engine, world, HighValueHold(), 9)
    svc = make_service(conn, engine)
    queue = svc.moderation_queue(moderator(world))
    assert txn in [c["transaction_id"] for c in queue]
    assert svc.moderation_queue(Actor(world.borrower2)) == []
    assert txn in [c["transaction_id"] for c in svc.moderation_queue(admin(world))]
    with pytest.raises(NotAuthorised):
        svc.moderator_case(Actor(world.borrower2), case_of(conn, txn)["id"])
