"""Score keyword-only against hybrid search (build item M11; Search Evaluation Design DA-25 section 5).

    cd backend
    uv run python ../scripts/score_search.py --labels final_labels.csv \
        --keyword run_keyword.csv --hybrid run_hybrid.csv

Inputs (all CSV, UTF-8):
  final_labels.csv   query_id,item_key,label     the resolved labels (0, 1 or 2), from two labellers
  run_<system>.csv   query_id,rank,item_key      the system's results for each query, best first
The queries and their types are read from data/derived/search/queries.csv. Prints and writes
precision@5, recall@10 and NDCG@10 per system and per query type with 95% bootstrap intervals over
queries, the paired difference hybrid minus keyword, and the pool depth. Queries with no relevant item
(no good answer) are left out of recall and NDCG and listed apart.

It refuses to run on a missing or empty label file: no label is ever invented. The labels need two
people labelling alone (data/derived/search/README.md). All data is SYNTHETIC.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.evaluation.search_metrics import paired_difference, per_query, summarise  # noqa: E402

QUERIES = ROOT / "data" / "derived" / "search" / "queries.csv"
OUT = ROOT / "docs" / "design" / "14_testing" / "results"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_run(path: Path) -> dict[str, list[str]]:
    by: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for r in rows(path):
        by[r["query_id"]].append((int(r["rank"]), r["item_key"]))
    return {q: [k for _, k in sorted(v)] for q, v in by.items()}


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--keyword", type=Path, required=True)
    ap.add_argument("--hybrid", type=Path, required=True)
    ap.add_argument("--threshold", type=int, default=1, help="relevant means label >= this (S-E3)")
    ap.add_argument("--resamples", type=int, default=1000)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    if not a.labels.exists() or not rows(a.labels):
        print(
            "No labels: refusing to score. The labels need two people (see README).",
            file=sys.stderr,
        )
        return 2
    types = {r["query_id"]: r["type"] for r in rows(QUERIES)}
    labels: dict[str, dict[str, int]] = defaultdict(dict)
    for r in rows(a.labels):
        labels[r["query_id"]][r["item_key"]] = int(r["label"])
    unknown = sorted(set(labels) - set(types))
    if unknown:
        print(f"Labels for unknown queries: {unknown}", file=sys.stderr)
        return 2
    missing = sorted(set(types) - set(labels))
    if missing:
        print(f"Queries without labels (left out): {missing}", file=sys.stderr)
    systems = {"keyword": read_run(a.keyword), "hybrid": read_run(a.hybrid)}
    scores = {n: per_query(run, labels, a.threshold) for n, run in systems.items()}
    result = {
        "label": "SYNTHETIC catalogue and queries; absolute numbers say little about real use",
        "threshold": a.threshold,
        "queries_scored": len(labels),
        "pool_depth_judged_items": {q: len(v) for q, v in sorted(labels.items())},
        "no_good_answer_queries": sorted(
            q for q, v in labels.items() if not any(x >= a.threshold for x in v.values())
        ),
        "systems": {n: summarise(s, types, a.resamples) for n, s in scores.items()},
        "hybrid_minus_keyword": {
            m: paired_difference(scores["hybrid"], scores["keyword"], m, a.resamples)
            for m in ("p@5", "r@10", "ndcg@10")
        },
    }
    a.out.mkdir(parents=True, exist_ok=True)
    path = a.out / "search_evaluation.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["hybrid_minus_keyword"], indent=2))
    print(f"written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
