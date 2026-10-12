"""Reference oracle for the assurance scenario fixtures (test suite 11) and the policy unit fixtures.

Recomputes, from the inputs in scenario_fixtures_iteration1.json and the parameters in the versioned engine
config, every derived value a fixture states (Beta posterior and 90% interval, trust-edge weights, k-hop paths,
noisy-OR and reliability, manipulation score / level / corroboration, decision-table rule, assurance state,
policy decision, hold reason and lifecycle state) and fails if any stored value disagrees.

It is a design-verification tool, not the production engine: Student 2's engine (Slice B) is tested against the
same fixtures. Pure Python (no SciPy), so it runs anywhere:

    python 14_testing/verify_fixtures.py          -> prints a table, writes fixture_verification_results.md

Algorithms: 11_assurance_engine/Algorithm_and_Data_Structure_Design.md §3-§6, ADR-0006, ADR-0007, ADR-0008.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "scenario_fixtures_iteration1.json")
CONFIG = os.path.join(HERE, "..", "11_assurance_engine", "Assurance_Engine_Config_Draft.json")
TOL = 0.0015            # fixtures store 3-4 decimals


# --------------------------------------------------------------------------- Beta distribution (no SciPy)
def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the regularised incomplete beta function (modified Lentz)."""
    tiny, eps = 1e-300, 1e-15
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 500):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        dl = d * c
        h *= dl
        if abs(dl - 1.0) < eps:
            break
    return h


def beta_cdf(x: float, a: float, b: float) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    bt = math.exp(lbt)
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1 - x) / b


def beta_ppf(q: float, a: float, b: float) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if beta_cdf(mid, a, b) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# --------------------------------------------------------------------------- Algorithm 1 and ADR-0006
def recency_weight(age_days: float, half_life: float) -> float:
    return 2.0 ** (-age_days / half_life)


def posterior(outcomes, a0, b0, half_life, level=0.90):
    """outcomes: [{age_days, success, similarity?}] -> dict like TrustEstimate."""
    s = f = 0.0
    for o in outcomes:
        w = recency_weight(o["age_days"], half_life) * o.get("similarity", 1.0)
        if o["success"]:
            s += w
        else:
            f += w
    return estimate(a0 + s, b0 + f, a0, b0, level, count=len(outcomes))


def estimate(alpha, beta, a0, b0, level=0.90, count=None):
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    return dict(alpha=alpha, beta=beta, mean=alpha / (alpha + beta), lower_90=beta_ppf(lo_q, alpha, beta),
                upper_90=beta_ppf(hi_q, alpha, beta), n_eff=alpha + beta - a0 - b0, direct_event_count=count)


def edge_weight(outcomes, a0, b0, half_life):
    """ADR-0006: recency-weighted Beta posterior mean of what the source confirmed about the target."""
    return posterior(outcomes, a0, b0, half_life)["mean"]


# --------------------------------------------------------------------------- Algorithm 2 (bounded k-hop)
def khop(edges: dict, u: str, v: str, k: int, gamma: float, cap: float, path_div: float, div_div: float,
         baseline: float, t_v: float | None):
    """edges: {(src, dst): weight}. Returns selected paths (strongest per first hop), I, rho, t_indirect."""
    out = {}
    for (a, b), w in edges.items():
        out.setdefault(a, []).append((b, w))
    paths = []

    def dfs(node, path, prod):
        for nxt, w in out.get(node, []):
            if nxt in path:
                continue                                   # simple paths only (cycle-safe)
            if nxt == v:
                paths.append((path + [v], prod * w))
            elif len(path) < k:                            # path has len(path)-1 edges so far
                dfs(nxt, path + [nxt], prod * w)

    if u != v:
        dfs(u, [u], 1.0)
    best = {}
    for nodes, prod in paths:
        hops = len(nodes) - 1
        q = prod * gamma ** (hops - 1)
        if nodes[1] not in best or q > best[nodes[1]][1]:
            best[nodes[1]] = (nodes, q)
    if not best:
        return dict(paths=[], I=0.0, rho=0.0, estimate=baseline, prior_backed=t_v is None)
    not_i = 1.0
    for _, q in best.values():
        not_i *= 1 - q
    big_i = 1 - not_i
    rho = min(cap, min(1.0, len(best) / path_div) * min(1.0, len(best) / div_div) * big_i)
    tv = baseline if t_v is None else t_v
    return dict(paths=[dict(nodes=n, hops=len(n) - 1, path_weight=q) for n, q in best.values()],
                I=big_i, rho=rho, estimate=baseline + rho * (tv - baseline), prior_backed=t_v is None)


