"""API dependencies: database engine, one-transaction-per-command, and the logged-in actor."""

from collections.abc import Callable
from typing import TypeVar

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Engine

from app.config.engine_config import load_engine_config
from app.config.settings import get_settings
from app.domain.accounts.auth import InvalidCredentials, decode_token
from app.domain.assurance.engine import AssuranceEngine
from app.domain.lifecycle.ports import IAssess
from app.domain.lifecycle.service import Actor, BorrowingService
from app.infra.db.evidence import PostgresEvidenceSource
from app.infra.eventstore.postgres import PostgresAuditLog, PostgresLifecycleStore

T = TypeVar("T")
bearer = HTTPBearer(auto_error=False)


class Commands:
    """Runs a command in its own DB transaction: commit on success, roll back on any error."""

    def __init__(self, engine: Engine, assess: IAssess) -> None:
        self.engine = engine
        self.assess = assess
        config = load_engine_config()
        self.config_version = config.config_version
        self.timeout_ms = int(config.section("decision_policy_alg4").get("engine_timeout_ms", 2000))

    def run(self, fn: Callable[[BorrowingService], T]) -> T:
        with self.engine.begin() as conn:
            service = BorrowingService(
                PostgresLifecycleStore(conn),
                self.assess,
                PostgresAuditLog(self.engine),
                config_version=self.config_version,
                engine_timeout_ms=self.timeout_ms,
            )
            return fn(service)


def get_commands(request: Request) -> Commands:
    return Commands(request.app.state.engine, request.app.state.assess)


def get_engine(request: Request) -> Engine:
    engine: Engine = request.app.state.engine
    return engine


def default_assessor(db: Callable[[], Engine]) -> IAssess:
    """The real assurance engine (Slice B); `db` returns the app's engine once it exists."""
    return AssuranceEngine(PostgresEvidenceSource(db), load_engine_config())


def current_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Actor:
    secret = get_settings().jwt_secret
    if credentials is None or not secret:
        raise HTTPException(status_code=401, detail="not logged in")
    try:
        return decode_token(credentials.credentials, secret)
    except InvalidCredentials as exc:
        raise HTTPException(status_code=401, detail="not logged in") from exc
