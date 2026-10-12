"""The borrowing lifecycle's transition table (design step A3), as plain data with no I/O.

`transition_leaves.csv` is generated from the design's single source of truth
(docs/design/_tools/lifecycle_model.py, `leaf_rows()`): 34 valid (state, event, next state) rows.
The same table is enforced by the database (`allowed_transition`); an integration test checks that the
two copies are identical, so they cannot drift apart. This module lets the service reject an invalid
move early, and lets suite 1 (transition matrix) run without a database.

Plain-language note: a *transition* is a legal move such as "ASSESSED --request_accepted--> ACCEPTED",
allowed only for certain actors. Any (state, event) pair that is not in the table is invalid.
"""

import csv
from dataclasses import dataclass
from pathlib import Path

CSV_PATH = Path(__file__).with_name("transition_leaves.csv")

# Pending states in the lifecycle (Use Cases section 2); a request in any of them can be cancelled
PENDING_STATES = frozenset({"REQUEST_CREATED", "LOCALITY_CHECKED", "HELD_FOR_REVIEW", "ASSESSED"})
TERMINAL_STATES = frozenset({"COMPLETED", "DECLINED", "CANCELLED", "EXPIRED", "NO_SHOW"})


@dataclass(frozen=True)
class Transition:
    from_state: str
    event_type: str
    to_state: str
    allowed_roles: frozenset[str]
    ref: str
    iteration: int


class TransitionTable:
    def __init__(self, transitions: list[Transition]) -> None:
        self.transitions = transitions
        self._by_key: dict[tuple[str, str], list[Transition]] = {}
        for t in transitions:
            self._by_key.setdefault((t.from_state, t.event_type), []).append(t)

    @classmethod
    def load(cls, path: Path = CSV_PATH) -> "TransitionTable":
        with path.open(encoding="utf-8", newline="") as f:
            rows = [
                Transition(
                    r["from_state"],
                    r["event_type"],
                    r["to_state"],
                    frozenset(r["allowed_roles"].split("|")),
                    r["ref"],
                    int(r["iteration"]),
                )
                for r in csv.DictReader(f)
            ]
        return cls(rows)

    def lookup(self, state: str, event_type: str) -> list[Transition]:
        """All valid transitions for this (state, event) pair; empty means the pair is invalid."""
        return list(self._by_key.get((state, event_type), []))

    def is_valid(self, state: str, event_type: str, to_state: str) -> bool:
        return any(t.to_state == to_state for t in self.lookup(state, event_type))

    def next_state(self, state: str, event_type: str) -> str | None:
        """The single next state, or None when the pair is invalid or ambiguous."""
        options = {t.to_state for t in self.lookup(state, event_type)}
        return next(iter(options)) if len(options) == 1 else None
