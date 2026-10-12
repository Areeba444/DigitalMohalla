# Algorithm and Data Structure Design
## Assurance Engine: Recency-Weighted Beta Posterior, Bounded k-Hop Trust, Manipulation-Risk Scoring and Decision Policy

| Field | Value |
|---|---|
| Project / module | Digital Mohalla, Module 5 Trust and Assurance Engine (design step A5) |
| Owner | Student 2 (estimation, detection, policy); §4 indirect trust shared with Student 1 (ADR-0006) |
| Version | 1.1, 11 October 2026. v1.0 (Student 2): final design baseline. v1.1 (integration): S4 active in iteration 1 and the level-4 corroboration rule made normative (ADR-0007); rule R6_SPARSE added and R1 no longer holds (ADR-0008, decision D12); contract fields `hold_reason` and `config_version` added |
| Status | Design baseline; awaiting A14 second-member review and Student 2's initials on ADR-0007 and ADR-0008 |
| Config | `Assurance_Engine_Config_Draft.json`, version 1.1.0-iteration1-draft |
| Handbook item | Design Phase, Data Structure and Algorithm Design |

> **Source of truth.** Overview section 5 (5.2 Beta posterior, 5.5 k-hop, 5.6 and 5.13 manipulation, 5.8 decision policy, 5.11 assurance states, 5.12 verified evidence) and the use cases D3/4/5, D6, I4. Where earlier defense notes differ (prior Beta(2,2), averaged paths, the 0 to 50 signal scale, the 6.6% to 95% interval), this document replaces them. All thresholds, weights and half-lives are **initial hypotheses to be tested**, not measured results.

---

## 1. Purpose, scope and conventions

For a request by user \(u\) to borrow from target \(v\), in role \(r\) and metric \(m\) (e.g. `borrower / returned_on_time`), the engine produces an **assurance result** describing the *evidence for this transaction*, never a verdict on a person.

```
Direct evidence -> Beta posterior -> k-hop indirect -> Manipulation risk -> Context policy -> Decision + Assurance state + Safeguards + Explanation
   (Alg. 1)           (Alg. 1)         (Alg. 2)          (Alg. 3)            (Alg. 4)
```

Conventions: roles and metrics are never mixed; raw events are immutable and derived estimates are recomputed when parameters change; trust and manipulation risk stay **separate dimensions** (never averaged); no single trust number is ever shown to users.

---

## 2. Data structures (contracts that become domain-model classes)

```text
OutcomeEvent {                       // immutable evidence
    event_id, subject_id, observer_id, transaction_id
    role: Role, metric: Metric
    success: bool
    status: CONFIRMED | DISPUTED | RESOLVED     // only CONFIRMED/RESOLVED count
    handover_confirmed: bool, return_confirmed: bool
    item_category, value_band, duration_days    // for similarity weighting
    occurred_at: timestamp
}
TrustEdge { source_id, target_id, role, metric, weight: [0,1], evidence_count, updated_at }
            // weight DERIVED from source's verified direct evidence, never a free vouch
TrustEstimate { subject_id, role, metric, alpha, beta, mean, lower_90, upper_90,
                effective_sample_size, direct_event_count, computed_at }
PathEvidence { nodes: list<id>, hops: int, path_weight: float }
IndirectTrustResult { requester_id, target_id, role, metric, paths_used: list<PathEvidence>,
                      evidence_strength I, reliability rho, diversity, estimate, prior_backed: bool }
ManipulationSignal { name, available: bool, value: [0,1], weight, evidence: list<string> }
ManipulationRiskAssessment { score: [0,100], level: 1..4, signals: list<ManipulationSignal>,
                             corroborated: bool }
TransactionContext { item_value, value_band, is_high_value: bool, medium_value: bool,
                     category_restricted: bool, transaction_type,
                     open_dispute: bool, resolved_disputes_12m: int,
                     verification_level, verification_ok: bool, request_similarity: [0,1] }
SafeguardRecommendation { type, parameters, reason }
DecisionPolicyResult { decision: PROCEED | PROCEED_WITH_SAFEGUARDS | REQUEST_VERIFICATION
                                 | RESTRICT_HIGH_VALUE | ESCALATE,
                       safeguards: list<SafeguardRecommendation>, escalate: bool, rule_fired: string,
                       hold_reason: manipulation_risk | high_value_low_confidence | none }
                       // escalate = (hold_reason != none): the lifecycle holds the request (ADR-0003, D12)
AssuranceResult { state: SUFFICIENT_EVIDENCE | REVIEW_RECOMMENDED | INSUFFICIENT_EVIDENCE | ACTIVE_DISPUTE,
                  direct: TrustEstimate, indirect: IndirectTrustResult,
                  manipulation: ManipulationRiskAssessment, decision: DecisionPolicyResult,
                  explanation: list<EvidenceRecord>, computed_at: timestamp, config_version: string }
EvidenceRecord { factor, value, confidence, supporting_event_ids }   // one per displayed factor
```

