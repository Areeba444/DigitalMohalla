"""Notifications (suite 22, plan item A2; ADR-0013, FR-C-02 in-app channel, part of FR-B-06).

Input, expected, actual: each test names the case it checks (TC-150 to TC-155). Dedupe holds in the
database; a member sees and marks only their own notifications; the lender is told once when a
request is assessed and the borrower is told the answer. All users are synthetic.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, text

from app.domain.notifications.notify import InvalidNotification
from app.infra.db.notifications import PostgresNotifier
from tests.integration.conftest import World
from tests.integration.test_api import client, dates, login  # noqa: F401 - shared fixture


def test_tc150_same_dedupe_key_notifies_once(conn: Connection, world: World) -> None:
    n = PostgresNotifier(conn)
    assert n.notify(world.borrower, "test_notice", {"k": 1}, "tc150:once") is True
    assert n.notify(world.borrower, "test_notice", {"k": 2}, "tc150:once") is False  # a rerun
    rows = conn.execute(
        text("SELECT payload FROM notification WHERE dedupe_key = 'tc150:once'")
    ).all()
    assert [r.payload for r in rows] == [{"k": 1}]  # the first one is kept, nothing overwritten


def test_tc151_same_key_for_another_member_is_a_separate_notice(
    conn: Connection, world: World
) -> None:
    n = PostgresNotifier(conn)
    assert n.notify_many([world.lender, world.moderator, world.lender], "t", {}, "tc151") == 2


@pytest.mark.parametrize("key", ["lat", "Longitude", "address", "location", "accuracy"])
def test_tc152_payload_with_location_is_refused(conn: Connection, world: World, key: str) -> None:
    with pytest.raises(InvalidNotification):
        PostgresNotifier(conn).notify(world.borrower, "t", {key: 1}, f"tc152:{key}")


def test_tc152_database_also_refuses_location_payload(conn: Connection, world: World) -> None:
    with pytest.raises(Exception, match="notification_payload_check|check constraint"):
        conn.execute(
            text(
                "INSERT INTO notification (user_id, type, payload, dedupe_key) "
                "VALUES (:u, 't', '{\"latitude\": 1}', 'tc152:db')"
            ),
            {"u": world.borrower},
        )


def test_tc153_member_reads_and_marks_only_their_own(conn: Connection, world: World) -> None:
    n = PostgresNotifier(conn)
    n.notify(world.borrower, "mine", {}, "tc153:b")
    n.notify(world.lender, "theirs", {}, "tc153:l")
    lender_id = conn.execute(
        text("SELECT id FROM notification WHERE dedupe_key = 'tc153:l'")
    ).scalar_one()
    assert [r["type"] for r in n.inbox(world.borrower, unread_only=True)] == ["mine"]
    assert n.mark_read(world.borrower, [lender_id]) == 0  # someone else's: nothing happens
    assert n.unread_count(world.lender) >= 1
    assert n.mark_read(world.borrower, None) == 1
    assert n.inbox(world.borrower, unread_only=True) == []


def test_tc155_mark_read_through_the_api(client: TestClient, world: World) -> None:  # noqa: F811
    lender = login(client, "lender@example.test")
    marked = client.post("/api/v1/notifications/read", json={}, headers=lender)
    assert marked.status_code == 200
    after = client.get("/api/v1/notifications?unread=true", headers=lender).json()
    assert after == {"unread_count": 0, "notifications": []}
    assert client.get("/api/v1/notifications").status_code == 401
    bad = client.post("/api/v1/notifications/read", json={"ids": ["x"]}, headers=lender)
    assert bad.status_code == 422
