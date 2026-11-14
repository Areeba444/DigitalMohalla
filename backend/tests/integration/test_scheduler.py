"""Scheduler on PostgreSQL (suite 19; ADR-0012, FR-B-18, NFR-R-05; plan item F4).

A rerun and a parallel run change no state and send no duplicate notice; the endpoint is protected
by the job token and ignores `as_of` unless the demo clock is on. TC-205 to TC-211, input / expected /
actual in each docstring. Loans are synthetic; time is moved forward by passing `now` to the runner,
never by backdating events (events keep their database timestamps).
"""

import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.api.jobs import run_jobs
from app.config.settings import get_settings
from app.main import create_app
from tests.integration.conftest import World
from tests.integration.test_api import client, dates, login  # noqa: F401 - shared fixture


def accepted_loan(client: TestClient, world: World, item: int, start: int) -> str:  # noqa: F811
    borrower = login(client, "borrower@example.test")
    created = client.post(
        "/api/v1/requests",
        json={"item_id": str(world.items[item]), **dates(start, 2)},
        headers=borrower,
    )
    assert created.status_code == 201, created.text
    txn = created.json()["transaction_id"]
    accepted = client.post(
        f"/api/v1/requests/{txn}/accept", headers=login(client, "lender@example.test")
    )
    assert accepted.json()["state"] == "ACCEPTED"
    return str(txn)


def at_day(days: float) -> datetime:
    base = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(days=days)


def state(engine: Engine, txn: str) -> str:
    with engine.connect() as c:
        return str(
            c.execute(
                text("SELECT current_state::text FROM borrowing_transaction WHERE id = :t"),
                {"t": txn},
            ).scalar_one()
        )


def count(engine: Engine, sql: str, **kw: object) -> int:
    with engine.connect() as c:
        return int(c.execute(text(sql), kw).scalar_one())


