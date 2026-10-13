"""Which verified outcomes a closing event produces (team decision D11; FR-B-15, FR-T-03).

Only two events produce outcomes: `transaction_closed` (both parties confirmed the return) and
`dispute_resolved` (a moderator decided). A loan that is still open, or a dispute that is still
open, produces nothing, so disputed evidence is never counted before it is resolved.

Plain-language rules (D11):
  * Borrower is measured on ON_TIME_RETURN, CONDITION_AGREED and DISPUTE_FREE.
  * Lender is measured on CONDITION_AGREED (the item was as described) and DISPUTE_FREE.
  * A normal close: every metric is a success, except on-time return, which follows the return
    time against the due date.
  * A resolved dispute: the party the moderator found at fault fails CONDITION_AGREED and
    DISPUTE_FREE; "no fault" counts as success for both parties.
  * A metric that does not apply is not recorded at all (a missing outcome is not a failure):
    on-time return when the item never changed hands, or when the dispute was not about the return.
Pure functions, no I/O (A8 layer rules).
"""

from dataclasses import dataclass
from typing import Literal

Role = Literal["BORROWER", "LENDER"]
Metric = Literal["ON_TIME_RETURN", "CONDITION_AGREED", "DISPUTE_FREE"]
Fault = Literal["borrower", "lender", "none"]

DISPUTE_STAGES = ("ACCEPTED", "ACTIVE", "RETURN_INITIATED")
FAULTS = ("borrower", "lender", "none")


@dataclass(frozen=True)
class OutcomeRecord:
    subject_role: Role
    metric: Metric
    success: bool


@dataclass(frozen=True)
class ClosedLoan:
    """A loan that ended with `transaction_closed`."""

    returned_on_time: bool


@dataclass(frozen=True)
class ResolvedDispute:
    """A loan that ended with `dispute_resolved`.

    stage: the state the dispute was opened from (the `previous_state` of `dispute_opened`).
    reason: the dispute reason (DAMAGE, NON_RETURN, CONDITION_MISMATCH, NO_SHOW, OTHER).
    at_fault: what the moderator found, from the decision's `resolved_outcome`.
    returned_on_time: whether `return_initiated` was on time; known only at stage RETURN_INITIATED.
    """

    stage: str
    reason: str
    at_fault: Fault
    returned_on_time: bool | None = None


def outcomes_for_closed_loan(loan: ClosedLoan) -> list[OutcomeRecord]:
    return [
        OutcomeRecord("BORROWER", "ON_TIME_RETURN", loan.returned_on_time),
        OutcomeRecord("BORROWER", "CONDITION_AGREED", True),
        OutcomeRecord("BORROWER", "DISPUTE_FREE", True),
        OutcomeRecord("LENDER", "CONDITION_AGREED", True),
        OutcomeRecord("LENDER", "DISPUTE_FREE", True),
    ]


def outcomes_for_resolved_dispute(d: ResolvedDispute) -> list[OutcomeRecord]:
    if d.stage not in DISPUTE_STAGES:
        raise ValueError(f"a dispute cannot be opened from {d.stage}")
    if d.at_fault not in FAULTS:
        raise ValueError(f"unknown finding {d.at_fault!r}; expected one of {FAULTS}")
    borrower_ok = d.at_fault != "borrower"
    lender_ok = d.at_fault != "lender"
    out: list[OutcomeRecord] = []
    if d.stage == "RETURN_INITIATED":
        if d.returned_on_time is None:
            raise ValueError("a dispute at return needs the return time")
        out.append(OutcomeRecord("BORROWER", "ON_TIME_RETURN", d.returned_on_time))
    elif d.stage == "ACTIVE" and d.reason == "NON_RETURN":
        out.append(OutcomeRecord("BORROWER", "ON_TIME_RETURN", False))
    if d.stage != "ACCEPTED":  # before handover the borrower never had the item
        out.append(OutcomeRecord("BORROWER", "CONDITION_AGREED", borrower_ok))
    out.append(OutcomeRecord("BORROWER", "DISPUTE_FREE", borrower_ok))
    out.append(OutcomeRecord("LENDER", "CONDITION_AGREED", lender_ok))
    out.append(OutcomeRecord("LENDER", "DISPUTE_FREE", lender_ok))
    return out
