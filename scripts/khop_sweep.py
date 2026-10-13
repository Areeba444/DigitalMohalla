"""k sweep for the bounded k-hop search (Test Plan suite 8, NFR-P-03): latency and coverage for k = 1 to 4.

    cd backend
    uv run python ../scripts/khop_sweep.py ../data/derived/standard
    uv run python ../scripts/khop_sweep.py ../data/interim/scale --sample 2000

Reads a generated tier's CSV files directly (no database): the trust graph for role BORROWER and
metric ON_TIME_RETURN from trust_edge.csv, and the (lender, borrower) pairs of its loans from
borrowing_transaction.csv. For each k it times one search per pair and reports how many pairs find a
community path and how many reach rho >= rho_sup (0.3, rule R9). Results are written, with the config
version, the generator manifest and the commit, to docs/design/14_testing/results/. Reported, not gated.
All data is SYNTHETIC.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import random
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config.engine_config import load_engine_config  # noqa: E402
from app.domain.assurance.indirect.khop import KHopParams, indirect_trust  # noqa: E402

OUT = ROOT / "docs" / "design" / "14_testing" / "results"


def read_graph(folder: Path) -> dict[str, dict[str, float]]:
    g: dict[str, dict[str, float]] = {}
    with (folder / "trust_edge.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["role"] == "BORROWER" and r["metric"] == "ON_TIME_RETURN":
                g.setdefault(r["source_id"], {})[r["target_id"]] = float(r["weight"])
    return g


def read_pairs(folder: Path) -> list[tuple[str, str]]:
    with (folder / "borrowing_transaction.csv").open(encoding="utf-8", newline="") as f:
        return sorted({(r["lender_id"], r["borrower_id"]) for r in csv.DictReader(f)})


def pct(xs: list[float], p: float) -> float:
    s = sorted(xs)
    return s[min(len(s) - 1, int(p * len(s)))]


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("folder", type=Path)
    ap.add_argument("--sample", type=int, default=0, help="random pairs to time (0 = all)")
    ap.add_argument("--seed", type=int, default=20261001)
    a = ap.parse_args()
    cfg = load_engine_config()
    section = cfg.section("indirect_trust_alg2")
    rho_sup = cfg.section("decision_policy_alg4")["thresholds"][
        "rho_sup_indirect_support_threshold"
    ]
    graph = read_graph(a.folder)
    pairs = read_pairs(a.folder)
    if a.sample and a.sample < len(pairs):
        pairs = random.Random(a.seed).sample(pairs, a.sample)
    manifest = json.loads((a.folder / "MANIFEST.json").read_text(encoding="utf-8"))
    rows = []
    for k in (1, 2, 3, 4):
        params = KHopParams.from_config(section, k=k)
        for u, v in pairs[:20]:  # warm-up, not timed
            indirect_trust(graph, u, v, params, None)
        times, with_path, supported, found = [], 0, 0, []
        for u, v in pairs:
            t0 = time.perf_counter()
            r = indirect_trust(graph, u, v, params, None)
            times.append((time.perf_counter() - t0) * 1000)
            found.append(r.paths_found)
            with_path += bool(r.paths)
            supported += r.reliability >= rho_sup
        rows.append(
            {
                "k": k,
                "pairs": len(pairs),
                "p50_ms": round(statistics.median(times), 3),
                "p95_ms": round(pct(times, 0.95), 3),
                "max_ms": round(max(times), 3),
                "pairs_with_a_path": with_path,
                "coverage": round(with_path / len(pairs), 4),
                "pairs_with_rho_ge_rho_sup": supported,
                "mean_paths_found": round(statistics.mean(found), 2),
                "max_paths_found": max(found),
            }
        )
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        commit = "unknown"
    meta = {
        "run_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "commit": commit,
        "config_version": cfg.config_version,
        "tier": manifest.get("tier"),
        "seed": manifest.get("seed"),
        "generator_version": manifest.get("generator_version"),
        "synthetic": True,
        "nodes_with_out_edges": len(graph),
        "edges": sum(len(n) for n in graph.values()),
        "machine": f"{platform.system()} {platform.machine()}, Python {platform.python_version()}",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    stem = f"khop_sweep_{meta['tier']}_{cfg.config_version}"
    (OUT / f"{stem}.json").write_text(
        json.dumps({"meta": meta, "rows": rows}, indent=1) + "\n", encoding="utf-8"
    )
    lines = [
        f"# k sweep, {meta['tier']} tier (SYNTHETIC data)",
        "",
        "Generated by `scripts/khop_sweep.py` (Test Plan suite 8, NFR-P-03). Reported, not gated.",
        "",
        "| Field | Value |",
        "| :--- | :--- |",
        *[f"| {k} | {v} |" for k, v in meta.items()],
        "",
        "| k | pairs | p50 ms | p95 ms | max ms | with a path | coverage | rho >= rho_sup | mean paths found | max paths found |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *[
            f"| {r['k']} | {r['pairs']} | {r['p50_ms']} | {r['p95_ms']} | {r['max_ms']} | {r['pairs_with_a_path']} | "
            f"{r['coverage']:.1%} | {r['pairs_with_rho_ge_rho_sup']} | {r['mean_paths_found']} | {r['max_paths_found']} |"
            for r in rows
        ],
        "",
        "Pairs are the (lender, borrower) pairs of the tier's loans, so many already have a direct edge (a 1-hop path); "
        "coverage at k = 1 is that share. Latency is one in-memory search per pair on this machine; the graph is read once.",
    ]
    (OUT / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
