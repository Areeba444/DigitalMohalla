"""Buttons shown per state and role: invalid ones must not appear (HCI constraint 3)."""

from datetime import UTC, datetime, timedelta

from app.domain.lifecycle.actions import available_actions

T0 = datetime(2026, 11, 1, tzinfo=UTC)


def report(minutes: int) -> dict[str, object]:
    return {"created_at": T0 + timedelta(minutes=minutes)}


def test_lender_sees_accept_and_decline_only_when_assessed() -> None:
    assert available_actions("ASSESSED", "LENDER", {}) == ["accept", "decline"]
    assert available_actions("ACCEPTED", "LENDER", {}) == ["handover_checklist", "raise_dispute"]
    assert available_actions("COMPLETED", "LENDER", {}) == []
    assert available_actions("DECLINED", "LENDER", {}) == []


def test_borrower_can_cancel_only_while_pending() -> None:
    for state in ("REQUEST_CREATED", "LOCALITY_CHECKED", "HELD_FOR_REVIEW", "ASSESSED"):
        assert available_actions(state, "BORROWER", {}) == ["cancel"]
    assert available_actions("ACCEPTED", "BORROWER", {}) == [
        "raise_dispute"
    ]  # waits for the lender's checklist
    assert available_actions("CANCELLED", "BORROWER", {}) == []


def test_borrower_confirms_handover_only_after_lender_checklist() -> None:
    lender = {("HANDOVER", "LENDER"): report(0)}
    assert available_actions("ACCEPTED", "BORROWER", lender) == [
        "handover_confirm",
        "raise_dispute",
    ]
    both = {**lender, ("HANDOVER", "BORROWER"): report(5)}
    assert available_actions("ACCEPTED", "BORROWER", both) == ["raise_dispute"]  # already confirmed
    redone = {("HANDOVER", "LENDER"): report(10), ("HANDOVER", "BORROWER"): report(5)}
    assert available_actions("ACCEPTED", "BORROWER", redone) == [
        "handover_confirm",
        "raise_dispute",
    ]


def test_lender_checklist_is_not_offered_again_after_return_report() -> None:
    assert available_actions("RETURN_INITIATED", "LENDER", {}) == [
        "return_checklist",
        "raise_dispute",
    ]
    done = {("RETURN", "LENDER"): report(0)}
    assert available_actions("RETURN_INITIATED", "LENDER", done) == ["raise_dispute"]
    assert available_actions("RETURN_INITIATED", "BORROWER", done) == [
        "return_confirm",
        "raise_dispute",
    ]


def test_active_loan_offers_return_to_the_borrower_only() -> None:
    assert available_actions("ACTIVE", "BORROWER", {}) == ["initiate_return", "raise_dispute"]
    assert available_actions("ACTIVE", "LENDER", {}) == ["raise_dispute"]


def test_no_actions_without_a_role_or_state() -> None:
    assert available_actions("ASSESSED", None, {}) == []
    assert available_actions(None, "LENDER", {}) == []


def test_a_disputed_loan_is_frozen_except_for_the_raisers_withdrawal() -> None:  # FR-B-16/17
    assert available_actions("DISPUTED", "LENDER", {}, dispute_raised_by="LENDER") == [
        "withdraw_dispute"
    ]
    assert available_actions("DISPUTED", "BORROWER", {}, dispute_raised_by="LENDER") == []
    assert available_actions("DISPUTED", "BORROWER", {}, dispute_raised_by=None) == []


def test_disputes_can_be_raised_only_in_accepted_active_and_return_initiated() -> None:
    for state in ("ASSESSED", "HELD_FOR_REVIEW", "COMPLETED", "CANCELLED", "DISPUTED"):
        for role in ("BORROWER", "LENDER"):
            assert "raise_dispute" not in available_actions(state, role, {})
