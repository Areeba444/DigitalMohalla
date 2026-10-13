"""TC-35: the database's assessment_rule_ck and the policy's RULES table agree, row for row.

Every rule's (decision, state, hold reason) from app/domain/assurance/policy/decision.py is stored
as an assessment row and accepted; a row whose rule and state disagree is refused. Each insert runs
in a savepoint inside a rolled-back connection. All data is synthetic.
"""

import pytest
from sqlalchemy import Connection, Engine
from sqlalchemy.exc import IntegrityError

from app.domain.assurance.policy.decision import RULES
from app.domain.lifecycle.ports import AssessmentResult
from app.infra.eventstore.postgres import PostgresLifecycleStore
from tests.integration.conftest import World, period
from tests.integration.test_borrowing_service import CONFIG, borrower, make_service

LEVEL = {"R2": 4, "R5": 3}  # the manipulation level each rule needs; the rest pass at level 1


def result(rule: str, state: str | None = None) -> AssessmentResult:
    decision, rule_state, hold = RULES[rule]
    return AssessmentResult(
        assurance_state=state or rule_state,
        policy_decision=decision,
        rule_fired=rule,
        hold_reason=hold,
        explanation="Synthetic constraint check.",
        config_version=CONFIG.config_version,
        manipulation_risk={"R2": 80, "R5": 50}.get(rule, 0),  # assessment_level_ck bands
        manipulation_level=LEVEL.get(rule, 1),
        manipulation_corroborated=rule == "R2",
        posterior_mean=0.5,
        ci90_low=0.05,
        ci90_high=0.95,
        effective_evidence=0.0,
    )


@pytest.mark.parametrize("rule", sorted(RULES))
def test_every_policy_rule_is_accepted_by_the_schema(
    conn: Connection, engine: Engine, world: World, rule: str
) -> None:
    txn = make_service(conn, engine).create_request(
        borrower(world), world.items[15], period(40, 42)
    )
    with conn.begin_nested():
        PostgresLifecycleStore(conn).insert_assessment(txn.transaction_id, result(rule))


def test_a_row_whose_rule_and_state_disagree_is_refused(
    conn: Connection, engine: Engine, world: World
) -> None:
    txn = make_service(conn, engine).create_request(
        borrower(world), world.items[15], period(40, 42)
    )
    with pytest.raises(IntegrityError, match="assessment_rule_ck"), conn.begin_nested():
        PostgresLifecycleStore(conn).insert_assessment(
            txn.transaction_id, result("R7", state="REVIEW_RECOMMENDED")
        )
