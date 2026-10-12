"""Replay of event streams in pure Python (NFR-R-03, FR-B-09)."""

import pytest

from app.domain.lifecycle.aggregate import BorrowingTransaction, ReplayError
from app.domain.lifecycle.transition_table import TransitionTable

TABLE = TransitionTable.load()


def event(seq: int, etype: str, prev: str | None, new: str) -> dict[str, object]:
    return {"stream_seq": seq, "event_type": etype, "previous_state": prev, "new_state": new}


HAPPY = [
    event(1, "request_created", None, "REQUEST_CREATED"),
    event(2, "locality_checked", "REQUEST_CREATED", "LOCALITY_CHECKED"),
    event(3, "assessment_generated", "LOCALITY_CHECKED", "ASSESSED"),
    event(4, "request_accepted", "ASSESSED", "ACCEPTED"),
    event(5, "handover_confirmed", "ACCEPTED", "ACTIVE"),
    event(6, "return_initiated", "ACTIVE", "RETURN_INITIATED"),
    event(7, "return_confirmed", "RETURN_INITIATED", "RETURNED"),
    event(8, "transaction_closed", "RETURNED", "COMPLETED"),
]


def test_happy_path_replays_to_completed() -> None:
    agg = BorrowingTransaction.replay(HAPPY, TABLE)
    assert (agg.state, agg.version) == ("COMPLETED", 8)


def test_replay_ignores_input_order() -> None:
    assert BorrowingTransaction.replay(reversed(HAPPY), TABLE).state == "COMPLETED"


def test_gap_in_stream_is_detected() -> None:
    with pytest.raises(ReplayError, match="gap"):
        BorrowingTransaction.replay([HAPPY[0], HAPPY[2]], TABLE)


def test_wrong_previous_state_is_detected() -> None:
    bad = [HAPPY[0], event(2, "locality_checked", "ASSESSED", "LOCALITY_CHECKED")]
    with pytest.raises(ReplayError, match="expects"):
        BorrowingTransaction.replay(bad, TABLE)


def test_invalid_transition_is_detected() -> None:
    bad = [HAPPY[0], event(2, "handover_confirmed", "REQUEST_CREATED", "ACTIVE")]
    with pytest.raises(ReplayError, match="not an allowed transition"):
        BorrowingTransaction.replay(bad, TABLE)


def test_first_event_must_be_request_created() -> None:
    with pytest.raises(ReplayError):
        BorrowingTransaction.replay([event(1, "locality_checked", None, "LOCALITY_CHECKED")], TABLE)
