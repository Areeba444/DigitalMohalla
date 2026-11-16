"""Appeal and reversal (suite 26; plan item M3; FR-T-11, UC-I4 ext 4b, 4c; ES-11 workflow).

The second moderator differs from the first; both decisions are kept; an overturned or reversed
dispute decision flags its outcomes, which then stop counting, so the next assessment changes.
TC-250 to TC-256, input / expected / actual in each docstring. Synthetic loans on PostgreSQL; a
second moderator is added to the test community for these tests.
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.config.settings import get_settings
from app.domain.accounts.auth import hash_password
from app.domain.lifecycle.errors import InvalidTransition
from app.domain.moderation.appeals import AppealService
from app.infra.db.appeals import PostgresAppealStore
from app.main import create_app
from tests.integration.conftest import World
from tests.integration.test_api import TEST_PASSWORD, dates, login


@pytest.fixture
def client(engine: Engine, world: World, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
    get_settings.cache_clear()
    with engine.begin() as c:
        for uid in (world.borrower, world.lender, world.borrower2, world.moderator, world.admin):
            c.execute(
                text("UPDATE app_user SET password_hash = :h WHERE id = :i"),
                {"h": hash_password(TEST_PASSWORD), "i": uid},
            )
        exists = c.execute(
            text("SELECT 1 FROM app_user WHERE email = 'moderator2@example.test'")
        ).first()
        if not exists:
            m2 = c.execute(
                text(
                    "INSERT INTO app_user (display_name, email, password_hash, verification_level, "
                    "status, is_synthetic) VALUES ('Moderator2', 'moderator2@example.test', :h, "
                    "'COMMUNITY_VERIFIED', 'ACTIVE', true) RETURNING id"
                ),
                {"h": hash_password(TEST_PASSWORD)},
            ).scalar_one()
            c.execute(
                text(
                    "INSERT INTO membership (user_id, community_id, role, status, decided_at) "
                    "VALUES (:u, :c, 'MODERATOR', 'APPROVED', now())"
                ),
                {"u": m2, "c": world.community},
            )
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


def decided_dispute(
    client: TestClient, world: World, item: int, start: int, after_return: bool = False
) -> tuple[str, str, str]:
    """An ACTIVE (with after_return, RETURN_INITIATED) loan disputed by the lender and resolved by Moderator as RETURNED, borrower at
    fault: (transaction id, case id, decision id). The decision writes the borrower's outcomes."""
    b, lender = login(client, "borrower@example.test"), login(client, "lender@example.test")
    txn = client.post(
        "/api/v1/requests", json={"item_id": str(world.items[item]), **dates(start, 1)}, headers=b
    ).json()["transaction_id"]
    client.post(f"/api/v1/requests/{txn}/accept", headers=lender)
    client.post(
        f"/api/v1/transactions/{txn}/handover/checklist", json={"checklist": {}}, headers=lender
    )
    client.post(f"/api/v1/transactions/{txn}/handover/confirm", json={}, headers=b)
    if after_return:  # a dispute from RETURN_INITIATED also writes ON_TIME_RETURN (ES-11)
        client.post(f"/api/v1/transactions/{txn}/return", headers=b)
    raised = client.post(
        f"/api/v1/transactions/{txn}/dispute",
        json={"reason": "DAMAGE", "description": "Synthetic: returned scratched"},
        headers=lender,
    )
    assert raised.json()["state"] == "DISPUTED", raised.text
    mod = login(client, "moderator@example.test")
    case_id = client.get(f"/api/v1/transactions/{txn}/dispute", headers=b).json()["case"]["id"]
    decided = client.post(
        f"/api/v1/moderation/cases/{case_id}/decision",
        json={
            "kind": "DISPUTE_RESOLVED",
            "reason": "Photos show damage",
            "at_fault": "borrower",
            "possession": "RETURNED",
        },
        headers=mod,
    )
    assert decided.json()["state"] == "COMPLETED", decided.text
    case = client.get(f"/api/v1/moderation/cases/{case_id}", headers=mod).json()
    return str(txn), str(case_id), case["decisions"][-1]["id"]


