"""Counter-offer: the lender proposes other dates, the borrower accepts or declines (ADR-0015, F6).

UC-B6 ext 3b, FR-B-10; lifecycle v3 I07, I08 and T29:

    I07  ASSESSED --counter_offered [lender; none open; other, future, bounded dates]--> ASSESSED
    I08  ASSESSED --counter_declined [borrower; one open]--> ASSESSED
    T29  ASSESSED --counter_accepted [borrower; one open; dates still free]--> LOCALITY_CHECKED
         then the assessment runs again (T05 to T08), because loan length feeds the similarity
         weighting (decision D17)

The database enforces every guard (`event_validate_v3`, `open_counter_offer`) and moves the request's
dates on acceptance (`event_apply_v3`); this module adds clear messages and notifications. The
response window restarts at a counter-offer (the request_expiry job reads it).
"""

from typing import Any
from uuid import UUID

from app.domain.lifecycle.errors import InvalidTransition
from app.domain.lifecycle.service import Actor, BorrowingService, CommandResult

_COUNTER = ("counter_offered", "counter_accepted", "counter_declined")


def open_counter_offer(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The latest counter_offered, if no counter_accepted or counter_declined came after it."""
    last = None
    for e in events:
        if e["event_type"] in _COUNTER:
            last = e
    return last if last is not None and last["event_type"] == "counter_offered" else None


class CounterOffers:
    def __init__(self, svc: BorrowingService) -> None:
        self.svc = svc

    def offer(
        self, actor: Actor, txn_id: UUID, period: str, message: str | None = None
    ) -> CommandResult:
        """I07: the lender proposes `period` (a bounded range literal) instead of declining."""
        view = self.svc._precheck(actor, txn_id, "counter_offered", "LENDER")
        if open_counter_offer(self.svc.store.events(txn_id)) is not None:
            self.svc._reject(actor, txn_id, "counter_offered", "a counter-offer is already open")
            raise InvalidTransition("you already proposed other dates; wait for the borrower")
        payload = {"proposed_period": period, **({"message": message} if message else {})}
        self.svc._party_event(actor, view, "counter_offered", "LENDER", payload)
        self.svc._tell(
            view.borrower_id,
            "counter_offered",
            txn_id,
            f"counter_offered:{period}",
            {"proposed_period": period},
        )
        return CommandResult(txn_id, "ASSESSED", "other dates proposed; the borrower decides")

    def accept(self, actor: Actor, txn_id: UUID) -> CommandResult:
        """T29: the borrower takes the offered dates; the request is assessed again."""
        view = self.svc._precheck(actor, txn_id, "counter_accepted", "BORROWER")
        offer = self._open_or_refuse(actor, txn_id, "counter_accepted")
        period = offer["payload"]["proposed_period"]
        self.svc._party_event(
            actor, view, "counter_accepted", "BORROWER", {"requested_period": period}
        )
        result = self.svc._assess(txn_id)  # ASSESSED again, or HELD_FOR_REVIEW
        self.svc._tell(
            view.lender_id,
            "counter_accepted",
            txn_id,
            f"counter_accepted:{period}",
            {"requested_period": period, "state": result.state},
        )
        return CommandResult(
            txn_id,
            result.state,
            "new dates accepted; the request was assessed again",
            result.hold_reason,
            result.assessment_id,
        )

    def decline(self, actor: Actor, txn_id: UUID) -> CommandResult:
        """I08: the borrower keeps the original dates; the lender can still accept or decline."""
        view = self.svc._precheck(actor, txn_id, "counter_declined", "BORROWER")
        offer = self._open_or_refuse(actor, txn_id, "counter_declined")
        self.svc._party_event(actor, view, "counter_declined", "BORROWER")
        self.svc._tell(
            view.lender_id,
            "counter_declined",
            txn_id,
            f"counter_declined:{offer['payload']['proposed_period']}",
        )
        return CommandResult(txn_id, "ASSESSED", "the borrower kept the original dates")

    def _open_or_refuse(self, actor: Actor, txn_id: UUID, action: str) -> dict[str, Any]:
        offer = open_counter_offer(self.svc.store.events(txn_id))
        if offer is None:
            self.svc._reject(actor, txn_id, action, "no open counter-offer")
            raise InvalidTransition("there is no counter-offer to answer")
        return offer
