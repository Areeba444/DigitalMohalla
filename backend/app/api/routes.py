"""REST endpoints of iteration 1, Slice A (Architecture_Design.md section 4), all under /api/v1.

Errors: 401 not logged in, 403 not allowed, 404 unknown id, 409 invalid transition / stale command /
dates taken, 422 invalid input. Every state-changing call is one command and one DB transaction.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Engine

from app.api import schemas
from app.api.deps import Commands, current_actor, get_commands, get_engine
from app.api.evidence import assessment_out, intermediaries
from app.config.settings import get_settings
from app.domain.accounts.auth import InvalidCredentials, create_token
from app.domain.lifecycle.service import Actor, BorrowingService, CommandResult
from app.domain.moderation.decisions import Decision
from app.infra.db.evidence import PostgresEvidenceSource
from app.infra.db.users import authenticate

router = APIRouter(prefix="/api/v1")


def _out(result: CommandResult) -> schemas.CommandOut:
    return schemas.CommandOut(
        transaction_id=result.transaction_id,
        state=result.state,
        message=result.message,
        hold_reason=result.hold_reason,
    )


# ----------------------------------------------------------------------------- login (A2)
@router.post("/auth/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, engine: Engine = Depends(get_engine)) -> schemas.TokenOut:
    settings = get_settings()
    if not settings.jwt_secret:
        raise HTTPException(status_code=503, detail="login is not configured")
    try:
        with engine.connect() as conn:
            actor = authenticate(conn, body.email, body.password)
    except InvalidCredentials as exc:
        raise HTTPException(status_code=401, detail="invalid email or password") from exc
    return schemas.TokenOut(
        access_token=create_token(actor, settings.jwt_secret, settings.jwt_minutes)
    )


# ----------------------------------------------------------------------------- items, requests (B5)
@router.get("/items/{item_id}", response_model=schemas.ItemOut)
def get_item(
    item_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.ItemOut:
    def read(svc: BorrowingService) -> schemas.ItemOut:
        item = svc.store.item(item_id)
        return schemas.ItemOut(
            id=item["id"],
            title=item["title"],
            value_band=item["value_band"],
            deposit_amount=float(item["deposit_amount"]),
            booked_periods=svc.store.booked_periods(item_id),
        )

    return commands.run(read)


@router.post("/requests", response_model=schemas.CommandOut, status_code=201)
def create_request(
    body: schemas.RequestIn,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    result = commands.run(
        lambda svc: svc.create_request(actor, body.item_id, body.period(), body.message)
    )
    return _out(result)


@router.get("/requests/{txn_id}", response_model=schemas.RequestOut)
def get_request(
    txn_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
    engine: Engine = Depends(get_engine),
) -> schemas.RequestOut:
    found = commands.run(lambda svc: svc.get_request(actor, txn_id))
    view, assessment, details = found["view"], found["assessment"], found["details"]
    names = (
        PostgresEvidenceSource(lambda: engine).display_names(intermediaries(assessment))
        if assessment
        else {}
    )
    return schemas.RequestOut(
        transaction_id=view.id,
        item_id=view.item_id,
        item_title=details["item_title"],
        state=view.state,
        hold_reason=view.hold_reason,
        your_role=found["role"],
        borrower_name=details["borrower_name"],
        lender_name=details["lender_name"],
        requested_period=details["requested_period"],
        message=details["message"],
        deposit_required=details["deposit_amount"] > 0,
        assessment=assessment_out(assessment, names) if assessment else None,
        reports=[schemas.ReportOut(**r) for r in found["reports"].values()],
        available_actions=found["actions"],
        moderator_safeguards=found["moderator_safeguards"],
    )


@router.get("/requests", response_model=list[schemas.MyRequestOut])
def my_requests(
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> list[schemas.MyRequestOut]:
    return [schemas.MyRequestOut(**r) for r in commands.run(lambda svc: svc.my_requests(actor))]


@router.get("/items", response_model=list[schemas.BrowseItemOut])
def browse_items(
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> list[schemas.BrowseItemOut]:
    rows = commands.run(lambda svc: svc.browse_items(actor))
    return [
        schemas.BrowseItemOut(**{**r, "deposit_amount": float(r["deposit_amount"])}) for r in rows
    ]


@router.get("/lender/requests", response_model=list[schemas.LenderRequestOut])
def lender_requests(
    state: str | None = Query(default=None),
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> list[schemas.LenderRequestOut]:
    rows = commands.run(lambda svc: svc.store.list_for_lender(actor.user_id, state))
    return [schemas.LenderRequestOut(**row) for row in rows]


# ----------------------------------------------------------------------------- respond (B6)
@router.post("/requests/{txn_id}/accept", response_model=schemas.CommandOut)
def accept(
    txn_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    result = commands.run(lambda svc: svc.accept(actor, txn_id))
    if result.state == "ACCEPTED":  # separate transaction: see BorrowingService.decline_overlapping
        commands.run(lambda svc: svc.decline_overlapping(txn_id))
    return _out(result)


@router.post("/requests/{txn_id}/decline", response_model=schemas.CommandOut)
def decline(
    txn_id: UUID,
    body: schemas.DeclineIn | None = None,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    reason = body.reason if body else None
    return _out(commands.run(lambda svc: svc.decline(actor, txn_id, reason)))


@router.post("/requests/{txn_id}/cancel", response_model=schemas.CommandOut)
def cancel(
    txn_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    return _out(commands.run(lambda svc: svc.cancel(actor, txn_id)))


# ----------------------------------------------------------------------------- handover (B7)
@router.post("/transactions/{txn_id}/handover/checklist", response_model=schemas.CommandOut)
def handover_checklist(
    txn_id: UUID,
    body: schemas.ChecklistIn,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    return _out(
        commands.run(
            lambda svc: svc.record_handover_checklist(
                actor,
                txn_id,
                checklist=body.checklist,
                deposit_received=body.deposit_received,
                notes=body.notes,
            )
        )
    )


@router.post("/transactions/{txn_id}/handover/confirm", response_model=schemas.CommandOut)
def handover_confirm(
    txn_id: UUID,
    body: schemas.ConfirmIn | None = None,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    b = body or schemas.ConfirmIn()
    return _out(
        commands.run(
            lambda svc: svc.confirm_handover(
                actor,
                txn_id,
                condition_agreed=b.condition_agreed,
                checklist=b.checklist,
                notes=b.notes,
            )
        )
    )


# ----------------------------------------------------------------------------- return (B8)
@router.post("/transactions/{txn_id}/return", response_model=schemas.CommandOut)
def initiate_return(
    txn_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    return _out(commands.run(lambda svc: svc.initiate_return(actor, txn_id)))


@router.post("/transactions/{txn_id}/return/confirm", response_model=schemas.CommandOut)
def return_confirm(
    txn_id: UUID,
    body: schemas.ConfirmIn | None = None,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    b = body or schemas.ConfirmIn()
    return _out(
        commands.run(
            lambda svc: svc.confirm_return(
                actor,
                txn_id,
                condition_agreed=b.condition_agreed,
                checklist=b.checklist,
                notes=b.notes,
            )
        )
    )


# ----------------------------------------------------------------------------- event stream
@router.get("/transactions/{txn_id}/events", response_model=list[schemas.EventOut])
def transaction_events(
    txn_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> list[schemas.EventOut]:
    def read(svc: BorrowingService) -> list[schemas.EventOut]:
        svc.get_request(actor, txn_id)  # party or admin only
        return [schemas.EventOut(**e) for e in svc.store.events(txn_id)]

    return commands.run(read)


# ----------------------------------------------------------------------------- disputes (B12, D6)
@router.post("/transactions/{txn_id}/dispute", response_model=schemas.CommandOut)
def raise_dispute(
    txn_id: UUID,
    body: schemas.DisputeIn,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    return _out(
        commands.run(lambda svc: svc.raise_dispute(actor, txn_id, body.reason, body.description))
    )


@router.post("/transactions/{txn_id}/dispute/withdraw", response_model=schemas.CommandOut)
def withdraw_dispute(
    txn_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    return _out(commands.run(lambda svc: svc.withdraw_dispute(actor, txn_id)))


@router.get("/transactions/{txn_id}/dispute", response_model=schemas.DisputeTrailOut)
def dispute_trail(
    txn_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
    engine: Engine = Depends(get_engine),
) -> schemas.DisputeTrailOut:
    found = commands.run(lambda svc: svc.dispute_case(actor, txn_id))
    view, assessment, details, case = (
        found["view"],
        found["assessment"],
        found["details"],
        found["case"],
    )
    names = (
        PostgresEvidenceSource(lambda: engine).display_names(intermediaries(assessment))
        if assessment
        else {}
    )
    return schemas.DisputeTrailOut(
        case=schemas.CaseOut(**{k: case[k] for k in schemas.CaseOut.model_fields}),
        transaction_id=view.id,
        item_title=details["item_title"],
        state=view.state,
        your_role=found["role"],
        borrower_name=details["borrower_name"],
        lender_name=details["lender_name"],
        requested_period=details["requested_period"],
        reports=[schemas.ReportOut(**r) for r in found["reports"].values()],
        events=[schemas.EventOut(**e) for e in found["events"]],
        assessment=assessment_out(assessment, names) if assessment else None,
        available_actions=found["actions"],
    )


# ----------------------------------------------------------------------------- moderation (I4)
@router.get("/moderation/cases", response_model=list[schemas.CaseQueueOut])
def moderation_queue(
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> list[schemas.CaseQueueOut]:
    return [
        schemas.CaseQueueOut(**c) for c in commands.run(lambda svc: svc.moderation_queue(actor))
    ]


@router.get("/moderation/cases/{case_id}", response_model=schemas.ModeratorCaseOut)
def moderator_case(
    case_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
    engine: Engine = Depends(get_engine),
) -> schemas.ModeratorCaseOut:
    found = commands.run(lambda svc: svc.moderator_case(actor, case_id))
    view, assessment, details, case = (
        found["view"],
        found["assessment"],
        found["details"],
        found["case"],
    )
    names = (
        PostgresEvidenceSource(lambda: engine).display_names(intermediaries(assessment))
        if assessment
        else {}
    )
    return schemas.ModeratorCaseOut(
        case=schemas.CaseOut(**{k: case[k] for k in schemas.CaseOut.model_fields}),
        transaction_id=view.id,
        item_title=details["item_title"],
        state=view.state,
        hold_reason=view.hold_reason,
        borrower_name=details["borrower_name"],
        lender_name=details["lender_name"],
        requested_period=details["requested_period"],
        reports=[schemas.ReportOut(**r) for r in found["reports"].values()],
        events=[schemas.EventOut(**e) for e in found["events"]],
        assessment=assessment_out(assessment, names) if assessment else None,
        decisions=[schemas.DecisionOut(**d) for d in found["decisions"]],
    )


@router.post("/moderation/cases/{case_id}/decision", response_model=schemas.CommandOut)
def decide_case(
    case_id: UUID,
    body: schemas.DecisionIn,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    decision = Decision(body.kind, body.reason, tuple(body.safeguards), body.at_fault)
    return _out(commands.run(lambda svc: svc.decide(actor, case_id, decision)))