Indexing: events by `(subject, role, metric)`; edges by `(source, role, metric)` outgoing and `(target, role, metric)` incoming.

---

## 3. Algorithm 1: Recency-weighted Beta posterior

**Inputs:** subject, role, metric, outcome events, prior \((\alpha_0,\beta_0)\), half-life \(h\), request similarity profile (optional).
**Outputs:** `TrustEstimate` (posterior mean, 90% credible interval, effective evidence count).
**Parameters:** \(\alpha_0=\beta_0=1\), \(h=180\) days, interval level 90%.

**Model.** Each outcome is Bernoulli(\(p\)) with \(p\sim\mathrm{Beta}(\alpha_0,\beta_0)\). The posterior is **Beta** (conjugate); the *Beta-Binomial* is the posterior-predictive for a future count of successes and is not the name of the posterior.

For an outcome \(d_i\) days old with similarity \(\sigma_i\in(0,1]\) to the requested item (same category, value band, duration; \(\sigma_i=1\) if unused):

\[
w_i = 2^{-d_i/h}\,\sigma_i,\quad s_w=\sum_i w_i y_i,\quad f_w=\sum_i w_i(1-y_i),\quad
\alpha=\alpha_0+s_w,\ \beta=\beta_0+f_w
\]
\[
\mu=\frac{\alpha}{\alpha+\beta},\qquad CI_{90}=[Q_{0.05},Q_{0.95}]\text{ of Beta}(\alpha,\beta),\qquad n_{\text{eff}}=\sum_i w_i .
\]

```text
FUNCTION EstimateDirectTrust(subject, role, metric, events, a0, b0, half_life, profile):
    alpha <- a0 ; beta <- b0 ; n_eff <- 0 ; n_raw <- 0
    FOR each e IN events WHERE e.subject_id=subject AND e.role=role AND e.metric=metric:
        IF e.status = DISPUTED OR NOT (e.handover_confirmed AND e.return_confirmed): CONTINUE
        IF e.occurred_at > Now(): RAISE ValidationError
        w <- 2 ^ ( -DaysBetween(e.occurred_at, Now()) / half_life )
        IF profile given: w <- w * Similarity(e, profile)       // in (0,1]
        IF e.success: alpha += w ELSE beta += w
        n_eff += w ; n_raw += 1
    RETURN TrustEstimate(alpha, beta, alpha/(alpha+beta),
                         BetaQuantile(0.05,alpha,beta), BetaQuantile(0.95,alpha,beta), n_eff, n_raw)
```

**Worked examples (exact).**
* No events: Beta(1,1), mean 0.5, CI [0.05, 0.95]. This is "no evidence", **not** "bad user".
* One success: Beta(2,1), mean 0.667, CI [0.224, 0.975] (quantiles \(\sqrt{0.05},\sqrt{0.95}\)). Very wide.
* 18 successes, 2 failures: Beta(19,3), mean 0.864, narrow interval (compute with the quantile function; never copy an unverified interval).
* Decay: success today (w=1), success 180 d ago (0.5), failure 360 d ago (0.25) gives Beta(2.5, 1.25), mean 0.667, \(n_{\text{eff}}=1.75\).

**Complexity:** \(O(n)\) time for \(n\) relevant events, \(O(1)\) extra space; \(O(1)\) amortised if \(\alpha,\beta\) are cached and updated incrementally (decay is then re-applied lazily on read).

**Edge cases:** no events returns the prior; all-success or all-failure stays finite (prior is non-zero); disputed or unconfirmed events are skipped until resolved; future timestamps are rejected; \(h\le 0\) is invalid; \(n_{\text{eff}}\) is a diagnostic, not a trust multiplier.

---

## 4. Algorithm 2: Bounded k-hop indirect trust

