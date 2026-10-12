"""Compare the shape of a generated lending graph with the public trust networks.

    python -I data/generators/graph_shape.py data/interim/scale

Edges are "lender -> borrower" pairs that have at least one completed loan (trust_edge.csv rows with
role BORROWER). The public numbers come from data/derived/public_graph_stats.json. A match is not
expected to be exact: the aim is the same kind of shape (a few busy members, many quiet ones,
some give-and-take, some clustering), not a copy.
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import PUBLIC_STATS_JSON, read_csv  # noqa: E402


def shape(folder: Path) -> dict:
    # lender -> borrower pairs only (role BORROWER). Every loan also creates a borrower -> lender edge
    # for the lender-side metrics, which would make reciprocity trivially 100%.
    edges = {
        (e["source_id"], e["target_id"])
        for e in read_csv(folder / "trust_edge.csv")
        if e["role"] == "BORROWER"
    }
    out: dict[str, int] = defaultdict(int)
    adj: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        out[a] += 1
        adj[a].add(b)
        adj[b].add(a)
    rec = sum(1 for a, b in edges if (b, a) in edges) / len(edges)
    rng = random.Random(7)
    nodes = sorted(n for n, nb in adj.items() if len(nb) >= 2)
    sample = rng.sample(nodes, min(2000, len(nodes)))
    cc = 0.0
    for n in sample:
        nb = sorted(adj[n])
        k = len(nb)
        links = sum(1 for i in range(k) for j in range(i + 1, k) if nb[j] in adj[nb[i]])
        cc += 2 * links / (k * (k - 1))
    degs = sorted(out.values())
    mean = sum(degs) / len(degs)
    q = {
        f"{p:.2f}": round(degs[min(len(degs) - 1, int(p * len(degs)))] / mean, 2)
        for p in (0.5, 0.9, 0.99)
    }
    return {
        "nodes_with_out_edges": len(out),
        "edges": len(edges),
        "mean_out_degree": round(mean, 2),
        "out_degree_over_mean_quantiles": q,
        "reciprocity": round(rec, 3),
        "clustering_sample": round(cc / len(sample), 3),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    mine = shape(Path(sys.argv[1]))
    pub = json.loads(PUBLIC_STATS_JSON.read_text(encoding="utf-8"))
    e = pub["epinions_trust"]
    ref = {
        "epinions_positive": {
            "out_degree_over_mean_quantiles": {
                k: e["positive_edges"]["out_degree_over_mean_quantiles"][k]
                for k in ("0.50", "0.90", "0.99")
            },
            "reciprocity": e["reciprocity_positive"],
            "clustering_sample": e["clustering_coefficient_sample_positive"],
        },
        "bitcoin_otc": {
            "out_degree_over_mean_quantiles": {
                k: pub["bitcoin_otc"]["out_degree_over_mean_quantiles"][k]
                for k in ("0.50", "0.90", "0.99")
            },
            "reciprocity": pub["bitcoin_otc"]["reciprocity"],
            "clustering_sample": pub["bitcoin_otc"]["clustering_coefficient_sample"],
        },
    }
    print(json.dumps({"this_dataset": mine, **ref}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
