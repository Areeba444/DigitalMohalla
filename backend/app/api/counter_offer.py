"""Counter-offer endpoints (UC-B6 ext 3b, FR-B-10, ADR-0015; DA-10 REST table; plan item F6).

POST /requests/{id}/counter-offer (lender), /counter-offer/accept and /counter-offer/decline
(borrower).
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api import schemas
from app.api.deps import Commands, current_actor, get_commands
from app.domain.lifecycle.counter_offer import CounterOffers
from app.domain.lifecycle.service import Actor, CommandResult

router = APIRouter(prefix="/api/v1")


def _out(r: CommandResult) -> schemas.CommandOut:
    return schemas.CommandOut(
        transaction_id=r.transaction_id, state=r.state, message=r.message, hold_reason=r.hold_reason
    )


@router.post("/requests/{txn_id}/counter-offer", response_model=schemas.CommandOut)
def counter_offer(
    txn_id: UUID,
    body: schemas.CounterOfferIn,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    return _out(
        commands.run(
            lambda svc: CounterOffers(svc).offer(actor, txn_id, body.period(), body.message)
        )
    )


@router.post("/requests/{txn_id}/counter-offer/accept", response_model=schemas.CommandOut)
def accept_counter_offer(
    txn_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    return _out(commands.run(lambda svc: CounterOffers(svc).accept(actor, txn_id)))


@router.post("/requests/{txn_id}/counter-offer/decline", response_model=schemas.CommandOut)
def decline_counter_offer(
    txn_id: UUID,
    actor: Actor = Depends(current_actor),
    commands: Commands = Depends(get_commands),
) -> schemas.CommandOut:
    return _out(commands.run(lambda svc: CounterOffers(svc).decline(actor, txn_id)))
