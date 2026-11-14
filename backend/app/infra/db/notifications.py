"""PostgreSQL adapter for in-app notifications (Module 7, ADR-0013, plan item A2).

`PostgresNotifier` works on the caller's open connection, so a notification is written in the
same transaction as the command that caused it: if the command rolls back, nobody is told.
"""

import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, text

from app.domain.notifications.notify import check


class PostgresNotifier:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def notify(
        self, user_id: UUID, type_: str, payload: Mapping[str, Any], dedupe_key: str
    ) -> bool:
        check(type_, payload, dedupe_key)
        row = self.conn.execute(
            text(
                "INSERT INTO notification (user_id, type, payload, dedupe_key) "
                "VALUES (:u, :t, CAST(:p AS jsonb), :k) "
                "ON CONFLICT ON CONSTRAINT notification_once_uq DO NOTHING RETURNING id"
            ),
            {
                "u": user_id,
                "t": type_,
                "p": json.dumps(dict(payload), default=str),
                "k": dedupe_key,
            },
        ).first()
        return row is not None

    def notify_many(
        self, user_ids: list[UUID], type_: str, payload: Mapping[str, Any], dedupe_key: str
    ) -> int:
        """The same notification to several people (e.g. a community's moderators)."""
        return sum(self.notify(u, type_, payload, dedupe_key) for u in dict.fromkeys(user_ids))

    def inbox(self, user_id: UUID, *, unread_only: bool, limit: int = 50) -> list[dict[str, Any]]:
        """The member's own notifications, newest first. Nobody can read another member's."""
        rows = self.conn.execute(
            text(
                "SELECT id, type, payload, created_at, read_at FROM notification "
                "WHERE user_id = :u AND (NOT :unread OR read_at IS NULL) "
                "ORDER BY created_at DESC, id LIMIT :n"
            ),
            {"u": user_id, "unread": unread_only, "n": limit},
        ).mappings()
        return [dict(r) for r in rows]

    def unread_count(self, user_id: UUID) -> int:
        return int(
            self.conn.execute(
                text("SELECT count(*) FROM notification WHERE user_id = :u AND read_at IS NULL"),
                {"u": user_id},
            ).scalar_one()
        )

    def mark_read(self, user_id: UUID, ids: list[UUID] | None) -> int:
        """Mark the given notifications (or all, when ids is None) read; only the member's own."""
        rows = self.conn.execute(
            text(
                "UPDATE notification SET read_at = clock_timestamp() "
                "WHERE user_id = :u AND read_at IS NULL "
                "AND (CAST(:all AS boolean) OR id = ANY(CAST(:ids AS uuid[]))) RETURNING id"
            ),
            {"u": user_id, "all": ids is None, "ids": [str(i) for i in ids or []]},
        ).all()
        return len(rows)

    def moderators_of(self, community_id: UUID) -> list[UUID]:
        """Approved moderators of a community: who hears about its queue."""
        rows = self.conn.execute(
            text(
                "SELECT user_id FROM membership WHERE community_id = :c AND role = 'MODERATOR' "
                "AND status = 'APPROVED' ORDER BY user_id"
            ),
            {"c": community_id},
        ).scalars()
        return list(rows)
