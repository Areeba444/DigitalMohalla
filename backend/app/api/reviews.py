"""Review endpoint (UC-D1, FR-T-09, FR-B-15; DA-10 REST table; plan item A3).

POST /transactions/{id}/review creates the party's review, or edits it inside the edit window. The
flags are written but never returned to the reviewer (sequence (f)).
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import Engine

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.config.engine_config import load_engine_config
from app.domain.assurance.detection.manipulation import ManipulationParams
from app.domain.lifecycle.service import Actor
from app.domain.reviews.service import ReviewConfig, ReviewService
from app.infra.db.notifications import PostgresNotifier
from app.infra.db.reviews import PostgresReviewStore

router = APIRouter(prefix="/api/v1")


@router.post("/transactions/{txn_id}/review", response_model=schemas.ReviewOut, status_code=201)
def submit_review(
    txn_id: UUID,
    body: schemas.ReviewIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.ReviewOut:
    config = load_engine_config()
    with engine.begin() as conn:
        result = ReviewService(
            PostgresReviewStore(conn),
            ReviewConfig.from_section(config.section("reviews_d1")),
            ManipulationParams.from_config(config.section("manipulation_detection_alg3")),
            now=datetime.now(UTC),
            notifier=PostgresNotifier(conn),
        ).submit(actor.user_id, txn_id, body.ratings, body.comment)
    return schemas.ReviewOut(
        id=result.id, reviewee_role=result.reviewee_role, editable_until=result.editable_until
    )
