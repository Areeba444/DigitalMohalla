"""Moderator decision rules (UC-I4; FR-T-11; ADR-0003, ADR-0009; TC-53 to TC-55, TC-140 to TC-144).

Pure, no database. ADR-0009: a dispute closes by the item's possession, checked against the stage.
"""

import pytest

from app.domain.moderation.decisions import Decision, InvalidDecision, plan


def test_resolving_a_dispute_completes_the_loan_with_the_finding() -> None:  # TC-53
    p = plan(
        "DISPUTED",
        None,
        Decision(
            "DISPUTE_RESOLVED",
            "Photos show new damage.",
            at_fault="borrower",
            possession="RETURNED",
        ),
        dispute_stage="ACTIVE",
    )
    assert (p.event_type, p.new_state, p.resolved_outcome) == (
        "dispute_resolved",
        "COMPLETED",
        {"at_fault": "borrower", "possession": "RETURNED"},
    )


@pytest.mark.parametrize(
    ("stage", "possession", "end_state"),
    [
        ("ACCEPTED", "NOT_HANDED_OVER", "NO_SHOW"),  # T25a: dates released, no return outcome
        ("ACTIVE", "WITH_BORROWER", "ACTIVE"),  # T25b: the loan goes on, dates stay held
        ("RETURN_INITIATED", "WITH_BORROWER", "ACTIVE"),
        ("ACTIVE", "RETURNED", "COMPLETED"),  # T25c
        ("RETURN_INITIATED", "RETURNED", "COMPLETED"),
        ("ACTIVE", "LOST", "COMPLETED"),
        ("RETURN_INITIATED", "LOST", "COMPLETED"),
    ],
)
def test_possession_decides_how_the_dispute_ends(  # TC-140 to TC-143, ADR-0009
    stage: str, possession: str, end_state: str
) -> None:
    p = plan(
        "DISPUTED",
        None,
        Decision("DISPUTE_RESOLVED", "Checked.", at_fault="none", possession=possession),
        dispute_stage=stage,
    )
    assert p.new_state == end_state
    assert p.resolved_outcome == {"at_fault": "none", "possession": possession}


@pytest.mark.parametrize(
    ("stage", "possession"),
    [
        ("ACCEPTED", "RETURNED"),  # TC-144: the item was never handed over
        ("ACCEPTED", "WITH_BORROWER"),
        ("ACCEPTED", "LOST"),
        ("ACTIVE", "NOT_HANDED_OVER"),  # handed over already
        ("RETURN_INITIATED", "NOT_HANDED_OVER"),
    ],
)
def test_possession_that_does_not_fit_the_stage_is_refused(stage: str, possession: str) -> None:
    with pytest.raises(InvalidDecision, match="does not fit"):
        plan(
            "DISPUTED",
            None,
            Decision("DISPUTE_RESOLVED", "x", at_fault="none", possession=possession),
            dispute_stage=stage,
        )


@pytest.mark.parametrize("possession", [None, "", "SOMEWHERE"])
def test_a_dispute_decision_must_say_where_the_item_is(possession: str | None) -> None:
    with pytest.raises(InvalidDecision, match="possession"):
        plan(
            "DISPUTED",
            None,
            Decision("DISPUTE_RESOLVED", "x", at_fault="none", possession=possession),
            dispute_stage="ACTIVE",
        )


@pytest.mark.parametrize("reason", ["", "   ", "\n"])
def test_every_decision_needs_a_reason(reason: str) -> None:  # TC-54
    with pytest.raises(InvalidDecision, match="reason"):
        plan("HELD_FOR_REVIEW", "manipulation_risk", Decision("CLEARED", reason))


@pytest.mark.parametrize(
    ("hold", "state"),
    [
        ("manipulation_risk", "ASSESSED"),
        ("high_value_low_confidence", "ASSESSED"),
        ("locality_inconclusive", "LOCALITY_CHECKED"),
        ("locality_conflict", "LOCALITY_CHECKED"),
        ("engine_failure", "LOCALITY_CHECKED"),
    ],
)
def test_clearing_a_hold_goes_where_adr_0003_says(hold: str, state: str) -> None:
    assert plan("HELD_FOR_REVIEW", hold, Decision("CLEARED", "Checked.")).new_state == state


def test_no_safeguards_on_an_engine_failure_hold() -> None:  # TC-55, UC-I4 3c
    with pytest.raises(InvalidDecision, match="engine failure"):
        plan("HELD_FOR_REVIEW", "engine_failure", Decision("SAFEGUARDS_IMPOSED", "x", ("Photos",)))


def test_safeguards_are_labelled_and_only_with_safeguards_imposed() -> None:
    p = plan(
        "HELD_FOR_REVIEW",
        "high_value_low_confidence",
        Decision("SAFEGUARDS_IMPOSED", "Strong elsewhere.", (" Deposit record ", "")),
    )
    assert (p.event_type, p.new_state, p.safeguards) == (
        "hold_cleared",
        "ASSESSED",
        [{"label": "Deposit record"}],
    )
    with pytest.raises(InvalidDecision, match="at least one safeguard"):
        plan("HELD_FOR_REVIEW", "manipulation_risk", Decision("SAFEGUARDS_IMPOSED", "x"))
    with pytest.raises(InvalidDecision, match="only with SAFEGUARDS_IMPOSED"):
        plan("HELD_FOR_REVIEW", "manipulation_risk", Decision("CLEARED", "x", ("Photos",)))


def test_restricting_declines_the_request() -> None:
    p = plan("HELD_FOR_REVIEW", "manipulation_risk", Decision("RESTRICTED", "Ring confirmed."))
    assert (p.event_type, p.new_state) == ("request_declined", "DECLINED")


@pytest.mark.parametrize(
    ("state", "decision", "match"),
    [
        ("DISPUTED", Decision("CLEARED", "x"), "only be resolved"),
        ("DISPUTED", Decision("DISPUTE_RESOLVED", "x"), "finding"),
        ("DISPUTED", Decision("DISPUTE_RESOLVED", "x", ("Photos",), "none"), "safeguards"),
        (
            "HELD_FOR_REVIEW",
            Decision("CLEARED", "x", possession="RETURNED"),
            "possession belong to disputes",
        ),
        ("HELD_FOR_REVIEW", Decision("DISPUTE_RESOLVED", "x", at_fault="none"), "a hold can be"),
        ("HELD_FOR_REVIEW", Decision("CLEARED", "x", at_fault="lender"), "finding of fault"),
        ("ASSESSED", Decision("CLEARED", "x"), "nothing to decide"),
    ],
)
def test_decisions_that_do_not_fit_the_case_are_refused(
    state: str, decision: Decision, match: str
) -> None:
    with pytest.raises(InvalidDecision, match=match):
        plan(state, "manipulation_risk", decision)
