from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import Engine

from app.api import (
    cases,
    counter_offer,
    extensions,
    jobs,
    listings,
    membership,
    notifications,
)
from app.api.deps import default_assessor
from app.api.routes import router
from app.config.settings import get_settings
from app.domain.lifecycle.errors import (
    DatesTaken,
    InvalidTransition,
    NotAuthorised,
    StaleCommand,
    StreamNotFound,
)
from app.domain.lifecycle.ports import IAssess
from app.domain.listings.service import InvalidListing
from app.domain.membership.locality import InvalidInvitation
from app.domain.membership.service import InvalidMembershipInput
from app.domain.moderation.cases import InvalidCaseInput
from app.domain.moderation.decisions import InvalidDecision
from app.infra.db.session import make_engine


def _refusal(status: int) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status, content={"detail": str(exc)})

    return handler


def create_app(engine: Engine | None = None, assess: IAssess | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if app.state.engine is None:  # created lazily so /health works without a database
            app.state.engine = make_engine()
        yield

    app = FastAPI(title="Digital Mohalla API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
        allow_origin_regex=get_settings().cors_origin_regex or None,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.engine = engine
    app.state.assess = assess or default_assessor(lambda: app.state.engine)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.add_exception_handler(NotAuthorised, _refusal(403))
    app.add_exception_handler(InvalidDecision, _refusal(422))
    app.add_exception_handler(InvalidInvitation, _refusal(422))
    app.add_exception_handler(InvalidListing, _refusal(422))
    app.add_exception_handler(InvalidCaseInput, _refusal(422))
    app.add_exception_handler(InvalidMembershipInput, _refusal(422))
    app.add_exception_handler(StreamNotFound, _refusal(404))
    for conflict in (InvalidTransition, StaleCommand, DatesTaken):
        app.add_exception_handler(conflict, _refusal(409))

    app.include_router(router)
    app.include_router(notifications.router)
    app.include_router(membership.router)
    app.include_router(listings.router)
    app.include_router(cases.router)
    app.include_router(jobs.router)
    app.include_router(extensions.router)
    app.include_router(counter_offer.router)
    return app


app = create_app()