def test_tc205_no_show_after_the_grace_period_and_a_rerun_changes_nothing(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: an ACCEPTED loan starting on day 90; jobs run at day 90 + 23 h, then + 25 h, then
    again. Expected: nothing before the 24 h grace; NO_SHOW once, booking released, both parties
    told once; the second run skips it (claimed)."""
    txn = accepted_loan(client, world, item=5, start=90)
    run_jobs(engine, at_day(90) + timedelta(hours=23))
    assert state(engine, txn) == "ACCEPTED"
    first = run_jobs(engine, at_day(90) + timedelta(hours=25))
    second = run_jobs(engine, at_day(90) + timedelta(hours=25))
    ran = {j.job: j for j in first.jobs}["no_show"]
    assert ran.ran >= 1 and ran.failed == 0
    assert {j.job: j for j in second.jobs}["no_show"].ran == 0
    assert state(engine, txn) == "NO_SHOW"
    assert (
        count(
            engine,
            "SELECT count(*) FROM lifecycle_event WHERE stream_id = :t AND event_type = 'no_show'",
            t=txn,
        )
        == 1
    )
    assert (
        count(
            engine,
            "SELECT count(*) FROM booking WHERE transaction_id = :t AND status = 'HELD'",
            t=txn,
        )
        == 0
    )
    assert (
        count(engine, "SELECT count(*) FROM notification WHERE dedupe_key = :k", k=f"{txn}:no_show")
        == 2
    )


def test_tc206_parallel_runs_do_the_work_once(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: four runs started at the same time after the grace period. Expected: one no_show
    event; at most one run holds the lock and the others report lock busy or skip."""
    txn = accepted_loan(client, world, item=6, start=94)
    later = at_day(94) + timedelta(hours=30)
    reports: list[object] = []
    threads = [
        threading.Thread(target=lambda: reports.append(run_jobs(engine, later))) for _ in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(reports) == 4
    assert (
        count(
            engine,
            "SELECT count(*) FROM lifecycle_event WHERE stream_id = :t AND event_type = 'no_show'",
            t=txn,
        )
        == 1
    )
    assert (
        count(
            engine,
            "SELECT count(*) FROM job_run WHERE job_name = 'no_show' AND due_key = :k",
            k=f"{UUID(txn)}:no_show",
        )
        == 1
    )


def test_tc207_listing_past_its_end_date_expires_once(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: a published listing ending tomorrow; jobs at day 2, twice. Expected: EXPIRED, the
    owner told once; the owner can publish it again."""
    h = login(client, "borrower@example.test")
    with engine.connect() as c:
        cat = c.execute(text("SELECT id FROM category WHERE name = 'Tools'")).scalar_one()
    item = client.post(
        "/api/v1/items",
        json={
            "community_id": str(world.community),
            "title": "Synthetic tent",
            "category_id": cat,
            "value_band": "LOW",
            "description": "Synthetic.",
            "condition": "GOOD",
            "publish": True,
            "expires_at": at_day(1).isoformat(),
        },
        headers=h,
    ).json()
    run_jobs(engine, at_day(2))
    run_jobs(engine, at_day(2))
    mine = {m["id"]: m for m in client.get("/api/v1/me/items", headers=h).json()}
    assert mine[item["id"]]["status"] == "EXPIRED"
    assert (
        count(
            engine,
            "SELECT count(*) FROM notification WHERE type = 'listing_expired' "
            "AND payload->>'item_id' = :i",
            i=item["id"],
        )
        == 1
    )
    again = client.patch(
        f"/api/v1/items/{item['id']}",
        json={"status": "PUBLISHED", "expires_at": at_day(30).isoformat()},
        headers=h,
    )
    assert again.json()["status"] == "PUBLISHED"


def test_tc208_work_out_of_attempts_is_not_retried(
    client: TestClient,  # noqa: F811
    world: World,
    engine: Engine,
) -> None:
    """Input: a due no-show whose claim already failed max_attempts (3) times. Expected: the run
    skips it and never retries again; the loan is unchanged; no claim is left RUNNING."""
    txn = accepted_loan(client, world, item=7, start=98)
    later = at_day(98) + timedelta(hours=30)
    with engine.begin() as c:  # a claim that already failed twice, as if earlier runs had failed
        c.execute(
            text(
                "INSERT INTO job_run (job_name, due_key, status, attempts, finished_at, error) "
                "VALUES ('no_show', :k, 'FAILED', 3, clock_timestamp(), 'earlier failure')"
            ),
            {"k": f"{UUID(txn)}:no_show"},
        )
    report = {j.job: j for j in run_jobs(engine, later).jobs}["no_show"]
    assert report.skipped >= 1  # out of attempts (max_attempts 3): skipped, never re-run
    assert state(engine, txn) == "ACCEPTED"
    assert count(engine, "SELECT count(*) FROM job_run WHERE status = 'RUNNING'") == 0


@pytest.fixture
def jobs_client(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("JOB_TOKEN", "test-only-job-token")
    get_settings.cache_clear()
    yield TestClient(create_app(engine=engine))
    get_settings.cache_clear()


def test_tc209_endpoint_needs_the_job_token(jobs_client: TestClient) -> None:
    """Expected: 401 without or with a wrong token; 200 with it, and a report per job."""
    url = "/api/v1/internal/jobs/run"
    assert jobs_client.post(url).status_code == 401
    assert jobs_client.post(url, headers={"Authorization": "Bearer nope"}).status_code == 401
    ok = jobs_client.post(url, headers={"Authorization": "Bearer test-only-job-token"})
    assert ok.status_code == 200, ok.text
    assert {j["job"] for j in ok.json()["jobs"]} >= {"no_show", "listing_expiry"}


def test_tc210_as_of_needs_the_demo_clock(
    jobs_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Expected: 403 for as_of in normal running; accepted with DEMO_CLOCK on."""
    url, h = "/api/v1/internal/jobs/run", {"Authorization": "Bearer test-only-job-token"}
    later = at_day(400).isoformat()
    assert jobs_client.post(url, json={"as_of": later}, headers=h).status_code == 403
    monkeypatch.setenv("DEMO_CLOCK", "true")
    get_settings.cache_clear()
    ok = jobs_client.post(url, json={"as_of": later}, headers=h)
    assert ok.status_code == 200 and ok.json()["now"].startswith(later[:10])


def test_tc211_unconfigured_endpoint_answers_503(engine: Engine) -> None:
    get_settings.cache_clear()
    assert (
        TestClient(create_app(engine=engine)).post("/api/v1/internal/jobs/run").status_code == 503
    )
