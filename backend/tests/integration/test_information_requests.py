"""Information requests, party responses, deadlines and routing (plan item M2; sequence (g)).

FR-B-17, FR-T-10, FR-T-11; escalation-case transitions C02 to C04. Test ids TC-190 to TC-196,
input / expected / actual in each docstring. A real dispute is raised through the API on a
synthetic loan; the scheduler side (C04) is called directly with a later clock, as F4's runner will.
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, text

from app.config.settings import get_settings
from app.domain.accounts.auth import hash_password
from app.domain.moderation.cases import CaseService
from app.infra.db.cases import PostgresCaseStore
from app.infra.db.notifications import PostgresNotifier
from app.main import create_app
from tests.integration.conftest import World
from tests.integration.test_api import TEST_PASSWORD, dates, login


@pytest.fixture
def client(engine: Engine, world: World, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    get_settings.cache_clear()
    with engine.begin() as conn:
        for uid in (world.borrower, world.lender, world.borrower2, world.moderator, world.admin):
            conn.execute(
                text("UPDATE app_user SET password_hash = :h WHERE id = :i"),
                {"h": hash_password(TEST_PASSWORD), "i": uid},
            )
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


def disputed_case(client: TestClient, world: World, item: int, start: int) -> tuple[str, str]:
    """A loan accepted by the lender and disputed by the borrower: (transaction id, case id)."""
    borrower = login(client, "borrower@example.test")
    lender = login(client, "lender@example.test")
    created = client.post(
        "/api/v1/requests",
        json={"item_id": str(world.items[item]), **dates(start, 2)},
        headers=borrower,
    )
    assert created.status_code == 201, created.text
    txn = created.json()["transaction_id"]
    assert client.post(f"/api/v1/requests/{txn}/accept", headers=lender).status_code == 200
    raised = client.post(
        f"/api/v1/transactions/{txn}/dispute",
        json={"reason": "OTHER", "description": "Synthetic: handover time disagreement"},
        headers=borrower,
    )
    assert raised.status_code == 200, raised.text
    trail = client.get(f"/api/v1/transactions/{txn}/dispute", headers=borrower).json()
    return txn, trail["case"]["id"]


def notices(engine: Engine, user: object, type_: str, case_id: str) -> int:
    with engine.connect() as c:
        return int(
            c.execute(
                text(
                    "SELECT count(*) FROM notification WHERE user_id = :u AND type = :t "
                    "AND payload->>'case_id' = :c"
                ),
                {"u": user, "t": type_, "c": case_id},
            ).scalar_one()
        )


def test_tc190_new_dispute_reaches_the_moderator_and_the_other_party(
    client: TestClient, world: World, engine: Engine
) -> None:
    """Input: the borrower disputes an accepted loan. Expected: the community's moderator is told
    case_opened; the lender (the other party) is told dispute_opened; the raiser is not."""
    _, case_id = disputed_case(client, world, item=0, start=70)
    assert notices(engine, world.moderator, "case_opened", case_id) == 1
    assert notices(engine, world.lender, "dispute_opened", case_id) == 1
    assert notices(engine, world.borrower, "dispute_opened", case_id) == 0


def test_tc191_to_tc193_question_answer_and_trail(
    client: TestClient, world: World, engine: Engine
) -> None:
    """Input: the moderator asks the lender; the borrower then the lender answer. Expected: case
    AWAITING_INFORMATION with a 72 h deadline and only the lender told (TC-191); the borrower,
    not asked, gets 409 (TC-192); the lender's answer reopens the case and tells the moderator;
    both trails show the question and the answer (TC-193)."""
    txn, case_id = disputed_case(client, world, item=1, start=74)
    mod = login(client, "moderator@example.test")
    asked = client.post(
        f"/api/v1/moderation/cases/{case_id}/information-requests",
        json={"to": "LENDER", "question": "When did you offer the handover?"},
        headers=mod,
    )
    assert asked.status_code == 200, asked.text
    deadline = datetime.fromisoformat(asked.json()["deadline"])
    assert timedelta(hours=71) < deadline - datetime.now(UTC) <= timedelta(hours=72)
    assert notices(engine, world.lender, "information_requested", case_id) == 1
    assert notices(engine, world.borrower, "information_requested", case_id) == 0

    borrower, lender = login(client, "borrower@example.test"), login(client, "lender@example.test")
    url = f"/api/v1/cases/{case_id}/statements"
    assert client.post(url, json={"statement": "x"}, headers=borrower).status_code == 409
    answered = client.post(url, json={"statement": "Synthetic: Saturday 10am."}, headers=lender)
    assert answered.status_code == 201 and answered.json()["case_status"] == "OPEN"
    assert notices(engine, world.moderator, "information_received", case_id) == 1

    case = client.get(f"/api/v1/moderation/cases/{case_id}", headers=mod).json()
    assert case["case"]["status"] == "OPEN" and case["case"]["info_deadline"]
    assert case["information_request"]["question"] == "When did you offer the handover?"
    assert [(s["author_role"], s["statement"]) for s in case["statements"]] == [
        ("LENDER", "Synthetic: Saturday 10am.")
    ]
    party_view = client.get(f"/api/v1/transactions/{txn}/dispute", headers=borrower).json()
    assert party_view["statements"][0]["author_name"] == "Lender"
    assert "author_id" not in party_view["statements"][0]


def test_tc194_who_may_ask_and_when(client: TestClient, world: World, engine: Engine) -> None:
    """Input: a party asks; the moderator asks with no text; asks twice. Expected: 403; 422; 409
    for the second while the first is open. The party's attempt is audited as REJECTED."""
    _, case_id = disputed_case(client, world, item=2, start=78)
    url = f"/api/v1/moderation/cases/{case_id}/information-requests"
    party = client.post(
        url, json={"to": "BOTH", "question": "?"}, headers=login(client, "lender@example.test")
    )
    assert party.status_code == 403
    mod = login(client, "moderator@example.test")
    assert client.post(url, json={"to": "BOTH", "question": "  "}, headers=mod).status_code == 422
    assert (
        client.post(url, json={"to": "BOTH", "question": "Photos?"}, headers=mod).status_code == 200
    )
    assert (
        client.post(url, json={"to": "BOTH", "question": "Again?"}, headers=mod).status_code == 409
    )
    with engine.connect() as c:
        rejected = c.execute(
            text(
                "SELECT count(*) FROM audit_log WHERE target_id = :c "
                "AND action = 'reject_request_information'"
            ),
            {"c": case_id},
        ).scalar_one()
    assert rejected == 2  # the party, and the second request