**Inputs:** requester \(u\), target \(v\), role, metric, trust graph, target's `TrustEstimate`, baseline \(b\) (role/metric population mean).
**Outputs:** `IndirectTrustResult` (indirect estimate and reliability \(\rho\) as its confidence).
**Parameters:** \(k=3\), \(\gamma=0.7\), \(\rho_{\max}=0.6\), path-count divisor 3, diversity divisor 2.

Edge \(x\to y\): \(x\)'s verified evidence supports \(y\) (same role, metric). Path \(P=(x_0{=}u,\dots,x_l{=}v)\), \(l\le k\):

\[
q(P)=\Big(\prod_{j} e(x_j,x_{j+1})\Big)\gamma^{\,l-1},\quad
I=1-\prod_{P\in\mathcal P}(1-q(P)),\quad
\rho=\min\!\Big(\rho_{\max},\ \min(1,\tfrac{|\mathcal P|}{3})\min(1,\tfrac{|\text{first hops}|}{2})\,I\Big),
\]
\[
t_{\text{ind}}=b+\rho\,(t_v-b),\qquad t_v=\text{target direct mean, else }b\ (\text{then } \texttt{prior\_backed}=\text{true}).
\]

The first hop is not penalised; each extra hop is multiplied by \(\gamma\). Keep **at most one (strongest) path per first-hop intermediary** so correlated paths are not counted as independent. Noisy-OR combines independent evidence without exceeding 1.

```text
FUNCTION BoundedSimplePaths(graph, src, dst, role, metric, k):
    results <- [] ; stack <- [ ([src], 1.0) ]
    WHILE stack not empty:
        (path, prod) <- POP(stack) ; node <- LAST(path)
        FOR each edge IN graph.out(node, role, metric):
            IF edge.target IN path: CONTINUE                 // no cycles
            newprod <- prod * edge.weight
            IF edge.target = dst: results.ADD(path+[dst], newprod)
            ELSE IF LENGTH(path) < k:                        // path has LENGTH-1 edges so far
                PUSH(stack, (path+[edge.target], newprod))
    RETURN results

FUNCTION EstimateIndirectTrust(graph, u, v, role, metric, target_est, baseline, k, gamma):
    IF u = v: RETURN none
    cands <- KeepStrongestPerFirstHop( BoundedSimplePaths(graph,u,v,role,metric,k) )  // by q(P)
    IF cands empty: RETURN (estimate=baseline, reliability=0)
    notI <- 1
    FOR each P IN cands: P.weight <- P.product * gamma^(P.hops-1) ; notI <- notI * (1 - P.weight)
    I <- 1 - notI
    div <- MIN(1, DistinctFirstHops(cands)/2)
    rho <- MIN(0.6, MIN(1, LENGTH(cands)/3) * div * I)
    t_v <- target_est.mean IF target_est.direct_event_count > 0 ELSE baseline
    RETURN (cands, I, rho, div, baseline + rho*(t_v-baseline), prior_backed = (target_est.direct_event_count = 0))
```

**Worked example.** \(u\to a\to v\): 0.9, 0.8 gives \(q=0.72\times0.7=0.504\). \(u\to b\to v\): 0.8, 0.9 gives 0.504. \(u\to c\to d\to v\): 0.9, 0.8, 0.7 gives \(0.504\times0.49=0.247\). Three distinct first hops: \(I=1-(0.496)^2(0.753)=0.815\), \(\rho=\min(0.6,0.815)=0.6\). With target mean 0.864 and \(b=0.5\): \(t_{\text{ind}}=0.5+0.6(0.364)=0.718\), always below the direct mean.

**Complexity:** worst case \(O(\sum_{i=1}^{k}\Delta^i)\) time for max out-degree \(\Delta\); \(O(k)\) state per stack frame; \(O(|\mathcal P|)\) for aggregation. In production, cap candidates per node (top-\(m\) edges by weight) to stay near \(O(m^k)\).

**Edge cases:** no path gives \(\rho=0\) and the baseline; disconnected users are never inferred trustworthy; cycles and self paths are excluded; shared intermediaries get no extra diversity credit; an edge built from the same event as the direct estimate must not be counted twice (record the dependency).

