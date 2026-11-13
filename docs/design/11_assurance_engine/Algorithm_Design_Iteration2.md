# Algorithm and Data Structure Design, Iteration 2 (DA-15 and DA-22)

| Field | Value |
|---|---|
| Owners | Areeba Javed owns Module 5 and the ranking and signs this document; Fatima Khursheed drafted it (plan rule: Minahil does not design detection signals or ranking weights, because she evaluates them) |
| Version | 1.2 draft, 3 November 2026 |
| Status | Draft for the 10 November design gate; needs Areeba's review and signature |
| Builds on | `../11_assurance_engine/Algorithm_and_Data_Structure_Design.md` v1.1 (Algorithms 1 to 4); this document lists only what changes, plus the new Algorithm 5 |
| Config | `Assurance_Engine_Config_v1.4.0.json` (config_version `1.4.0-iteration2-draft`), a superset of the backend's 1.3.0 |
| Worked example | `generate_ranking_example.py` and `ranking_example_results.md` |
| GenAI | Drafted with Claude (Claude Code); reviewed by the owner. Log in `docs/ai-usage-log.md` and on Form 13 |

## 1. What changes

| Change | Algorithm | Requirement | Config key |
|---|---|---|---|
| Estimates per role and metric; the lender role added | 1 | FR-T-02, FR-T-03, FR-S-04 | `trust_estimation_alg1.roles_and_metrics` |
| Pair-repeat discount against trivial exchanges | 1 | FR-T-03, threat model §5.13 | `trust_estimation_alg1.pair_repeat_discount` |
| Population baseline per role and metric | 2, 5 | FR-T-04 baseline b | `indirect_trust_alg2.baseline.population_baseline` |
| Signals S2, S3, S5 active; S5 from invitation links only | 3 | FR-T-05 | `manipulation_detection_alg3.signal_weights`, `s5_linkage` |
| Rule R4 before R3 (proposed, ADR-0010) | 4 | FR-T-06, FR-B-07, review DM09 | `decision_policy_alg4.rule_order` |
| Hybrid ranking for search (new) | 5 | FR-S-01, FR-S-02, FR-S-04 | `ranking_alg5` |

No iteration 1 parameter value changes, so the seven iteration 1 scenarios must still pass with the same states and rules. ES-06 is the exception to check: R4 already fired there, so its result should not change.

## 2. Algorithm 1 changes

**Roles and metrics.** The posterior is computed per (subject, role, metric), never mixing them, as the overview requires. A borrower's request is decided on BORROWER / ON_TIME_RETURN, the metric that protects the lender. A lender's evidence for search and the item page uses LENDER / CONDITION_AGREED ("items are as described"). The other metrics are computed and shown as separate factors, never averaged into one number.

**Pair-repeat discount.** The threat model lists "many short, low-value loans between the same few accounts" as a way to manufacture reputation. In iteration 1, value-band similarity already weights low-value loans down for a high-value request. Iteration 2 adds a discount for repeats with the same counterpart:

```text
w_i := recency(age_i) * max(similarity_floor, sim_i) * factor ^ m_i
m_i  = number of earlier VALID outcomes of the same subject, role and metric with the same observer
       inside window_days before outcome i                       (factor 0.5, window 30 days)
```

*Worked example.* Five on-time loans with the same neighbour within 20 days contribute 1 + 0.5 + 0.25 + 0.125 + 0.0625 = **1.94** effective outcomes instead of 5, so they cannot reach `n_min` = 3 alone. The same five loans with five different neighbours contribute 5. Honest repeat borrowing still counts; it is only bounded. Cost: one pass over the subject's outcomes sorted by time with a per-observer queue, O(n) for n outcomes.

**Sudden high-value requests** (threat model §5.13) need no new rule. A request two value bands above anything the borrower has done has low request similarity, so R4 fires (the iteration 1 design). With ADR-0010, R4 also fires for a borrower with no history.

