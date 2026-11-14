"""Loan extensions: request, approve, decline (UC-B8 ext 1a, FR-B-14; lifecycle v3 I03 to I05; F5).

Internal transitions of ACTIVE: the loan stays ACTIVE and the event records what happened. Only the
borrower asks and only the lender answers. One request may be pending at a time: a request is
pending until an `extension_approved` or `extension_declined` follows it. Approval moves the due date
and the held booking in one database transaction (event_apply), so the new dates must still be free
of other bookings (ADR-0002); if they are not, nothing changes and the API answers 409.

Kept out of `service.py` (the plan's rule for new commands); it uses BorrowingService's own checks
(right party, valid transition, audit of refusals) and its notifier.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.lifecycle.errors import InvalidTransition
from app.domain.lifecycle.service import Actor, BorrowingService, CommandResult

_OUTCOMES = ("extension_approved", "extension_declined")


def pending_extension(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The latest extension_requested with no answer after it, or None."""
    pending: dict[str, Any] | None = None
    for e in events:
        if e["event_type"] == "extension_requested":
            pending = e
        elif e["event_type"] in _OUTCOMES:
            pending = None
    return pending


class Extensions:
    def __init__(self, svc: BorrowingService) -> None:
        self.svc = svc

    def request(
        self, actor: Actor, txn_id: UUID, new_due: datetime, reason: str | None = None
    ) -> CommandResult:
        """I03: the borrower asks for a later due date."""
        view = self.svc._precheck(actor, txn_id, "extension_requested", "BORROWER")
        if pending_extension(self.svc.store.events(txn_id)) is not None:
            self.svc._reject(
                actor, txn_id, "extension_requested", "an extension is already pending"
            )
            raise InvalidTransition("an extension request is already waiting for the lender")
        if view.due_at is None or new_due <= view.due_at:
            raise InvalidTransition("the new due date must be later than the current one")
        payload = {"new_due": new_due.isoformat(), **({"reason": reason} if reason else {})}
        self.svc._party_event(actor, view, "extension_requested", "BORROWER", payload)
        self.svc._tell(
            view.lender_id,
            "extension_requested",
            txn_id,
            f"extension_requested:{payload['new_due']}",
            {"new_due": payload["new_due"]},
        )
        return CommandResult(txn_id, "ACTIVE", "extension requested; the lender decides")

    def approve(self, actor: Actor, txn_id: UUID) -> CommandResult:
        """I04: the lender agrees; due date and booking move together, or nothing changes."""
        view = self.svc._precheck(actor, txn_id, "extension_approved", "LENDER")
        asked = self._pending_or_refuse(actor, txn_id, "extension_approved")
        new_due = asked["payload"]["new_due"]
        self.svc._party_event(actor, view, "extension_approved", "LENDER", {"new_due": new_due})
        self.svc._tell(
            view.borrower_id,
            "extension_decided",
            txn_id,
            f"extension_approved:{new_due}",
            {"approved": True, "new_due": new_due},
        )
        return CommandResult(txn_id, "ACTIVE", f"due date moved to {new_due}")

    def decline(self, actor: Actor, txn_id: UUID, reason: str | None = None) -> CommandResult:
        """I05: the lender says no; the due date stays."""
        view = self.svc._precheck(actor, txn_id, "extension_declined", "LENDER")
        asked = self._pending_or_refuse(actor, txn_id, "extension_declined")
        payload = {"new_due": asked["payload"]["new_due"], **({"reason": reason} if reason else {})}
        self.svc._party_event(actor, view, "extension_declined", "LENDER", payload)
        self.svc._tell(
            view.borrower_id,
            "extension_decided",
            txn_id,
            f"extension_declined:{payload['new_due']}",
            {"approved": False, "new_due": payload["new_due"]},
        )
        return CommandResult(txn_id, "ACTIVE", "extension declined; the due date is unchanged")

    def _pending_or_refuse(self, actor: Actor, txn_id: UUID, action: str) -> dict[str, Any]:
        asked = pending_extension(self.svc.store.events(txn_id))
        if asked is None:
            self.svc._reject(actor, txn_id, action, "no extension request is pending")
            raise InvalidTransition("there is no extension request to answer")
        return asked
