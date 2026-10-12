"""Buttons shown per state and role: invalid ones must not appear (HCI constraint 3)."""

from datetime import UTC, datetime, timedelta

from app.domain.lifecycle.actions import available_actions

T0 = datetime(2026, 11, 1, tzinfo=UTC)


def report(minutes: int) -> dict[str, object]:
    return {"created_at": T0 + timedelta(minutes=minutes)}


def test_lender_sees_accept_and_decline_only_when_assessed() -> None:
    assert available_actions("ASSESSED", "LENDER", {}) == ["accept", "decline"]
    assert available_actions("ACCEPTED", "LENDER", {}) == ["handover_checklist"]
    assert available_actions("COMPLETED", "LENDER", {}) == []
    assert available_actions("DECLINED", "LENDER", {}) == []


def test_borrower_can_cancel_only_while_pending() -> None:
    for state in ("REQUEST_CREATED", "LOCALITY_CHECKED", "HELD_FOR_REVIEW", "ASSESSED"):
        assert available_actions(state, "BORROWER", {}) == ["cancel"]
    assert available_actions("ACCEPTED", "BORROWER", {}) == []  # waits for the lender's checklist
    assert available_actions("CANCELLED", "BORROWER", {}) == []


def test_borrower_confirms_handover_only_after_lender_checklist() -> None:
    lender = {("HANDOVER", "LENDER"): report(0)}
    assert available_actions("ACCEPTED", "BORROWER", lender) == ["handover_confirm"]
    both = {**lender, ("HANDOVER", "BORROWER"): report(5)}
    assert available_actions("ACCEPTED", "BORROWER", both) == []  # already confirmed
    redone = {("HANDOVER", "LENDER"): report(10), ("HANDOVER", "BORROWER"): report(5)}
    assert available_actions("ACCEPTED", "BORROWER", redone) == ["handover_confirm"]


def test_lender_checklist_is_not_offered_again_after_return_report() -> None:
    assert available_actions("RETURN_INITIATED", "LENDER", {}) == ["return_checklist"]
    done = {("RETURN", "LENDER"): report(0)}
    assert available_actions("RETURN_INITIATED", "LENDER", done) == []
    assert available_actions("RETURN_INITIATED", "BORROWER", done) == ["return_confirm"]


def test_active_loan_offers_return_to_the_borrower_only() -> None:
    assert available_actions("ACTIVE", "BORROWER", {}) == ["initiate_return"]
    assert available_actions("ACTIVE", "LENDER", {}) == []


def test_no_actions_without_a_role_or_state() -> None:
    assert available_actions("ASSESSED", None, {}) == []
    assert available_actions(None, "LENDER", {}) == []
