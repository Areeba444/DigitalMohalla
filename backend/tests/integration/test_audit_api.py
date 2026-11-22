"""Audit log view on a real PostgreSQL (UC-I6 v1.4; FR-M-05, NFR-S-05; suite 29, TC-154 to TC-158).

The API tests commit a few synthetic audit rows (the audit log is append-only, so they stay; the
assertions only look at what each test itself wrote). The tamper test changes a row inside a
rolled-back connection. All data is synthetic.
"""

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, text

from app.config.settings import get_settings
from app.domain.accounts.auth import hash_password
from app.domain.audit.view import concentration
from app.infra.db import audit as store
from app.main import create_app
from tests.integration.conftest import World
from tests.integration.test_api import TEST_PASSWORD, login


@pytest.fixture
def client(engine: Engine, world: World, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    get_settings.cache_clear()
    with engine.begin() as c:
        for uid in (world.admin, world.moderator, world.borrower):
            c.execute(
                text("UPDATE app_user SET password_hash = :h WHERE id = :i"),
                {"h": hash_password(TEST_PASSWORD), "i": uid},
            )
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


def email_of(engine: Engine, uid: UUID) -> str:
    with engine.connect() as c:
        return str(c.execute(text("SELECT email FROM app_user WHERE id = :i"), {"i": uid}).scalar())


def seed_entry(engine: Engine, world: World, marker: str) -> None:
    with engine.begin() as c:
        c.execute(
            text(
                "INSERT INTO audit_log (actor_id, authorisation, action, target_type, target_id, "
                "new_value, outcome) VALUES (:a, 'role:admin', 'info_requested', 'escalation_case', "
                ":t, CAST(:v AS jsonb), 'SUCCESS')"
            ),
            {
                "a": world.moderator,
                "t": marker,
                "v": json.dumps({"question": "Ring me on 0300-1234567", "deadline": "2026-11-30"}),
            },
        )


def test_tc154_only_an_admin_reads_the_audit_log(
    client: TestClient, engine: Engine, world: World
) -> None:
    for who in (world.borrower, world.moderator):
        headers = login(client, email_of(engine, who))
        assert client.get("/api/v1/admin/audit", headers=headers).status_code == 403
    assert client.get("/api/v1/admin/audit").status_code == 401


def test_tc155_entries_are_masked_by_default_and_filters_narrow_the_list(
    client: TestClient, engine: Engine, world: World
) -> None:
    marker = "case-tc155"
    seed_entry(engine, world, marker)
    headers = login(client, email_of(engine, world.admin))
    page = client.get(
        "/api/v1/admin/audit", params={"target": marker, "result": "SUCCESS"}, headers=headers
    ).json()
    [entry] = page["entries"]
    assert entry["masked"] is True and entry["category"] == "DISPUTE"
    assert entry["new_value"]["question"] == "[masked]"  # free text is hidden
    assert entry["new_value"]["deadline"] == "2026-11-30"  # a date is not
    assert entry["actor"].startswith("usr_...") and str(world.moderator) not in json.dumps(page)
    assert entry["hash_valid"] is True and page["tampered"] == 0
    by_action = client.get(
        "/api/v1/admin/audit",
        params={"action": "info_requested", "target": marker},
        headers=headers,
    ).json()
    assert len(by_action["entries"]) == 1
    rejected = client.get(
        "/api/v1/admin/audit", params={"target": marker, "result": "REJECTED"}, headers=headers
    ).json()
    assert rejected["entries"] == []
    by_actor = client.get(
        "/api/v1/admin/audit",
        params={"actor": str(world.moderator), "target": marker},
        headers=headers,
    ).json()
    assert len(by_actor["entries"]) == 1


def test_tc155_the_view_itself_is_logged_with_its_filters(
    client: TestClient, engine: Engine, world: World
) -> None:
    headers = login(client, email_of(engine, world.admin))
    client.get("/api/v1/admin/audit", params={"target": "case-tc155b"}, headers=headers)
    with engine.connect() as c:
        row = c.execute(
            text(
                "SELECT new_value FROM audit_log WHERE action = 'audit_viewed' AND actor_id = :a "
                "ORDER BY id DESC LIMIT 1"
            ),
            {"a": world.admin},
        ).scalar_one()
    assert row["filters"] == {"target": "case-tc155b"}


def test_tc155_unmasking_needs_a_purpose_and_is_logged(
    client: TestClient, engine: Engine, world: World
) -> None:
    seed_entry(engine, world, "case-tc155c")
    headers = login(client, email_of(engine, world.admin))
    page = client.get(
        "/api/v1/admin/audit", params={"target": "case-tc155c"}, headers=headers
    ).json()
    entry = page["entries"][0]
    url = f"/api/v1/admin/audit/{entry['source']}/{entry['id']}/unmask"
    assert client.post(url, json={"purpose": "short"}, headers=headers).status_code == 422
    done = client.post(
        url, json={"purpose": "Checking a complaint about this request."}, headers=headers
    )
    assert done.status_code == 200 and done.json()["masked"] is False
    assert done.json()["new_value"]["question"].startswith("Ring me")
    with engine.connect() as c:
        logged = c.execute(
            text(
                "SELECT new_value FROM audit_log WHERE action = 'audit_unmasked' AND target_id = :t"
            ),
            {"t": f"{entry['source']}:{entry['id']}"},
        ).scalar_one()
    assert logged["purpose"].startswith("Checking a complaint")
    missing = client.post(
        "/api/v1/admin/audit/audit/999999999/unmask",
        json={"purpose": "Checking a complaint about this."},
        headers=headers,
    )
    assert missing.status_code == 404


def test_tc156_a_changed_entry_fails_its_hash_check_and_is_still_shown(
    conn: Connection, world: World
) -> None:
    conn.execute(
        text(
            "INSERT INTO audit_log (actor_id, authorisation, action, target_type, target_id, "
            "new_value, outcome) VALUES (:a, 'role:admin', 'decision_reversed', 'escalation_case', "
            "'case-tc156', CAST(:v AS jsonb), 'SUCCESS')"
        ),
        {"a": world.admin, "v": json.dumps({"kind": "REVERSAL"})},
    )
    flt = store.AuditFilter(target="case-tc156")
    [before] = store.search(conn, flt, 10, 0)
    assert before.hash_valid is True
    # test database only: switch audit_log's own triggers off, edit the row, switch them back on
    conn.execute(text("ALTER TABLE audit_log DISABLE TRIGGER USER"))
    conn.execute(
        text("UPDATE audit_log SET new_value = CAST(:v AS jsonb) WHERE target_id = 'case-tc156'"),
        {"v": json.dumps({"kind": "EDITED"})},
    )
    conn.execute(text("ALTER TABLE audit_log ENABLE TRIGGER USER"))
    [after] = store.search(conn, flt, 10, 0)  # still listed
    assert after.hash_valid is False


def test_tc158_the_concentration_query_runs_on_the_real_schema(conn: Connection) -> None:
    pairs = store.moderator_member_pairs(conn, datetime.now(UTC) - timedelta(days=90))
    assert isinstance(pairs, list)
    assert isinstance(concentration(pairs, 3, 0.6), list)
