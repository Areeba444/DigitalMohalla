"""JobRunner rules without a database (suite 19, unit part; ADR-0012).

A fake ledger and unit of work stand in for PostgreSQL: they keep claims in a dict with the same
rules as `job_run` (a SUCCEEDED or RUNNING claim is never reclaimed; a FAILED one is, until
max_attempts). TC-200 to TC-204.
"""

from contextlib import contextmanager, nullcontext
from datetime import UTC, datetime
from typing import Any

from app.domain.scheduler.runner import DueItem, JobRunner

NOW = datetime(2026, 11, 20, 12, tzinfo=UTC)


class Ledger:
    def __init__(self, free: bool = True) -> None:
        self.free = free

    @contextmanager
    def lock(self):  # type: ignore[no-untyped-def]
        yield self.free


class Claims:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict[str, Any]] = {}

    @contextmanager
    def uow(self):  # type: ignore[no-untyped-def]
        yield Uow(self)


class Uow:
    def __init__(self, claims: Claims) -> None:
        self.c = claims

    def claim(self, job: str, key: str, max_attempts: int) -> bool:
        row = self.c.rows.get((job, key))
        if row is None:
            self.c.rows[(job, key)] = {"status": "RUNNING", "attempts": 1}
            return True
        if row["status"] == "FAILED" and row["attempts"] < max_attempts:
            row.update(status="RUNNING", attempts=row["attempts"] + 1)
            return True
        return False

    def succeed(self, job: str, key: str) -> None:
        self.c.rows[(job, key)]["status"] = "SUCCEEDED"

    def fail(self, job: str, key: str, error: str) -> None:
        self.c.rows[(job, key)].update(status="FAILED", error=error)

    def savepoint(self):  # type: ignore[no-untyped-def]
        return nullcontext()


class Job:
    def __init__(self, name: str, keys: list[str], broken: set[str] | None = None) -> None:
        self.name, self.keys, self.broken = name, keys, broken or set()
        self.done: list[str] = []

    def due(self, uow: Any, now: datetime) -> list[DueItem]:
        return [DueItem(k, {}) for k in self.keys]

    def run(self, uow: Any, item: DueItem, now: datetime) -> None:
        if item.key in self.broken:
            raise ValueError("state changed")
        self.done.append(item.key)


def test_tc200_rerun_does_nothing_twice() -> None:
    claims, job = Claims(), Job("j", ["a", "b"])
    runner = JobRunner(Ledger(), claims.uow, [job], max_attempts=3)
    first = runner.run_due_jobs(NOW).jobs["j"]
    second = runner.run_due_jobs(NOW).jobs["j"]
    assert (first.ran, first.skipped, second.ran, second.skipped) == (2, 0, 0, 2)
    assert job.done == ["a", "b"]


def test_tc201_busy_lock_runs_nothing() -> None:
    job = Job("j", ["a"])
    report = JobRunner(Ledger(free=False), Claims().uow, [job], max_attempts=3).run_due_jobs(NOW)
    assert (report.lock_acquired, report.jobs, job.done) == (False, {}, [])


def test_tc202_a_failure_is_recorded_and_the_run_goes_on() -> None:
    claims, job = Claims(), Job("j", ["bad", "good"], broken={"bad"})
    counts = JobRunner(Ledger(), claims.uow, [job], max_attempts=3).run_due_jobs(NOW).jobs["j"]
    assert (counts.ran, counts.failed, job.done) == (1, 1, ["good"])
    assert claims.rows[("j", "bad")]["status"] == "FAILED"
    assert "state changed" in counts.errors[0]


def test_tc203_failed_work_is_retried_up_to_max_attempts() -> None:
    claims, job = Claims(), Job("j", ["bad"], broken={"bad"})
    runner = JobRunner(Ledger(), claims.uow, [job], max_attempts=3)
    failed = [runner.run_due_jobs(NOW).jobs["j"].failed for _ in range(4)]
    assert failed == [1, 1, 1, 0]  # three attempts, then skipped
    assert claims.rows[("j", "bad")]["attempts"] == 3


def test_tc204_a_retry_that_succeeds_is_not_run_again() -> None:
    claims, job = Claims(), Job("j", ["flaky"], broken={"flaky"})
    runner = JobRunner(Ledger(), claims.uow, [job], max_attempts=3)
    runner.run_due_jobs(NOW)
    job.broken.clear()
    assert runner.run_due_jobs(NOW).jobs["j"].ran == 1
    assert runner.run_due_jobs(NOW).jobs["j"].skipped == 1
    assert job.done == ["flaky"]