def test_tc195_no_response_by_the_deadline_returns_the_case_to_the_moderator(
    client: TestClient, world: World, engine: Engine
) -> None:
    """Input: the moderator asks; nobody answers; the deadline job runs twice after the deadline.
    Expected: the case is OPEN again with the deadline kept, one info_deadline_passed audit entry
    and one notice; the second run finds nothing (C04, NFR-R-05). A late answer is refused."""
    _, case_id = disputed_case(client, world, item=3, start=82)
    mod = login(client, "moderator@example.test")
    client.post(
        f"/api/v1/moderation/cases/{case_id}/information-requests",
        json={"to": "BOTH", "question": "Any photos?"},
        headers=mod,
    )
    later = datetime.now(UTC) + timedelta(hours=73)

    def run() -> int:
        with engine.begin() as conn:
            svc = CaseService(
                PostgresCaseStore(conn),
                now=later,
                response_hours=72,
                notifier=PostgresNotifier(conn),
            )
            return svc.expire_information()

    assert run() >= 1
    assert run() == 0
    with engine.connect() as c:
        status, deadline = c.execute(
            text("SELECT status::text, info_deadline FROM escalation_case WHERE id = :c"),
            {"c": case_id},
        ).one()
        passed = c.execute(
            text(
                "SELECT count(*) FROM audit_log WHERE target_id = :c "
                "AND action = 'info_deadline_passed'"
            ),
            {"c": case_id},
        ).scalar_one()
    assert (status, deadline is not None, passed) == ("OPEN", True, 1)
    assert notices(engine, world.moderator, "information_deadline_passed", case_id) == 1
    late = client.post(
        f"/api/v1/cases/{case_id}/statements",
        json={"statement": "Sorry, late"},
        headers=login(client, "lender@example.test"),
    )
    assert late.status_code == 409


def test_tc196_case_without_a_moderator_goes_to_an_admin(
    conn: Connection, client: TestClient, world: World
) -> None:
    """Input: the community's moderator is no longer approved; a case is routed. Expected: the
    active admins are told instead (UC-D6 2a, FR-T-10). Rolled back afterwards."""
    _, case_id = disputed_case(client, world, item=4, start=86)
    conn.execute(
        text(
            "UPDATE membership SET status = 'REVOKED' WHERE community_id = :c "
            "AND role = 'MODERATOR'"  # every moderator, including any another suite added
        ),
        {"c": world.community},
    )
    svc = CaseService(
        PostgresCaseStore(conn),
        now=datetime.now(UTC),
        response_hours=72,
        notifier=PostgresNotifier(conn),
    )
    told = svc.route_new_case(case_id)  # type: ignore[arg-type]
    assert world.admin in told and world.moderator not in told
