"""Admin audit log endpoints (UC-I6 v1.4; FR-M-05; NFR-S-05; DA-10 REST table; plan item M5).

GET /admin/audit: filtered, masked entries newest first, each with its hash check, plus the
moderator concentration highlight. The view itself is written to the audit log. POST
/admin/audit/{source}/{id}/unmask shows one entry unmasked, only with a stated purpose, and that
is logged too. Admin only (the design's REST table); a moderator-scoped view is a later extension.
"""

from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Engine

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.config.engine_config import load_engine_config
from app.domain.audit.view import concentration, present
from app.domain.lifecycle.service import Actor
from app.infra.db import audit as store

router = APIRouter(prefix="/api/v1")


def _admin(actor: Actor) -> None:
    if actor.platform_role != "ADMIN":
        raise HTTPException(status_code=403, detail="only an admin can read the audit log")


@router.get("/admin/audit", response_model=schemas.AuditPageOut)
def audit_log(
    actor_id: UUID | None = Query(default=None, alias="actor"),
    target: str | None = Query(default=None, max_length=100),
    action: str | None = Query(default=None, max_length=100, pattern="^[a-z][a-z0-9_]*$"),
    result: Literal["SUCCESS", "REJECTED"] | None = Query(default=None),
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.AuditPageOut:
    _admin(actor)
    cfg = load_engine_config().section("audit_i6")
    limit = min(limit, int(cfg["page_size_max"]))
    flt = store.AuditFilter(actor_id, target, action, result, since, until)
    with engine.begin() as conn:
        rows = store.search(conn, flt, limit, offset)
        pairs = store.moderator_member_pairs(
            conn, datetime.now(UTC) - timedelta(days=float(cfg["concentration_window_days"]))
        )
        # the view is itself logged (UC-I6 step 4), after it has been read
        store.log_view(
            conn,
            actor.user_id,
            "audit_viewed",
            "audit_log",
            {
                "filters": {
                    k: str(v)
                    for k, v in {
                        "actor": actor_id,
                        "target": target,
                        "action": action,
                        "result": result,
                        "from": since,
                        "to": until,
                    }.items()
                    if v is not None
                },
                "entries": len(rows),
            },
        )
    flagged = concentration(
        pairs, int(cfg["concentration_min_decisions"]), float(cfg["concentration_min_share"])
    )
    entries = [schemas.AuditEntryOut(**present(r)) for r in rows]
    return schemas.AuditPageOut(
        entries=entries,
        tampered=sum(1 for e in entries if not e.hash_valid),
        concentration=[schemas.AuditConcentrationOut(**vars(c)) for c in flagged],
        limit=limit,
        offset=offset,
    )


@router.post("/admin/audit/{source}/{entry_id}/unmask", response_model=schemas.AuditEntryOut)
def unmask_entry(
    source: Literal["event", "audit"],
    entry_id: int,
    body: schemas.AuditUnmaskIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.AuditEntryOut:
    _admin(actor)
    with engine.begin() as conn:
        row = store.get_entry(conn, source, entry_id)
        if row is None:
            raise HTTPException(status_code=404, detail="no such audit entry")
        store.log_view(
            conn,
            actor.user_id,
            "audit_unmasked",
            f"{source}:{entry_id}",
            {"purpose": body.purpose.strip(), "action": row.action},
        )
    return schemas.AuditEntryOut(**present(row, masked=False))
