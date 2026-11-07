"""Computes the ES-07 to ES-12 scenario fixtures with the real engine (DA-04, Student 3, iteration 2).

    cd backend
    uv run python ../docs/design/14_testing/generate_fixtures_iteration2.py
      ->  ../docs/design/14_testing/scenario_fixtures_iteration2.json

Every number in the JSON comes from running `AssuranceEngine.assess` on the evidence written below with
the configuration in `backend/config/engine.json`; nothing is typed in by hand. The outcome each
resolved dispute adds comes from `outcomes_for_resolved_dispute` (decision D11), so the fixtures follow
the same rules as the running system. `Scenario_Specifications_ES07_ES12.md` explains each case and
works the arithmetic by hand, so the generator and the hand calculation check each other.

Plain-language note: an outcome of the same kind as the request (same category, value band and
duration) has similarity 1, so its weight is only the recency weight 2^(-age / 180). alpha = 1 plus
the weights of on-time returns, beta = 1 plus the weights of late or missing ones. All data is
SYNTHETIC: no real people, items or places.
"""

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid5

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.normpath(os.path.join(HERE, "..", "..", "..", "backend"))
sys.path.insert(0, BACKEND)

from app.config.engine_config import load_engine_config  # noqa: E402
from app.domain.assurance.detection.manipulation import Complaint, ReviewSnapshot  # noqa: E402
from app.domain.assurance.engine import AssuranceEngine, OutcomeSnapshot  # noqa: E402
from app.domain.assurance.estimation.outcomes import (  # noqa: E402
    ResolvedDispute,
    outcomes_for_resolved_dispute,
)
from app.domain.lifecycle.ports import AssessmentRequest, AssessmentResult  # noqa: E402

NOW = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)  # same "as of" as the iteration 1 fixtures
NS = UUID("6f1d3c2e-0000-4000-8000-000000000a04")  # fixed namespace: ids are reproducible
CATEGORY, DURATION = 1, 3.0


def uid(name: str) -> UUID:
    return uuid5(NS, name)


@dataclass
class Evidence:
    """EvidenceSource for one scenario: fixed outcomes and context, no reviews, no trust paths."""

    outcomes: list[OutcomeSnapshot]
    open: bool = False
    resolved: int = 0
    verified: bool = True
    graph: dict[str, dict[str, float]] = field(default_factory=dict)

    def borrower_outcomes(self, borrower_id: UUID) -> list[OutcomeSnapshot]:
        return self.outcomes

    def trust_graph(self) -> dict[str, dict[str, float]]:
        return self.graph

    def open_dispute(self, borrower_id: UUID) -> bool:
        return self.open

    def resolved_disputes_since(self, borrower_id: UUID, since: datetime) -> int:
        return self.resolved

    def verification_ok(self, borrower_id: UUID, item_id: UUID) -> bool:
        return self.verified

    def display_names(self, user_ids: list[str]) -> dict[str, str]:
        return {}

    def reviews_since(self, since: datetime) -> list[ReviewSnapshot]:
        return []

    def complaints_by(self, user_id: UUID, since: datetime) -> list[Complaint]:
        return []


def loan(age_days: float, on_time: bool, band: str, status: str = "VALID") -> OutcomeSnapshot:
    return OutcomeSnapshot(NOW - timedelta(days=age_days), on_time, status, CATEGORY, band, DURATION)


def dispute_outcome(age_days: float, band: str, d: ResolvedDispute) -> list[OutcomeSnapshot]:
    """The ON_TIME_RETURN outcome (if any) a resolved dispute adds for the borrower (D11)."""
    return [
        loan(age_days, r.success, band)
        for r in outcomes_for_resolved_dispute(d)
        if r.subject_role == "BORROWER" and r.metric == "ON_TIME_RETURN"
    ]


CFG = load_engine_config()


