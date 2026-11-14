"""Search endpoint (UC-B3; FR-S-02, FR-S-03; DA-10 REST table; plan item F10, then M9 and A9).

GET /search?q=&category=&community=&from=&to=&max_deposit=&condition=&sort=&page=
Results carry a reason line and the search `mode`, never a score (NFR-U-01).
"""

import logging
import time
from dataclasses import asdict
from datetime import UTC, date, datetime
from datetime import time as day_start
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.config.engine_config import load_engine_config
from app.domain.lifecycle.service import Actor
from app.domain.search.log import SearchLogger
from app.domain.search.service import PAGE_SIZE, SearchFilters, SearchResult, SearchService
from app.infra.db.search import PostgresSearchStore
from app.infra.db.search_log import PostgresSearchLogStore

router = APIRouter(prefix="/api/v1")
log = logging.getLogger(__name__)


def _day(d: date | None) -> datetime | None:
    return datetime.combine(d, day_start(0), tzinfo=UTC) if d else None


def search_service(conn: Connection) -> SearchService:
    retrieval = load_engine_config().section("ranking_alg5")["retrieval"]
    return SearchService(
        PostgresSearchStore(conn),
        min_relevance=float(retrieval["min_relevance"]),
        candidate_pool=int(retrieval["candidate_pool"]),
    )


def _log(
    engine: Engine,
    actor: Actor,
    q: str,
    filters: SearchFilters,
    sort: str,
    found: SearchResult,
    latency_ms: int,
    page: int,
) -> UUID | None:
    """FR-S-05 log in its own transaction after the search; a failure here never fails the
    member's search (sequence (i)), it only leaves this query unlogged."""
    config_version = load_engine_config().config_version
    logged = {**{k: str(v) if v is not None else None for k, v in asdict(filters).items()}}
    logged.update(sort=sort, page=str(page))
    try:
        with engine.begin() as conn:
            return SearchLogger(PostgresSearchLogStore(conn), config_version).log_search(
                actor.user_id,
                q,
                logged,
                found.mode,
                found.results,
                latency_ms,
                offset=(page - 1) * PAGE_SIZE,
            )
    except SQLAlchemyError:
        log.warning("search log failed for one query; results were still returned")
        return None


@router.post("/search/{query_id}/clicks", status_code=202, response_model=schemas.ClickOut)
def record_click(
    query_id: UUID,
    body: schemas.ClickIn,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.ClickOut:
    """UC-B3 step 6: the member opened a shown result. 404 for someone else's search or an item
    that was not shown."""
    config_version = load_engine_config().config_version
    with engine.begin() as conn:
        click = SearchLogger(PostgresSearchLogStore(conn), config_version).log_click(
            actor.user_id, query_id, body.item_id
        )
    return schemas.ClickOut(id=click)


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
    started = time.perf_counter()
    with engine.connect() as conn:
        found = search_service(conn).search(actor.user_id, q, filters, sort, page)
    latency_ms = int((time.perf_counter() - started) * 1000)
    query_id = _log(engine, actor, q, filters, sort, found, latency_ms, page)
    return schemas.SearchOut(
        query_id=query_id,
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
