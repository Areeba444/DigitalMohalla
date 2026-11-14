"""Labeller agreement for the search query set (DA-25 section 4; plan item M9).

    python -I data/generators/search_agreement.py labels_a.csv labels_b.csv

Each file has columns query_id, item_key, label (0 = does not meet the need, 1 = partly, 2 = meets
it), written by one labeller alone. Rows are matched on (query_id, item_key); a pair labelled by only
one person is reported and left out. Prints exact agreement, Cohen's kappa and quadratic-weighted
kappa, which DA-25 requires to be reported before disagreements are discussed.

Plain-language note: kappa compares the agreement seen with the agreement two people would reach by
chance given how often each uses each label; 1 is perfect, 0 is chance. The quadratic weights count
a 0-versus-2 disagreement as worse than 0-versus-1. Standard library only.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

LABELS = (0, 1, 2)


def read(path: Path) -> dict[tuple[str, str], int]:
    with path.open(encoding="utf-8") as fh:
        out = {}
        for row in csv.DictReader(fh):
            label = int(row["label"])
            if label not in LABELS:
                raise ValueError(f"{path}: label {label} is not 0, 1 or 2")
            out[(row["query_id"], row["item_key"])] = label
        return out


def kappa(a: list[int], b: list[int], weights: str = "none") -> float:
    """Cohen's kappa for two raters over the same items; weights "none" or "quadratic"."""
    if len(a) != len(b) or not a:
        raise ValueError("need two equal, non-empty lists")
    n, k = len(a), len(LABELS)
    observed = Counter(zip(a, b, strict=True))
    pa, pb = Counter(a), Counter(b)

    def w(i: int, j: int) -> float:
        if weights == "quadratic":
            return ((i - j) / (k - 1)) ** 2
        return 0.0 if i == j else 1.0

    disagree_obs = sum(w(i, j) * observed[(i, j)] / n for i in LABELS for j in LABELS)
    disagree_exp = sum(w(i, j) * (pa[i] / n) * (pb[j] / n) for i in LABELS for j in LABELS)
    if disagree_exp == 0:  # both used one label throughout: agreement is total but uninformative
        return 1.0
    return 1.0 - disagree_obs / disagree_exp


def compare(a: dict[tuple[str, str], int], b: dict[tuple[str, str], int]) -> dict[str, float]:
    both = sorted(set(a) & set(b))
    xa, xb = [a[k] for k in both], [b[k] for k in both]
    return {
        "pairs": len(both),
        "only_one_labeller": len(set(a) ^ set(b)),
        "exact_agreement": sum(i == j for i, j in zip(xa, xb, strict=True)) / len(both),
        "cohen_kappa": kappa(xa, xb),
        "quadratic_kappa": kappa(xa, xb, "quadratic"),
    }


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: search_agreement.py labels_a.csv labels_b.csv")
    result = compare(read(Path(sys.argv[1])), read(Path(sys.argv[2])))
    for k, v in result.items():
        print(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")


if __name__ == "__main__":
    main()
