"""Suite 11 on the hand-checked fixtures: TC-40 to TC-47 (ES-01 to ES-06, ES-13 and its counterfactual).

Each fixture runs through the decision policy and the explanation builder with the fixture's own
numbers, and the result is compared with its expected rule, state, decision, lifecycle state and
the facts its test case asks the explanation to show. Where the fixture can be rebuilt from raw
evidence (ES-01: none; ES-02: ten successful loans of the same kind; ES-13: two outcomes and four
trust edges) the real engine runs on it and must reproduce the fixture's numbers. Parts that need
manipulation detection (signals for ES-04, the retaliation flag for ES-05) arrive in Slice C and are
strict expected failures. All data is SYNTHETIC.

Plain-language note on ES-02: ten loans at the same age a have recency weights 10 * 2^(-a / h);
choosing a = h * log2(10 / 9.5) makes them add up to the fixture's effective evidence 9.5.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.domain.assurance.engine import AssuranceEngine, OutcomeSnapshot
from app.domain.assurance.estimation.posterior import EstimatorParams
from app.domain.assurance.indirect.khop import KHopParams
from app.domain.assurance.policy.decision import PolicyDecision, PolicyInputs, PolicyThresholds
from app.domain.assurance.policy.decision import decide as policy_decide
from app.domain.assurance.policy.explanation import NO_HISTORY, build_explanation
from app.domain.lifecycle.ports import AssessmentRequest, AssessmentResult
from tests.scenarios.conftest import CFG, FIXTURES, assert_no_verdict

NOW = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
TH = PolicyThresholds.from_config(CFG.data)
RHO_MAX = KHopParams.from_config(CFG.section("indirect_trust_alg2")).rho_max
HALF_LIFE = EstimatorParams.from_config(CFG.section("trust_estimation_alg1")).half_life_days
LOOKBACK = int(
    CFG.section("decision_policy_alg4")["context_windows"]["resolved_disputes_lookback_months"]
)


# ----------------------------------------------------------------------------- fixture layer
def decide(sid: str) -> PolicyDecision:
    f = FIXTURES[sid]
    ctx, de = f["transaction_context"], f["direct_evidence"]
    return policy_decide(
        PolicyInputs(
            mean=de["mean"],
            lower_90=de["lower_90"],
            n_eff=de["n_eff"],
            direct_event_count=de["direct_event_count"],
            rho=f.get("indirect_evidence", {}).get("reliability_rho", 0.0),
            risk_level=f["manipulation_risk"]["level"],
            value_band=ctx["value_band"],
            open_dispute=ctx["open_dispute"],
            resolved_disputes_12m=ctx["resolved_disputes_12m"],
            verification_ok=ctx["verification_ok"],
            request_similarity=ctx["request_similarity"],
        ),
        TH,
    )


def explain(sid: str) -> str:
    """The explanation for a fixture without community paths, from the fixture's numbers."""
    f, d = FIXTURES[sid], decide(sid)
    ctx, de = f["transaction_context"], f["direct_evidence"]
    return build_explanation(
        rule=d.rule,
        state=d.state,
        mean=de["mean"],
        lower_90=de["lower_90"],
        upper_90=de["upper_90"],
        n_eff=de["n_eff"],
        direct_event_count=de["direct_event_count"],
        rho=f.get("indirect_evidence", {}).get("reliability_rho", 0.0),
        paths=[],
        resolved_disputes_12m=ctx["resolved_disputes_12m"],
        open_dispute=ctx["open_dispute"],
        is_high_value=ctx["is_high_value"],
        request_similarity=ctx["request_similarity"],
        manipulation_active=False,
        n_min=TH.n_min,
        rho_max=RHO_MAX,
        similarity_floor=TH.similarity_floor,
        lookback_months=LOOKBACK,
    )


@pytest.mark.parametrize("sid", sorted(FIXTURES))
def test_fixture_rule_state_decision_and_lifecycle(sid: str) -> None:  # TC-40 to TC-46
    want, d = FIXTURES[sid]["expected_result"], decide(sid)
    assert (d.rule, d.state, d.decision) == (want["rule_fired"], want["state"], want["decision"])
    assert ("HELD_FOR_REVIEW" if d.escalate else "ASSESSED") == want["lifecycle_state"]
    assert d.hold_reason == want.get("hold_reason")
    if "safeguards" in want:
        assert [s["code"].lower() for s in d.safeguards] == want["safeguards"]


def test_tc40_es01_newcomer_explanation() -> None:
    text = explain("ES-01")
    assert text.startswith(NO_HISTORY)  # the fixture's explanation_message
    assert FIXTURES["ES-01"]["expected_result"]["explanation_message"] == NO_HISTORY
    assert "not a negative finding" in text and "no verified loans yet" in text
    assert_no_verdict(text)


def test_tc41_es02_explanation_states_interval_and_evidence() -> None:
    text = explain("ES-02")
    assert "90% interval of 0.75 to 1.00" in text  # [0.752, 0.995]
    assert "9.5 effective outcomes" in text
    assert_no_verdict(text)


def test_tc42_es03_explanation_names_the_resolved_dispute() -> None:
    text = explain("ES-03")
    assert f"Resolved disputes in the last {LOOKBACK} months: 1." in text
    assert "Review recommended" in text
    assert_no_verdict(text)


@pytest.mark.xfail(reason="manipulation signals and their evidence arrive in Slice C", strict=True)
def test_tc43_es04_explanation_shows_both_signals() -> None:
    text = explain("ES-04")
    assert "not proof" in text and "reciprocal" in text.lower()


