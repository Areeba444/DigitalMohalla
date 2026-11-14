"""Extension endpoints (UC-B8 ext 1a, FR-B-14; DA-10 REST table; plan item F5).

POST /transactions/{id}/extension (borrower), /extension/approve and /extension/decline (lender).
"""

from datetime import UTC, datetime, time
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api import schemas
from app.api.deps import Commands, current_actor, get_commands
from app.domain.lifecycle.extensions import Extensions
from app.domain.lifecycle.service import Actor, CommandResult

router = APIRouter(prefix="/api/v1")


def _out(r: CommandResult) -> schemas.CommandOut:
    return schemas.CommandOut(transaction_id=r.transaction_id, state=r.state, message=r.message)


@router.post("/transactions/{txn_id}/extension", response_model=schemas.CommandOut)
def request_extension(
    txn_id: UUID,
    body: schemas.ExtensionIn,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    # a loan's due date is the end of its booked period, midnight UTC (as request dates are)
    new_due = datetime.combine(body.new_due_date, time(0), tzinfo=UTC)
    return _out(
        commands.run(lambda svc: Extensions(svc).request(actor, txn_id, new_due, body.reason))
    )


@router.post("/transactions/{txn_id}/extension/approve", response_model=schemas.CommandOut)
def approve_extension(
    txn_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    return _out(commands.run(lambda svc: Extensions(svc).approve(actor, txn_id)))


@router.post("/transactions/{txn_id}/extension/decline", response_model=schemas.CommandOut)
def decline_extension(
    txn_id: UUID,
    body: schemas.DeclineIn | None = None,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    reason = body.reason if body else None
    return _out(commands.run(lambda svc: Extensions(svc).decline(actor, txn_id, reason)))