def assess(sid: str, ev: Evidence, band: str) -> AssessmentResult:
    engine = AssuranceEngine(ev, CFG, clock=lambda: NOW)
    return engine.assess(
        AssessmentRequest(uid(sid + "/txn"), uid(sid + "/borrower"), uid(sid + "/lender"),
                          uid(sid + "/item"), band, CATEGORY, CFG.config_version, DURATION)
    )


def summary(r: AssessmentResult) -> dict[str, Any]:
    de = r.direct_evidence
    return {
        "direct_evidence": {k: (round(de[k], 4) if isinstance(de[k], float) else de[k])
                            for k in ("alpha", "beta", "mean", "lower_90", "upper_90", "n_eff",
                                      "direct_event_count", "request_similarity")},
        "manipulation_level": r.manipulation_level,
        "rule_fired": r.rule_fired,
        "state": r.assurance_state,
        "decision": r.policy_decision,
        "hold_reason": r.hold_reason,
        "lifecycle_state": "HELD_FOR_REVIEW" if r.hold_reason else "ASSESSED",
        "safeguards": [s["code"].lower() for s in r.safeguards],
        "explanation": r.explanation,
    }


def history(ages: list[float], band: str) -> list[OutcomeSnapshot]:
    return [loan(a, True, band) for a in ages]


