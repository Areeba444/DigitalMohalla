"""Listing endpoints (UC-B1, FR-B-01; plan item F9; DA-10 REST table).

POST /items and PATCH /items/{id} create, edit, draft, publish and pause a listing. Two small reads
support the create-and-edit screen (W22): GET /categories and GET /me/items (the member's own
listings, drafts included). Any approved member can list: lending is a role on a loan, not a kind
of account.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import Engine

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.config.engine_config import load_engine_config
from app.domain.lifecycle.service import Actor
from app.domain.listings.service import ListingDraft, ListingService
from app.infra.db.listings import PostgresListingStore

router = APIRouter(prefix="/api/v1")


def listing_out(item: dict[str, Any], viewer: UUID) -> dict[str, Any]:
    return {
        **{k: item[k] for k in schemas.ListingOut.model_fields if k in item},
        "deposit_amount": float(item["deposit_amount"]),
        "is_yours": item["owner_id"] == viewer,
    }


def _service(store: PostgresListingStore) -> ListingService:
    days = load_engine_config().section("scheduler_b13")["listing_default_expiry_days"]
    return ListingService(store, now=datetime.now(UTC), default_expiry_days=float(days))


def _draft(body: schemas.ListingFields) -> ListingDraft:
    return ListingDraft(**{k: getattr(body, k) for k in schemas.ListingFields.model_fields})


@router.get("/categories", response_model=list[schemas.CategoryOut])
def categories(
    actor: Actor = Depends(current_actor), engine: Engine = Depends(get_engine)
) -> list[schemas.CategoryOut]:
    with engine.connect() as conn:
        return [schemas.CategoryOut(**c) for c in PostgresListingStore(conn).categories()]


@router.get("/me/items", response_model=list[schemas.MyListingOut])
def my_listings(
    actor: Actor = Depends(current_actor), engine: Engine = Depends(get_engine)
) -> list[schemas.MyListingOut]:
    with engine.connect() as conn:
        rows = PostgresListingStore(conn).owned_by(actor.user_id)
    return [
        schemas.MyListingOut(**{**r, "deposit_amount": float(r["deposit_amount"])}) for r in rows
    ]


@router.post("/items", response_model=schemas.ListingOut, status_code=201)
def create_listing(
    body: schemas.ListingCreateIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.ListingOut:
    with engine.begin() as conn:
        item = _service(PostgresListingStore(conn)).create(
            actor.user_id, body.community_id, _draft(body), publish=body.publish
        )
    return schemas.ListingOut(**listing_out(item, actor.user_id))


@router.patch("/items/{item_id}", response_model=schemas.ListingOut)
def update_listing(
    item_id: UUID,
    body: schemas.ListingUpdateIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.ListingOut:
    with engine.begin() as conn:
        item = _service(PostgresListingStore(conn)).update(
            actor.user_id, item_id, _draft(body), body.status
        )
    return schemas.ListingOut(**listing_out(item, actor.user_id))
