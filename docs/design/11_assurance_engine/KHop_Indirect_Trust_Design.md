# Bounded k-hop indirect evidence (design step A5, indirect-trust part)

| Field | Value |
|---|---|
| Owner | Student 1 (Module 5, indirect trust; plan work division) |
| Version | 1.2, 11 October 2026: role in the decision fixed by ADR-0008 (rule R6_SPARSE) and ES-13 rebuilt. v1.1: edge weight rule added (ADR-0006, awaiting Student 2's confirmation) |
| Source | Overview §5.5 and §5.10 item 2, FR-T-04 and its acceptance criterion, UC-D3/4/5 step 3 and ext 3a, 3b, ES-13 |
| Files | `khop_worked_example.drawio` (graph and calculation), `khop_example_results.md` (generated numbers), `generate_khop_example.py`, `Edge_Weight_Rule_Student2_Confirmation.md` |
| Author note | Drafted with Claude (GenAI); to be disclosed on Form 13 and in the AI usage log. |

## 1. Edge weight rule (ADR-0006)

An edge A→B (role r, metric m) holds what A has verified about B: every VALID outcome in which A is the observer, B the subject, in role r and metric m.

```text
s_w = Σ 2^(-age_days / half_life) over successes      f_w = Σ 2^(-age_days / half_life) over failures
weight(A→B, r, m) = (α0 + s_w) / (α0 + β0 + s_w + f_w)     # recency-weighted Beta posterior mean
evidence_count    = number of outcomes used
```

`α0 = β0 = 1` and the 180-day half-life come from the same versioned config as Student 2's direct estimator (Overview §5.2), so direct and indirect evidence use one formula and one parameter set. The weight is always in (0, 1), as `trust_edge.weight` requires, and an edge exists only when at least one outcome exists, so "no history" never becomes an edge.

| Outcomes A confirmed about B (recent) | Weight |
|---|---|
| 1 success | 0.67 |
| 3 successes | 0.80 |
| 5 successes | 0.86 |
| 18 successes, 2 failures | 0.86 |
| 1 success, 1 failure | 0.50 |
| 1 failure | 0.33 |

**What counts.** Outcomes come only from confirmed closings (`transaction_closed`) or resolved disputes (`dispute_resolved`), as for direct evidence (FR-T-03). Outcomes flagged for re-evaluation (ES-11) are left out, and the edge is recomputed when a flag is set or cleared.

**When it is computed.** `TrustEdgeProjector.on_outcomes()` recomputes the affected edges whenever new outcomes arrive (sequence (b), messages 38–40). Recency drifts slowly: with a 180-day half-life an outcome loses under 2% of its weight in 5 days. So iteration 1 keeps edges current through outcome events alone, and a scheduled refresh is added with the scheduler in iteration 2.

**Why this rule.** It reuses Student 2's estimator, gives visible indirect evidence for ES-13 (the plan risk "k-hop changes nothing"), and is easy to explain. Its weakness is that a single success already gives 0.67. That is accepted because the path decay (0.7 per extra hop), the path-diversity factors and the 0.6 cap bound what thin edges can contribute. The alternatives (lower credible bound; mean × evidence factor) were considered and are recorded in ADR-0006.

## 2. Algorithm

Parameters come from the versioned config (NFR-D-01): `k` (initial 3), `gamma` (0.7), `cap` (0.6).

```text
indirect_evidence(u = lender, v = borrower, role, metric, t_v, b):
    paths = []
    dfs(node = u, path = [u]):                       # bounded, simple paths only
        if len(path) - 1 > k: return
        if node == v and len(path) > 1: paths.append(path); return
        for edge in graph.neighbours(node, role, metric):
            if edge.target not in path: dfs(edge.target, path + [edge.target])
    for P in paths: q(P) = product(edge weights of P) * gamma ** (hops(P) - 1)
    best = {}                                        # strongest path per first-hop neighbour
    for P in paths: if P[1] not in best or q(P) > q(best[P[1]]): best[P[1]] = P
    if best is empty: return none                    # D3 ext 3a: direct evidence or prior only
    I = 1 - product(1 - q(P) for P in best.values()) # noisy-OR
    rho = min(cap, min(1, |best| / 3) * min(1, |first hops| / 2) * I)
    t_indirect = b + rho * (t_v - b)                 # t_v = b and prior_backed = true if v has no direct history
    return IndirectEvidence(paths = best, I, rho, t_indirect, prior_backed)
```

Here |best| equals the number of first hops, because one path is kept per first hop.

**Complexity.** The bounded DFS explores at most Σ_{h≤k} d^h partial paths, O(d^k) for maximum out-degree d; with k = 3 and neighbourhood-sized degrees this is small. Selection is O(|paths|) and noisy-OR O(|first hops|). Latency for k = 1 to 4 is reported, not gated (NFR-P-03).

## 3. Worked example

The 8-node graph in `khop_worked_example.drawio` derives every edge weight from synthetic outcome counts with the rule above, then exercises every property test suite 7 asks for: decay, one path per first hop, noisy-OR, the 0.6 cap, the k bound and cycle safety. At k = 3, three paths are selected (q = 0.54, 0.2195, 0.21), I = 0.7164, ρ = 0.6 (capped) and t_indirect = 0.76, with the illustrative t_v = 0.80 and b = 0.70. The k sweep gives ρ = 0, 0.424, 0.600 and 0.600 for k = 1 to 4. All values are in `khop_example_results.md`, generated by the script, and become the unit-test fixture.

## 4. Role in the decision (ADR-0008)

Overview §5.11: indirect evidence alone never gives SUFFICIENT_EVIDENCE. Because an edge into the borrower exists only when someone has confirmed an outcome about them (§1), a borrower reachable by any path always has some direct history, so ρ can matter only when that history is **sparse**. ADR-0008 therefore adds rule R6_SPARSE to Student 2's decision table: n_eff < 3 and ρ < 0.3 → INSUFFICIENT_EVIDENCE. With ρ ≥ 0.3 the request falls through to R9, REVIEW_RECOMMENDED with safeguards.

**ES-13 (fixture, computed by `14_testing/verify_fixtures.py`).** Borrower v has borrowed once from a and once from b (n_eff 1.77, posterior mean 0.735, 90% CI [0.339, 0.982]) and never from lender u. The edge weights (ADR-0006) are u→a 0.801 (four loans), u→b 0.777 (three loans), a→v 0.658 and b→v 0.648. The two selected paths have q = 0.369 and 0.352, so I = 0.591, ρ = min(0.6, 2/3 × 1 × 0.591) = 0.394 and t_indirect = 0.593. The result is rule R9, **REVIEW_RECOMMENDED**, and the explanation lists both paths. Without the paths the same request is R6_SPARSE, **INSUFFICIENT_EVIDENCE**. This is what the demo shows in step 2.2.

## 5. Open, for Student 2 to confirm

See `Edge_Weight_Rule_Student2_Confirmation.md`: shared estimator and config, which outcomes count, edges of accounts flagged by the manipulation detector, and the refresh timing. Q4 (baseline b = 0.5, `default_population_baseline` in the config) and Q6 (ADR-0008) are now answered by the integrated design; Student 2 still signs the page.
