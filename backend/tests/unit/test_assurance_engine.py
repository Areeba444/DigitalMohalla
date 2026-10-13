"""The assurance engine end to end on a fake evidence source (suites 6, 7, 9; TC-74).

ES-13 is rebuilt from the fixture's raw inputs (two outcomes 20 and 45 days old, four trust edges)
and must give the oracle's numbers: alpha 2.7668, rho 0.3942, indirect estimate 0.5925, rule R9.
Without the paths it must be R6_SPARSE (the fixture's counterfactual). TC-74: a missing or
out-of-range parameter stops the engine from being built. All people and items are synthetic.
"""

import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.config.engine_config import EngineConfig, load_engine_config
from app.domain.assurance.detection.manipulation import Complaint, ReviewSnapshot
from app.domain.assurance.engine import AssuranceEngine, ConfigError, OutcomeSnapshot
from app.domain.lifecycle.ports import AssessmentRequest

NOW = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
CFG = load_engine_config()
FIXTURES = json.loads(
    (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "design"
        / "14_testing"
        / "scenario_fixtures_iteration1.json"
    ).read_text(encoding="utf-8")
)
ES13 = next(f for f in FIXTURES["fixtures"] if f["scenario_id"] == "ES-13")
U, A, B, V = uuid4(), uuid4(), uuid4(), uuid4()


class FakeSource:
    def __init__(
        self,
        outcomes: list[OutcomeSnapshot] | None = None,
        graph: dict[str, dict[str, float]] | None = None,
        open_dispute: bool = False,
        resolved: int = 0,
        verified: bool = True,
    ) -> None:
        self.outcomes = outcomes or []
        self.graph = graph or {}
        self.dispute = open_dispute
        self.resolved = resolved
        self.verified = verified
        self.since: datetime | None = None
        self.reviews: list[ReviewSnapshot] = []
        self.complaints: list[Complaint] = []
        self.names_asked: list[str] = []

    def borrower_outcomes(self, borrower_id: UUID) -> list[OutcomeSnapshot]:
        return self.outcomes

    def trust_graph(self) -> dict[str, dict[str, float]]:
        return self.graph

    def open_dispute(self, borrower_id: UUID) -> bool:
        return self.dispute

    def resolved_disputes_since(self, borrower_id: UUID, since: datetime) -> int:
        self.since = since
        return self.resolved

    def verification_ok(self, borrower_id: UUID, item_id: UUID) -> bool:
        return self.verified

    def display_names(self, user_ids: list[str]) -> dict[str, str]:
        self.names_asked = user_ids
        return {str(A): "Neighbour A", str(B): "Neighbour B"}

    def reviews_since(self, since: datetime) -> list[ReviewSnapshot]:
        return self.reviews

    def complaints_by(self, user_id: UUID, since: datetime) -> list[Complaint]:
        return self.complaints


def request(band: str = "LOW", category: int = 1, days: float = 3.0) -> AssessmentRequest:
    return AssessmentRequest(uuid4(), V, U, uuid4(), band, category, CFG.config_version, days)


def outcome(age_days: float, success: bool = True, **kw: Any) -> OutcomeSnapshot:
    fields: dict[str, Any] = {
        "status": "VALID",
        "category_id": 1,
        "value_band": "LOW",
        "duration_days": 3.0,
    }
    fields.update(kw)
    return OutcomeSnapshot(occurred_at=NOW - timedelta(days=age_days), success=success, **fields)


def es13_source(with_paths: bool = True) -> FakeSource:
    ages = [o["age_days"] for o in ES13["direct_evidence"]["outcomes"]]
    w = {
        (e["source"], e["target"]): e["weight"] for e in ES13["indirect_evidence"]["edge_outcomes"]
    }
    ids = {"u": str(U), "a": str(A), "b": str(B), "v": str(V)}
    graph: dict[str, dict[str, float]] = {}
    for (s, t), weight in w.items():
        graph.setdefault(ids[s], {})[ids[t]] = weight
    outcomes = [outcome(a, value_band="MEDIUM") for a in ages]
    return FakeSource(outcomes, graph if with_paths else {})