## 3. Algorithm 2 change: population baseline

The baseline b, the prior mean used when the target has no direct events, was fixed at 0.5. Iteration 2 computes it nightly as the recency-weighted mean of VALID outcomes per (role, metric) across the community. It keeps 0.5 until at least 30 weighted outcomes exist, so a new community is not pulled to a noisy mean. The same value is the neutral lender evidence in Algorithm 5.

## 4. Algorithm 3 changes: all five signals

S2 and S3 keep the iteration 1 definitions and bounds (Algorithm doc §5 table). S5 is narrowed to data the system actually holds:

| Signal | Definition in iteration 2 | Available when |
|---|---|---|
| S2 rating velocity | recent rate (7 d) / baseline rate (83 d); s2 = clamp((ratio − 2) / 3) | at least 3 ratings received in the last 7 days |
| S3 new-account activity | 0 if the account is older than 30 days; else clamp((N − 3) / 7), N = ratings received in 14 days | account at most 30 days old |
| S5 invitation linkage | m = accounts invited by the same inviter as the subject, or invited by the subject, within 90 days, that also rated the subject; s5 = clamp((m − 2) / 8) | the subject joined through an invitation |

Device and network linkage are not collected (FR-A-03 is iteration 3), so S5 uses only the invitation tree that A11 already stores. Unavailable signals are left out and the weights renormalised, exactly as in iteration 1.

**Worked examples** (weights 0.3, 0.2, 0.2, 0.2, 0.1):

| Case | s1 | s2 | s3 | s4 | s5 | Score | Level | Held? |
|---|---|---|---|---|---|---|---|---|
| New-account burst: 10-day-old account, 8 ratings in 14 days, none before, near-identical texts, 4 linked invitees | 0.20 | 1.00 | 0.71 | 0.90 | 0.25 | 60.8 | 4, corroborated (three signals ≥ 0.5) | Yes, R2 |
| Family group of iteration 1 (fixture PU-02), if all five signals are available | 0.83 | 0 | 0 | 0.10 | 0 | 26.9 | 2 | No |

The second row shows an effect worth reporting: when all five signals are available, the family group's score falls from 53.8 (level 3, S1 and S4 only) to 26.9 (level 2). The quiet signals now count as evidence of normal behaviour. Suite 24 keeps this group in CI as the false-positive guard.

## 5. Algorithm 4 change: R4 before R3 (ADR-0010, proposed)

Rule order becomes R1, R2, **R4, R3**, R5, R6_DISPUTE, R6_SPARSE, R7, R8, R9. R4 tests HIGH value only, so the change affects exactly one case: a high-value request from a borrower with no history and community support below `rho_sup`. That request is now held for a moderator (REVIEW_RECOMMENDED with `high_value_low_confidence`) instead of reaching the lender as INSUFFICIENT_EVIDENCE. FR-B-07 states this behaviour, and the review (DM09) found that the code did the opposite. The explanation still says that no history is not a negative finding. Areeba decides and the supervisor accepts; the new test is "HIGH value, zero history, rho 0 → R4, held".

## 6. Algorithm 5: hybrid ranking for search (new)

**Inputs:** query text, filters, the member's communities, optional dates; candidate items from retrieval; lender evidence through `ILenderEvidence`.
**Output:** a ranked list of items, each with `score_parts` (stored in `search_impression`, never shown) and one reason line.

