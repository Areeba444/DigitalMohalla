"""Trust-edge weights (ADR-0006, Test Plan suite 7: TC-27 edge weights)."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.config.engine_config import load_engine_config
from app.domain.assurance.estimation.posterior import EstimatorParams, WeightedOutcome
from app.domain.assurance.indirect.edges import ConfirmedOutcome, build_edges, edge_weight

NOW = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
P = EstimatorParams.from_config(load_engine_config().section("trust_estimation_alg1"))
FIXTURES = (
    Path(__file__).resolve().parents[3] / "docs/design/14_testing/scenario_fixtures_iteration1.json"
)


def today(success: bool = True) -> WeightedOutcome:
    return WeightedOutcome(NOW, success)


def seen(
    src: str, dst: str, days: float, ok: bool = True, status: str = "VALID"
) -> ConfirmedOutcome:
    return ConfirmedOutcome(
        src, dst, "BORROWER", "ON_TIME_RETURN", ok, NOW - timedelta(days=days), status
    )


def test_adr_0006_worked_values() -> None:
    assert edge_weight([today()], P, NOW) == pytest.approx(2 / 3)
    assert edge_weight([today()] * 5, P, NOW) == pytest.approx(6 / 7)  # "five give 0.86"
    assert edge_weight([today(False)], P, NOW) == pytest.approx(1 / 3)


def test_similarity_is_never_applied_to_edges() -> None:
    assert edge_weight([WeightedOutcome(NOW, True, 0.5)], P, NOW) == pytest.approx(2 / 3)


def test_tc27_es13_edge_weights_from_their_outcomes() -> None:
    fx = {f["scenario_id"]: f for f in json.loads(FIXTURES.read_text(encoding="utf-8"))["fixtures"]}
    for e in fx["ES-13"]["indirect_evidence"]["edge_outcomes"]:
        got = edge_weight(
            [
                WeightedOutcome(NOW - timedelta(days=o["age_days"]), o["success"])
                for o in e["outcomes"]
            ],
            P,
            NOW,
        )
        assert got == pytest.approx(e["weight"], abs=5e-4), (e["source"], e["target"])


def test_edges_group_by_observer_subject_role_and_metric() -> None:
    edges = build_edges(
        [
            seen("u", "a", 30),
            seen("u", "a", 60),
            seen("a", "v", 20),
            seen("u", "a", 10, status="FLAGGED_FOR_REEVALUATION"),
        ],
        P,
        NOW,
    )
    by_key = {(e.source_id, e.target_id): e for e in edges}
    assert set(by_key) == {("u", "a"), ("a", "v")}
    assert by_key[("u", "a")].evidence_count == 2  # the flagged outcome is not counted
    assert all(0 < e.weight <= 1 for e in edges)
    assert by_key[("u", "a")].weight == round(by_key[("u", "a")].weight, 3)


def test_no_outcome_no_edge_and_only_flagged_outcomes_no_edge() -> None:
    assert build_edges([], P, NOW) == []
    assert build_edges([seen("u", "a", 5, status="FLAGGED_FOR_REEVALUATION")], P, NOW) == []


def test_a_self_edge_is_refused() -> None:
    with pytest.raises(ValueError):
        build_edges([seen("u", "u", 1)], P, NOW)