> **Design note D-1 (limitation to state openly; its effect on decisions is settled by ADR-0008).** When the target has *no* direct evidence, \(t_v=b\) so \(t_{\text{ind}}=b\): indirect evidence then contributes only **reliability and the "prior-backed" label**, not a raised estimate. When direct evidence exists, \(t_{\text{ind}}\) is a *shrunken copy* of it. The policy therefore treats \(\rho\) as supporting context (section 6): with sparse direct evidence, \(\rho\ge\rho_{\text{sup}}\) keeps the request out of R6_SPARSE (REVIEW_RECOMMENDED instead of INSUFFICIENT_EVIDENCE). Note that under ADR-0006 a borrower reachable by any path always has some direct history, so R3's \(\rho\) clause can never change R3's outcome. The ablation study should compare this against a variant that propagates the last-hop observers' own outcomes with \(v\).

---

## 5. Algorithm 3: Manipulation-risk scoring (overview 5.6, 5.13)

**Inputs:** ratings given and **received** (separate sets), account metadata, review text, optional device/IP/invite linkage, window \(W\).
**Outputs:** `ManipulationRiskAssessment` (score 0 to 100, level, per-signal evidence).
It is a **risk detector, not proof of fraud**; it never changes transaction records and never restricts anyone automatically.

| # | Signal | Input data | Normalised value \(s_i\in[0,1]\) | Evidence shown | Initial weight |
|---|---|---|---|---|---|
| S1 | Reciprocal-rating clustering | out-neighbours \(O\), in-neighbours \(In\) within \(W\); needs \(\lvert O\rvert\ge3\) | \(r=\lvert O\cap In\rvert/\lvert O\rvert\); \(s_1=\mathrm{clamp}\big((r-0.3)/0.6\big)\) | partner list, mutual fraction | 0.30 |
| S2 | Rating velocity | counts in last 7 d vs prior 83 d; needs \(\ge3\) recent | ratio \(=\) recent rate / (baseline rate \(+\epsilon\)); \(s_2=\mathrm{clamp}\big((\text{ratio}-2)/3\big)\) | the two rates, ratio | 0.20 |
| S3 | New-account activity | account age; ratings received in last 14 d | 0 if age > 30 d; else \(\mathrm{clamp}\big((N-3)/7\big)\) | age, N, rater ids | 0.20 |
| S4 | Review similarity | review texts (char n-gram TF-IDF, works for Roman Urdu) | max pairwise cosine \(c\); \(s_4=\mathrm{clamp}\big((c-0.7)/0.25\big)\) | the similar review pairs | 0.20 |
| S5 | Linkage (optional) | accounts sharing device/IP/invite where legitimately available | \(m\) = other linked accounts; \(s_5=\mathrm{clamp}\big((m-2)/8\big)\) | linked-account count | 0.10 |

> **Iteration 1 (Mid-1) Scope Note (ADR-0007).** In Iteration 1, the engine actively deploys **S1 (Reciprocal-rating clustering)**, **S4 (Review text similarity)** and the **Suspected Retaliation Check** (below). Signals S2 (velocity), S3 (new-account activity) and S5 (linkage) are fully designed above but activated in Iteration 2. S4 is needed in iteration 1 because level 4 requires two corroborating signals: with S1 alone no request could be held, and ES-04 would fail. When S2, S3 and S5 are unavailable, the combination rule renormalises active weights over available signals as defined below.

**Suspected Retaliation Check (FR-T-09, ES-05):**
- **Trigger:** A rating/review submitted by party \(A\) against party \(B\) within \(W_{\text{retaliation}} = 14\) days following an adverse complaint, dispute opening, or low rating filed by \(B\) against \(A\).
- **Condition:** The submitted rating is negative (failure/poor condition claim) but conflicts with objective transaction records (e.g., both handover and return confirmations are confirmed: `handover_confirmed = true` AND `return_confirmed = true`).
- **Action:** The event is flagged with `retaliation_suspected = true`. It is down-weighted in evidence calculation (\(w_i \leftarrow 0.1 \cdot w_i\) or excluded pending moderator review) and attached as an anomaly record to the transaction explanation, preventing reputation sabotage without accusing the user.

**Combination rule.** Unavailable signals (e.g. no linkage data) are excluded and the remaining weights renormalised:
\[
\text{score}=\min\!\Big(100,\ 100\cdot\frac{\sum_{i\in A} w_i s_i}{\sum_{i\in A} w_i}\Big).
\]
Levels: **1** 0 to 19 proceed normally, **2** 20 to 39 monitor, **3** 40 to 59 request additional verification, **4** 60 to 100 flag for moderator review (restrict only after a human decision). **Corroboration rule (false-positive guard, normative by ADR-0007):** level 4 requires at least two signals with \(s_i\ge0.5\); otherwise the level is capped at 3. Only level 4 holds the request (rule R2).

