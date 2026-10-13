"""Bounded k-hop indirect trust (Algorithm 2; FR-T-04; Overview §5.5; KHop_Indirect_Trust_Design.md).

Plain-language note: the lender u has no history with borrower v, but people u trusts may have lent
to v. Every simple path u -> x -> ... -> v of at most k hops through trust edges is a piece of
indirect evidence. A path's strength is the product of its edge weights, discounted by gamma (0.7)
for every hop after the first. Paths through the same first neighbour are correlated, so only the
strongest one per first neighbour is kept. The kept strengths are combined with noisy-OR into I,
then scaled by how many independent first neighbours there are and capped at 0.6, giving the
reliability rho. Indirect evidence pulls the population baseline b towards v's own direct mean t_v
by rho: t_indirect = b + rho (t_v - b). It supplements direct evidence and never replaces it.

Complexity: the bounded depth-first search visits at most sum_{h<=k} d^h partial paths (d = largest
out-degree), O(d^k); selection is linear in the paths found. Pure functions, no I/O.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

Graph = Mapping[str, Mapping[str, float]]  # source -> {target: weight}, one role and metric


@dataclass(frozen=True)
class KHopParams:
    k: int
    gamma: float
    rho_max: float
    path_divisor: float
    diversity_divisor: float
    baseline: float

    @classmethod
    def from_config(cls, section: Mapping[str, Any], k: int | None = None) -> "KHopParams":
        """`section` is indirect_trust_alg2 of engine.json; `k` overrides it for the k sweep."""
        agg = section["aggregation"]
        p = cls(
            k=int(k if k is not None else section["graph_traversal"]["max_hops_k"]),
            gamma=float(section["attenuation_decay"]["hop_decay_gamma"]),
            rho_max=float(agg["reliability_cap_rho_max"]),
            path_divisor=float(agg["path_count_divisor"]),
            diversity_divisor=float(agg["diversity_divisor"]),
            baseline=float(section["baseline"]["default_population_baseline"]),
        )
        if p.k < 1 or not 0 < p.gamma <= 1 or not 0 < p.rho_max <= 1:
            raise ValueError("invalid k-hop parameters")
        return p


@dataclass(frozen=True)
class TrustPath:
    nodes: tuple[str, ...]
    strength: float  # q(P) = product of edge weights x gamma^(hops - 1)

    @property
    def hops(self) -> int:
        return len(self.nodes) - 1


@dataclass(frozen=True)
class IndirectResult:
    paths: list[TrustPath]  # the selected paths, strongest per first hop
    evidence_strength: float  # I, noisy-OR of the selected strengths
    reliability: float  # rho, capped
    estimate: float  # t_indirect
    prior_backed: bool  # True when v has no direct mean and the baseline stands in for it
    paths_found: int = 0
    first_hops: list[str] = field(default_factory=list)


def find_paths(graph: Graph, u: str, v: str, k: int) -> list[tuple[str, ...]]:
    """Every simple path from u to v with 1 to k hops. Neighbours are visited in sorted order."""
    out: list[tuple[str, ...]] = []
    if u == v:
        return out
    stack: list[tuple[str, tuple[str, ...]]] = [(u, (u,))]
    while stack:
        node, path = stack.pop()
        for nxt in sorted(graph.get(node, {}), reverse=True):
            if nxt in path:  # simple paths only: cycles and self-loops are never followed
                continue
            p = (*path, nxt)
            if nxt == v:
                out.append(p)
            elif len(p) - 1 < k:
                stack.append((nxt, p))
    return sorted(out, key=lambda p: (len(p), p))


def path_strength(graph: Graph, nodes: tuple[str, ...], gamma: float) -> float:
    w = 1.0
    for a, b in zip(nodes, nodes[1:], strict=False):
        weight = graph[a][b]
        if not 0 < weight <= 1:
            raise ValueError(f"edge weight {weight} outside (0, 1]")
        w *= weight
    return w * gamma ** (len(nodes) - 2)


def indirect_trust(
    graph: Graph,
    u: str,
    v: str,
    params: KHopParams,
    target_mean: float | None,
    excluded_edges: frozenset[tuple[str, str]] = frozenset(),
) -> IndirectResult:
    """Indirect evidence from lender u about borrower v. `excluded_edges` removes edges, for example
    those inside a flagged manipulation cluster (ADR-0006 question 3), before the search."""
    g: Graph = (
        {
            a: {b: w for b, w in nb.items() if (a, b) not in excluded_edges}
            for a, nb in graph.items()
        }
        if excluded_edges
        else graph
    )
    found = find_paths(g, u, v, params.k)
    best: dict[str, TrustPath] = {}
    for nodes in found:
        tp = TrustPath(nodes, path_strength(g, nodes, params.gamma))
        current = best.get(nodes[1])
        if current is None or tp.strength > current.strength:
            best[nodes[1]] = tp
    selected = [best[h] for h in sorted(best)]
    prod = 1.0
    for tp in selected:
        prod *= 1.0 - tp.strength
    i_strength = 1.0 - prod if selected else 0.0
    n = len(selected)
    rho = (
        min(
            params.rho_max,
            min(1.0, n / params.path_divisor) * min(1.0, n / params.diversity_divisor) * i_strength,
        )
        if selected
        else 0.0
    )
    prior_backed = target_mean is None
    t_v = params.baseline if target_mean is None else target_mean
    return IndirectResult(
        paths=selected,
        evidence_strength=i_strength,
        reliability=rho,
        estimate=params.baseline + rho * (t_v - params.baseline),
        prior_backed=prior_backed,
        paths_found=len(found),
        first_hops=sorted(best),
    )
