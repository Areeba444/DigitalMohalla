# Evaluation protocol v0 (DA-18)

| Field | Value |
| :--- | :--- |
| Version | 0.1 draft |
| Date | 2026-11-07 |
| Author | Minahil Kashif (Student 3), drafted with Claude Code; review: Areeba Javed (Student 2) pending |
| Status | Draft. **Freeze before any result is read** (handbook C.5.3): the team fixes the open points in section 9, the success targets included, at the design gate (10 November). After freezing, any change gets a new version with its reason, and results under both versions are reported |
| Realises | NFR-Q-02, NFR-Q-03, NFR-Q-05, NFR-Q-07; review actions DM06 (time-ordered holdout) and DM07 (one predicted target); build items M7 (harness, baselines, first result) and M11 (search) |

## 1. Three separate claims

The report keeps three things apart, because each needs different evidence.

| Claim | Evidence | Where |
| :--- | :--- | :--- |
| **Conformance:** the code does what the design says | Scenario fixtures ES-01 to ES-13 pass with state, rule and explanation (suite 11) | `14_testing/Test_Plan.md` |
| **Decision quality:** the engine predicts better than simple baselines on unseen data | The time-ordered holdout below | This protocol |
| **Acceptance:** residents understand and accept it | Pilot: task completion, SUS, perceived fairness | FYP-2 (section 8) |

Scenario passes prove only conformance. A first result that shows no gain is still a valid result and is reported as measured.

## 2. What is predicted

**Proposed target (DM07; Student 2 to confirm):** *"the borrower returns this loan on time"*. This is the borrower's ON_TIME_RETURN outcome for one loan, success or failure, as recorded by `transaction_closed` or `dispute_resolved` (decision D11). A loan with no ON_TIME_RETURN outcome (never handed over) is not a test case. Every probability below is a probability of this one event, so the Brier score has one meaning.

## 3. Data

| Use | Tier | Size (from `data/derived/README.md`) | Why |
| :--- | :--- | :--- | :--- |
| Measured result (FYP-1 Final) | `scale`, built on demand (`python -I data/generators/build.py --tier scale`), generator seed 20261001 | 2,000 users | Enough test loans for calibration bins |
| Development of the harness only | `standard` | 90 users, 286 loans over 18 months | Small and committed; never used for the reported numbers |
| Scenario conformance | Fixture files | 13 scenarios | Section 1 |

- All data is SYNTHETIC and labelled so in every table and figure.
- The hidden ground truth (`labels/user_truth.csv`: `true_p_on_time_return` per user) is read only by the scoring step, never by the code under test.
- The generator version, seed and manifest checksum are recorded with each result.

## 4. Split: time-ordered holdout (DM06)

1. Sort all ON_TIME_RETURN outcomes by `occurred_at`.
2. Set the cutoff T at the time of the outcome at the 70th percentile (proposed).
3. **Training history:** every outcome, trust edge and review with a time before T.
4. **Test cases:** every loan *requested* after T that has an ON_TIME_RETURN outcome.
5. **Predict each test loan from the training history only**, frozen at T. Nothing after T is used, not even other test loans, so nothing can leak from the future.
6. **Unseen-pair subset (DM06):** test loans whose (borrower, lender) pair has no loan before T. Report these separately. Indirect evidence matters most here, and it is the case the reviewers asked about.

A rolling variant, where each loan uses all history before its own request, is a FYP-2 sensitivity check, not the main result.

## 5. Methods compared

| # | Method | Probability it gives for a test loan |
| :--- | :--- | :--- |
| B0 | Global average | On-time rate over all training outcomes |
| B1 | Role average | On-time rate over training outcomes of borrowers (the same as B0 while only the borrower role is measured; kept so the lender role can be added) |
| B2 | Recency-weighted average | The borrower's on-time rate with weights 2^(−age/180); B0 if the borrower has no history |
| B3 | Direct-only Beta | Mean of the recency-weighted Beta posterior from Beta(1, 1), without similarity weighting |
| F | Full system | The engine's posterior mean at the request (recency- and similarity-weighted), through `AssuranceEngine.assess` with the frozen config version |

