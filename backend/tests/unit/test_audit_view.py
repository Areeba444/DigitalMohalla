"""Audit view rules (UC-I6 v1.4; FR-M-05; suite 29, TC-155 and TC-158): masking, groups, concentration.

All values are synthetic.
"""

import pytest

from app.domain.audit.view import (
    MASK,
    AuditRow,
    category,
    concentration,
    mask_text,
    mask_value,
    present,
    short_id,
)


def row(**over: object) -> AuditRow:
    base: dict[str, object] = {
        "source": "audit",
        "id": 7,
        "occurred_at": "2026-11-21T10:00:00+00:00",
        "actor_id": "11111111-2222-3333-4444-555566667777",
        "authorisation": "role:admin",
        "action": "info_requested",
        "target_type": "escalation_case",
        "target_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeee1234",
        "previous_value": None,
        "new_value": {"question": "Call me on 0300-1234567", "deadline": "2026-11-24"},
        "evidence_refs": {},
        "outcome": "SUCCESS",
        "reason": None,
        "hash_valid": True,
    }
    base.update(over)
    return AuditRow(**base)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "text",
    [
        "write to someone@example.test please",
        "my number is +92 300 1234567",
        "call 0300-1234567 today",
        "card 35202-1234567-1",
        "card 3520212345671",
    ],
)
def test_contact_details_and_identity_numbers_are_masked(text: str) -> None:  # TC-155
    out = mask_text(text)
    assert MASK in out
    assert not any(ch.isdigit() for ch in out.replace(MASK, "")) or "@" not in out


def test_dates_and_amounts_are_not_mistaken_for_phone_numbers() -> None:
    assert mask_text("due 2026-11-24, deposit 500") == "due 2026-11-24, deposit 500"


def test_free_text_fields_are_masked_whatever_they_say() -> None:
    out = mask_value({"reason": "the lender was rude", "deadline": "2026-11-24", "notes": ""})
    assert out == {"reason": MASK, "deadline": "2026-11-24", "notes": ""}


def test_nested_values_are_masked() -> None:
    out = mask_value({"statement": {"text": "secret"}, "parts": [{"comment": "x"}]})
    assert out == {"statement": {"text": MASK}, "parts": [{"comment": MASK}]}


def test_present_masks_by_default_and_shows_everything_when_unmasked() -> None:
    r = row(reason="Called the borrower at 0300-1234567")
    masked = present(r)
    assert masked["actor"] == "usr_...7777"
    assert masked["new_value"]["question"] == MASK
    assert masked["reason"] == MASK and masked["masked"] is True
    assert "0300" not in masked["summary"]
    full = present(r, masked=False)
    assert full["actor"] == r.actor_id
    assert full["new_value"]["question"].startswith("Call me")
    assert full["reason"].startswith("Called") and full["masked"] is False


def test_lifecycle_rows_summarise_the_state_change() -> None:
    r = row(
        source="event",
        action="dispute_opened",
        target_type="borrowing_transaction",
        previous_value="ACTIVE",
        new_value="DISPUTED",
    )
    assert "ACTIVE -> DISPUTED" in present(r)["summary"]


@pytest.mark.parametrize(
    ("action", "target", "expected"),
    [
        ("request_created", "borrowing_transaction", "TRANSACTION"),
        ("dispute_opened", "borrowing_transaction", "DISPUTE"),
        ("appeal_filed", "escalation_case", "DISPUTE"),
        ("info_requested", "escalation_case", "DISPUTE"),
        ("membership_requested", "membership", "MEMBERSHIP"),
        ("assessment_generated", "borrowing_transaction", "ASSURANCE"),
        ("held_for_review", "borrowing_transaction", "ASSURANCE"),
        ("audit_viewed", "audit_log", "AUDIT"),
    ],
)
def test_actions_fall_into_the_screen_groups(action: str, target: str, expected: str) -> None:
    assert category(action, target) == expected


def test_short_id_hides_most_of_the_id() -> None:
    assert short_id("abcdef12-3456") == "usr_...3456"
    assert short_id(None) is None


def test_concentration_flags_a_moderator_who_keeps_deciding_on_one_member() -> None:  # TC-158
    decisions = [("mod-a", "user-1")] * 4 + [("mod-a", "user-2")] + [("mod-b", "user-3")] * 2
    flagged = concentration(decisions, min_decisions=3, min_share=0.6)
    assert len(flagged) == 1
    c = flagged[0]
    assert (c.moderator, c.member, c.decisions, c.share) == ("usr_...od-a", "usr_...er-1", 4, 0.8)


def test_spread_out_decisions_are_not_flagged() -> None:
    decisions = [("mod-a", f"user-{i}") for i in range(10)]
    assert concentration(decisions, min_decisions=3, min_share=0.6) == []