def outcome_status(engine: Engine, txn: str) -> list[str]:
    with engine.connect() as c:
        return list(
            c.execute(
                text("SELECT status::text FROM outcome WHERE transaction_id = :t ORDER BY metric"),
                {"t": txn},
            ).scalars()
        )


def test_tc250_party_appeals_and_a_second_moderator_upholds(
    client: TestClient, world: World, engine: Engine
) -> None:
    """Input: the borrower appeals; the first moderator tries to decide it; Moderator2 upholds.
    Expected: APPEALED and Moderator2 told; 403 for the first decider; DECIDED with both decisions
    kept and the outcomes still VALID (C08, C09)."""
    txn, case_id, _ = decided_dispute(client, world, item=0, start=300)
    b = login(client, "borrower@example.test")
    filed = client.post(
        f"/api/v1/cases/{case_id}/appeal", json={"reason": "Scratch was there before"}, headers=b
    )
    assert filed.status_code == 202 and filed.json()["status"] == "APPEALED", filed.text
    url = f"/api/v1/moderation/cases/{case_id}/appeal-decision"
    body = {"result": "UPHELD", "reason": "Handover photos show no scratch"}
    assert (
        client.post(url, json=body, headers=login(client, "moderator@example.test")).status_code
        == 403
    )
    ok = client.post(url, json=body, headers=login(client, "moderator2@example.test"))
    assert ok.status_code == 200 and ok.json()["status"] == "DECIDED", ok.text
    case = client.get(
        f"/api/v1/moderation/cases/{case_id}", headers=login(client, "moderator2@example.test")
    ).json()
    assert [d["kind"] for d in case["decisions"]] == ["DISPUTE_RESOLVED", "APPEAL_UPHELD"]
    assert set(outcome_status(engine, txn)) == {"VALID"}