def engine(source: FakeSource, config: EngineConfig = CFG) -> AssuranceEngine:
    return AssuranceEngine(source, config, clock=lambda: NOW)


def test_es13_matches_the_oracle() -> None:
    source = es13_source()
    r = engine(source).assess(request("MEDIUM"))
    de, ie = ES13["direct_evidence"], ES13["indirect_evidence"]
    assert r.direct_evidence["alpha"] == pytest.approx(de["alpha"], abs=1e-3)
    assert r.posterior_mean == pytest.approx(de["mean"], abs=1e-3)
    assert r.ci90_low == pytest.approx(de["lower_90"], abs=1.5e-3)
    assert r.effective_evidence == pytest.approx(de["n_eff"], abs=1e-3)
    assert r.indirect_evidence["reliability_rho"] == pytest.approx(ie["reliability_rho"], abs=1e-3)
    assert r.indirect_evidence["estimate"] == pytest.approx(ie["estimate"], abs=1e-3)
    assert sorted(p["nodes"] for p in r.indirect_evidence["paths"]) == sorted(
        [[str(U), str(A), str(V)], [str(U), str(B), str(V)]]
    )
    want = ES13["expected_result"]
    assert (r.rule_fired, r.assurance_state, r.policy_decision) == (
        want["rule_fired"],
        want["state"],
        want["decision"],
    )
    assert [s["code"].lower() for s in r.safeguards] == want["safeguards"]
    assert "via Neighbour A" in r.explanation and "via Neighbour B" in r.explanation
    assert sorted(source.names_asked) == sorted([str(A), str(B)])  # intermediaries only


def test_es13_without_paths_is_insufficient_evidence() -> None:
    r = engine(es13_source(with_paths=False)).assess(request("MEDIUM"))
    want = ES13["counterfactual_without_paths"]
    assert (r.rule_fired, r.assurance_state) == (want["rule_fired"], want["state"])
    assert r.indirect_evidence["paths"] == []


def test_newcomer_is_insufficient_evidence_not_negative() -> None:  # ES-01
    r = engine(FakeSource()).assess(request())
    assert (r.rule_fired, r.assurance_state, r.policy_decision) == (
        "R3",
        "INSUFFICIENT_EVIDENCE",
        "REQUEST_VERIFICATION",
    )
    assert r.explanation.startswith("Insufficient verified history; lender review required.")
    assert r.hold_reason is None
    assert (r.posterior_mean, r.effective_evidence) == (0.5, 0.0)
    assert r.config_version == CFG.config_version  # TC-71 / TC-74


def test_strong_recent_history_proceeds() -> None:  # ES-02 pattern
    r = engine(FakeSource([outcome(10 * k + 1) for k in range(10)])).assess(request())
    assert (r.rule_fired, r.assurance_state) == ("R7", "SUFFICIENT_EVIDENCE")
    assert r.ci90_low is not None and r.posterior_mean is not None and r.ci90_high is not None
    assert r.ci90_low <= r.posterior_mean <= r.ci90_high  # the schema's interval check
    assert r.direct_evidence["direct_event_count"] == 10
    assert r.manipulation_level == 1 and r.manipulation_risk == 0  # no reviews at all
    assert not any(s.get("available") for s in r.manipulation_signals)


def test_flagged_outcomes_are_not_counted() -> None:  # ES-11
    flagged = [outcome(5, status="FLAGGED_FOR_REEVALUATION") for _ in range(10)]
    r = engine(FakeSource(flagged)).assess(request())
    assert r.rule_fired == "R3" and r.direct_evidence["direct_event_count"] == 0


