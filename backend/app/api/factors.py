"""Evidence factors on the API (A5, A7, A10; FR-T-08, FR-S-04, NFR-U-01; DA-10 REST table).

GET /me/evidence: the member's own evidence, per role and metric, suppressed when there are too few
loans. The same factor code gives the lender's evidence on the item screen and in search results, and
the internal ranking value (never returned). No single trust number is ever produced or shown.
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import Connection, Engine

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.config.engine_config import load_engine_config
from app.domain.assurance.estimation.factors import (
    Factor,
    OutcomeRow,
    population_baseline,
    ranking_value,
    role_factors,
)
from app.domain.assurance.estimation.posterior import EstimatorParams
from app.domain.lifecycle.service import Actor
from app.infra.db import factors as store

router = APIRouter(prefix="/api/v1")

NOTE = (
    "This is the evidence behind your requests, factor by factor. It is decision support, not a "
    "guarantee, and there is no single score. Few verified loans is an absence of evidence, never a "
    "negative finding."
)


def _settings() -> tuple[EstimatorParams, float]:
    cfg = load_engine_config()
    params = EstimatorParams.from_config(cfg.section("trust_estimation_alg1"))
    n_min = float(cfg.section("decision_policy_alg4")["thresholds"]["n_min_effective_observations"])
    return params, n_min


def factor_out(f: Factor) -> schemas.FactorOut:
    return schemas.FactorOut(
        metric=f.metric,
        label=f.label,
        verified_loans=f.verified_loans,
        enough=f.enough,
        estimate=f.mean,
        interval_low=f.lower_90,
        interval_high=f.upper_90,
        confidence=f.confidence,
        note=f.note,
    )


def lender_out(rows: list[OutcomeRow], now: datetime | None = None) -> schemas.LenderEvidenceOut:
    """The lender's factors in words (FR-S-04): 'not enough history yet' for a new lender."""
    params, n_min = _settings()
    factors = role_factors(rows, "LENDER", params, n_min, now or datetime.now(UTC))
    has_history = any(f.verified_loans for f in factors)
    cond = factors[0]
    if not has_history:
        summary = "New lender: not enough verified history yet. That is not a negative finding."
    elif cond.enough:
        summary = f"Items have been as described ({cond.confidence}, {cond.verified_loans} verified loans)."
    else:
        summary = f"{cond.verified_loans} verified loan(s) so far: too few to show detail."
    return schemas.LenderEvidenceOut(
        has_history=has_history, summary=summary, factors=[factor_out(f) for f in factors]
    )


def lender_evidence(
    conn: Connection, owner_ids: list[UUID]
) -> dict[UUID, schemas.LenderEvidenceOut]:
    rows = store.lender_rows(conn, owner_ids)
    return {o: lender_out(rows[o]) for o in owner_ids}


def lender_ranking_values(conn: Connection, owner_ids: list[UUID]) -> dict[UUID, float]:
    """Algorithm 5: the posterior mean when there is enough evidence, else the population baseline."""
    params, n_min = _settings()
    now = datetime.now(UTC)
    pb = load_engine_config().section("indirect_trust_alg2")["baseline"]["population_baseline"]
    baseline = population_baseline(
        store.baseline_rows(conn, None, "LENDER", "CONDITION_AGREED"),
        params.half_life_days,
        now,
        float(pb["min_weighted_outcomes"]),
        float(pb["fallback"]),
    )
    rows = store.lender_rows(conn, owner_ids)
    return {
        o: ranking_value(role_factors(rows[o], "LENDER", params, n_min, now)[0], baseline)
        for o in owner_ids
    }


@router.get("/me/evidence", response_model=schemas.MyEvidenceOut)
def my_evidence(
    actor: Actor = Depends(current_actor), engine: Engine = Depends(get_engine)
) -> schemas.MyEvidenceOut:
    params, n_min = _settings()
    now = datetime.now(UTC)
    with engine.connect() as conn:
        rows = store.outcome_rows(conn, actor.user_id)
    return schemas.MyEvidenceOut(
        roles=[
            schemas.RoleEvidenceOut(
                role=role,  # type: ignore[arg-type]
                factors=[factor_out(f) for f in role_factors(rows, role, params, n_min, now)],
            )
            for role in ("BORROWER", "LENDER")
        ],
        note=NOTE,
    )