# --------------------------------------------------------------------------- Algorithm 3 (ADR-0007)
def manipulation(signals, weights, guard):
    avail = [s for s in signals if s.get("available", True)]
    if not avail:
        return dict(score=0.0, level=1, corroborated=False)
    num = sum(weights[s["name"]] * s["value"] for s in avail)
    den = sum(weights[s["name"]] for s in avail)
    score = min(100.0, 100.0 * num / den)
    level = 1 if score < 20 else 2 if score < 40 else 3 if score < 60 else 4
    corroborated = sum(1 for s in avail if s["value"] >= guard["min_signal_threshold"]) >= guard["required_corroborating_signals"]
    if level == 4 and not corroborated:
        level = 3
    return dict(score=score, level=level, corroborated=corroborated)


# --------------------------------------------------------------------------- Algorithm 4 (decision table)
RULES = {"R1": ("ESCALATE", "ACTIVE_DISPUTE", None), "R2": ("ESCALATE", "REVIEW_RECOMMENDED", "manipulation_risk"),
         "R3": ("REQUEST_VERIFICATION", "INSUFFICIENT_EVIDENCE", None),
         "R4": ("RESTRICT_HIGH_VALUE", "REVIEW_RECOMMENDED", "high_value_low_confidence"),
         "R5": ("REQUEST_VERIFICATION", "REVIEW_RECOMMENDED", None),
         "R6_DISPUTE": ("PROCEED_WITH_SAFEGUARDS", "REVIEW_RECOMMENDED", None),
         "R6_SPARSE": ("REQUEST_VERIFICATION", "INSUFFICIENT_EVIDENCE", None),
         "R7": ("PROCEED", "SUFFICIENT_EVIDENCE", None), "R8": ("PROCEED_WITH_SAFEGUARDS", "SUFFICIENT_EVIDENCE", None),
         "R9": ("PROCEED_WITH_SAFEGUARDS", "REVIEW_RECOMMENDED", None)}


def decide(direct, rho, level, ctx, th, similarity_floor):
    """First match wins (Algorithm doc §6 as amended by ADR-0007, ADR-0008 and decision D12)."""
    if ctx["open_dispute"]:
        return "R1"
    if level == 4:
        return "R2"
    if direct["direct_event_count"] == 0 and rho < th["rho_sup_indirect_support_threshold"]:
        return "R3"
    if ctx["is_high_value"] and (ctx["request_similarity"] < similarity_floor
                                 or direct["lower_90"] < th["tau_L_lower_bound_threshold"]):
        return "R4"
    if level == 3:
        return "R5"
    if ctx["resolved_disputes_12m"] > 0:
        return "R6_DISPUTE"
    if direct["n_eff"] < th["n_min_effective_observations"] and rho < th["rho_sup_indirect_support_threshold"]:
        return "R6_SPARSE"
    strong = (direct["mean"] >= th["tau_mu_mean_threshold"] and direct["lower_90"] >= th["tau_L_lower_bound_threshold"]
              and direct["n_eff"] >= th["n_min_effective_observations"])
    if strong and level == 1 and ctx["verification_ok"] and not ctx["medium_value"] and not ctx["is_high_value"]:
        return "R7"
    if strong and level <= 2 and ctx["verification_ok"]:
        return "R8"
    return "R9"


# --------------------------------------------------------------------------- fixture checking
class Checker:
    def __init__(self):
        self.problems = []

    def num(self, fid, what, stored, computed, tol=TOL):
        if stored is None:
            return
        if abs(float(stored) - float(computed)) > tol:
            self.problems.append(f"{fid}: {what} stored {stored} but computed {computed:.4f}")

    def same(self, fid, what, stored, computed):
        if stored is not None and stored != computed:
            self.problems.append(f"{fid}: {what} stored {stored!r} but computed {computed!r}")