def build() -> dict[str, Any]:
    out: dict[str, Any] = {}
    eight = [15, 30, 45, 60, 75, 90, 105, 120]

    # ES-07: conflicting condition reports at return, dispute raised from RETURN_INITIATED.
    h7 = history(eight, "LOW")
    out["ES-07"] = {
        "name": "Conflicting condition reports at return",
        "evidence": {"history_ages_days": eight, "all_on_time": True, "value_band": "LOW"},
        "steps": {
            "without_dispute": summary(assess("ES-07a", Evidence(h7), "LOW")),
            "while_dispute_open": summary(assess("ES-07b", Evidence(h7, open=True), "LOW")),
            "after_resolution": summary(assess("ES-07c", Evidence(
                h7 + dispute_outcome(2, "LOW", ResolvedDispute("RETURN_INITIATED", "CONDITION_MISMATCH",
                                                                "borrower", returned_on_time=True)),
                resolved=1), "LOW")),
        },
        "resolution": {"stage": "RETURN_INITIATED", "reason": "CONDITION_MISMATCH", "at_fault": "borrower",
                       "possession": "RETURNED", "returned_on_time": True, "resolved_days_ago": 2},
    }

    # ES-08: failure to return, automatic dispute (NON_RETURN) from ACTIVE after the overdue limit.
    six = [30, 60, 90, 120, 150, 180]
    h8 = history(six, "MEDIUM")
    out["ES-08"] = {
        "name": "Failure to return",
        "evidence": {"history_ages_days": six, "all_on_time": True, "value_band": "MEDIUM"},
        "steps": {
            "while_dispute_open": summary(assess("ES-08b", Evidence(h8, open=True), "MEDIUM")),
            "after_resolution": summary(assess("ES-08c", Evidence(
                h8 + dispute_outcome(2, "MEDIUM", ResolvedDispute("ACTIVE", "NON_RETURN", "borrower")),
                resolved=1), "MEDIUM")),
        },
        "resolution": {"stage": "ACTIVE", "reason": "NON_RETURN", "at_fault": "borrower",
                       "possession": "LOST", "resolved_days_ago": 2},
    }

    # ES-09: location mismatch. CONFLICTING stored result -> held before any assessment; cleared -> engine.
    four = [10, 50, 90, 130]
    out["ES-09"] = {
        "name": "Location mismatch (stored locality result CONFLICTING)",
        "evidence": {"history_ages_days": four, "all_on_time": True, "value_band": "LOW"},
        "steps": {
            "at_request": {"lifecycle_state": "HELD_FOR_REVIEW", "hold_reason": "locality_conflict",
                           "state": None, "note": "the engine does not run before the locality hold is cleared"},
            "after_hold_cleared": summary(assess("ES-09c", Evidence(history(four, "LOW")), "LOW")),
        },
    }

    # ES-10: location permission refused at join (stored INCONCLUSIVE), newcomer.
    out["ES-10"] = {
        "name": "Location-permission refusal (stored locality result INCONCLUSIVE), no history",
        "evidence": {"history_ages_days": [], "value_band": "LOW"},
        "steps": {
            "at_request": {"lifecycle_state": "HELD_FOR_REVIEW", "hold_reason": "locality_inconclusive",
                           "state": None, "note": "the engine does not run before the locality hold is cleared"},
            "after_hold_cleared": summary(assess("ES-10c", Evidence([]), "LOW")),
        },
    }

    # ES-11: moderator reversal. A dispute decided against the borrower is reversed; its outcome is flagged.
    five = [20, 40, 60, 80, 100]
    failure = dispute_outcome(30, "LOW", ResolvedDispute("ACTIVE", "NON_RETURN", "borrower"))
    flagged = [loan(30, o.success, "LOW", status="FLAGGED_FOR_REEVALUATION") for o in failure]
    out["ES-11"] = {
        "name": "Moderator reversal",
        "evidence": {"history_ages_days": five, "all_on_time": True, "value_band": "LOW",
                     "disputed_loan": {"stage": "ACTIVE", "reason": "NON_RETURN", "first_finding": "borrower",
                                       "decided_days_ago": 30}},
        "steps": {
            "before_reversal": summary(assess("ES-11a", Evidence(history(five, "LOW") + failure, resolved=1), "LOW")),
            "after_reversal": summary(assess("ES-11b", Evidence(history(five, "LOW") + flagged, resolved=1), "LOW")),
            "after_reversal_if_reversed_disputes_not_counted": summary(
                assess("ES-11c", Evidence(history(five, "LOW") + flagged, resolved=0), "LOW")),
        },
    }

    # ES-12: sparse or old history.
    old = [540, 576, 612, 648, 684, 720]
    out["ES-12"] = {
        "name": "Old history (six on-time loans, 18 to 24 months ago)",
        "evidence": {"history_ages_days": old, "all_on_time": True, "value_band": "LOW"},
        "steps": {"at_request": summary(assess("ES-12", Evidence(history(old, "LOW")), "LOW"))},
    }
    out["ES-12b"] = {
        "name": "Sparse history (two recent on-time loans)",
        "evidence": {"history_ages_days": [10, 20], "all_on_time": True, "value_band": "LOW"},
        "steps": {"at_request": summary(assess("ES-12b", Evidence(history([10, 20], "LOW")), "LOW"))},
    }
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    doc = {
        "metadata": {
            "suite_name": "Digital Mohalla iteration 2 scenario fixtures, ES-07 to ES-12 (SYNTHETIC)",
            "config_version": CFG.config_version,
            "as_of": NOW.isoformat(),
            "generated_by": "14_testing/generate_fixtures_iteration2.py (real engine, no hand-typed numbers)",
            "spec": "14_testing/Scenario_Specifications_ES07_ES12.md",
            "owners": "Student 3 (DA-04); review: Student 2",
        },
        "fixtures": build(),
    }
    path = os.path.join(HERE, "scenario_fixtures_iteration2.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    for sid, f in doc["fixtures"].items():
        for step, r in f["steps"].items():
            de = r.get("direct_evidence", {})
            print(f"{sid:7} {step:48} {r.get('rule_fired') or '-':10} {r.get('state') or '-':22} "
                  f"{r['lifecycle_state']:16} a={de.get('alpha', '-')} b={de.get('beta', '-')} "
                  f"m={de.get('mean', '-')} ci=[{de.get('lower_90', '-')}, {de.get('upper_90', '-')}] "
                  f"n={de.get('n_eff', '-')} k={de.get('direct_event_count', '-')}")
    print(path)
