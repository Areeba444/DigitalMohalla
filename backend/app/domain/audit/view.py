"""Audit log view rules (UC-I6 v1.4; FR-M-05; NFR-S-05, NFR-PR-01; plan item M5). Pure, no I/O.

Plain-language rules:
- The audit view shows lifecycle events and the other audited actions together, newest first.
- Sensitive content is masked by default (UC-I6 ext 3d): free-text fields (reasons, statements,
  descriptions, questions, comments, notes), e-mail addresses, phone numbers and identity-card
  numbers. User ids are shortened. An admin can unmask one entry only by stating a purpose, and
  that unmasking is itself written to the audit log.
- Every entry carries the result of its hash-chain check; a failed check is shown as a tamper
  warning and the entry is still shown (UC-I6 ext 3c).
- The concentration highlight flags a moderator whose decisions keep landing on the same member
  (UC-I6 ext 3b; supports the moderator-misuse case). It is a prompt to look, never a finding.
"""

import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

MASK = "[masked]"
FREE_TEXT_KEYS = frozenset(
    {"reason", "statement", "description", "question", "comment", "message", "notes", "text"}
)
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_CNIC = re.compile(r"\b\d{5}-?\d{7}-?\d\b")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")  # an ISO date is not a phone number
_PHONE = re.compile(r"(?<!\w)\+?\d[\d\s-]{8,}\d(?!\w)")

# Filter chips of the audit screen (W21): which actions belong to which group
CATEGORY_PREFIXES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("DISPUTE", ("dispute_", "appeal_", "decision_", "info_", "case_", "reject_case")),
    ("MEMBERSHIP", ("membership_", "invitation", "reject_issue_invitation", "locality_")),
    ("ASSURANCE", ("assessment_", "held_for_review", "hold_cleared", "review_")),
)


def category(action: str, target_type: str) -> str:
    """TRANSACTION, DISPUTE, MEMBERSHIP, ASSURANCE or AUDIT (views and unmasking of the log)."""
    if action.startswith("audit_"):
        return "AUDIT"
    for name, prefixes in CATEGORY_PREFIXES:
        if action.startswith(prefixes):
            return name
    if target_type in ("membership", "invitation", "community"):
        return "MEMBERSHIP"
    if target_type == "escalation_case":
        return "DISPUTE"
    return "TRANSACTION"


def short_id(value: Any) -> str | None:
    """A user id as 'usr_...4f2a': enough to tell people apart, not to look them up."""
    if value is None:
        return None
    text = str(value)
    return f"usr_...{text[-4:]}" if len(text) > 4 else "usr_..."


def mask_text(text: str) -> str:
    """E-mail, identity-card and phone numbers inside free text are replaced by MASK."""
    text = _EMAIL.sub(MASK, text)
    text = _CNIC.sub(MASK, text)
    return _PHONE.sub(lambda m: m.group(0) if _DATE.fullmatch(m.group(0)) else MASK, text)


def mask_value(value: Any, key: str | None = None) -> Any:
    """Masks a JSON value: free-text keys entirely, other strings for contact details."""
    if isinstance(value, Mapping):
        return {k: mask_value(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [mask_value(v, key) for v in value]
    if isinstance(value, str):
        if key in FREE_TEXT_KEYS and value.strip():
            return MASK
        return mask_text(value)
    return value


@dataclass(frozen=True)
class AuditRow:
    """One audit entry as read from the database (lifecycle event or audit_log row)."""

    source: str  # "event" or "audit"
    id: int
    occurred_at: str
    actor_id: str | None
    authorisation: str
    action: str
    target_type: str
    target_id: str
    previous_value: Any
    new_value: Any
    evidence_refs: Any
    outcome: str
    reason: str | None
    hash_valid: bool


def summary(row: AuditRow, masked: bool = True) -> str:
    """One line for the feed, e.g. 'borrowing_transaction ...1a2b · ACTIVE -> DISPUTED · reason [masked]'."""
    parts = [f"{row.target_type} ...{row.target_id[-4:]}"]
    prev, new = row.previous_value, row.new_value
    if isinstance(prev, str) or isinstance(new, str):
        parts.append(f"{prev or '-'} -> {new or '-'}")
    elif isinstance(new, Mapping) and new:
        shown = mask_value(new) if masked else new
        parts.append(", ".join(f"{k}: {v}" for k, v in list(shown.items())[:4]))
    if row.outcome == "REJECTED":
        parts.append("REJECTED")
    if row.reason:
        parts.append(f"reason: {MASK if masked else row.reason}")
    return " · ".join(parts)


def present(row: AuditRow, masked: bool = True) -> dict[str, Any]:
    """The entry as the API returns it; masked unless an unmasking was requested and logged."""
    return {
        "source": row.source,
        "id": row.id,
        "occurred_at": row.occurred_at,
        "action": row.action,
        "category": category(row.action, row.target_type),
        "actor": short_id(row.actor_id) if masked else row.actor_id,
        "authorisation": row.authorisation,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "outcome": row.outcome,
        "summary": summary(row, masked),
        "previous_value": mask_value(row.previous_value) if masked else row.previous_value,
        "new_value": mask_value(row.new_value) if masked else row.new_value,
        "reason": (MASK if row.reason else None) if masked else row.reason,
        "hash_valid": row.hash_valid,
        "masked": masked,
    }


@dataclass(frozen=True)
class Concentration:
    moderator: str
    member: str
    decisions: int
    share: float


def concentration(
    decisions: Iterable[tuple[str, str]], min_decisions: int, min_share: float
) -> list[Concentration]:
    """(moderator, member) pairs where one moderator's decisions keep involving the same member.

    `decisions` holds one (moderator id, member id) pair per member a decision was about. A pair is
    flagged when it has at least `min_decisions` decisions and makes up at least `min_share` of that
    moderator's decisions. Ids are shortened in the result.
    """
    per_mod: Counter[str] = Counter()
    per_pair: Counter[tuple[str, str]] = Counter()
    for mod, member in decisions:
        per_mod[mod] += 1
        per_pair[(mod, member)] += 1
    flagged = [
        Concentration(str(short_id(mod)), str(short_id(member)), n, round(n / per_mod[mod], 2))
        for (mod, member), n in per_pair.items()
        if n >= min_decisions and n / per_mod[mod] >= min_share
    ]
    return sorted(flagged, key=lambda c: (-c.decisions, c.moderator, c.member))
