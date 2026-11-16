"""Scheduled jobs outside the lifecycle: case information deadlines (C04) and listing expiry."""

from datetime import datetime
from typing import Any

from sqlalchemy import text

from app.domain.scheduler.runner import DueItem


class InformationDeadline:
    """C04 (sequence (g)): a case whose information deadline passed goes back to the moderator.

    The work is CaseService.expire_information (plan item M2); the claim key includes the deadline,
    so a later information request on the same case is a new unit of work."""

    name = "information_deadline"

    def due(self, uow: Any, now: datetime) -> list[DueItem]:
        rows = uow.conn.execute(
            text(
                "SELECT id, info_deadline FROM escalation_case "
                "WHERE status = 'AWAITING_INFORMATION' AND info_deadline <= :now ORDER BY id"
            ),
            {"now": now},
        ).all()
        return [DueItem(f"{r.id}:{r.info_deadline.isoformat()}", {"case": r.id}) for r in rows]

    def run(self, uow: Any, item: DueItem, now: datetime) -> None:
        uow.cases.now = now
        uow.cases.expire_information(case_id=item.ref["case"])


class ListingExpiry:
    """A published listing past its end date becomes EXPIRED and its owner is told (FR-B-01).

    Publishing sets the end date (`listing_default_expiry_days` ahead when the lender gives none,
    F9), so this job reads only `expires_at` (index item_expiry_ix). Iteration 1 seed listings have
    no end date and never expire by themselves. The owner can publish again (EXPIRED -> PUBLISHED)."""

    name = "listing_expiry"

    def due(self, uow: Any, now: datetime) -> list[DueItem]:
        rows = uow.conn.execute(
            text(
                "SELECT id, expires_at FROM item WHERE status = 'PUBLISHED' "
                "AND expires_at IS NOT NULL AND expires_at <= :now ORDER BY id"
            ),
            {"now": now},
        ).all()
        return [DueItem(f"{r.id}:{r.expires_at.isoformat()}", {"item": r.id}) for r in rows]

    def run(self, uow: Any, item: DueItem, now: datetime) -> None:
        row = uow.conn.execute(
            text(
                "UPDATE item SET status = 'EXPIRED', updated_at = now() "
                "WHERE id = :i AND status = 'PUBLISHED' RETURNING owner_id, title"
            ),
            {"i": item.ref["item"]},
        ).first()
        if row is None:
            raise RuntimeError("listing is no longer published")
        uow.notifier.notify(
            row.owner_id,
            "listing_expired",
            {"item_id": str(item.ref["item"]), "item_title": row.title},
            f"{item.key}:listing_expired",
        )
