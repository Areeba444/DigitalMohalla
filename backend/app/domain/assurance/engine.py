"""The assurance engine behind IAssess (Module 5): direct evidence, indirect evidence, context, decision.

Pipeline (Algorithm doc §1): the borrower's verified outcomes (role BORROWER, metric ON_TIME_RETURN)
-> recency- and similarity-weighted Beta posterior (B2) -> k-hop community paths from the lender (B3)
-> manipulation risk from the borrower's reviews (C1: S1, S4 and the retaliation check; Algorithm 3)
-> context (open or recent disputes, verification, value band) -> decision table R1 to R9 -> result.

Data comes through `EvidenceSource`, so the engine itself does no I/O and is unit-tested with a fake.
The configuration is checked when the engine is built: a missing or invalid parameter stops start-up
instead of silently falling back to a default (TC-74). `clock` makes "now" explicit for tests.
"""

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from app.config.engine_config import EngineConfig
from app.domain.assurance.detection.manipulation import (
    Complaint,
    ManipulationParams,
    ReviewSnapshot,
    assess_manipulation,
)
from app.domain.assurance.estimation.posterior import (
    EstimatorParams,
    WeightedOutcome,
    estimate,
    recency_weight,
)
from app.domain.assurance.estimation.similarity import (
    LoanProfile,
    SimilarityParams,
    floored,
    request_similarity,
    similarity,
)
from app.domain.assurance.indirect.khop import KHopParams, indirect_trust
from app.domain.assurance.policy.decision import PolicyInputs, PolicyThresholds, decide
from app.domain.assurance.policy.explanation import ExplainedPath, build_explanation
from app.domain.lifecycle.ports import AssessmentRequest, AssessmentResult


class ConfigError(Exception):
    """The engine configuration is missing a parameter or has an invalid value."""


@dataclass(frozen=True)
class OutcomeSnapshot:
    occurred_at: datetime
    success: bool
    status: str
    category_id: int
    value_band: str
    duration_days: float


class EvidenceSource(Protocol):
    def borrower_outcomes(self, borrower_id: UUID) -> list[OutcomeSnapshot]: ...

    def trust_graph(self) -> Mapping[str, Mapping[str, float]]: ...

    def open_dispute(self, borrower_id: UUID) -> bool: ...

    def resolved_disputes_since(self, borrower_id: UUID, since: datetime) -> int: ...

    def verification_ok(self, borrower_id: UUID, item_id: UUID) -> bool: ...

    def display_names(self, user_ids: list[str]) -> dict[str, str]: ...

    def reviews_since(self, since: datetime) -> list[ReviewSnapshot]: ...

    def complaints_by(self, user_id: UUID, since: datetime) -> list[Complaint]: ...


