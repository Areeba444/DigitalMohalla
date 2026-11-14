"""Scheduled lifecycle transitions (ADR-0012; lifecycle v3 T19, plus the F5 jobs).

Every event a job appends is a SYSTEM event with authorisation `system:scheduler`. The database
still checks the transition (`allowed_transition`) and its guards, so a job can never make a move
that a person could not; if the loan changed state since `due()` ran, the append fails, the claim is
marked FAILED, and the next run no longer finds the loan due.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.domain.scheduler.runner import DueItem

SCHEDULER = "system:scheduler"


def system_event(
    uow: Any, txn: UUID, event_type: str, new_state: str, payload: dict[str, Any]
) -> int:
    return int(
        uow.store.append(
            txn,
            event_type,
            new_state,
            actor_id=None,
            authorisation=SCHEDULER,
            payload=payload,
        )
    )


def tell_parties(uow: Any, txn: UUID, type_: str, key: str, extra: dict[str, Any]) -> None:
    """Notify both parties once (dedupe `<transaction>:<key>`)."""
    details = uow.store.details(txn)
    view = uow.store.view(txn)
    payload = {"transaction_id": str(txn), "item_title": details["item_title"], **extra}
    for user in (view.borrower_id, view.lender_id):
        uow.notifier.notify(user, type_, payload, f"{txn}:{key}")


class NoShow:
    """T19: ACCEPTED, the handover time plus `handover_grace_hours` passed without a handover.

    The booking is released by the database with the NO_SHOW state (event_apply)."""

    name = "no_show"

    def due(self, uow: Any, now: datetime) -> list[DueItem]:
        grace = timedelta(hours=float(uow.timers["handover_grace_hours"]))
        rows = uow.conn.execute(
            text(
                "SELECT id FROM borrowing_transaction WHERE current_state = 'ACCEPTED' "
                "AND lower(requested_period) + CAST(:grace AS interval) < :now ORDER BY id"
            ),
            {"grace": grace, "now": now},
        ).scalars()
        return [DueItem(f"{t}:no_show", {"txn": t}) for t in rows]

    def run(self, uow: Any, item: DueItem, now: datetime) -> None:
        txn = item.ref["txn"]
        system_event(
            uow, txn, "no_show", "NO_SHOW", {"grace_hours": uow.timers["handover_grace_hours"]}
        )
        tell_parties(uow, txn, "no_show", "no_show", {})
