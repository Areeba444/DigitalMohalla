"""Suite 11 end to end: the scenarios of the synthetic `mini` dataset through the lifecycle service.

For each labelled case in data/derived/mini/labels/scenario_manifest.csv, the probe borrower sends a
new request for the probe item (same loan length, dates in the future) through BorrowingService,
as the app would: request -> locality check -> real engine (PostgresEvidenceSource, clock at the
case's as_of time) -> stored assessment -> ASSESSED or HELD_FOR_REVIEW. The test compares the
lifecycle state, the stored state and rule, the facts the explanation must state, and the
config_version on the assessment and its event (TC-71). Each case runs in a rolled-back transaction.
All data is SYNTHETIC.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import Engine, text

from app.domain.assurance.engine import AssuranceEngine
from app.domain.lifecycle.service import Actor, BorrowingService
from app.infra.db.evidence import PostgresEvidenceSource
from app.infra.eventstore.postgres import PostgresAuditLog, PostgresLifecycleStore
from tests.scenarios.conftest import CFG, assert_no_verdict, manifest

# What each case's explanation must state (Test Plan 6.3), on top of its state and rule
FACTS = {
    "ES-01": ["Insufficient verified history; lender review required.", "not a negative finding"],
    "ES-02": ["Sufficient verified evidence", "90% interval of"],
    "ES-03": ["Review recommended", "Resolved disputes in the last 12 months: 1."],
    "ES-03b": ["An open dispute must be resolved first."],
    "ES-05": ["Sufficient verified evidence"],
    "ES-06": ["High-value item: similarity", "nobody is restricted without a human decision"],
    "ES-06b": ["Sufficient verified evidence", "High-value item: similarity"],
    "ES-07": ["An open dispute must be resolved first."],
    "ES-08": ["An open dispute must be resolved first."],
    "ES-11": ["Review recommended"],
    "ES-12": ["Not enough verified evidence"],
    "ES-13": ["via ", "Without these paths the request would be INSUFFICIENT_EVIDENCE."],
    "ES-13b": ["Community paths from the lender: none found."],
}
HELD_RULES = {"R2", "R4"}  # the rules that hold a request for a moderator


def send_request(eng: Engine, case: dict[str, str], offset_days: int) -> tuple[str, dict, str]:
    """Send the probe borrower's request through the service; returns (lifecycle state,
    stored assessment, config_version on the assessment's event). Rolled back afterwards."""
    as_of = datetime.fromisoformat(case["as_of"])
    engine = AssuranceEngine(PostgresEvidenceSource(lambda: eng), CFG, clock=lambda: as_of)
    with eng.connect() as conn:
        outer = conn.begin()
        try:
            days = conn.execute(
                text(
                    "SELECT EXTRACT(EPOCH FROM upper(requested_period) - lower(requested_period)) "
                    "/ 86400.0 FROM borrowing_transaction WHERE id = :t"
                ),
                {"t": case["transaction_id"]},
            ).scalar_one()
            start = datetime.now(UTC).replace(microsecond=0) + timedelta(days=60 + offset_days)
            period = f"[{start.isoformat()},{(start + timedelta(days=float(days))).isoformat()})"
            store = PostgresLifecycleStore(conn)
            service = BorrowingService(
                store, engine, PostgresAuditLog(eng), config_version=CFG.config_version
            )
            result = service.create_request(
                Actor(UUID(case["borrower_id"])), UUID(case["item_id"]), period, "synthetic"
            )
            assessment = store.latest_assessment(result.transaction_id)
            assert assessment is not None, result
            event_version = conn.execute(
                text(
                    "SELECT config_version FROM lifecycle_event WHERE stream_id = :t "
                    "AND event_type IN ('assessment_generated', 'held_for_review')"
                ),
                {"t": result.transaction_id},
            ).scalar_one()
            return str(result.state), assessment, event_version
        finally:
            outer.rollback()


CASES = [c for c in manifest().values() if c["case_id"] in FACTS]


@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_scenario_through_the_lifecycle(mini_db: Engine, case: dict[str, str]) -> None:
    state, assessment, event_version = send_request(mini_db, case, CASES.index(case))
    rule = case["expected_rule"]
    lifecycle = case["expected_lifecycle"] or (
        "HELD_FOR_REVIEW" if rule in HELD_RULES else "ASSESSED"
    )
    assert state == lifecycle, assessment["explanation"]
    assert assessment["assurance_state"] == case["expected_state"], assessment["explanation"]
    if rule:
        assert assessment["rule_fired"] == rule, assessment["explanation"]
    for fact in FACTS[case["case_id"]]:
        assert fact in assessment["explanation"], (fact, assessment["explanation"])
    assert_no_verdict(assessment["explanation"])
    assert assessment["config_version"] == event_version == CFG.config_version  # TC-71


def test_every_target_scenario_is_in_the_dataset() -> None:  # NFR-Q-01: 7 of 7 at Mid-1
    ids = {c["case_id"] for c in CASES}
    assert {"ES-01", "ES-02", "ES-03", "ES-05", "ES-06", "ES-13", "ES-13b"} <= ids