def run():
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    fx = json.load(open(FIXTURES, encoding="utf-8"))
    t1, t2 = cfg["trust_estimation_alg1"], cfg["indirect_trust_alg2"]
    m3, p4 = cfg["manipulation_detection_alg3"], cfg["decision_policy_alg4"]
    a0, b0 = t1["prior"]["alpha_0"], t1["prior"]["beta_0"]
    h = t1["recency_decay"]["half_life_days"]
    level_ci = t1["credible_interval"]["confidence_level"]
    k, gamma = t2["graph_traversal"]["max_hops_k"], t2["attenuation_decay"]["hop_decay_gamma"]
    agg, base = t2["aggregation"], t2["baseline"]["default_population_baseline"]
    weights = dict(m3["signal_weights"]["weights"])
    active = set(m3["signal_weights"]["iteration_1_active"])
    th, floor = p4["thresholds"], t1["similarity_weighting"]["similarity_floor"]
    chk = Checker()
    if fx["metadata"]["config_version"] != cfg["config_metadata"]["config_version"]:
        chk.problems.append("fixtures and engine config have different config_version")
    rows = []
    for f in fx["fixtures"] + fx.get("policy_unit_fixtures", []):
        fid, ctx, de = f["scenario_id"], f["transaction_context"], f["direct_evidence"]
        # ---- direct evidence
        if "outcomes" in de:
            d = posterior(de["outcomes"], a0, b0, h, level_ci)
            chk.num(fid, "alpha", de.get("alpha"), d["alpha"])
            chk.num(fid, "beta", de.get("beta"), d["beta"])
        else:
            d = estimate(de["alpha"], de["beta"], a0, b0, level_ci, count=de["direct_event_count"])
        d["direct_event_count"] = de["direct_event_count"]
        for key in ("mean", "lower_90", "upper_90", "n_eff"):
            chk.num(fid, f"direct.{key}", de.get(key), d[key])
        # ---- indirect evidence
        ie = f.get("indirect_evidence", {})
        t_v = d["mean"] if d["direct_event_count"] else None
        if "edge_outcomes" in ie:
            edges = {}
            for e in ie["edge_outcomes"]:
                wgt = edge_weight(e["outcomes"], a0, b0, h)
                edges[(e["source"], e["target"])] = wgt
                chk.num(fid, f"edge {e['source']}->{e['target']}", e.get("weight"), wgt)
            ind = khop(edges, ie["lender"], ie["borrower"], k, gamma, agg["reliability_cap_rho_max"],
                       agg["path_count_divisor"], agg["diversity_divisor"], base, t_v)
            stored_paths = {tuple(p["nodes"]): p["path_weight"] for p in ie.get("paths", [])}
            got_paths = {tuple(p["nodes"]): p["path_weight"] for p in ind["paths"]}
            chk.same(fid, "selected paths", sorted(stored_paths), sorted(got_paths))
            for nodes, q in got_paths.items():
                chk.num(fid, f"q{list(nodes)}", stored_paths.get(nodes), q)
        else:
            ind = dict(rho=ie.get("reliability_rho", 0.0), I=ie.get("evidence_strength_I", 0.0),
                       estimate=None, prior_backed=t_v is None)
            if ie.get("paths"):
                qs = [p["path_weight"] for p in ie["paths"]]
                n = len(qs)
                big_i = 1 - math.prod(1 - q for q in qs)
                ind["I"] = big_i
                ind["rho"] = min(agg["reliability_cap_rho_max"], min(1, n / agg["path_count_divisor"])
                                 * min(1, n / agg["diversity_divisor"]) * big_i)
                tv = base if t_v is None else t_v
                ind["estimate"] = base + ind["rho"] * (tv - base)
        chk.num(fid, "indirect.I", ie.get("evidence_strength_I"), ind["I"])
        chk.num(fid, "indirect.rho", ie.get("reliability_rho"), ind["rho"])
        if ind.get("estimate") is not None:
            chk.num(fid, "indirect.estimate", ie.get("estimate"), ind["estimate"])
        chk.same(fid, "indirect.prior_backed", ie.get("prior_backed"), ind["prior_backed"])
        # ---- manipulation
        mr = f["manipulation_risk"]
        if "signals" in mr:
            for s in mr["signals"]:
                if s["name"] not in active:
                    chk.problems.append(f"{fid}: signal {s['name']} is not active in iteration 1")
                chk.num(fid, f"weight of {s['name']}", s.get("weight"), weights[s["name"]])
            m = manipulation(mr["signals"], weights, m3["corroboration_guard"])
            chk.num(fid, "manipulation.score", mr.get("score"), m["score"], tol=0.05)
        else:
            sc = mr["score"]
            m = dict(score=sc, corroborated=mr.get("corroborated", False))
            m["level"] = 1 if sc < 20 else 2 if sc < 40 else 3 if sc < 60 or not m["corroborated"] else 4
        chk.same(fid, "manipulation.level", mr.get("level"), m["level"])
        chk.same(fid, "manipulation.corroborated", mr.get("corroborated"), m["corroborated"])
        # ---- value band consistency (config thresholds)
        vb = p4["value_bands_pkr"]
        v = ctx["item_value_pkr"]
        band = "LOW" if v <= vb["low_value_max"] else "MEDIUM" if v <= vb["medium_value_max"] else "HIGH"
        chk.same(fid, "value_band", ctx["value_band"], band)
        chk.same(fid, "is_high_value", ctx["is_high_value"], band == "HIGH")
        chk.same(fid, "medium_value", ctx["medium_value"], band == "MEDIUM")
        if ctx["verification_level"] not in ("UNVERIFIED", "CONTACT_VERIFIED", "COMMUNITY_VERIFIED"):
            chk.problems.append(f"{fid}: verification_level {ctx['verification_level']!r} is not a schema value (D14)")
        # ---- policy
        rule = decide(d, ind["rho"], m["level"], ctx, th, floor)
        decision, state, hold = RULES[rule]
        exp = f["expected_result"]
        chk.same(fid, "rule_fired", exp["rule_fired"], rule)
        chk.same(fid, "decision", exp["decision"], decision)
        chk.same(fid, "state", exp["state"], state)
        chk.same(fid, "escalate", exp.get("escalate"), hold is not None)
        chk.same(fid, "hold_reason", exp.get("hold_reason"), hold)
        chk.same(fid, "lifecycle_state", exp["lifecycle_state"], "HELD_FOR_REVIEW" if hold else "ASSESSED")
        cf = f.get("counterfactual_without_paths")
        if cf:
            rule_cf = decide(d, 0.0, m["level"], ctx, th, floor)
            chk.same(fid, "counterfactual rule", cf["rule_fired"], rule_cf)
            chk.same(fid, "counterfactual state", cf["state"], RULES[rule_cf][1])
        rows.append((fid, f["name"], rule, state, "HELD_FOR_REVIEW" if hold else "ASSESSED", hold or "—",
                     f"{d['mean']:.3f} [{d['lower_90']:.3f}, {d['upper_90']:.3f}], n_eff {d['n_eff']:.2f}",
                     f"{ind['rho']:.3f}", f"{m['score']:.1f} / L{m['level']}"))
    return rows, chk.problems, cfg["config_metadata"]["config_version"]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows, problems, cv = run()
    lines = ["# Fixture verification results", "",
             f"Generated by `verify_fixtures.py` (do not edit by hand). Config `{cv}`. "
             "Each row is recomputed from the fixture inputs; the run fails on any mismatch.", "",
             "| Fixture | Name | Rule | Assurance state | Lifecycle state | Hold reason | Direct: mean [90% CI], n_eff | ρ | Risk / level |",
             "|---|---|---|---|---|---|---|---|---|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    lines += ["", f"**{len(rows) - len({p.split(':')[0] for p in problems})}/{len(rows)} fixtures consistent**"]
    if problems:
        lines += ["", "Problems:", ""] + [f"- {p}" for p in problems]
    with open(os.path.join(HERE, "fixture_verification_results.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
