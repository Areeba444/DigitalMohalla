"""Suite 11 on the iteration 2 fixtures: ES-07 to ES-12 (plan item A6, M6; TC-110 to TC-116).

The fixtures (docs/design/14_testing/scenario_fixtures_iteration2.json) were produced by the engine
at config 1.3.0 and checked by hand in Scenario_Specifications_ES07_ES12.md. Here each step is rebuilt
from its raw evidence (ages of past on-time loans, the disputed loan, whether a dispute is open or
resolved) and sent through the real engine at the current config; the fixture's numbers, rule, state,
decision and the facts its explanation must show are compared. The two locality steps (ES-09 and
ES-10 at request) are lifecycle behaviour, not engine behaviour: they are checked on the fixture and
in the database layer (TestDatabaseLifecycle in test_dataset_scenarios.py). All data is SYNTHETIC.

Plain-language note: a past loan of age a has weight 2^(-a/180). The disputed loan in ES-08 and
ES-11 is a failed on-time return, which adds to beta; a decision under re-evaluation is flagged and
not counted at all (ES-11 after the reversal).
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.domain.assurance.engine import AssuranceEngine, OutcomeSnapshot
from app.domain.lifecycle.ports import AssessmentRequest, AssessmentResult
from tests.scenarios.conftest import CFG, ROOT, assert_no_verdict
from tests.scenarios.test_fixture_scenarios import RawEvidence

FIXTURE_FILE = ROOT / "docs" / "design" / "14_testing" / "scenario_fixtures_iteration2.json"
F2: dict[str, Any] = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))["fixtures"]
NOW = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)

# step -> (extra outcome as (age_days, success, status) or None, open dispute, resolved disputes)
STEPS: dict[tuple[str, str], tuple[tuple[float, bool, str] | None, bool, int]] = {
    ("ES-07", "without_dispute"): (None, False, 0),
    ("ES-07", "while_dispute_open"): (None, True, 0),
    ("ES-07", "after_resolution"): ((2, True, "VALID"), False, 1),
    ("ES-08", "while_dispute_open"): (None, True, 0),
    ("ES-08", "after_resolution"): ((2, False, "VALID"), False, 1),
    ("ES-09", "after_hold_cleared"): (None, False, 0),
    ("ES-10", "after_hold_cleared"): (None, False, 0),
    ("ES-11", "before_reversal"): ((30, False, "VALID"), False, 1),
    ("ES-11", "after_reversal"): ((30, False, "FLAGGED_FOR_REEVALUATION"), False, 1),
    ("ES-12", "at_request"): (None, False, 0),
    ("ES-12b", "at_request"): (None, False, 0),
}


class Source(RawEvidence):
    def __init__(self, outcomes: list[OutcomeSnapshot], open_dispute: bool, resolved: int) -> None:
        super().__init__(outcomes)
        self.is_open, self.resolved = open_dispute, resolved

    def open_dispute(self, borrower_id: object) -> bool:
        return self.is_open

    def resolved_disputes_since(self, borrower_id: object, since: datetime) -> int:
        return self.resolved


def assess(sid: str, step: str) -> AssessmentResult:
    extra, is_open, resolved = STEPS[(sid, step)]
    band = F2[sid]["evidence"]["value_band"]
    rows = [
        OutcomeSnapshot(NOW - timedelta(days=a), True, "VALID", 1, band, 3.0)
        for a in F2[sid]["evidence"]["history_ages_days"]
    ]
    if extra:
        age, ok, status = extra
        rows.append(OutcomeSnapshot(NOW - timedelta(days=age), ok, status, 1, band, 3.0))
    engine = AssuranceEngine(Source(rows, is_open, resolved), CFG, clock=lambda: NOW)
    return engine.assess(
        AssessmentRequest(uuid4(), uuid4(), uuid4(), uuid4(), band, 1, CFG.config_version, 3)
    )


@pytest.mark.parametrize(("sid", "step"), sorted(STEPS))
def test_engine_reproduces_the_fixture_numbers_rule_state_and_decision(sid: str, step: str) -> None:
    want = F2[sid]["steps"][step]
    de, r = want["direct_evidence"], assess(sid, step)
    assert r.posterior_mean == pytest.approx(de["mean"], abs=1e-3)
    assert r.ci90_low == pytest.approx(de["lower_90"], abs=1.5e-3)
    assert r.ci90_high == pytest.approx(de["upper_90"], abs=1.5e-3)
    assert r.effective_evidence == pytest.approx(de["n_eff"], abs=1e-3)
    assert (r.rule_fired, r.assurance_state) == (want["rule_fired"], want["state"])
    assert r.policy_decision == want["decision"]
    assert_no_verdict(r.explanation)


@pytest.mark.parametrize(("sid", "step"), sorted(STEPS))
def test_explanation_matches_the_fixture(sid: str, step: str) -> None:
    assert assess(sid, step).explanation == F2[sid]["steps"][step]["explanation"]


def test_tc110_tc111_es07_an_open_dispute_wins_over_strong_evidence_and_is_counted_afterwards() -> (
    None
):
    open_ = assess("ES-07", "while_dispute_open")
    assert (
        open_.rule_fired == "R1" and "An open dispute must be resolved first." in open_.explanation
    )
    after = assess("ES-07", "after_resolution")
    assert "Resolved disputes in the last 12 months: 1." in after.explanation
    assert after.assurance_state == "REVIEW_RECOMMENDED"


def test_tc112_es08_a_lost_item_lowers_the_estimate_and_keeps_review_recommended() -> None:
    before, after = assess("ES-08", "while_dispute_open"), assess("ES-08", "after_resolution")
    assert after.posterior_mean < before.posterior_mean  # 0.836 -> 0.718
    assert after.assurance_state == "REVIEW_RECOMMENDED"
    assert {x["code"].lower() for x in after.safeguards} == {
        "condition_photos_checklist",
        "deposit_record",
        "explicit_return_reminder",
    }


def test_tc113_tc114_es09_and_es10_locality_holds_stop_the_engine_until_cleared() -> None:
    for sid, reason in (("ES-09", "locality_conflict"), ("ES-10", "locality_inconclusive")):
        held = F2[sid]["steps"]["at_request"]
        assert (held["lifecycle_state"], held["hold_reason"], held["state"]) == (
            "HELD_FOR_REVIEW",
            reason,
            None,
        )
    assert assess("ES-09", "after_hold_cleared").assurance_state == "REVIEW_RECOMMENDED"
    es10 = assess("ES-10", "after_hold_cleared")
    assert es10.assurance_state == "INSUFFICIENT_EVIDENCE"
    assert "not a negative finding" in es10.explanation  # zero history is an absence of evidence


def test_tc115_es11_a_reversed_decision_is_no_longer_counted() -> None:
    before, after = assess("ES-11", "before_reversal"), assess("ES-11", "after_reversal")
    assert after.posterior_mean > before.posterior_mean  # 0.725 -> 0.833: the failure is set aside
    assert (
        after.rule_fired == "R6_DISPUTE"
    )  # a reversed case still counts as a resolved dispute (Q2)


@pytest.mark.parametrize("sid", ["ES-12", "ES-12b"])
def test_tc116_es12_old_or_few_loans_are_insufficient_not_negative(sid: str) -> None:
    r = assess(sid, "at_request")
    assert r.assurance_state == "INSUFFICIENT_EVIDENCE" and r.rule_fired == "R6_SPARSE"
    assert "Not enough verified evidence" in r.explanation