class AssuranceEngine:
    def __init__(
        self,
        source: EvidenceSource,
        config: EngineConfig,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        try:
            self.estimator = EstimatorParams.from_config(config.section("trust_estimation_alg1"))
            self.sim = SimilarityParams.from_config(
                config.section("trust_estimation_alg1")["similarity_weighting"]
            )
            self.khop = KHopParams.from_config(config.section("indirect_trust_alg2"))
            self.thresholds = PolicyThresholds.from_config(config.data)
            self.manipulation = ManipulationParams.from_config(
                config.section("manipulation_detection_alg3")
            )
            self.lookback_months = int(
                config.section("decision_policy_alg4")["context_windows"][
                    "resolved_disputes_lookback_months"
                ]
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigError(f"engine config {config.config_version}: {exc!r}") from exc
        if self.estimator.half_life_days <= 0 or not 0 < self.estimator.level < 1:
            raise ConfigError("half-life must be positive and the interval level in (0, 1)")
        self.config_version = config.config_version
        self.source = source
        self.clock = clock

    def assess(self, request: AssessmentRequest) -> AssessmentResult:
        now = self.clock()
        wanted = LoanProfile(request.category_id, request.value_band, request.duration_days or 1.0)
        weighted: list[WeightedOutcome] = []
        history: list[tuple[float, float]] = []
        for o in self.source.borrower_outcomes(request.borrower_id):
            if o.status != "VALID":
                continue
            raw = similarity(
                LoanProfile(o.category_id, o.value_band, o.duration_days), wanted, self.sim
            )
            weighted.append(WeightedOutcome(o.occurred_at, o.success, floored(raw, self.sim)))
            age = max(0.0, (now - o.occurred_at).total_seconds() / 86400.0)
            history.append((recency_weight(age, self.estimator.half_life_days), raw))
        direct = estimate(weighted, self.estimator, now)
        req_sim = request_similarity(history)
        lender, borrower = str(request.lender_id), str(request.borrower_id)
        indirect = indirect_trust(
            self.source.trust_graph(),
            lender,
            borrower,
            self.khop,
            target_mean=direct.mean if direct.n_raw else None,
        )
        open_dispute = self.source.open_dispute(request.borrower_id)
        since = now - timedelta(days=30.4375 * self.lookback_months)  # mean month = 365.25 / 12
        recent = self.source.resolved_disputes_since(request.borrower_id, since)
        verified = self.source.verification_ok(request.borrower_id, request.item_id)
        mp = self.manipulation
        reach = now - timedelta(days=mp.window_days + mp.retaliation_window_days)
        risk = assess_manipulation(
            borrower,
            self.source.reviews_since(reach),
            self.source.complaints_by(request.borrower_id, reach),
            now,
            mp,
        )
        d = decide(
            PolicyInputs(
                mean=direct.mean,
                lower_90=direct.lower_90,
                n_eff=direct.n_eff,
                direct_event_count=direct.n_raw,
                rho=indirect.reliability,
                risk_level=risk.level,
                value_band=request.value_band,
                open_dispute=open_dispute,
                resolved_disputes_12m=recent,
                verification_ok=verified,
                request_similarity=req_sim,
            ),
            self.thresholds,
        )
        names = self.source.display_names(
            sorted({n for p in indirect.paths for n in p.nodes[1:-1]})
        )
        explanation = build_explanation(
            rule=d.rule,
            state=d.state,
            mean=direct.mean,
            lower_90=direct.lower_90,
            upper_90=direct.upper_90,
            n_eff=direct.n_eff,
            direct_event_count=direct.n_raw,
            rho=indirect.reliability,
            paths=[
                ExplainedPath([names.get(n, "a member") for n in p.nodes[1:-1]], p.strength)
                for p in indirect.paths
            ],
            resolved_disputes_12m=recent,
            open_dispute=open_dispute,
            is_high_value=request.value_band == "HIGH",
            request_similarity=req_sim,
            manipulation=risk,
            n_min=self.thresholds.n_min,
            rho_max=self.khop.rho_max,
            similarity_floor=self.thresholds.similarity_floor,
            lookback_months=self.lookback_months,
        )
        direct_json: dict[str, Any] = {
            "alpha": direct.alpha,
            "beta": direct.beta,
            "mean": direct.mean,
            "lower_90": direct.lower_90,
            "upper_90": direct.upper_90,
            "n_eff": direct.n_eff,
            "direct_event_count": direct.n_raw,
            "request_similarity": req_sim,
            "role": "BORROWER",
            "metric": "ON_TIME_RETURN",
        }
        indirect_json: dict[str, Any] = {
            "paths": [
                {"nodes": list(p.nodes), "hops": p.hops, "path_weight": p.strength}
                for p in indirect.paths
            ],
            "evidence_strength_I": indirect.evidence_strength,
            "reliability_rho": indirect.reliability,
            "estimate": indirect.estimate,
            "prior_backed": indirect.prior_backed,
            "k": self.khop.k,
        }
        return AssessmentResult(
            assurance_state=d.state,
            policy_decision=d.decision,
            rule_fired=d.rule,
            hold_reason=d.hold_reason,
            explanation=explanation,
            config_version=self.config_version,
            manipulation_risk=risk.stored_score,
            manipulation_level=risk.level,
            manipulation_corroborated=risk.corroborated,
            posterior_mean=round(direct.mean, 4),
            ci90_low=round(direct.lower_90, 4),
            ci90_high=round(direct.upper_90, 4),
            effective_evidence=round(direct.n_eff, 3),
            direct_evidence=direct_json,
            indirect_evidence=indirect_json,
            manipulation_signals=[asdict(s) for s in risk.signals]
            + [{"name": "retaliation_check", **asdict(f)} for f in risk.retaliation],
            safeguards=d.safeguards,
        )
