"""Search endpoint (UC-B3; FR-S-02, FR-S-03; DA-10 REST table; plan item F10, then M9 and A9).

GET /search?q=&category=&community=&from=&to=&max_deposit=&condition=&sort=&page=
Results carry a reason line and the search `mode`, never a score (NFR-U-01).
"""

from datetime import UTC, date, datetime, time
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Connection, Engine

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.config.engine_config import load_engine_config
from app.domain.lifecycle.service import Actor
from app.domain.search.service import SearchFilters, SearchService
from app.infra.db.search import PostgresSearchStore

router = APIRouter(prefix="/api/v1")


def _day(d: date | None) -> datetime | None:
    return datetime.combine(d, time(0), tzinfo=UTC) if d else None


def search_service(conn: Connection) -> SearchService:
    retrieval = load_engine_config().section("ranking_alg5")["retrieval"]
    return SearchService(
        PostgresSearchStore(conn),
        min_relevance=float(retrieval["min_relevance"]),
        candidate_pool=int(retrieval["candidate_pool"]),
    )


@router.get("/search", response_model=schemas.SearchOut)
def search(
    q: str = Query(default="", max_length=200),
    category: int | None = Query(default=None),
    community: UUID | None = Query(default=None),
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
    max_deposit: float | None = Query(default=None, ge=0),
    condition: Literal["NEW", "GOOD", "FAIR", "WORN"] | None = Query(default=None),
    sort: Literal["relevance", "evidence", "newest"] = Query(default="relevance"),
    page: int = Query(default=1, ge=1, le=50),
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.SearchOut:
    filters = SearchFilters(category, community, _day(from_), _day(to), max_deposit, condition)
    with engine.connect() as conn:
        found = search_service(conn).search(actor.user_id, q, filters, sort, page)
    return schemas.SearchOut(
        query_id=None,
        mode=found.mode,
        total=found.total,
        results=[
            schemas.SearchResultOut(
                **{k: r[k] for k in schemas.SearchResultOut.model_fields if k in r},
                item_id=r["id"],
            )
            for r in found.results
        ],
    )