```text
FUNCTION AssessManipulation(subject, data, W, weights):
    signals <- [ S1(...), S2(...), S3(...), S4(...), S5(...) ]   // each: value, available, evidence
    A <- signals WHERE available
    IF A empty: RETURN (score=0, level=1, note="no data")
    score <- MIN(100, 100 * SUM(w_i*s_i over A) / SUM(w_i over A))
    level <- BAND(score)                                           // 1..4
    corroborated <- COUNT(s_i >= 0.5 over A) >= 2
    IF level = 4 AND NOT corroborated: level <- 3
    RETURN ManipulationRiskAssessment(score, level, signals, corroborated)
```

**Worked examples.** *Friend group* (all of S1 to S4 available): \(r=0.8\Rightarrow s_1=0.83\), others 0, no linkage: \(100\times0.30\times0.83/0.9=27.8\), level 2 (monitor), not escalated. *Friend group in iteration 1* (S1 and S4 only): \(s_1=0.83, s_4=0.10\): \(100\times(0.249+0.02)/0.5=53.8\), level 3, not held (fixture PU-02). *Single strong signal*: \(s_1=1.0, s_4=0.2\): 68, uncorroborated, capped at level 3 (PU-01). *Colluding group* (ES-04): \(s_1=1.0, s_4=0.92\): 96.8, corroborated, level 4. *Fraud ring*: all signals 1 gives 100, corroborated, level 4.

**Complexity:** S1 \(O(\deg)\) with hash sets; S2 and S3 \(O(R)\) over ratings in window; S4 \(O(m^2L)\) for \(m\) reviews of length \(L\) (bounded by capping \(m\) per window, or use nearest-neighbour hashing); S5 \(O(1)\) with an index. Total \(O(\deg+R+m^2L)\) per subject.

**Edge cases:** insufficient observations make the signal *unavailable*, not zero-evidence-of-fraud; reciprocity must be computed against the **received** set, not inferred from the user's own submissions; windows are isolated so old activity does not fire velocity; family or friend groups are expected to produce S1, which is why S1 alone can never reach level 4; retaliation flags isolate dispute fallout from legitimate transaction evidence.

---

## 6. Algorithm 4: Decision policy and assurance-state mapping (overview 5.8, 5.11)

**Inputs:** direct `TrustEstimate`, `IndirectTrustResult`, `ManipulationRiskAssessment`, `TransactionContext` (value, type, dispute history, verification status, request similarity).
**Outputs:** decision, one of four assurance states, safeguards, escalation flag, explanation.
**Parameters:** \(\tau_\mu=0.75\) (mean), \(\tau_L=0.60\) (lower 90% bound), \(n_{\min}=3\) effective observations, \(\rho_{\text{sup}}=0.3\), similarity floor 0.5, high-value band set by community config.

Uncertainty-aware: a high mean with a low lower bound (sparse evidence) is **not** "sufficient". Check: Beta(6,1) has lower bound 0.607, so about five clean recent outcomes are needed to clear \(\tau_L\).

**Rules (first match wins):**

| # | Condition | Decision | State | Escalate |
|---|---|---|---|---|
| R1 | open dispute affects the parties/transaction | ESCALATE | ACTIVE_DISPUTE | no: reaches the lender as ACTIVE_DISPUTE; the dispute already has its own case (D12) |
| R2 | manipulation level 4 (score ≥ 60 and corroborated, ADR-0007) | ESCALATE | REVIEW_RECOMMENDED | yes (`manipulation_risk`) |
| R3 | no verified direct history AND \(\rho<\rho_{\text{sup}}\) | REQUEST_VERIFICATION | INSUFFICIENT_EVIDENCE | no (lender review required) |
| R4 | high value AND (similarity < 0.5 OR lower bound < \(\tau_L\)) | RESTRICT_HIGH_VALUE | REVIEW_RECOMMENDED | yes (`high_value_low_confidence`, pending human) |
| R5 | manipulation level 3 | REQUEST_VERIFICATION | REVIEW_RECOMMENDED | no |
| R6_DISPUTE | resolved dispute in last 12m (ES-03) | PROCEED_WITH_SAFEGUARDS | REVIEW_RECOMMENDED | no |
| R6_SPARSE | \(n_{\text{eff}}<n_{\min}\) AND \(\rho<\rho_{\text{sup}}\): sparse direct evidence without community support (ADR-0008) | REQUEST_VERIFICATION | INSUFFICIENT_EVIDENCE | no (lender review required) |
| R7 | \(\mu\ge\tau_\mu\), \(L\ge\tau_L\), \(n_{\text{eff}}\ge n_{\min}\), no recent disputes, level 1, standard value, verification ok | PROCEED | SUFFICIENT_EVIDENCE | no |
| R8 | as R7 but level 2, medium-value, or high-value with strong evidence | PROCEED_WITH_SAFEGUARDS | SUFFICIENT_EVIDENCE | no |
| R9 | fall-through: sparse direct evidence supported by community paths (\(\rho\ge\rho_{\text{sup}}\), ES-13), lower bound < \(\tau_L\), or unverified | PROCEED_WITH_SAFEGUARDS | REVIEW_RECOMMENDED | no |
| E | engine failure/timeout | route to human review, log failure | (no default state) | yes |

