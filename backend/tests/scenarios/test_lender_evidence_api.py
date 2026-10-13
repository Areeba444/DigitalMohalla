"""TC-100 (API side): what the lender's screen receives for ES-01, ES-02 and ES-13.

On the synthetic `mini` database, each case's borrower logs in and sends a request through the REST
API for the case's item, and the lender reads it back. The engine's clock is fixed at the dataset's
reference time, so the numbers are deterministic. The responses are checked here and compared with
frontend/__tests__/fixtures/lender-requests.json, which the screen tests render, so the UI tests
always use what the API really returns. After an intended API or engine change, regenerate it:

    UPDATE_UI_FIXTURES=1 uv run pytest tests/scenarios/test_lender_evidence_api.py

All data is SYNTHETIC; the test passwords are throwaway values for the scratch database only.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.config.settings import get_settings
from app.domain.accounts.auth import hash_password
from app.domain.assurance.engine import AssuranceEngine
from app.infra.db.evidence import PostgresEvidenceSource
from app.main import create_app
from tests.scenarios.conftest import CFG, ROOT, manifest

FIXTURE_FILE = ROOT / "frontend" / "__tests__" / "fixtures" / "lender-requests.json"
REF = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)  # the generator's reference date
TEST_PASSWORD = "synthetic-test-password"  # noqa: S105 - scratch database only
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
CASES = ("ES-01", "ES-02", "ES-13")


@pytest.fixture(scope="module")
def client(mini_db: Engine) -> Iterator[TestClient]:
    os.environ["JWT_SECRET"] = "test-only-secret-not-for-production-0123456789"
    get_settings.cache_clear()
    with mini_db.begin() as c:
        c.execute(
            text("UPDATE app_user SET password_hash = :h"), {"h": hash_password(TEST_PASSWORD)}
        )
    engine = AssuranceEngine(PostgresEvidenceSource(lambda: mini_db), CFG, clock=lambda: REF)
    yield TestClient(create_app(engine=mini_db, assess=engine))
    os.environ.pop("JWT_SECRET", None)
    get_settings.cache_clear()


def login(client: TestClient, mini_db: Engine, user_id: str) -> dict[str, str]:
    with mini_db.connect() as c:
        email = c.execute(text("SELECT email FROM app_user WHERE id = :u"), {"u": user_id}).scalar()
    r = client.post("/api/v1/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def lender_view(client: TestClient, mini_db: Engine, case: dict[str, str]) -> dict[str, Any]:
    with mini_db.connect() as c:
        days = c.execute(
            text(
                "SELECT (upper(requested_period)::date - lower(requested_period)::date) "
                "FROM borrowing_transaction WHERE id = :t"
            ),
            {"t": case["transaction_id"]},
        ).scalar_one()
    start = date.today() + timedelta(days=200)
    created = client.post(
        "/api/v1/requests",
        json={
            "item_id": case["item_id"],
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=days)).isoformat(),
            "message": "Synthetic request for the evidence screen test.",
        },
        headers=login(client, mini_db, case["borrower_id"]),
    )
    assert created.status_code == 201, created.text
    txn = created.json()["transaction_id"]
    r = client.get(f"/api/v1/requests/{txn}", headers=login(client, mini_db, case["lender_id"]))
    assert r.status_code == 200, r.text
    body: dict[str, Any] = r.json()
    assert body["your_role"] == "LENDER"
    return body


def normalised(body: dict[str, Any], case_id: str) -> dict[str, Any]:
    """Stable copy for the UI fixtures: ids and dates replaced, the rest as the API returned it."""
    out = {**body, "transaction_id": f"txn-{case_id}", "item_id": f"item-{case_id}"}
    out["requested_period"] = '["2026-10-23 00:00:00+00","2026-10-26 00:00:00+00")'
    return out


@pytest.fixture(scope="module")
def responses(client: TestClient, mini_db: Engine) -> dict[str, dict[str, Any]]:
    cases = manifest()
    return {cid: lender_view(client, mini_db, cases[cid]) for cid in CASES}


def test_es01_newcomer_gets_the_prior_interval_and_no_paths(responses: dict) -> None:
    a = responses["ES-01"]["assessment"]
    assert a["assurance_state"] == "INSUFFICIENT_EVIDENCE"
    assert (a["ci90_low"], a["ci90_high"]) == (0.05, 0.95)  # TC-100: the API's bounds
    assert a["verified_loans"] == 0
    assert a["community"]["paths"] == []


def test_es02_reliable_borrower_gets_loans_interval_and_safeguard(responses: dict) -> None:
    a = responses["ES-02"]["assessment"]
    assert a["assurance_state"] == "SUFFICIENT_EVIDENCE"
    assert a["verified_loans"] == 10
    assert 0.6 <= a["ci90_low"] < a["posterior_mean"] < a["ci90_high"] <= 1
    assert [s["code"] for s in a["safeguards"]] == ["STANDARD_RETURN_REMINDER"]


def test_es13_paths_are_named_and_carry_no_user_ids(responses: dict) -> None:
    body = responses["ES-13"]
    a = body["assessment"]
    assert a["assurance_state"] == "REVIEW_RECOMMENDED" and a["rule_fired"] == "R9"
    paths = a["community"]["paths"]
    assert len(paths) == 2 and all(len(p["via"]) == 1 for p in paths)
    assert a["community"]["reliability"] >= 0.3
    for p in paths:
        assert p["via"][0] in a["explanation"]  # the names the explanation uses
    # the only ids in the response are the request's own and the item's
    own = {body["transaction_id"], body["item_id"]}
    assert set(UUID_RE.findall(json.dumps(body))) <= own


def test_ui_fixtures_match_the_api(responses: dict) -> None:
    current = {cid: normalised(responses[cid], cid) for cid in CASES}
    if os.environ.get("UPDATE_UI_FIXTURES"):
        FIXTURE_FILE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE_FILE.write_text(
            json.dumps({"synthetic": True, "cases": current}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    saved = json.loads(Path(FIXTURE_FILE).read_text(encoding="utf-8"))
    assert saved["cases"] == current, "API changed: regenerate with UPDATE_UI_FIXTURES=1"
