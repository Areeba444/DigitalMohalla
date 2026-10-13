"""Decision policy (Algorithm 4, test suite 9): fixture rules, the oracle, and the safety properties.

TC-29 to TC-33 run the policy unit fixtures PU-01 to PU-06 and the scenario fixtures ES-01 to ES-06
and ES-13 (inputs and expected outputs from scenario_fixtures_iteration1.json). The Hypothesis tests
compare `decide` with the design oracle (verify_fixtures.decide) on random inputs and check TC-34
(indirect evidence alone is never SUFFICIENT_EVIDENCE) and TC-39 (one well-formed decision for every
input; restrictions are always holds for a human). All inputs are synthetic.
"""

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.config.engine_config import load_engine_config
from app.domain.assurance.policy.decision import (
    RULES,
    PolicyInputs,
    PolicyThresholds,
    decide,
    safeguards_for,
)

TESTING = Path(__file__).resolve().parents[3] / "docs" / "design" / "14_testing"
FIXTURES = json.loads((TESTING / "scenario_fixtures_iteration1.json").read_text(encoding="utf-8"))
CFG = load_engine_config()
TH = PolicyThresholds.from_config(CFG.data)
STATES = {"SUFFICIENT_EVIDENCE", "REVIEW_RECOMMENDED", "INSUFFICIENT_EVIDENCE", "ACTIVE_DISPUTE"}


def _oracle() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_fixtures", TESTING / "verify_fixtures.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ORACLE = _oracle()


def inputs_from(f: dict[str, Any]) -> PolicyInputs:
    ctx, de = f["transaction_context"], f["direct_evidence"]
    return PolicyInputs(
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
    )


ALL = FIXTURES["fixtures"] + FIXTURES["policy_unit_fixtures"]


@pytest.mark.parametrize("fixture", ALL, ids=[f["scenario_id"] for f in ALL])
def test_fixture_gives_the_expected_rule_state_and_decision(fixture: dict[str, Any]) -> None:
    want = fixture["expected_result"]
    d = decide(inputs_from(fixture), TH)
    assert d.rule == want["rule_fired"]
    assert d.decision == want["decision"]
    assert d.state == want["state"]
    assert d.escalate == want["escalate"]
    assert d.hold_reason == want.get("hold_reason")
    if "safeguards" in want:
        assert [s["code"].lower() for s in d.safeguards] == want["safeguards"]


def test_es13_without_the_paths_is_insufficient_evidence() -> None:
    es13 = next(f for f in FIXTURES["fixtures"] if f["scenario_id"] == "ES-13")
    x = inputs_from(es13)
    d = decide(PolicyInputs(**{**x.__dict__, "rho": 0.0}), TH)
    assert (d.rule, d.state) == ("R6_SPARSE", es13["counterfactual_without_paths"]["state"])


def test_open_dispute_comes_before_everything_and_is_not_a_hold() -> None:  # TC-29, D12
    x = PolicyInputs(0.95, 0.85, 12.0, 12, 0.6, 4, "HIGH", True, 2, False, 0.1)
    d = decide(x, TH)
    assert (d.rule, d.state, d.escalate) == ("R1", "ACTIVE_DISPUTE", False)


def test_rules_table_matches_the_schema_constraint() -> None:  # TC-35 (DB side in integration)
    assert set(RULES) == {
        "R1", "R2", "R3", "R4", "R5", "R6_DISPUTE", "R6_SPARSE", "R7", "R8", "R9"
    }  # fmt: skip
    held = {r for r, (_, _, hold) in RULES.items() if hold}
    assert held == {"R2", "R4"}


def test_safeguard_codes_are_upper_case_with_labels() -> None:
    for rule in RULES:
        for band in ("LOW", "MEDIUM", "HIGH"):
            for s in safeguards_for(rule, band):
                assert s["code"] == s["code"].upper() and s["label"]


def test_risk_level_outside_1_to_4_is_refused() -> None:
    with pytest.raises(ValueError):
        decide(PolicyInputs(0.5, 0.1, 0.0, 0, 0.0, 5, "LOW", False, 0, True, 1.0), TH)


unit = st.floats(0.0, 1.0, allow_nan=False)


@st.composite
def inputs(draw: st.DrawFn) -> PolicyInputs:
    """Consistent inputs (lower bound <= mean, n_eff <= outcomes, since weights are at most 1),
    biased so every rule is reached: half the draws have strong direct evidence, and disputes and
    high risk are less common than quiet requests."""
    if draw(st.booleans()):  # strong direct evidence
        count = draw(st.integers(3, 30))
        mean = draw(st.floats(0.75, 1.0))
        lower = draw(st.floats(0.55, mean))  # around tau_L = 0.60
        n_eff = count * draw(st.floats(0.5, 1.0))
    else:
        count = draw(st.integers(0, 30))
        mean = draw(unit)
        lower = mean * draw(unit)
        n_eff = count * draw(unit)
    return PolicyInputs(
        mean=mean,
        lower_90=lower,
        n_eff=n_eff,
        direct_event_count=count,
        rho=draw(st.floats(0.0, 0.6, allow_nan=False)),
        risk_level=draw(st.sampled_from([1, 1, 1, 2, 3, 4])),
        value_band=draw(st.sampled_from(["LOW", "MEDIUM", "HIGH"])),
        open_dispute=draw(st.sampled_from([False, False, False, True])),
        resolved_disputes_12m=draw(st.sampled_from([0, 0, 0, 1, 2])),
        verification_ok=draw(st.sampled_from([True, True, False])),
        request_similarity=draw(unit),
    )


@settings(max_examples=500, deadline=None)
@given(inputs())
def test_decide_agrees_with_the_design_oracle(x: PolicyInputs) -> None:
    direct = {"mean": x.mean, "lower_90": x.lower_90, "n_eff": x.n_eff}
    direct["direct_event_count"] = x.direct_event_count
    ctx = {
        "open_dispute": x.open_dispute,
        "is_high_value": x.value_band == "HIGH",
        "medium_value": x.value_band == "MEDIUM",
        "request_similarity": x.request_similarity,
        "resolved_disputes_12m": x.resolved_disputes_12m,
        "verification_ok": x.verification_ok,
    }
    th = CFG.section("decision_policy_alg4")["thresholds"]
    assert decide(x, TH).rule == ORACLE.decide(
        direct, x.rho, x.risk_level, ctx, th, TH.similarity_floor
    )


@settings(max_examples=500, deadline=None)
@given(inputs())
def test_indirect_evidence_alone_is_never_sufficient(x: PolicyInputs) -> None:  # TC-34
    if x.n_eff < TH.n_min:
        assert decide(x, TH).state != "SUFFICIENT_EVIDENCE"


@settings(max_examples=500, deadline=None)
@given(inputs())
def test_every_input_gets_one_well_formed_decision(x: PolicyInputs) -> None:  # TC-39
    d = decide(x, TH)
    assert d.state in STATES
    assert (d.decision, d.state, d.hold_reason) == RULES[d.rule]
    assert d.escalate == (d.hold_reason is not None)
    if d.decision == "RESTRICT_HIGH_VALUE":  # no restriction without human review
        assert d.escalate and x.value_band == "HIGH"
    if x.direct_event_count == 0 and x.rho < TH.rho_sup and not x.open_dispute and x.risk_level < 4:
        # zero history is INSUFFICIENT_EVIDENCE, not a negative finding, even for a high-value item
        assert (d.rule, d.state) == ("R3", "INSUFFICIENT_EVIDENCE")
