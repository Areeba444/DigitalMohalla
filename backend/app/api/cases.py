"""Case endpoints for information requests and party responses (UC-I4 step 2, UC-B12; plan M2).

POST /moderation/cases/{id}/information-requests (moderator) and POST /cases/{id}/statements
(party), as in the DA-10 REST table and sequence (g). Attachments on statements come with uploads
(M4). `case_extras` adds the question and the responses to the evidence trails of W5 and W7.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import Connection, Engine

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.config.engine_config import load_engine_config
from app.domain.lifecycle.service import Actor
from app.domain.moderation.cases import CaseService
from app.infra.db.cases import PostgresCaseStore
from app.infra.db.notifications import PostgresNotifier

router = APIRouter(prefix="/api/v1")


def case_service(conn: Connection, audit_engine: Engine | None = None) -> CaseService:
    hours = load_engine_config().section("scheduler_b13")["party_response_deadline_hours"]
    return CaseService(
        PostgresCaseStore(conn, audit_engine),
        now=datetime.now(UTC),
        response_hours=float(hours),
        notifier=PostgresNotifier(conn),
    )


def case_extras(engine: Engine, case_id: UUID) -> dict[str, Any]:
    """The open question (if any was asked) and the parties' responses, for a case view."""
    with engine.connect() as conn:
        store = PostgresCaseStore(conn)
        asked = store.information_request(case_id)
        return {
            "information_request": schemas.InformationRequestOut(**asked) if asked else None,
            "statements": [schemas.StatementOut(**s) for s in store.statements(case_id)],
        }


@router.post(
    "/moderation/cases/{case_id}/information-requests",
    response_model=schemas.InformationRequestedOut,
)
def request_information(
    case_id: UUID,
    body: schemas.InformationRequestIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.InformationRequestedOut:
    with engine.begin() as conn:
        deadline = case_service(conn, engine).request_information(
            actor.user_id, actor.platform_role, case_id, body.to, body.question
        )
    return schemas.InformationRequestedOut(
        case_id=case_id, status="AWAITING_INFORMATION", deadline=deadline
    )


@router.post(
    "/cases/{case_id}/statements", response_model=schemas.StatementCreatedOut, status_code=201
)
def add_statement(
    case_id: UUID,
    body: schemas.StatementIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.StatementCreatedOut:
    with engine.begin() as conn:
        statement_id = case_service(conn, engine).add_statement(
            actor.user_id, case_id, body.statement
        )
    return schemas.StatementCreatedOut(id=statement_id, case_status="OPEN")