**Honest limit, to state in the report.** In the engine, indirect evidence and context (disputes, value, manipulation) change the *assurance state*, not the posterior mean (Algorithm doc, design note D-1). So F differs from B3 in probability only through similarity weighting. The value of indirect evidence and context is measured with the decision metrics in section 6.2, not with the Brier score.

## 6. Metrics

### 6.1 Probability quality (FYP-1 Final)

| Metric | Definition |
| :--- | :--- |
| Brier score | Mean of (p − y)², with y = 1 for an on-time return; lower is better |
| Log loss | Mean of −[y ln p + (1 − y) ln(1 − p)], with p clipped to [10⁻⁶, 1 − 10⁻⁶] |
| Calibration | Reliability diagram with 10 equal-width bins, plus expected calibration error (bin-size-weighted mean of the absolute gap) |
| Interval coverage | For B3 and F: the share of test borrowers whose 90% credible interval contains their `true_p_on_time_return`. Near 90% means the stated uncertainty is honest. Reported separately for borrowers with fewer and more than n_min effective outcomes |
| Uncertainty of each number | 95% bootstrap interval over test loans (1,000 resamples, fixed seed), so a difference between methods is shown together with its noise |

### 6.2 Decision quality (first run at FYP-1 Final; full study in FYP-2)

These definitions use the hidden truth and are fixed before the first run. The threshold p* = 0.75 is proposed, the same value as tau_mu.

| Metric | Definition |
| :--- | :--- |
| False trust rate | Share of test requests given SUFFICIENT_EVIDENCE whose borrower has true p below p* |
| False suspicion rate | Share of test requests from borrowers with true p of at least p* that are held or given REVIEW_RECOMMENDED for a manipulation reason (R2, R5) |
| Detection rate and false-positive rate | On the development attack set (`mini` and `standard` labels): the share of attack accounts reaching level 4, and the share of non-attack accounts that do |
| Fairness between new and established users (NFR-Q-07) | Distribution of states for borrowers with no history and with history, at equal true p |
| Latency and coverage at k = 1 to 4 | Assessment time per request and the share of test requests with at least one community path (NFR-P-03) |

## 7. Procedure

1. Freeze this protocol: version, commit hash, and the success targets of section 9.
2. Build the `scale` tier and record the generator version, seed and manifest checksum.
3. Run the harness (build item M7) once on the frozen split, saving the results file with the protocol version, config version, commit and run date.
4. Report every number from that file, the bootstrap intervals included; nothing is quoted from memory.
5. If a bug is found after the run, fix it, rerun, and report both runs with the reason.

## 8. Planned for FYP-2

- **Ablations:** without uncertainty (the mean only), without indirect trust, without detection, without the context policy.
- **Sensitivity:** half-life, decay, path cap, thresholds, each across its `sensitivity_range` in `engine.json`.
- **Held-out attacks (iteration 3):** a separate module with its own seed namespace, written by Student 3 and never imported by tuning code. A different author alone does not guarantee independence (review), so the attack families are also fixed in advance.
- **Public networks:** propagation behaviour only (Student 1 chooses Epinions or Bitcoin OTC and records why). Neither holds neighbourhood-loan outcomes, so they say nothing about predicting returns.
- **Pilot:** community, size, consent and withdrawal; task completion, SUS and perceived fairness, reported separately from the simulation results.
- **Search:** keyword against hybrid, defined in `14_testing/Search_Evaluation_Design.md` (DA-25).

## 9. To fix before freezing (design gate)

| # | Point | Owner | Proposal |
| :--- | :--- | :--- | :--- |
| E1 | Predicted target | Student 2 | Section 2 |
| E2 | Cutoff percentile | Students 3 and 1 | 70th percentile of outcome times |
| E3 | p* for the decision metrics | Student 2 | 0.75 (= tau_mu) |
| E4 | Success targets. The proposal says at least 70% accuracy and under 5% false positives; NFR-Q-03 says TBD. Accuracy is not defined for a probability, so restate it, for example as a Brier score below B0's with a non-overlapping bootstrap interval | All three | To be chosen and justified before any result |
| E5 | Whether the first measured result includes the decision metrics or only probability quality | All three | Probability quality required; decision metrics if the harness is ready |
| E6 | Public network | Student 1 | — |