**Resolution of Issue N-7 (Hold vs. Review for High-Value Transactions):**
- **Weak or Dissimilar Evidence:** When a request is high-value and has weak/dissimilar evidence (similarity < 0.5 or lower bound < \(\tau_L\)), Rule **R4** fires (`RESTRICT_HIGH_VALUE`, Assurance State `REVIEW_RECOMMENDED`, `escalate=true`). At the lifecycle workflow layer (ADR-0003), this transitions the request into `HELD_FOR_REVIEW` with hold reason `high_value_low_confidence`. It is held for human moderator review before reaching the lender, because automated restriction without human discretion is prohibited. If the moderator clears it (`hold_cleared` event), the request transitions to `ASSESSED` and reaches the lender as `REVIEW_RECOMMENDED` with mandatory safeguards (ADR-0003, UC-B5 ext. 5c, ES-06).
- **Strong Similar Evidence:** When a high-value request has strong, similar evidence (similarity \(\ge 0.5\), lower bound \(\ge \tau_L\), mean \(\ge \tau_\mu\), \(n_{\text{eff}} \ge n_{\min}\), risk level \(\le 2\), 0 recent disputes), Rule R4 does not trigger. It falls through to Rule **R8** (`PROCEED_WITH_SAFEGUARDS`, Assurance State `SUFFICIENT_EVIDENCE`, `escalate=false`), advancing directly to lifecycle state `ASSESSED` without a moderator hold, but attaching value-appropriate safeguards (e.g. deposit record, handover checklist).
- **Non-High-Value Weak Evidence:** Ordinary items with weak direct evidence or cold-start users (Rules R3, R6_SPARSE, R9) advance directly to `ASSESSED` and reach the lender as `INSUFFICIENT_EVIDENCE` or `REVIEW_RECOMMENDED` without entering `HELD_FOR_REVIEW`. A user with **no** verified history gets R3 even on a high-value item (R3 precedes R4, so FR-T-02 holds for every newcomer; fixture PU-04).

**Decision to state mapping (matches overview 5.11):** Proceed → SUFFICIENT · Proceed with safeguards → SUFFICIENT or REVIEW · Request verification → INSUFFICIENT or REVIEW · Restrict high-value → REVIEW pending human · Escalate → REVIEW, or ACTIVE_DISPUTE when a dispute is open.

**Invariants and mapping rules:** (a) ACTIVE_DISPUTE always wins (R1); (b) indirect evidence alone never yields SUFFICIENT_EVIDENCE, at most it moves INSUFFICIENT to REVIEW (with \(\rho\ge\rho_{\text{sup}}\), R6_SPARSE does not fire and R9 applies; ADR-0008); (c) PROCEED_WITH_SAFEGUARDS maps to SUFFICIENT only when evidence is strong (R8), otherwise REVIEW; (d) no-history always maps to INSUFFICIENT with the message *"Insufficient verified history; lender review required."*; (e) high-value restriction requires a human decision before it takes effect.

