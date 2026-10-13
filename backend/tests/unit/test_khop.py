"""Bounded k-hop indirect trust (Test Plan suite 7: TC-25, TC-26, TC-28; ES-13 paths).

The A5 worked example (docs/design/11_assurance_engine/generate_khop_example.py) is the oracle:
its graph is rebuilt here from the same outcome counts with the ADR-0006 edge rule.
"""

import json
from pathlib import Path

import networkx as nx
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.config.engine_config import load_engine_config
from app.domain.assurance.indirect.khop import KHopParams, find_paths, indirect_trust

SECTION = load_engine_config().section("indirect_trust_alg2")
P = KHopParams.from_config(SECTION)
FIXTURES = (
    Path(__file__).resolve().parents[3] / "docs/design/14_testing/scenario_fixtures_iteration1.json"
)

# A5 worked example: (successes, failures) per edge, all recent; weight = (1 + s) / (2 + s + f)
COUNTS = {
    ("L", "A"): (8, 0), ("L", "C"): (3, 0), ("L", "D"): (2, 1), ("A", "B"): (5, 0),
    ("A", "E"): (8, 0), ("E", "B"): (3, 0), ("C", "E"): (6, 2), ("C", "F"): (8, 0),
    ("F", "G"): (8, 0), ("G", "B"): (8, 0), ("D", "B"): (1, 1), ("B", "A"): (3, 0),
}  # fmt: skip
A5: dict[str, dict[str, float]] = {}
for (a, b), (s, f) in COUNTS.items():
    A5.setdefault(a, {})[b] = (1 + s) / (2 + s + f)


def test_parameters_come_from_the_config() -> None:
    assert (P.k, P.gamma, P.rho_max, P.path_divisor, P.diversity_divisor) == (3, 0.7, 0.6, 3.0, 2.0)


def test_tc25_a5_example_at_k3() -> None:
    r = indirect_trust(A5, "L", "B", P, target_mean=0.80)
    assert [round(p.strength, 4) for p in r.paths] == pytest.approx([0.54, 0.2195, 0.21], abs=1e-4)
    assert r.first_hops == ["A", "C", "D"]
    assert r.evidence_strength == pytest.approx(0.7164, abs=1e-4)
    assert r.reliability == pytest.approx(0.6)  # capped
    # the oracle's illustrative baseline was 0.70; the engine uses the configured baseline
    assert r.estimate == pytest.approx(P.baseline + 0.6 * (0.80 - P.baseline))


@pytest.mark.parametrize(("k", "rho"), [(1, 0.0), (2, 0.424), (3, 0.6), (4, 0.6)])
def test_tc26_k_sweep_on_the_a5_graph(k: int, rho: float) -> None:
    r = indirect_trust(A5, "L", "B", KHopParams.from_config(SECTION, k=k), target_mean=0.80)
    assert r.reliability == pytest.approx(rho, abs=5e-4)
    assert all(p.hops <= k for p in r.paths)


def test_k4_finds_a_longer_path_but_keeps_the_stronger_one_through_the_same_first_hop() -> None:
    r3 = indirect_trust(A5, "L", "B", KHopParams.from_config(SECTION, k=3), 0.8)
    r4 = indirect_trust(A5, "L", "B", KHopParams.from_config(SECTION, k=4), 0.8)
    assert r4.paths_found > r3.paths_found
    assert [p.nodes for p in r4.paths] == [p.nodes for p in r3.paths]


def test_tc28_cycles_and_self_loops_are_safe() -> None:
    g = {"u": {"u": 0.9, "x": 0.8}, "x": {"u": 0.8, "x": 0.5, "v": 0.7}, "v": {"x": 0.6}}
    paths = find_paths(g, "u", "v", 4)
    assert paths == [("u", "x", "v")]
    assert all(len(set(p)) == len(p) for p in paths)


def test_es13_fixture_paths() -> None:
    fx = {f["scenario_id"]: f for f in json.loads(FIXTURES.read_text(encoding="utf-8"))["fixtures"]}
    ie = fx["ES-13"]["indirect_evidence"]
    g: dict[str, dict[str, float]] = {}
    for e in ie["edge_outcomes"]:
        g.setdefault(e["source"], {})[e["target"]] = e["weight"]
    t_v = fx["ES-13"]["direct_evidence"]["mean"]
    r = indirect_trust(g, ie["lender"], ie["borrower"], P, target_mean=t_v)
    assert {p.nodes: round(p.strength, 4) for p in r.paths} == {
        tuple(p["nodes"]): pytest.approx(p["path_weight"], abs=5e-4) for p in ie["paths"]
    }
    assert r.evidence_strength == pytest.approx(ie["evidence_strength_I"], abs=5e-4)
    assert r.reliability == pytest.approx(ie["reliability_rho"], abs=5e-4)
    assert r.estimate == pytest.approx(ie["estimate"], abs=5e-4)
    assert r.prior_backed is False


def test_no_path_means_no_indirect_support_and_the_baseline() -> None:
    r = indirect_trust({"u": {"x": 0.9}}, "u", "v", P, target_mean=None)
    assert (r.paths, r.reliability, r.estimate, r.prior_backed) == ([], 0.0, P.baseline, True)


def test_excluded_edges_are_not_used() -> None:
    r = indirect_trust(A5, "L", "B", P, 0.8, excluded_edges=frozenset({("L", "A")}))
    assert "A" not in r.first_hops


def test_a_weight_outside_the_unit_interval_is_refused() -> None:
    with pytest.raises(ValueError):
        indirect_trust({"u": {"v": 1.5}}, "u", "v", P, 0.5)


@settings(max_examples=60, deadline=None)
@given(
    st.lists(st.tuples(st.integers(0, 6), st.integers(0, 6)), max_size=25),
    st.integers(1, 4),
)
def test_paths_match_networkx_and_rho_never_exceeds_the_cap(
    edges: list[tuple[int, int]], k: int
) -> None:
    g: dict[str, dict[str, float]] = {}
    for a, b in edges:
        if a != b:
            g.setdefault(str(a), {})[str(b)] = 0.5 + (a + b) % 5 / 10
    ours = set(find_paths(g, "0", "6", k))
    graph = nx.DiGraph([(a, b) for a, nb in g.items() for b in nb])
    expected = (
        {tuple(p) for p in nx.all_simple_paths(graph, "0", "6", cutoff=k)}
        if "0" in graph and "6" in graph
        else set()
    )
    assert ours == expected
    r = indirect_trust(g, "0", "6", KHopParams.from_config(SECTION, k=k), target_mean=0.7)
    assert 0.0 <= r.reliability <= P.rho_max
    assert len(r.paths) == len(set(r.first_hops))
