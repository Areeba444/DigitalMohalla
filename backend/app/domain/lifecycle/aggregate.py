"""BorrowingTransaction aggregate: state changes only by applying an event; replay rebuilds it.

Pure Python, no I/O (A8 layer rules). `replay(events)` is what the replay test compares with the
state the database stored (NFR-R-03, FR-B-09).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from app.domain.lifecycle.transition_table import TransitionTable


class ReplayError(Exception):
    """The event stream is not a legal history (gap, wrong previous_state, invalid transition)."""


@dataclass
class BorrowingTransaction:
    state: str | None = None
    version: int = 0

    def apply(self, event: Mapping[str, Any], table: TransitionTable) -> None:
        seq = event["stream_seq"]
        if seq != self.version + 1:
            raise ReplayError(f"gap before stream_seq {seq} (expected {self.version + 1})")
        if event["previous_state"] != self.state:
            raise ReplayError(
                f"event {seq} expects {event['previous_state']} but replay is in {self.state}"
            )
        if seq == 1:
            if event["event_type"] != "request_created" or event["new_state"] != "REQUEST_CREATED":
                raise ReplayError("the first event must be request_created")
        elif not table.is_valid(event["previous_state"], event["event_type"], event["new_state"]):
            raise ReplayError(
                f"event {seq}: {event['previous_state']} --{event['event_type']}--> "
                f"{event['new_state']} is not an allowed transition"
            )
        self.state = event["new_state"]
        self.version = seq

    @classmethod
    def replay(
        cls, events: Iterable[Mapping[str, Any]], table: TransitionTable
    ) -> "BorrowingTransaction":
        aggregate = cls()
        for event in sorted(events, key=lambda e: e["stream_seq"]):
            aggregate.apply(event, table)
        return aggregate
