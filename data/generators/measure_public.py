"""Measure shape statistics from the public trust networks and write them to a small JSON file.

Only AGGREGATES leave this script (quantile tables, shares, counts). No row of Epinions or Bitcoin
OTC/Alpha is copied anywhere: the licences do not show redistribution permission (see
data/datasets/epinions.md and bitcoin-otc-alpha.md). The generator reads the JSON, so building the
synthetic dataset needs none of the raw files and works in CI.

Run (from the repository root):
    python -I data/generators/measure_public.py

Inputs (gitignored):  data/raw/epinions/{user_rating,rating}.txt, data/raw/bitcoin-otc/*.csv
Output (committed):   data/derived/public_graph_stats.json

What each statistic is used for is written next to it in the output ("used_for").
Plain-language note: a "quantile table" lists the value below which 5%, 10%, ... 99% of the
members fall. The generator draws from such a table to give simulated people the same uneven
activity that real members show (a few very active people, many quiet ones).
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "derived" / "public_graph_stats.json"
SEED = 20261001
QUANTILES = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99]


def quantiles(values: list[float], qs: list[float] = QUANTILES) -> dict[str, float]:
    """Value at each quantile of a list (nearest rank)."""
    if not values:
        return {}
    s = sorted(values)
    n = len(s)
    return {f"{q:.2f}": round(float(s[min(n - 1, int(q * n))]), 4) for q in qs}


def share(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def degree_table(edges: list[tuple[int, int]]) -> dict:
    out_deg: Counter[int] = Counter(a for a, _ in edges)
    in_deg: Counter[int] = Counter(b for _, b in edges)
    mean_out = sum(out_deg.values()) / len(out_deg)
    mean_in = sum(in_deg.values()) / len(in_deg)
    return {
        "n_sources": len(out_deg),
        "n_targets": len(in_deg),
        "out_degree_mean": round(mean_out, 4),
        "in_degree_mean": round(mean_in, 4),
        # degree divided by the mean: a size-free shape the generator can rescale
        "out_degree_over_mean_quantiles": quantiles([d / mean_out for d in out_deg.values()]),
        "in_degree_over_mean_quantiles": quantiles([d / mean_in for d in in_deg.values()]),
    }


def reciprocity(edges: list[tuple[int, int]]) -> float:
    """Share of edges A->B for which B->A also exists."""
    s = set(edges)
    return share(sum(1 for a, b in s if (b, a) in s), len(s))


def clustering_sample(
    edges: list[tuple[int, int]], rng: random.Random, n_sample: int = 3000
) -> float:
    """Average local clustering coefficient of the undirected graph, over a random node sample."""
    adj: dict[int, set[int]] = defaultdict(set)
    for a, b in edges:
        if a != b:
            adj[a].add(b)
            adj[b].add(a)
    nodes = sorted(n for n, nb in adj.items() if len(nb) >= 2)
    sample = rng.sample(nodes, min(n_sample, len(nodes)))
    total = 0.0
    for n in sample:
        nb = sorted(adj[n])
        k = len(nb)
        if k > 400:  # very large neighbourhoods: sample pairs to keep the run short
            pairs = [(rng.choice(nb), rng.choice(nb)) for _ in range(20000)]
            links = sum(1 for x, y in pairs if x != y and y in adj[x])
            total += links / sum(1 for x, y in pairs if x != y)
        else:
            links = sum(1 for i in range(k) for j in range(i + 1, k) if nb[j] in adj[nb[i]])
            total += 2 * links / (k * (k - 1))
    return round(total / len(sample), 4)


def measure_bitcoin(path: Path, rng: random.Random) -> dict:
    rows = []
    with path.open(newline="") as f:
        for r in csv.reader(f):
            if len(r) >= 4:
                rows.append((int(r[0]), int(r[1]), int(r[2]), int(float(r[3]))))
    rows.sort(key=lambda x: x[3])
    n = len(rows)
    pos = [r for r in rows if r[2] > 0]
    edges = [(r[0], r[1]) for r in rows]
    dist = Counter(r[2] for r in rows)

    by_rater: dict[int, list[int]] = defaultdict(list)
    first_seen: dict[int, int] = {}
    for s, t, _, ts in rows:
        by_rater[s].append(ts)
        first_seen.setdefault(s, ts)
        first_seen.setdefault(t, ts)
    day = 86400
    gaps_ratio: list[float] = []
    within_24h = total_gaps = 0
    for times in by_rater.values():
        if len(times) < 6:
            continue
        gaps = [b - a for a, b in zip(times, times[1:], strict=False)]
        med = sorted(gaps)[len(gaps) // 2] or 1
        gaps_ratio.extend(g / med for g in gaps)
        within_24h += sum(1 for g in gaps if g <= day)
        total_gaps += len(gaps)
    # how much a rater does in the first 7 days after first appearing as a rater
    first7: list[int] = []
    for s, times in by_rater.items():
        t0 = first_seen[s]
        first7.append(sum(1 for t in times if t - t0 <= 7 * day))
    return {
        "n_edges": n,
        "n_nodes": len(set(a for a, _ in edges) | set(b for _, b in edges)),
        "positive_share": share(len(pos), n),
        "rating_share_by_value": {str(k): share(v, n) for k, v in sorted(dist.items())},
        "first_date": datetime.fromtimestamp(rows[0][3], UTC).date().isoformat(),
        "last_date": datetime.fromtimestamp(rows[-1][3], UTC).date().isoformat(),
        **degree_table(edges),
        "reciprocity": reciprocity(edges),
        "clustering_coefficient_sample": clustering_sample(edges, rng),
        "same_rater_gap_over_own_median_quantiles": quantiles(gaps_ratio),
        "share_of_gaps_within_24h": share(within_24h, total_gaps),
        "ratings_in_first_7_days_per_rater_quantiles": quantiles([float(x) for x in first7]),
    }


def measure_epinions_trust(path: Path, rng: random.Random) -> dict:
    edges_all: list[tuple[int, int, int, str]] = []
    with path.open() as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) == 4:
                edges_all.append((int(p[0]), int(p[1]), int(p[2]), p[3]))
    pos = [(a, b) for a, b, v, _ in edges_all if v > 0]
    per_day = Counter(d for *_, d in edges_all)
    busiest = sorted(per_day.values(), reverse=True)
    top1pct = max(1, len(busiest) // 100)
    return {
        "n_edges": len(edges_all),
        "positive_share": share(len(pos), len(edges_all)),
        "first_date": min(d for *_, d in edges_all),
        "last_date": max(d for *_, d in edges_all),
        "positive_edges": degree_table(pos),
        "reciprocity_positive": reciprocity(pos),
        "clustering_coefficient_sample_positive": clustering_sample(pos, rng),
        "share_of_edges_on_busiest_1pct_of_days": share(sum(busiest[:top1pct]), len(edges_all)),
    }


def measure_epinions_ratings(path: Path) -> dict:
    """Helpfulness-rating spread and update behaviour. The file is CUT OFF (see the card), so the
    last line is dropped and the shares describe the part we hold, not all of Epinions."""
    stars: Counter[int] = Counter()
    modified = rows = 0
    mod_delay: list[int] = []
    per_member: Counter[int] = Counter()
    by_year: Counter[str] = Counter()
    first: str | None = None
    last: str | None = None
    with path.open(encoding="latin-1") as f:
        prev = None
        for line in f:
            if prev is not None:
                _count_row(prev, stars, per_member, by_year, mod_delay)
                rows += 1
            prev = line
    # `prev` is the cut-off last line: not counted
    for y in sorted(by_year):
        first = first or y
        last = y
    modified = len(mod_delay)
    return {
        "rows_read": rows,
        "last_line_dropped_because_cut_off": True,
        "star_share": {str(k): share(v, rows) for k, v in sorted(stars.items())},
        "share_with_a_later_modification_date": share(modified, rows),
        "modification_delay_days_quantiles": quantiles([float(x) for x in mod_delay]),
        "ratings_per_member_quantiles": quantiles([float(x) for x in per_member.values()]),
        "rows_by_creation_year": dict(sorted(by_year.items())),
        "first_year_seen": first,
        "last_year_seen": last,
    }


def _count_row(line, stars, per_member, by_year, mod_delay) -> None:
    p = line.rstrip("\n").split("\t")
    if len(p) < 6:
        return
    r = int(p[2])
    stars[min(r, 5)] += 1  # the NOTE says the few 6s count as 5
    per_member[int(p[1])] += 1
    by_year[p[4][:4]] += 1
    if p[5]:
        try:
            d1 = date(*map(int, p[4].split("/")))
            d2 = date(*map(int, p[5].split("/")))
            mod_delay.append((d2 - d1).days)
        except ValueError:
            pass


def main() -> int:
    rng = random.Random(SEED)
    stats: dict = {
        "about": (
            "Aggregate shape statistics measured from public trust networks. No rows are copied. "
            "Produced by data/generators/measure_public.py; read by the synthetic-data generator."
        ),
        "seed": SEED,
        "citations": {
            "epinions": "Hamedani, Ali, Hong, Kim. TrustRec... Computer Science and Information Systems 18(1), 2020 (as given on the Kaggle page)",
            "bitcoin": "Kumar et al., ICDM 2016; Kumar et al., WSDM 2018 (REV2)",
        },
    }
    for name, fname in (
        ("bitcoin_otc", "soc-sign-bitcoinotc.csv"),
        ("bitcoin_alpha", "soc-sign-bitcoinalpha.csv"),
    ):
        print("measuring", name, flush=True)
        stats[name] = measure_bitcoin(RAW / "bitcoin-otc" / fname, rng)
    print("measuring epinions trust", flush=True)
    stats["epinions_trust"] = measure_epinions_trust(RAW / "epinions" / "user_rating.txt", rng)
    print("measuring epinions ratings (large file, takes a few minutes)", flush=True)
    stats["epinions_ratings"] = measure_epinions_ratings(RAW / "epinions" / "rating.txt")
    stats["used_for"] = {
        "out/in_degree_over_mean_quantiles": "how uneven borrowing activity and lender popularity are",
        "reciprocity": "chance that a lender later borrows back from a borrower",
        "same_rater_gap_over_own_median_quantiles": "spacing of one person's loans over time, including bursts",
        "share_of_gaps_within_24h": "how often a person acts again within a day",
        "ratings_in_first_7_days_per_rater_quantiles": "how busy a brand-new account is (new-account burst attack)",
        "star_share": "skew of 1-5 star ratings when people are mostly satisfied",
        "clustering_coefficient_*": "reported only; checked against the simulated neighbourhood graph",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
