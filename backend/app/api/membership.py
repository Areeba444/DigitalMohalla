"""Community and membership endpoints (UC-A3, UC-A4; plan items F2 and F3; sequence (d)).

The join body carries a one-time location fix. It goes straight to the LocalityVerifier in memory
and is never logged, stored or echoed (NFR-PR-01); the response holds only the coarse outcome.
"""

from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Connection, Engine

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.config.engine_config import load_engine_config
from app.domain.lifecycle.service import Actor
from app.domain.membership.locality import Fix, LocalityConfig
from app.domain.membership.service import JoinInput, MembershipService
from app.infra.db.membership import PostgresMembershipStore
from app.infra.db.notifications import PostgresNotifier

router = APIRouter(prefix="/api/v1")

LOCALITY_WORDS = {
    "VERIFIED": "Your location check and invitation agree.",
    "INCONCLUSIVE": "We could not confirm your location yet. A moderator will look at your "
    "request. This is not a negative finding.",
    "CONFLICTING": "Some signals did not match. A moderator will review your request; nothing "
    "has been rejected.",
}
Outcome = Literal["VERIFIED", "INCONCLUSIVE", "CONFLICTING"]


def _service(conn: Connection, engine: Engine) -> MembershipService:
    cfg = LocalityConfig.from_section(load_engine_config().section("locality_a11"))
    return MembershipService(
        PostgresMembershipStore(conn, audit_engine=engine),
        cfg,
        now=datetime.now(UTC),
        notifier=PostgresNotifier(conn),
    )


@router.get("/communities", response_model=list[schemas.CommunityListOut])
def communities(
    query: str | None = Query(default=None, max_length=80),
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> list[schemas.CommunityListOut]:
    with engine.connect() as conn:
        rows = _service(conn, engine).communities(query)
    return [schemas.CommunityListOut(**r) for r in rows]


@router.post("/communities/{community_id}/join", response_model=schemas.JoinOut, status_code=201)
def join(
    community_id: UUID,
    body: schemas.JoinIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.JoinOut:
    fix = (
        Fix(body.fix.lat, body.fix.lng, body.fix.accuracy_m, body.fix.mock_provider)
        if body.fix
        else None
    )
    with engine.begin() as conn:
        outcome = _service(conn, engine).request_join(
            actor.user_id,
            community_id,
            JoinInput(fix, body.permission_refused, body.invitation_code),
        )
    r = outcome.locality
    return schemas.JoinOut(
        membership_id=outcome.membership_id,
        status=outcome.status,
        locality=schemas.LocalityOut(
            outcome=cast(Outcome, r.outcome),
            message=LOCALITY_WORDS[r.outcome],
            invitation_used=r.invitation_used,
        ),
    )


@router.post(
    "/communities/{community_id}/invitations",
    response_model=schemas.InvitationOut,
    status_code=201,
)
def invite(
    community_id: UUID,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.InvitationOut:
    with engine.begin() as conn:
        code, expires = _service(conn, engine).issue_invitation(actor.user_id, community_id)
    return schemas.InvitationOut(code=code, expires_at=expires)


@router.get("/moderation/memberships", response_model=list[schemas.MembershipQueueOut])
def membership_queue(
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> list[schemas.MembershipQueueOut]:
    with engine.connect() as conn:
        rows = _service(conn, engine).queue(actor.user_id, actor.platform_role)
    return [schemas.MembershipQueueOut(**r) for r in rows]


@router.post(
    "/moderation/memberships/{membership_id}/decision",
    response_model=schemas.MembershipDecisionOut,
)
def decide_membership(
    membership_id: UUID,
    body: schemas.MembershipDecisionIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.MembershipDecisionOut:
    with engine.begin() as conn:
        status = _service(conn, engine).decide(
            actor.user_id,
            actor.platform_role,
            membership_id,
            body.kind,
            body.reason,
            body.reverses_decision_id,
        )
    return schemas.MembershipDecisionOut(membership_id=membership_id, status=status)
