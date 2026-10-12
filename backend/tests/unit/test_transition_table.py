"""Test suite 1 (transition matrix), domain half: every (state, event) pair of the design's oracle.

The oracle is docs/design/14_testing/transition_test_matrix.csv, generated from the same lifecycle
model as the table under test. 294 pairs: 31 valid, 263 must be rejected (FR-B-08, NFR-R-02).
"""

import csv
from pathlib import Path

import pytest

from app.domain.lifecycle.transition_table import TransitionTable

MATRIX = Path(__file__).resolve().parents[3] / "docs/design/14_testing/transition_test_matrix.csv"
TABLE = TransitionTable.load()


def matrix_rows() -> list[dict[str, str]]:
    with MATRIX.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_matrix_has_expected_shape() -> None:
    rows = matrix_rows()
    assert len(rows) == 294
    assert sum(r["expected"] == "VALID" for r in rows) == 31
    assert len(TABLE.transitions) == 34


@pytest.mark.parametrize("row", matrix_rows(), ids=lambda r: r["case"])
def test_pair_matches_oracle(row: dict[str, str]) -> None:
    found = TABLE.lookup(row["state"], row["event_type"])
    if row["expected"] == "VALID":
        assert {t.to_state for t in found} == set(row["next_states"].split("|"))
        roles = set().union(*(t.allowed_roles for t in found))
        assert roles == set(row["actors"].split("|"))
    else:
        assert found == [], f"{row['state']} --{row['event_type']}--> should be rejected"


def test_next_state_is_none_for_invalid_and_ambiguous_pairs() -> None:
    assert TABLE.next_state("COMPLETED", "request_accepted") is None  # invalid (TC-02)
    assert (
        TABLE.next_state("HELD_FOR_REVIEW", "hold_cleared") is None
    )  # ambiguous: needs hold reason
    assert TABLE.next_state("ASSESSED", "request_accepted") == "ACCEPTED"


def test_disputes_cannot_start_from_returned() -> None:  # decision D4, TC-05
    assert TABLE.lookup("RETURNED", "dispute_opened") == []