def test_dissimilar_history_on_a_high_value_item_is_held() -> None:  # ES-06 pattern
    history = [outcome(5 * k + 1, category_id=7) for k in range(6)]
    r = engine(FakeSource(history)).assess(request("HIGH", category=2, days=14))
    assert (r.rule_fired, r.hold_reason) == ("R4", "high_value_low_confidence")
    assert r.direct_evidence["request_similarity"] < 0.5


def test_open_dispute_and_lookback_window() -> None:  # ES-08, ES-03
    source = FakeSource([outcome(3)], open_dispute=True, resolved=1)
    r = engine(source).assess(request())
    assert (r.rule_fired, r.assurance_state, r.hold_reason) == ("R1", "ACTIVE_DISPUTE", None)
    assert source.since is not None
    assert (NOW - source.since).days == 365  # 12 months from the config


def _broken(path: list[str], value: Any = None, delete: bool = False) -> EngineConfig:
    data = copy.deepcopy(CFG.data)
    node = data
    for key in path[:-1]:
        node = node[key]
    if delete:
        del node[path[-1]]
    else:
        node[path[-1]] = value
    return EngineConfig(CFG.config_version, data)


@pytest.mark.parametrize(
    "config",
    [
        _broken(["indirect_trust_alg2"], delete=True),
        _broken(["decision_policy_alg4", "thresholds", "tau_mu_mean_threshold"], delete=True),
        _broken(["trust_estimation_alg1", "recency_decay", "half_life_days"], 0),
        _broken(["trust_estimation_alg1", "credible_interval", "confidence_level"], 1.5),
        _broken(["decision_policy_alg4", "thresholds", "n_min_effective_observations"], "three"),
    ],
    ids=["no-indirect-section", "no-tau-mu", "zero-half-life", "level-above-1", "n-min-text"],
)
def test_bad_config_stops_the_engine(config: EngineConfig) -> None:  # TC-74
    with pytest.raises(ConfigError):
        engine(FakeSource(), config)


def review(rid: str, by: str, about: str, age: float, text: str, low: int = 5) -> ReviewSnapshot:
    return ReviewSnapshot(rid, by, about, low, text, NOW - timedelta(days=age), True)


def test_review_ring_is_held_for_a_moderator() -> None:  # ES-04 pattern, TC-43
    ring = [str(V), "p1", "p2", "p3"]
    text = "Excellent person, very trustworthy, highly recommended to everyone"
    source = FakeSource([outcome(10 * k + 1) for k in range(8)])
    source.reviews = [
        review(f"{a}>{b}", a, b, 5, text) for a in ring for b in ring if a != b
    ]  # everyone reviews everyone with the same text
    r = engine(source).assess(request())
    assert (r.rule_fired, r.policy_decision, r.hold_reason) == (
        "R2",
        "ESCALATE",
        "manipulation_risk",
    )
    assert r.manipulation_level == 4 and r.manipulation_corroborated
    assert r.manipulation_risk == 100
    assert "partners reviewing one another 1.00" in r.explanation
    assert "not proof of wrongdoing" in r.explanation
    assert "nobody is restricted without a human decision" in r.explanation


def test_retaliatory_review_is_set_aside_and_does_not_change_the_decision() -> None:  # ES-05, TC-44
    source = FakeSource([outcome(10 * k + 1) for k in range(10)])
    lender = str(U)
    source.complaints = [Complaint(str(V), lender, NOW - timedelta(days=20))]
    source.reviews = [review("rev-1", lender, str(V), 17, "Rude and careless borrower.", low=1)]
    r = engine(source).assess(request())
    assert (r.rule_fired, r.assurance_state, r.manipulation_level) == (
        "R7",
        "SUFFICIENT_EVIDENCE",
        1,
    )
    flagged = [s for s in r.manipulation_signals if s["name"] == "retaliation_check"]
    assert flagged == [
        {
            "name": "retaliation_check",
            "review_id": "rev-1",
            "reviewer": lender,
            "days_after_complaint": 3.0,
        }
    ]
    assert "set aside as suspected retaliation" in r.explanation
    assert "does not count against the borrower" in r.explanation