```text
FUNCTION Search(member, query, filters):
    eligible <- items WHERE status = PUBLISHED AND community IN member's communities
                AND owner not blocking member AND owner <> member AND filters hold      // inside the query (I-5)
    kw   <- keyword scores over eligible (full-text 'simple' + trigram), normalised to [0, 1] by the best one
    TRY  sem <- cosine(embed(query), item_embedding) over eligible           // exact scan, no ANN index
    EXCEPT ModelUnavailable: sem <- none; mode <- KEYWORD_ONLY
    cand <- top candidate_pool (100) by (sem if available else kw)
    FOR c IN cand:
        rel   <- 0.7*sem_c + 0.3*kw_c                 (keyword-only mode: rel <- kw_c)
        IF rel < min_relevance (0.25): drop c
        lend  <- mean_LENDER,CONDITION_AGREED(owner) IF n_eff >= n_min ELSE population_baseline
        avail <- 1 if the dates are free of held bookings, 0.5 if no dates given, 0 if a held booking overlaps
        same  <- 1 if c is in the member's home community else 0
        fresh <- 2^(-age_days / 30)
        score <- 0.40*rel + 0.30*lend + 0.15*avail + 0.10*same + 0.05*fresh
    RETURN cand sorted by score, with reason lines; log query, impressions and mode
```

**Why these choices.**
- *The weights* are the overview's Tier 1 formula. Distance becomes same community, because the system stores no coordinates (NFR-PR-01).
- *New lenders get the population baseline*, not a low bound. A lower bound of the 90% interval would give a lender with no history 0.05 and push every newcomer to the bottom, which breaks claim C5 ("newcomers are not excluded"). The worked example shows a new lender scoring exactly what an established lender at the baseline scores.
- *A relevance floor* stops trust from lifting an irrelevant item. In the example, a garden hose with an excellent lender is dropped for the query "drill".
- *Lender evidence is used, never shown as a number.* The reason line names factors ("lender has a confirmed record of items as described") in the same words as the request screen (FR-S-04, NFR-U-01).
- *Keyword mode is a full fallback*, not an error page (FR-S-02), and the logged `mode` lets evaluation separate the two.

**Complexity.** Eligibility filtering is an index scan. Exact cosine search is O(n · d) for n eligible items and d = 384, about 0.2 million multiply-adds for 500 items, then O(n log n) to sort. Re-ranking is O(k) for k ≤ 100 candidates, plus one `ILenderEvidence` call per distinct lender, cached per request. NFR-P-01 and P-02 measure the real latency.

**Worked example.** `ranking_example_results.md`, generated from config 1.4.0, ranks I1 > I2 > I5 > I4 > I3 and drops I6.

**Open question for the evaluation.** In the example, a screwdriver set that is free on the borrower's dates (relevance 0.385) ranks above a hammer drill whose dates are taken (relevance 0.788). Showing unavailable items after the available ones may be right, or they may be better hidden behind a "booked on your dates" separator. The labelled query set (DA-25) decides, before the FYP-1 baseline is frozen.

## 7. Parameters added for the sensitivity study

| Parameter | Initial | Range | Measured by |
|---|---|---|---|
| `pair_repeat_discount.factor` | 0.5 | 0.3 to 1.0 | trivial-exchange attack in the development set; honest repeat borrowers |
| `population_baseline.min_weighted_outcomes` | 30 | 10 to 50 | calibration on the `scale` tier |
| `ranking_alg5.weights.lender_evidence` | 0.30 | 0.10 to 0.40 | precision@5 and exposure of new lenders |
| `ranking_alg5.weights.relevance` | 0.40 | 0.30 to 0.60 | precision@5, NDCG@10 |
| `ranking_alg5.retrieval.min_relevance` | 0.25 | 0.15 to 0.40 | recall@10 |

## 8. Tests this design needs

| Suite | Test | Oracle |
|---|---|---|
| 6 (extended) | Five outcomes with one observer in 20 days give 1.9375 effective outcomes; five observers give 5 | §2 example |
| 9 (extended) | HIGH value, zero history, rho 0 → R4, held; LOW value, zero history → R3, not held | §5 |
| 24 | Burst case → level 4 and held; family group with five signals → level 2; S5 unavailable without an invitation | §4 table |
| 29 | Ranking order I1 > I2 > I5 > I4 > I3 and I6 dropped; new lender equals baseline lender; keyword-only mode when the provider raises | `ranking_example_results.md` |