def test_tc251_overturned_appeal_flags_the_outcomes(
    client: TestClient, world: World, engine: Engine
) -> None:
    """Input: appeal, Moderator2 overturns. Expected: REVERSED; APPEAL_OVERTURNED references the
    first decision; the decision's outcomes are FLAGGED_FOR_REEVALUATION by it; loan not rewound
    (still COMPLETED); both parties told (C10)."""
    txn, case_id, first = decided_dispute(client, world, item=1, start=305)
    client.post(
        f"/api/v1/cases/{case_id}/appeal",
        json={"reason": "Wrong party"},
        headers=login(client, "borrower@example.test"),
    )
    ok = client.post(
        f"/api/v1/moderation/cases/{case_id}/appeal-decision",
        json={"result": "OVERTURNED", "reason": "Damage predates the loan"},
        headers=login(client, "moderator2@example.test"),
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "REVERSED" and ok.json()["flagged_outcomes"] >= 1
    statuses = outcome_status(engine, txn)
    assert statuses and set(statuses) == {"FLAGGED_FOR_REEVALUATION"}
    with engine.connect() as c:
        reverses, state, flagged_by = c.execute(
            text(
                "SELECT d.reverses_decision_id::text, t.current_state::text, "
                "(SELECT DISTINCT o.flagged_by_decision_id::text FROM outcome o WHERE o.transaction_id = t.id) "
                "FROM moderator_decision d JOIN escalation_case ec ON ec.id = d.case_id "
                "JOIN borrowing_transaction t ON t.id = ec.transaction_id "
                "WHERE d.case_id = :c AND d.kind = 'APPEAL_OVERTURNED'"
            ),
            {"c": case_id},
        ).one()
        told = c.execute(
            text(
                "SELECT count(*) FROM notification WHERE type = 'appeal_overturned' AND payload->>'case_id' = :c"
            ),
            {"c": case_id},
        ).scalar_one()
    assert (reverses, state, told) == (first, "COMPLETED", 2)
    assert flagged_by == str(ok.json()["decision_id"])


def test_tc252_one_appeal_per_case_by_a_party_only(
    client: TestClient, world: World, engine: Engine
) -> None:
    """Expected: a stranger gets 403; an empty reason 422; after an appeal is upheld, a second
    appeal is 409 (one per case)."""
    _, case_id, _ = decided_dispute(client, world, item=2, start=310)
    url = f"/api/v1/cases/{case_id}/appeal"
    assert (
        client.post(
            url, json={"reason": "x"}, headers=login(client, "borrower2@example.test")
        ).status_code
        == 403
    )
    lender = login(client, "lender@example.test")
    assert client.post(url, json={"reason": "  "}, headers=lender).status_code == 422
    assert client.post(url, json={"reason": "Too lenient"}, headers=lender).status_code == 202
    client.post(
        f"/api/v1/moderation/cases/{case_id}/appeal-decision",
        json={"result": "UPHELD", "reason": "Stands"},
        headers=login(client, "moderator2@example.test"),
    )
    assert client.post(url, json={"reason": "Again"}, headers=lender).status_code == 409


def test_tc253_appeal_window_closes(engine: Engine, client: TestClient, world: World) -> None:
    """Input: an appeal 8 days after the decision. Expected: refused (7-day window, C08 guard)."""
    _, case_id, _ = decided_dispute(client, world, item=3, start=315)
    with engine.connect() as conn:
        svc = AppealService(
            PostgresAppealStore(conn),
            now=datetime.now(UTC) + timedelta(days=8),
            appeal_window_days=7,
        )
        with pytest.raises(InvalidTransition, match="window"):
            svc.file_appeal(world.borrower, case_id, "late")  # type: ignore[arg-type]
        conn.rollback()


def test_tc254_es11_reversal_flags_outcomes_and_the_next_assessment_changes(
    client: TestClient, world: World, engine: Engine
) -> None:
    """ES-11 workflow. Input: a decided dispute; the admin reverses the decision. Expected: case
    REVERSED, both decisions kept (REVERSAL references the first), outcomes flagged, and the
    borrower's next assessment counts fewer verified loans than before."""
    txn, case_id, first = decided_dispute(client, world, item=4, start=320, after_return=True)
    b = login(client, "borrower@example.test")

    def verified_loans() -> int:
        r = client.post(
            "/api/v1/requests", json={"item_id": str(world.items[5]), **dates(330, 1)}, headers=b
        ).json()
        seen = client.get(
            f"/api/v1/requests/{r['transaction_id']}", headers=login(client, "lender@example.test")
        ).json()
        client.post(f"/api/v1/requests/{r['transaction_id']}/cancel", headers=b)
        return int(seen["assessment"]["verified_loans"])

    before = verified_loans()
    rev = client.post(
        f"/api/v1/moderation/decisions/{first}/reversal",
        json={"reason": "New evidence: the damage was pre-existing"},
        headers=login(client, "admin@example.test"),
    )
    assert rev.status_code == 200 and rev.json()["status"] == "REVERSED", rev.text
    assert set(outcome_status(engine, txn)) == {"FLAGGED_FOR_REEVALUATION"}
    with engine.connect() as c:
        kinds = (
            c.execute(
                text(
                    "SELECT kind::text FROM moderator_decision WHERE case_id = :c ORDER BY decided_at"
                ),
                {"c": case_id},
            )
            .scalars()
            .all()
        )
    assert kinds == ["DISPUTE_RESOLVED", "REVERSAL"]
    assert verified_loans() == before - 1


def test_tc255_reversal_needs_the_latest_decision_of_a_decided_case(
    client: TestClient, world: World
) -> None:
    """Expected: a party cannot reverse (403); a reason is required (422); reversing twice is 409."""
    _, _, first = decided_dispute(client, world, item=6, start=335)
    url = f"/api/v1/moderation/decisions/{first}/reversal"
    assert (
        client.post(
            url, json={"reason": "x"}, headers=login(client, "lender@example.test")
        ).status_code
        == 403
    )
    mod = login(client, "moderator@example.test")
    assert client.post(url, json={"reason": " "}, headers=mod).status_code == 422
    assert client.post(url, json={"reason": "Mistake"}, headers=mod).status_code == 200
    assert client.post(url, json={"reason": "Again"}, headers=mod).status_code == 409
