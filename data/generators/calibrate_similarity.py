"""
calibrate_similarity.py — measure real review-text cosine similarity from YelpChi data.

Purpose
-------
The validator (validate.py) uses character 3-gram TF-IDF cosine with two hard-coded thresholds:
  - 0.70: flag a legitimate review as "suspiciously similar" to another review of the same person
  - 0.80: minimum mean cosine required inside an attack group (ring/farm/burst)

This script measures the same metric on real Yelp reviews to confirm those thresholds are
safe (i.e. legitimate reviews rarely exceed 0.70 naturally).

Usage
-----
    python -I data/generators/calibrate_similarity.py [path/to/yelpchi_train.csv]

Default path: data/raw/yelpchi/new_data_train.csv
Delimiter:    tab (the Kaggle re-upload is TSV)
Label column: flagged  (0 = legit, 1 = spam)
Text column:  reviewContent

Output
------
Prints percentile table for legit reviews and mean cosine for spam reviews,
then writes data/raw/yelpchi/calibration_result.txt with the same content.

Seed / determinism
------------------
Uses random.seed(20261001) for the sample — same project seed. The sample is a
max of SAMPLE_N reviews per class to keep runtime under 60 s.
"""

from __future__ import annotations

import csv
import math
import random
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "data" / "raw" / "yelpchi" / "new_data_train.csv"
SAMPLE_N = 1500  # reviews per class; O(N²) pairs — keep reasonable
SEED = 20261001
LEGIT_THRESHOLDS = [0.50, 0.60, 0.65, 0.70, 0.75, 0.80]  # thresholds to report % above


# ---------------------------------------------------------------------------
# Same 3-gram + TF-IDF cosine as validate.py — keep in sync.


def _grams(s: str) -> Counter:
    s = " " + " ".join(s.lower().split()) + " "
    return Counter(s[i : i + 3] for i in range(len(s) - 2))


def _tfidf_vecs(texts: list[str]) -> list[dict[str, float]]:
    grams = [_grams(t) for t in texts]
    n = len(grams)
    df: Counter = Counter()
    for g in grams:
        df.update(g.keys())
    vecs = []
    for g in grams:
        v = {k: (1 + math.log(c)) * math.log((1 + n) / (1 + df[k]) + 1) for k, c in g.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({k: x / norm for k, x in v.items()})
    return vecs


def _cos(a: dict, b: dict) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(k, 0.0) for k, x in a.items())


def _pairwise(vecs: list[dict]) -> list[float]:
    return [_cos(vecs[i], vecs[j]) for i in range(len(vecs)) for j in range(i + 1, len(vecs))]


def _percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = (len(s) - 1) * p / 100
    lo, hi = int(idx), min(int(idx) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (idx - lo)


# ---------------------------------------------------------------------------


def load(path: Path) -> tuple[list[str], list[str]]:
    legit, spam = [], []
    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            text = row.get("reviewContent", "").strip()
            flag = row.get("flagged", "").strip()
            if not text:
                continue
            if flag == "0":
                legit.append(text)
            elif flag == "1":
                spam.append(text)
    return legit, spam


def run(csv_path: Path) -> str:
    rng = random.Random(SEED)

    legit_all, spam_all = load(csv_path)
    legit = rng.sample(legit_all, min(SAMPLE_N, len(legit_all)))
    spam = rng.sample(spam_all, min(SAMPLE_N, len(spam_all)))

    print(f"Loaded {len(legit_all):,} legit and {len(spam_all):,} spam reviews.")
    print(f"Sampling {len(legit):,} legit and {len(spam):,} spam for pairwise comparison …")

    legit_vecs = _tfidf_vecs(legit)
    spam_vecs = _tfidf_vecs(spam)

    print("Computing pairwise cosines for legit sample …")
    legit_sims = _pairwise(legit_vecs)
    print("Computing pairwise cosines for spam sample …")
    spam_sims = _pairwise(spam_vecs)

    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("YelpChi similarity calibration")
    lines.append(f"Source:  {csv_path}")
    lines.append("Method:  character 3-gram TF-IDF cosine (same as validate.py)")
    lines.append(f"Sample:  {len(legit):,} legit, {len(spam):,} spam  (seed {SEED})")
    lines.append("=" * 60)

    lines.append("\n--- Legit reviews: pairwise cosine percentiles ---")
    for p in [50, 75, 90, 95, 99, 100]:
        lines.append(f"  p{p:3d}: {_percentile(legit_sims, p):.4f}")

    lines.append(f"\n  mean: {sum(legit_sims) / len(legit_sims):.4f}")

    lines.append("\n  % of legit pairs exceeding threshold:")
    n = len(legit_sims)
    for thr in LEGIT_THRESHOLDS:
        above = sum(1 for s in legit_sims if s >= thr)
        lines.append(f"    >= {thr:.2f}: {above / n * 100:.3f}%  ({above:,} / {n:,} pairs)")

    lines.append("\n--- Spam reviews: pairwise cosine percentiles ---")
    for p in [50, 75, 90, 95, 99, 100]:
        lines.append(f"  p{p:3d}: {_percentile(spam_sims, p):.4f}")
    lines.append(f"\n  mean: {sum(spam_sims) / len(spam_sims):.4f}")

    lines.append("\n--- Threshold recommendation ---")
    # Find the highest threshold where < 1% of legit pairs exceed it
    safe_thr = None
    for thr in LEGIT_THRESHOLDS:
        above_pct = sum(1 for s in legit_sims if s >= thr) / len(legit_sims) * 100
        if above_pct < 1.0:
            safe_thr = thr
    if safe_thr:
        lines.append(f"  Highest threshold where < 1% of legit pairs are flagged: {safe_thr:.2f}")
        lines.append("  Current validate.py legit lookalike threshold: 0.70")
        if safe_thr >= 0.70:
            lines.append("  VERDICT: 0.70 threshold is SAFE — confirmed by real data.")
        else:
            lines.append(
                f"  VERDICT: Consider raising threshold to {safe_thr:.2f} to avoid false positives."
            )
    else:
        lines.append(
            "  VERDICT: All thresholds have >= 1% legit false-positive rate. Review manually."
        )

    result = "\n".join(lines)
    print("\n" + result)

    out = csv_path.parent / "calibration_result.txt"
    out.write_text(result + "\n", encoding="utf-8")
    print(f"\nResult written to: {out}")
    return result


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        sys.exit(1)
    run(path)
