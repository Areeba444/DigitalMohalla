"""Notification inbox endpoints (G3, FR-C-02 in-app channel, ADR-0013; plan item A2).

The app polls `GET /notifications?unread=true` while it is open. A member only ever sees and marks
their own notifications.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Engine

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.domain.lifecycle.service import Actor
from app.infra.db.notifications import PostgresNotifier

router = APIRouter(prefix="/api/v1")


@router.get("/notifications", response_model=schemas.InboxOut)
def inbox(
    unread: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.InboxOut:
    with engine.connect() as conn:
        notifier = PostgresNotifier(conn)
        rows = notifier.inbox(actor.user_id, unread_only=unread, limit=limit)
        return schemas.InboxOut(
            unread_count=notifier.unread_count(actor.user_id),
            notifications=[schemas.NotificationOut(**r) for r in rows],
        )


@router.post("/notifications/read", response_model=schemas.MarkReadOut)
def mark_read(
    body: schemas.MarkReadIn | None = None,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.MarkReadOut:
    with engine.begin() as conn:
        marked = PostgresNotifier(conn).mark_read(actor.user_id, body.ids if body else None)
    return schemas.MarkReadOut(marked=marked)
