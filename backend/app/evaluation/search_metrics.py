"""Search metrics: precision@k, recall@k and NDCG@k per query, averaged with bootstrap intervals over
queries (M11; Search Evaluation Design DA-25 section 5). Pure functions, synthetic data only.

Plain-language notes:
- Precision@5: of the first five results, the share with label 1 or 2 (relevant).
- Recall@10: of all relevant items judged for the query, the share found in the first ten.
- NDCG@10: relevant items near the top count more. The gain of a result is 2^label - 1, divided by
  log2(rank + 1); the sum is divided by the same sum for the best possible order of the judged items.
- Items nobody judged count as label 0 (the pool depth is reported with the result).
- Queries with no relevant item ("no good answer") are left out of recall and NDCG, and shown apart.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Mapping, Sequence

Labels = Mapping[str, int]  # item_key -> 0, 1 or 2 for one query


def precision_at(ranked: Sequence[str], labels: Labels, k: int = 5, threshold: int = 1) -> float:
    return sum(labels.get(i, 0) >= threshold for i in ranked[:k]) / k


def recall_at(
    ranked: Sequence[str], labels: Labels, k: int = 10, threshold: int = 1
) -> float | None:
    relevant = {i for i, v in labels.items() if v >= threshold}
    if not relevant:
        return None  # no good answer: left out
    return len(relevant & set(ranked[:k])) / len(relevant)


def ndcg_at(ranked: Sequence[str], labels: Labels, k: int = 10) -> float | None:
    ideal = sorted(labels.values(), reverse=True)[:k]
    best = sum((2**v - 1) / math.log2(r + 2) for r, v in enumerate(ideal))
    if best == 0:
        return None
    got: float = sum(
        (2 ** labels.get(i, 0) - 1) / math.log2(r + 2) for r, i in enumerate(ranked[:k])
    )
    return float(got / best)


def bootstrap_mean_ci(
    values: Sequence[float], resamples: int = 1000, seed: int = 20261001
) -> tuple[float, float]:
    """95% interval of the mean over queries (resampling queries with replacement)."""
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    return means[int(0.025 * resamples)], means[int(0.975 * resamples) - 1]


def per_query(
    runs: Mapping[str, Sequence[str]], labels: Mapping[str, Labels], threshold: int = 1
) -> dict[str, dict[str, float | None]]:
    return {
        q: {
            "p@5": precision_at(runs.get(q, []), labels[q], 5, threshold),
            "r@10": recall_at(runs.get(q, []), labels[q], 10, threshold),
            "ndcg@10": ndcg_at(runs.get(q, []), labels[q], 10),
        }
        for q in labels
    }


def summarise(
    scores: Mapping[str, Mapping[str, float | None]],
    types: Mapping[str, str],
    resamples: int = 1000,
) -> dict[str, dict[str, dict[str, float | int | list[float]]]]:
    """Mean and 95% interval per metric, for all queries and for each query type."""
    groups: dict[str, list[str]] = defaultdict(list)
    for q in scores:
        groups["all"].append(q)
        groups[types[q]].append(q)
    out: dict[str, dict[str, dict[str, float | int | list[float]]]] = {}
    for g, qs in groups.items():
        out[g] = {}
        for m in ("p@5", "r@10", "ndcg@10"):
            vals = [v for q in qs if (v := scores[q][m]) is not None]
            if vals:
                lo, hi = bootstrap_mean_ci(vals, resamples)
                out[g][m] = {
                    "mean": round(sum(vals) / len(vals), 4),
                    "ci95": [round(lo, 4), round(hi, 4)],
                    "queries": len(vals),
                }
    return out


def paired_difference(
    a: Mapping[str, Mapping[str, float | None]],
    b: Mapping[str, Mapping[str, float | None]],
    metric: str,
    resamples: int = 1000,
) -> dict[str, float | int | list[float]] | None:
    """Mean of (a - b) over queries where both have the metric, with its 95% interval."""
    diffs = [
        x - y
        for q in a
        if (x := a[q][metric]) is not None and (y := b.get(q, {}).get(metric)) is not None
    ]
    if not diffs:
        return None
    lo, hi = bootstrap_mean_ci(diffs, resamples)
    return {
        "mean": round(sum(diffs) / len(diffs), 4),
        "ci95": [round(lo, 4), round(hi, 4)],
        "queries": len(diffs),
    }
