"""JobRunner: `run_due_jobs(now)` for the scheduled work of FR-B-18 (ADR-0012, plan item F4).

The free API sleeps, so nothing runs on an in-process timer. A token-protected endpoint calls this
runner (a GitHub Actions cron every 15 minutes, sequence (e)). One run:

1. takes a session advisory lock; if another run holds it, this run does nothing ("lock busy");
2. asks every job what is due at `now` (jobs act on what is due, so a late trigger only delays them);
3. for each due item, in its own DB transaction, *claims* it by inserting `(job_name, due_key)` into
   `job_run`. The unique constraint makes the claim a database fact: a rerun or a parallel run finds
   the row and skips the item (NFR-R-05). A FAILED claim is retried on a later run, up to
   `max_attempts`;
4. runs the item's work inside a savepoint. Success marks the claim SUCCEEDED; an error rolls the
   work back and marks the claim FAILED in the same transaction, so a claim is never left RUNNING,
   and the run goes on with the next item.

Notifications sent by a job are written in the same transaction as its work and carry their own
dedupe keys, so a retried or repeated job never tells anyone twice.

Plain-language note: "idempotent" means running the jobs twice has the same effect as running them
once. Here that holds because every unit of work has a name (its due key) that can be used once.
"""

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class DueItem:
    """One unit of due work. `key` names it for the claim; `ref` is what the job needs to act."""

    key: str
    ref: dict[str, Any]


@dataclass
class JobCounts:
    ran: int = 0
    skipped: int = 0  # claimed by an earlier run (or a failed claim out of attempts)
    failed: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class JobReport:
    """What one run did, per job (returned by POST /internal/jobs/run)."""

    now: datetime
    lock_acquired: bool
    jobs: dict[str, JobCounts] = field(default_factory=dict)

    @property
    def total_ran(self) -> int:
        return sum(c.ran for c in self.jobs.values())


class UnitOfWork(Protocol):
    """One DB transaction with the services a job needs (store, notifier, case service, ...)."""

    def claim(self, job_name: str, due_key: str, max_attempts: int) -> bool: ...

    def succeed(self, job_name: str, due_key: str) -> None: ...

    def fail(self, job_name: str, due_key: str, error: str) -> None: ...

    def savepoint(self) -> AbstractContextManager[Any]: ...


class Job(Protocol):
    name: str

    def due(self, uow: Any, now: datetime) -> list[DueItem]: ...

    def run(self, uow: Any, item: DueItem, now: datetime) -> None: ...


class Ledger(Protocol):
    """Run-level concerns outside any one unit of work."""

    def lock(self) -> AbstractContextManager[bool]:
        """Yields True if this run holds the advisory lock, False if another run does."""
        ...


class JobRunner:
    def __init__(
        self,
        ledger: Ledger,
        unit_of_work: Callable[[], AbstractContextManager[Any]],
        jobs: list[Job],
        *,
        max_attempts: int,
    ) -> None:
        self.ledger = ledger
        self.unit_of_work = unit_of_work
        self.jobs = jobs
        self.max_attempts = max_attempts

    def run_due_jobs(self, now: datetime) -> JobReport:
        with self.ledger.lock() as acquired:
            report = JobReport(now=now, lock_acquired=acquired)
            if not acquired:
                return report
            for job in self.jobs:
                report.jobs[job.name] = self._run_job(job, now)
            return report

    def _run_job(self, job: Job, now: datetime) -> JobCounts:
        counts = JobCounts()
        with self.unit_of_work() as uow:
            due = job.due(uow, now)
        for item in due:
            outcome = self._run_item(job, item, now)
            if outcome is None:
                counts.ran += 1
            elif outcome == "":
                counts.skipped += 1
            else:
                counts.failed += 1
                counts.errors.append(f"{item.key}: {outcome}")
        return counts

    def _run_item(self, job: Job, item: DueItem, now: datetime) -> str | None:
        """None when the work ran, "" when skipped, the error text when it failed."""
        with self.unit_of_work() as uow:
            if not uow.claim(job.name, item.key, self.max_attempts):
                return ""
            try:
                with uow.savepoint():
                    job.run(uow, item, now)
            except Exception as exc:  # the work is rolled back; the claim is kept as FAILED
                error = f"{type(exc).__name__}: {exc}"[:500]
                uow.fail(job.name, item.key, error)  # same transaction: never left RUNNING
                return error
            uow.succeed(job.name, item.key)
        return None


def iter_counts(report: JobReport) -> Iterator[tuple[str, JobCounts]]:
    yield from sorted(report.jobs.items())
