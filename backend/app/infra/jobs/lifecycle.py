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


class RequestExpiry:
    """T15: an ASSESSED request the lender did not answer within `request_response_window_hours`.

    The window starts at the latest of: the assessment reaching the lender, a moderator clearing a
    hold (T11), or a counter-offer (ADR-0015 restarts it)."""

    name = "request_expiry"

    def due(self, uow: Any, now: datetime) -> list[DueItem]:
        window = timedelta(hours=float(uow.timers["request_response_window_hours"]))
        rows = uow.conn.execute(
            text(
                "SELECT t.id FROM borrowing_transaction t WHERE t.current_state = 'ASSESSED' "
                "AND (SELECT max(e.occurred_at) FROM lifecycle_event e WHERE e.stream_id = t.id "
                " AND e.event_type IN ('assessment_generated', 'hold_cleared', 'counter_offered')) "
                " + CAST(:w AS interval) < :now ORDER BY t.id"
            ),
            {"w": window, "now": now},
        ).scalars()
        return [DueItem(f"{t}:request_expired", {"txn": t}) for t in rows]

    def run(self, uow: Any, item: DueItem, now: datetime) -> None:
        txn = item.ref["txn"]
        hours = uow.timers["request_response_window_hours"]
        system_event(uow, txn, "request_expired", "EXPIRED", {"window_hours": hours})
        tell_parties(uow, txn, "request_expired", "request_expired", {})


class HandoverReminder:
    """I01: on the handover day (the start of the booked period), remind both parties once."""

    name = "handover_reminder"

    def due(self, uow: Any, now: datetime) -> list[DueItem]:
        rows = uow.conn.execute(
            text(
                "SELECT id FROM borrowing_transaction WHERE current_state = 'ACCEPTED' "
                "AND lower(requested_period) <= :now ORDER BY id"
            ),
            {"now": now},
        ).scalars()
        return [DueItem(f"{t}:handover_reminder", {"txn": t}) for t in rows]

    def run(self, uow: Any, item: DueItem, now: datetime) -> None:
        txn = item.ref["txn"]
        system_event(uow, txn, "reminder_sent", "ACCEPTED", {"kind": "handover"})
        tell_parties(uow, txn, "handover_reminder", "handover_reminder", {})


class ReturnReminder:
    """I02: reminder 1 `return_reminder_before_due_hours` before the due date, reminder 2 at it.

    The claim key carries the due date, so an approved extension starts a new pair of reminders."""

    name = "return_reminder"

    def due(self, uow: Any, now: datetime) -> list[DueItem]:
        before = timedelta(hours=float(uow.timers["return_reminder_before_due_hours"]))
        rows = uow.conn.execute(
            text(
                "SELECT id, due_at FROM borrowing_transaction WHERE current_state = 'ACTIVE' "
                "AND due_at IS NOT NULL AND due_at - CAST(:b AS interval) <= :now ORDER BY id"
            ),
            {"b": before, "now": now},
        ).all()
        items = []
        for r in rows:
            due = r.due_at.isoformat()
            ref = {"txn": r.id, "due": due}
            items.append(DueItem(f"{r.id}:return_reminder:{due}:1", {**ref, "n": 1}))
            if r.due_at <= now:
                items.append(DueItem(f"{r.id}:return_reminder:{due}:2", {**ref, "n": 2}))
        return items

    def run(self, uow: Any, item: DueItem, now: datetime) -> None:
        txn, n, due = item.ref["txn"], item.ref["n"], item.ref["due"]
        system_event(
            uow, txn, "reminder_sent", "ACTIVE", {"kind": "return_due", "n": n, "due": due}
        )
        view = uow.store.view(txn)
        title = uow.store.details(txn)["item_title"]
        payload = {"transaction_id": str(txn), "item_title": title, "due": due, "n": n}
        uow.notifier.notify(view.borrower_id, "return_reminder", payload, item.key)
        if n == 2:  # the due date has come: the lender is told too
            uow.notifier.notify(view.lender_id, "return_due_today", payload, item.key)


class OverdueEscalation:
    """T24 (sequence (e)): ACTIVE, `overdue_limit_hours` past the due date, and at least
    `min_reminders_before_escalation` return reminders sent for that due date: the system opens a
    NON_RETURN dispute (the only reason the database lets the system use) and the case is routed to
    the community's moderators, or to an admin when there are none."""

    name = "overdue_escalation"

    def due(self, uow: Any, now: datetime) -> list[DueItem]:
        limit = timedelta(hours=float(uow.timers["overdue_limit_hours"]))
        rows = uow.conn.execute(
            text(
                "SELECT t.id, t.due_at FROM borrowing_transaction t "
                "WHERE t.current_state = 'ACTIVE' AND t.due_at + CAST(:l AS interval) < :now "
                "AND (SELECT count(*) FROM lifecycle_event e WHERE e.stream_id = t.id "
                " AND e.event_type = 'reminder_sent' AND e.payload->>'kind' = 'return_due' "
                " AND (e.payload->>'due')::timestamptz = t.due_at) >= :m ORDER BY t.id"
            ),
            {"l": limit, "now": now, "m": int(uow.timers["min_reminders_before_escalation"])},
        ).all()
        return [DueItem(f"{r.id}:overdue:{r.due_at.isoformat()}", {"txn": r.id}) for r in rows]

    def run(self, uow: Any, item: DueItem, now: datetime) -> None:
        txn = item.ref["txn"]
        hours = uow.timers["overdue_limit_hours"]
        payload = {
            "reason": "NON_RETURN",
            "description": f"Not returned {hours} h after the due date",
        }
        system_event(uow, txn, "dispute_opened", "DISPUTED", payload)
        case = uow.store.open_case(txn)
        if case is not None:
            uow.cases.route_new_case(case["id"])


class ConfirmationReminder:
    """I06: RETURN_INITIATED and nobody has finished confirming after `confirmation_reminder_hours`."""

    name = "confirmation_reminder"

    def due(self, uow: Any, now: datetime) -> list[DueItem]:
        wait = timedelta(hours=float(uow.timers["confirmation_reminder_hours"]))
        rows = uow.conn.execute(
            text(
                "SELECT t.id FROM borrowing_transaction t WHERE t.current_state = 'RETURN_INITIATED' "
                "AND (SELECT max(e.occurred_at) FROM lifecycle_event e WHERE e.stream_id = t.id "
                " AND e.event_type = 'return_initiated') + CAST(:w AS interval) < :now ORDER BY t.id"
            ),
            {"w": wait, "now": now},
        ).scalars()
        return [DueItem(f"{t}:confirmation_reminder", {"txn": t}) for t in rows]

    def run(self, uow: Any, item: DueItem, now: datetime) -> None:
        txn = item.ref["txn"]
        system_event(uow, txn, "reminder_sent", "RETURN_INITIATED", {"kind": "confirm_return"})
        tell_parties(uow, txn, "confirm_return_reminder", "confirmation_reminder", {})