```text
FUNCTION DecideAssurance(direct, indirect, risk, ctx, P):
    // Precedence 1: Open dispute takes precedence over all automated evaluations
    IF ctx.open_dispute:              // reaches the lender; the dispute has its own case (D12)
        RETURN Build(ESCALATE, ACTIVE_DISPUTE, escalate=false, rule="R1")

    // Precedence 2: High manipulation risk (corroborated level 4, ADR-0007)
    IF risk.level = 4:
        RETURN Build(ESCALATE, REVIEW_RECOMMENDED, escalate=true, hold="manipulation_risk", rule="R2")

    // Precedence 3: Cold-start without indirect community support
    IF direct.direct_event_count = 0 AND indirect.reliability < P.rho_sup:
        RETURN Build(REQUEST_VERIFICATION, INSUFFICIENT_EVIDENCE, escalate=false, rule="R3")

    // Precedence 4: High-value transaction with weak or dissimilar evidence (Resolves N-7)
    IF ctx.is_high_value AND (ctx.request_similarity < 0.5 OR direct.lower_90 < P.tau_L):
        RETURN Build(RESTRICT_HIGH_VALUE, REVIEW_RECOMMENDED, escalate=true, hold="high_value_low_confidence", rule="R4")

    // Precedence 5: Moderate manipulation risk
    IF risk.level = 3:
        RETURN Build(REQUEST_VERIFICATION, REVIEW_RECOMMENDED, escalate=false, rule="R5")

    // Precedence 6: Recent resolved dispute within 12 months requires review and safeguards (ES-03)
    IF ctx.resolved_disputes_12m > 0:
        RETURN Build(PROCEED_WITH_SAFEGUARDS, REVIEW_RECOMMENDED, escalate=false, rule="R6_DISPUTE")

    // Precedence 7: Sparse direct evidence without community support (ADR-0008, ES-12 pattern)
    IF direct.n_eff < P.n_min AND indirect.reliability < P.rho_sup:
        RETURN Build(REQUEST_VERIFICATION, INSUFFICIENT_EVIDENCE, escalate=false, rule="R6_SPARSE")

    // Direct evidence strength evaluation
    strong <- (direct.mean >= P.tau_mu AND
               direct.lower_90 >= P.tau_L AND
               direct.n_eff >= P.n_min AND
               ctx.resolved_disputes_12m = 0)

    // Precedence 8: Strong evidence, clean risk, standard value
    IF strong AND risk.level = 1 AND ctx.verification_ok AND NOT ctx.medium_value AND NOT ctx.is_high_value:
        RETURN Build(PROCEED, SUFFICIENT_EVIDENCE, escalate=false, rule="R7")

    // Precedence 9: Strong evidence with medium/high value or level 2 monitoring
    IF strong AND risk.level <= 2 AND ctx.verification_ok:
        RETURN Build(PROCEED_WITH_SAFEGUARDS, SUFFICIENT_EVIDENCE, escalate=false, rule="R8")

    // Precedence 10: Fall-through (sparse direct evidence supported by paths, weak lower bound, or unverified)
    RETURN Build(PROCEED_WITH_SAFEGUARDS, REVIEW_RECOMMENDED, escalate=false, rule="R9")
// Build() attaches safeguards, rule_fired, hold (default none) and the explanation (all factors shown separately)
```

**Safeguards** (selected by value band and uncertainty; amounts are configuration, not fixed): security deposit scaled to item value and to interval width, handover photos and condition checklist, fixed return date with reminders, additional identity/community verification, public-place handover, lender review of the evidence summary.

**Explanation record** (always, never a single number): state, mean with 90% credible interval, effective evidence, direct vs indirect contribution (and "prior-backed" if applicable), manipulation level with signal evidence, the rule that fired, and the safeguards with reasons.

**Complexity:** \(O(1)\) rule evaluation given precomputed inputs; end to end \(O(n)+O(\Delta^k)+O(\deg+R+m^2L)\).

**Edge cases:** missing manipulation data defaults to level 1 but is flagged "unchecked"; Trust Engine unavailable means default safeguard policy plus human review; rules are ordered so safety conditions (dispute, manipulation) cannot be overridden by a high mean; a moderator reversal re-flags affected evidence until re-evaluated.

---

## 7. Parameters and ranges for the sensitivity study

