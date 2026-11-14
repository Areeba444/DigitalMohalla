"""PostgreSQL side of the JobRunner (ADR-0012, plan item F4): advisory lock, claims, unit of work.

The lock is a session-level `pg_try_advisory_lock` held on its own connection for the whole run. A
claim is a row in `job_run` whose `(job_name, due_key)` is unique; a FAILED row is reclaimed with
`attempts + 1` until `max_attempts`, and a SUCCEEDED or RUNNING row is never reclaimed.
"""

from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime
from typing import Any

from sqlalchemy import Connection, Engine, text

from app.config.engine_config import EngineConfig
from app.domain.moderation.cases import CaseService
from app.infra.db.cases import PostgresCaseStore
from app.infra.db.notifications import PostgresNotifier
from app.infra.eventstore.postgres import PostgresLifecycleStore

LOCK_KEY = "dm.jobs"


class PostgresLedger:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    @contextmanager
    def lock(self) -> Iterator[bool]:
        with self.engine.connect() as conn:
            got = bool(
                conn.execute(
                    text("SELECT pg_try_advisory_lock(hashtext(:k))"), {"k": LOCK_KEY}
                ).scalar_one()
            )
            conn.commit()
            try:
                yield got
            finally:
                if got:
                    conn.execute(text("SELECT pg_advisory_unlock(hashtext(:k))"), {"k": LOCK_KEY})
                    conn.commit()


class PostgresUnitOfWork:
    """One DB transaction for one job step, with the adapters jobs use."""

    def __init__(self, conn: Connection, config: EngineConfig, now: datetime) -> None:
        self.conn = conn
        self.config = config
        self.timers = config.section("scheduler_b13")
        self.store = PostgresLifecycleStore(conn)
        self.notifier = PostgresNotifier(conn)
        self.cases = CaseService(
            PostgresCaseStore(conn),
            now=now,
            response_hours=float(self.timers["party_response_deadline_hours"]),
            notifier=self.notifier,
        )

    def claim(self, job_name: str, due_key: str, max_attempts: int) -> bool:
        row = self.conn.execute(
            text(
                "INSERT INTO job_run (job_name, due_key) VALUES (:j, :k) "
                "ON CONFLICT ON CONSTRAINT job_run_once_uq DO UPDATE SET status = 'RUNNING', "
                "attempts = job_run.attempts + 1, started_at = clock_timestamp(), "
                "finished_at = NULL, error = NULL "
                "WHERE job_run.status = 'FAILED' AND job_run.attempts < :max RETURNING id"
            ),
            {"j": job_name, "k": due_key, "max": max_attempts},
        ).first()
        return row is not None

    def succeed(self, job_name: str, due_key: str) -> None:
        self._finish(job_name, due_key, "SUCCEEDED", None)

    def fail(self, job_name: str, due_key: str, error: str) -> None:
        self._finish(job_name, due_key, "FAILED", error)

    def savepoint(self) -> AbstractContextManager[Any]:
        return self.conn.begin_nested()

    def _finish(self, job_name: str, due_key: str, status: str, error: str | None) -> None:
        self.conn.execute(
            text(
                "UPDATE job_run SET status = CAST(:s AS job_status), finished_at = clock_timestamp(), "
                "error = :e WHERE job_name = :j AND due_key = :k"
            ),
            {"s": status, "e": error, "j": job_name, "k": due_key},
        )


def unit_of_work_factory(engine: Engine, config: EngineConfig, now: datetime) -> "Any":
    @contextmanager
    def factory() -> Iterator[PostgresUnitOfWork]:
        with engine.begin() as conn:
            yield PostgresUnitOfWork(conn, config, now)

    return factory
