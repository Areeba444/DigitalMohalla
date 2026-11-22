"""Latency of transition commits and of the whole assessment path (F8; TC-61, NFR-P-03, NFR-P-04).

Reported, not gated (the test plan records P95 with the config version; target for transition commits
is 500 ms). It runs the real service against a scratch PostgreSQL loaded with the synthetic `mini`
dataset: 100 new requests (each commits locality check + engine assessment + events) and 100 accepts
(one transition commit each), one command per connection as the API does, one after another. The
numbers come from this machine and a local database, so they bound the code path, not the hosted
deployment. Results go to docs/design/14_testing/results/latency_<config>.json. All data synthetic.

Run:  cd backend && uv run pytest tests/performance -q -s
"""

from __future__ import annotations

import importlib.util
import json
import os
import platform
import statistics
import subprocess
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import Engine, create_engine, make_url, text

from app.config.engine_config import load_engine_config
from app.domain.assurance.engine import AssuranceEngine
from app.domain.lifecycle.service import Actor, BorrowingService
from app.infra.db.evidence import PostgresEvidenceSource
from app.infra.db.session import make_engine
from app.infra.eventstore.postgres import PostgresAuditLog, PostgresLifecycleStore

ROOT = Path(__file__).resolve().parents[3]
DB_NAME = "dm_latency_test"
CFG = load_engine_config()
N = 100


@pytest.fixture(scope="module")
def latency_db() -> Iterator[Engine]:
    base = os.environ.get("TEST_DATABASE_URL")
    if not base:
        pytest.skip("TEST_DATABASE_URL is not set")
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as c:
            c.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME} WITH (FORCE)"))
            c.execute(text(f"CREATE DATABASE {DB_NAME}"))
    except Exception as exc:
        pytest.skip(f"cannot create a scratch database: {exc}")
    eng = make_engine(make_url(base).set(database=DB_NAME).render_as_string(hide_password=False))
    spec = importlib.util.spec_from_file_location(
        "load_dataset", ROOT / "scripts" / "load_dataset.py"
    )
    assert spec and spec.loader
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    loader.reset_schema(eng)
    loader.load(eng, ROOT / "data" / "derived" / "mini")
    yield eng
    eng.dispose()
    with admin.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME} WITH (FORCE)"))
    admin.dispose()


def pairs(eng: Engine, n: int) -> list[tuple[UUID, UUID, UUID]]:
    """(borrower, lender, item): published items of other members in the borrower's community."""
    with eng.connect() as c:
        rows = c.execute(
            text(
                "SELECT DISTINCT ON (i.id) m.user_id, i.owner_id, i.id FROM item i "
                "JOIN membership m ON m.community_id = i.community_id AND m.status = 'APPROVED' "
                "JOIN app_user b ON b.id = m.user_id AND b.status = 'ACTIVE' "
                "WHERE i.status = 'PUBLISHED' AND m.user_id <> i.owner_id "
                "AND b.platform_role = 'MEMBER' AND i.required_verification = 'COMMUNITY_VERIFIED' "
                "ORDER BY i.id, m.user_id LIMIT :n"
            ),
            {"n": n},
        ).all()
    return [(r[0], r[1], r[2]) for r in rows]


def pct(xs: list[float], p: float) -> float:
    s = sorted(xs)
    return s[min(len(s) - 1, int(p * len(s)))]


def summary(ms: list[float]) -> dict[str, float | int]:
    return {
        "n": len(ms),
        "p50_ms": round(statistics.median(ms), 1),
        "p95_ms": round(pct(ms, 0.95), 1),
        "max_ms": round(max(ms), 1),
    }


def test_tc61_transition_and_assessment_latency_is_recorded(latency_db: Engine) -> None:
    eng = latency_db
    engine = AssuranceEngine(PostgresEvidenceSource(lambda: eng), CFG)
    chosen = pairs(eng, N)
    assert len(chosen) >= 20, "the mini dataset has too few eligible items for a latency run"

    def service(conn: object) -> BorrowingService:
        return BorrowingService(
            PostgresLifecycleStore(conn),  # type: ignore[arg-type]
            engine,
            PostgresAuditLog(eng),
            config_version=CFG.config_version,
        )

    start = datetime.now(UTC).replace(microsecond=0) + timedelta(days=120)
    created: list[tuple[UUID, UUID]] = []
    request_ms: list[float] = []
    refused = 0
    for i in range(N):  # eligible items are reused with later, non-overlapping dates
        borrower, lender, item = chosen[i % len(chosen)]
        day = start + timedelta(days=3 * i)
        period = f"[{day.isoformat()},{(day + timedelta(days=2)).isoformat()})"
        t0 = time.perf_counter()
        try:
            with eng.begin() as conn:
                result = service(conn).create_request(Actor(borrower), item, period, "synthetic")
        except Exception:
            refused += 1  # a rule refused this pair (reported, not hidden)
            continue
        request_ms.append((time.perf_counter() - t0) * 1000)
        if str(result.state) == "ASSESSED":
            created.append((lender, result.transaction_id))
    accept_ms: list[float] = []
    for lender, txn in created:
        t0 = time.perf_counter()
        with eng.begin() as conn:
            service(conn).accept(Actor(lender), txn)
        accept_ms.append((time.perf_counter() - t0) * 1000)
    assert request_ms and accept_ms

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
    except OSError:
        commit = "unknown"
    out = {
        "synthetic": True,
        "test_case": "TC-61 (NFR-P-04) and full assessment path (NFR-P-03)",
        "config_version": CFG.config_version,
        "commit": commit,
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "machine": f"{platform.system()} {platform.machine()}, Python {platform.python_version()}, local PostgreSQL",
        "create_request_including_assessment": summary(request_ms),
        "accept_one_transition": summary(accept_ms),
        "requests_refused_by_rules": refused,
        "target_transition_commit_p95_ms": 500,
        "note": "one command at a time on a local database; reported, not gated; not the hosted deployment",
    }
    results = ROOT / "docs" / "design" / "14_testing" / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / f"latency_{CFG.config_version}.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(out, indent=1))