| Parameter | Initial | Range to test | Measure effect on |
|---|---|---|---|
| Prior \((\alpha_0,\beta_0)\) | (1,1) | (0.5,0.5), (1,1), (2,2) | calibration, cold-start coverage |
| Half-life \(h\) | 180 d | 90, 180, 365 | log loss, Brier |
| Interval level | 90% | 80, 90, 95 | coverage, abstention rate |
| Similarity floor | 0.5 | 0.3 to 0.7 | high-value escalations |
| Max hops \(k\) | 3 | 1, 2, 3, 4 | coverage, latency, false trust |
| Hop decay \(\gamma\) | 0.7 | 0.5 to 0.9 (step 0.1) | indirect strength, calibration |
| Indirect cap \(\rho_{\max}\) | 0.6 | 0.4 to 0.8 | false trust, coverage |
| Mean threshold \(\tau_\mu\) | 0.75 | 0.65 to 0.85 | false trust, over-escalation |
| Lower-bound threshold \(\tau_L\) | 0.60 | 0.50 to 0.70 | appropriate abstention |
| Minimum evidence \(n_{\min}\) | 3 | 2, 3, 5 | new-user fairness |
| Window \(W\) | 90 d | 30, 60, 90 | signal stability |
| S1 bounds (0.3, 0.9), S2 ratio (2, 5), S3 count (3, 10), S4 cosine (0.7, 0.95) | as given | ±20% | false-positive rate on friend groups |
| Signal weights (30/20/20/20/10) | as given | leave-one-out, ±10 points | manipulation-detection rate |
| Band cut-offs 20/40/60 | as given | ±10 | moderator workload |

Evaluate with **time-ordered holdout** (predict each transaction from earlier evidence only). Report log loss, Brier score, credible-interval coverage, escalation precision/recall, false-trust and false-suspicion rates, and new-versus-established-user fairness. Do not state any accuracy figure before it is measured.

---

## 8. Unit tests (minimum set)

1. Posterior equals prior plus weighted successes/failures; no events returns exactly the prior.
2. Newer outcomes outweigh older identical ones; interval narrows as \(n_{\text{eff}}\) grows; disputed or unconfirmed events are ignored.
3. Paths never exceed \(k\) hops; cycles terminate; one path per first hop; equal edges never gain strength with length.
4. Missing target evidence gives baseline estimate, low reliability and `prior_backed=true`.
5. Reciprocity uses the received set; time-window isolation; copied text fires S4; new-account burst fires S3; unavailable linkage renormalises weights.
6. Friend group stays at level 2; fraud ring reaches level 4; level 4 without two corroborating signals is capped at 3.
7. Dispute precedence (R1, not held), cold start (R3, also on a high-value item), high-value restriction (R4), sparse without paths (R6_SPARSE) versus with paths (R9, ES-13), deterministic decision-to-state mapping, same inputs give the same output. All cases are in `14_testing/scenario_fixtures_iteration1.json`, checked by `14_testing/verify_fixtures.py`.

---

## 9. Traceability to the domain model

| Algorithm output | Class / attribute |
|---|---|
| Beta estimate | `TrustEstimate` (alpha, beta, mean, interval, role, metric) |
| Graph edges and paths | `TrustEdge`, `PathEvidence`, `IndirectTrustResult` |
| Signals and risk score | `ManipulationSignal`, `ManipulationRiskAssessment` |
| Decision and mapping | `DecisionPolicyResult`, `SafeguardRecommendation` |
| Final explanation | `AssuranceResult`, `EvidenceRecord` |
| Evidence input | `OutcomeEvent` (with `status`, confirmations, item profile) |

---

## 10. Research basis

Beta-Bernoulli conjugacy (standard Bayesian inference); Jøsang (2016) belief and uncertainty representation; Golbeck (2005) trust propagation with decreasing influence; Akoglu, Tong and Koutra (2015) graph anomaly detection; Ferrara et al. (2014) coordinated and automated accounts. The values \(h\), \(\gamma\), \(k\), \(\rho_{\max}\), band cut-offs and weights are **project hypotheses**, not constants from these papers, and are justified only by the sensitivity analysis and held-out evaluation above.

---

## 11. Finalisation and implementation boundary

This document is the final algorithm and data-structure design baseline. Its
thresholds, weights and half-lives remain hypotheses until the time-ordered
evaluation in section 7 measures calibration, fairness and escalation
performance; this is an evaluation obligation, not an unresolved design choice.

`phase2_assurance.py` is the dependency-free Phase 2 policy slice. It currently
implements the manipulation-signal adapter, decision policy and state mapping
over already-computed trust inputs. The direct Beta estimator, bounded graph
traversal and domain-model classes in this document are integration contracts
for the application layer, not claims that the current module stores events or
implements the complete engine. The adapter must preserve the following
invariants when the remaining components are integrated:

1. unresolved disputes take precedence over every automated decision;
2. indirect evidence never overrides strong negative direct evidence;
3. manipulation signals are investigation evidence, never proof or an automatic ban;
4. cold-start users receive insufficient-evidence treatment rather than a low-trust label;
5. high-value restrictions require human review before taking effect; and
6. every result includes factor-level evidence and uncertainty, not a standalone score.
