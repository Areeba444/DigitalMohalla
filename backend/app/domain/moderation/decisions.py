"""Moderator decisions on escalation cases (UC-I4; FR-T-11; ADR-0003; suite 13).

Plain-language rules:
- Every decision needs a reason (FR-T-11). It is recorded first, then applied as one lifecycle
  event that points to it; the database checks that pairing again.
- A dispute (the loan is DISPUTED) can only be resolved, with a finding: the borrower was at fault,
  the lender was, or nobody was. The loan ends COMPLETED and the finding becomes trust evidence.
- A hold (the request is HELD_FOR_REVIEW) can be cleared, cleared with safeguards for the lender,
  or restricted (the request is declined; nobody is restricted without this human decision).
  Clearing a locality or engine-failure hold sends the request back to LOCALITY_CHECKED so the
  assessment runs again; clearing a manipulation or high-value hold releases the existing
  assessment to the lender (ASSESSED). An engine-failure hold has no assessment, so safeguards
  cannot be imposed on it (UC-I4 3c).
Pure, no I/O.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from app.domain.lifecycle.errors import EventStoreError

FAULTS = ("borrower", "lender", "none")
HOLD_KINDS = ("CLEARED", "SAFEGUARDS_IMPOSED", "RESTRICTED")
REASSESS = ("locality_inconclusive", "locality_conflict", "engine_failure")


class InvalidDecision(EventStoreError):
    """The decision is incomplete or does not fit the case (refused before anything is stored)."""


@dataclass(frozen=True)
class Decision:
    kind: str
    reason: str
    safeguards: Sequence[str] = field(default_factory=tuple)
    at_fault: str | None = None


@dataclass(frozen=True)
class Plan:
    event_type: str
    new_state: str
    safeguards: list[dict[str, Any]]
    resolved_outcome: dict[str, Any] | None


def plan(state: str | None, hold_reason: str | None, d: Decision) -> Plan:
    """What applying `d` to a case whose transaction is in `state` means, or InvalidDecision."""
    if not d.reason or not d.reason.strip():
        raise InvalidDecision("a decision needs a reason (FR-T-11)")
    safeguards = [{"label": s.strip()} for s in d.safeguards if s and s.strip()]
    if state == "DISPUTED":
        if d.kind != "DISPUTE_RESOLVED":
            raise InvalidDecision("a dispute can only be resolved")
        if d.at_fault not in FAULTS:
            raise InvalidDecision(
                f"resolving a dispute needs a finding: one of {', '.join(FAULTS)}"
            )
        if safeguards:
            raise InvalidDecision("safeguards belong to holds, not to resolved disputes")
        return Plan("dispute_resolved", "COMPLETED", [], {"at_fault": d.at_fault})
    if state != "HELD_FOR_REVIEW":
        raise InvalidDecision(f"nothing to decide while the request is {state}")
    if d.kind not in HOLD_KINDS:
        raise InvalidDecision(f"a hold can be {', '.join(k.lower() for k in HOLD_KINDS)}")
    if d.at_fault is not None:
        raise InvalidDecision("a finding of fault belongs to disputes")
    if d.kind == "SAFEGUARDS_IMPOSED":
        if hold_reason == "engine_failure":
            raise InvalidDecision(
                "no assessment exists after an engine failure, so no safeguards (UC-I4 3c)"
            )
        if not safeguards:
            raise InvalidDecision("name at least one safeguard")
    elif safeguards:
        raise InvalidDecision("safeguards are given only with SAFEGUARDS_IMPOSED")
    if d.kind == "RESTRICTED":
        return Plan("request_declined", "DECLINED", [], None)
    new_state = "LOCALITY_CHECKED" if hold_reason in REASSESS else "ASSESSED"
    return Plan("hold_cleared", new_state, safeguards, None)
