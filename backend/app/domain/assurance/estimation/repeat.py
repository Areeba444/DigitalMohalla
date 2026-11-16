"""Pair-repeat discount against trivial exchanges (Algorithm 1 change, DA-15 section 2; A4).

The threat model lists many short, low-value loans between the same few accounts as a way to
manufacture reputation. Each outcome's weight is multiplied by `factor ** m`, where m is the number
of earlier VALID outcomes of the same subject (role and metric) observed by the same counterpart in
the `window_days` before it:

    w_i := recency(age_i) * max(similarity_floor, sim_i) * factor ^ m_i

Worked example (factor 0.5, window 30 days): five on-time loans with one neighbour within 20 days
weigh 1 + 0.5 + 0.25 + 0.125 + 0.0625 = 1.9375 effective outcomes, not 5, so they cannot reach
n_min = 3 alone; five loans with five different neighbours still weigh 5. Honest repeat borrowing
still counts, it is only bounded. One pass over the outcomes in time order with a queue per
observer: O(n) for n outcomes (after sorting).
"""

from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class RepeatParams:
    window_days: float
    factor: float

    @classmethod
    def from_config(cls, section: Mapping[str, Any] | None) -> "RepeatParams | None":
        """None when the config has no discount (iteration 1 configs): every multiplier is 1."""
        if not section:
            return None
        return cls(float(section["window_days"]), float(section["factor"]))


def repeat_multipliers(
    outcomes: Sequence[tuple[datetime, str | None]], p: RepeatParams | None
) -> list[float]:
    """`factor ** m_i` for each (occurred_at, observer) in the given order. An unknown observer
    (None) is never discounted."""
    if p is None:
        return [1.0] * len(outcomes)
    window = timedelta(days=p.window_days)
    order = sorted(range(len(outcomes)), key=lambda i: outcomes[i][0])
    seen: dict[str, deque[datetime]] = defaultdict(deque)
    result = [1.0] * len(outcomes)
    for i in order:
        at, observer = outcomes[i]
        if observer is None:
            continue
        earlier = seen[observer]
        while earlier and earlier[0] < at - window:
            earlier.popleft()
        result[i] = p.factor ** len(earlier)
        earlier.append(at)
    return result
