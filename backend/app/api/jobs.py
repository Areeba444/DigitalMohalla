"""POST /internal/jobs/run: the scheduler's trigger (ADR-0012, FR-B-18; plan item F4).

Called every 15 minutes by the GitHub Actions workflow `scheduled-jobs.yml` with the job token; the
call also wakes the sleeping free-tier API. Returns what ran, what was skipped and what failed.
"""

import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import Engine

from app.api import schemas
from app.api.deps import get_engine
from app.config.engine_config import load_engine_config
from app.config.settings import get_settings
from app.domain.scheduler.runner import JobRunner, iter_counts
from app.infra.db.jobs import PostgresLedger, unit_of_work_factory
from app.infra.jobs import default_jobs

router = APIRouter(prefix="/api/v1")


def run_jobs(engine: Engine, now: datetime) -> schemas.JobReportOut:
    config = load_engine_config()
    runner = JobRunner(
        PostgresLedger(engine),
        unit_of_work_factory(engine, config, now),
        default_jobs(),
        max_attempts=int(config.section("scheduler_b13")["max_attempts"]),
    )
    report = runner.run_due_jobs(now)
    return schemas.JobReportOut(
        now=report.now,
        lock_acquired=report.lock_acquired,
        jobs=[
            schemas.JobCountsOut(
                job=name, ran=c.ran, skipped=c.skipped, failed=c.failed, errors=c.errors
            )
            for name, c in iter_counts(report)
        ],
    )


@router.post("/internal/jobs/run", response_model=schemas.JobReportOut)
def run_due_jobs(
    body: schemas.JobRunIn | None = None,
    authorization: str | None = Header(default=None),
    engine: Engine = Depends(get_engine),
) -> schemas.JobReportOut:
    settings = get_settings()
    if not settings.job_token:
        raise HTTPException(status_code=503, detail="scheduled jobs are not configured")
    sent = (authorization or "").removeprefix("Bearer ").strip()
    if not secrets.compare_digest(sent.encode(), settings.job_token.encode()):
        raise HTTPException(status_code=401, detail="job token required")
    now = datetime.now(UTC)
    if body is not None and body.as_of is not None:
        if not settings.demo_clock:
            raise HTTPException(status_code=403, detail="as_of is only allowed with DEMO_CLOCK on")
        now = body.as_of
    return run_jobs(engine, now)
