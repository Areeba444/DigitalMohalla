"""Appeal and reversal endpoints (UC-I4 ext 4b, 4c; FR-T-11; DA-10 REST table; plan item M3).

POST /cases/{id}/appeal (party), POST /moderation/cases/{id}/appeal-decision (second moderator),
POST /moderation/decisions/{id}/reversal (moderator of the community or admin). Sequence (h).
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import Connection, Engine

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.config.engine_config import load_engine_config
from app.domain.lifecycle.service import Actor
from app.domain.moderation.appeals import AppealService
from app.infra.db.appeals import PostgresAppealStore
from app.infra.db.notifications import PostgresNotifier

router = APIRouter(prefix="/api/v1")


def _service(conn: Connection, engine: Engine) -> AppealService:
    days = load_engine_config().section("moderation_i4")["appeal_window_days"]
    return AppealService(
        PostgresAppealStore(conn, engine),
        now=datetime.now(UTC),
        appeal_window_days=float(days),
        notifier=PostgresNotifier(conn),
    )


@router.post("/cases/{case_id}/appeal", response_model=schemas.AppealFiledOut, status_code=202)
def file_appeal(
    case_id: UUID,
    body: schemas.AppealIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.AppealFiledOut:
    with engine.begin() as conn:
        _service(conn, engine).file_appeal(actor.user_id, case_id, body.reason)
    return schemas.AppealFiledOut(case_id=case_id, status="APPEALED")


@router.post("/moderation/cases/{case_id}/appeal-decision", response_model=schemas.AppealDecidedOut)
def decide_appeal(
    case_id: UUID,
    body: schemas.AppealDecisionIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.AppealDecidedOut:
    with engine.begin() as conn:
        result = _service(conn, engine).decide_appeal(
            actor.user_id, actor.platform_role, case_id, body.result == "UPHELD", body.reason
        )
    return schemas.AppealDecidedOut(**result)


@router.post(
    "/moderation/decisions/{decision_id}/reversal", response_model=schemas.AppealDecidedOut
)
def reverse_decision(
    decision_id: UUID,
    body: schemas.AppealIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.AppealDecidedOut:
    with engine.begin() as conn:
        result = _service(conn, engine).reverse(
            actor.user_id, actor.platform_role, decision_id, body.reason
        )
    return schemas.AppealDecidedOut(**result)