@pytest.mark.xfail(reason="the retaliation check arrives in Slice C (C1)", strict=True)
def test_tc44_es05_explanation_flags_the_retaliatory_review() -> None:
    assert "retaliation" in explain("ES-05").lower()


def test_tc45_es06_explanation_gives_similarity_lower_bound_and_hold() -> None:
    text = explain("ES-06")
    assert "similarity of earlier loans to this one 0.25" in text
    assert "90% interval of 0.30 to" in text
    assert "nobody is restricted without a human decision" in text
    assert_no_verdict(text)


# ----------------------------------------------------------------------------- real engine
class RawEvidence:
    """EvidenceSource with fixed outcomes and trust graph (no disputes, verification passes)."""

    def __init__(
        self,
        outcomes: list[OutcomeSnapshot],
        graph: dict[str, dict[str, float]] | None = None,
        names: dict[str, str] | None = None,
    ) -> None:
        self.outcomes, self.graph, self.names = outcomes, graph or {}, names or {}

    def borrower_outcomes(self, borrower_id: UUID) -> list[OutcomeSnapshot]:
        return self.outcomes

    def trust_graph(self) -> dict[str, dict[str, float]]:
        return self.graph

    def open_dispute(self, borrower_id: UUID) -> bool:
        return False

    def resolved_disputes_since(self, borrower_id: UUID, since: datetime) -> int:
        return 0

    def verification_ok(self, borrower_id: UUID, item_id: UUID) -> bool:
        return True

    def display_names(self, user_ids: list[str]) -> dict[str, str]:
        return {u: self.names[u] for u in user_ids if u in self.names}


U, A, B, V = uuid4(), uuid4(), uuid4(), uuid4()


def run(source: RawEvidence, band: str) -> AssessmentResult:
    engine = AssuranceEngine(source, CFG, clock=lambda: NOW)
    return engine.assess(AssessmentRequest(uuid4(), V, U, uuid4(), band, 1, CFG.config_version, 3))


def same_kind(age_days: float, band: str) -> OutcomeSnapshot:
    return OutcomeSnapshot(NOW - timedelta(days=age_days), True, "VALID", 1, band, 3.0)


def check_numbers(r: AssessmentResult, de: dict[str, Any]) -> None:
    assert r.posterior_mean == pytest.approx(de["mean"], abs=1e-3)
    assert r.ci90_low == pytest.approx(de["lower_90"], abs=1.5e-3)
    assert r.ci90_high == pytest.approx(de["upper_90"], abs=1.5e-3)
    assert r.effective_evidence == pytest.approx(de["n_eff"], abs=1e-3)


def test_tc40_es01_real_engine() -> None:
    r = run(RawEvidence([]), "LOW")
    check_numbers(r, FIXTURES["ES-01"]["direct_evidence"])
    assert (r.rule_fired, r.assurance_state) == ("R3", "INSUFFICIENT_EVIDENCE")
    assert r.explanation.startswith(NO_HISTORY)


def test_tc41_es02_real_engine_reproduces_the_interval() -> None:
    de = FIXTURES["ES-02"]["direct_evidence"]
    age = HALF_LIFE * math.log2(de["direct_event_count"] / de["n_eff"])
    r = run(RawEvidence([same_kind(age, "LOW") for _ in range(10)]), "LOW")
    check_numbers(r, de)
    assert (r.rule_fired, r.assurance_state) == ("R7", "SUFFICIENT_EVIDENCE")
    assert "90% interval of 0.75 to 1.00" in r.explanation
    assert_no_verdict(r.explanation)


def es13(with_paths: bool) -> RawEvidence:
    f = FIXTURES["ES-13"]
    ids = {"u": str(U), "a": str(A), "b": str(B), "v": str(V)}
    graph: dict[str, dict[str, float]] = {}
    for e in f["indirect_evidence"]["edge_outcomes"]:
        graph.setdefault(ids[e["source"]], {})[ids[e["target"]]] = e["weight"]
    outcomes = [same_kind(o["age_days"], "MEDIUM") for o in f["direct_evidence"]["outcomes"]]
    names = {str(A): "Neighbour A", str(B): "Neighbour B"}
    return RawEvidence(outcomes, graph if with_paths else {}, names)


def test_tc46_es13_real_engine_lists_both_paths() -> None:
    f = FIXTURES["ES-13"]
    r = run(es13(with_paths=True), "MEDIUM")
    check_numbers(r, f["direct_evidence"])
    ie = f["indirect_evidence"]
    assert r.indirect_evidence["reliability_rho"] == pytest.approx(ie["reliability_rho"], abs=1e-3)
    assert sorted(p["path_weight"] for p in r.indirect_evidence["paths"]) == pytest.approx(
        sorted(p["path_weight"] for p in ie["paths"]), abs=1e-3
    )
    assert (r.rule_fired, r.assurance_state) == ("R9", "REVIEW_RECOMMENDED")
    assert "via Neighbour A (path strength 0.37)" in r.explanation
    assert "via Neighbour B (path strength 0.35)" in r.explanation
    assert "indirect reliability 0.39" in r.explanation
    assert "Without these paths the request would be INSUFFICIENT_EVIDENCE." in r.explanation
    assert_no_verdict(r.explanation)


def test_tc47_es13_without_paths_is_insufficient_evidence() -> None:
    want = FIXTURES["ES-13"]["counterfactual_without_paths"]
    r = run(es13(with_paths=False), "MEDIUM")
    assert (r.rule_fired, r.assurance_state) == (want["rule_fired"], want["state"])
    assert "Community paths from the lender: none found." in r.explanation
