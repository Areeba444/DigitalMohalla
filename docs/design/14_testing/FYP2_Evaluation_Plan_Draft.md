# FYP-2 evaluation plan (M8) — DRAFT, not frozen

| Field | Value |
| :--- | :--- |
| Version | 0.1 draft, 22 November 2026 |
| Owners | Minahil Kashif, Areeba Javed (plan item M8) |
| Status | **Draft.** Becomes the frozen plan only when all three students sign it off before any FYP-2 result is read. Nothing here is a result |
| Builds on | `Evaluation_Protocol_v0.md` section 8, `Search_Evaluation_Design.md`; tools: `scripts/evaluate_engine.py`, `scripts/score_search.py`, `scripts/khop_sweep.py`, `backend/tests/performance` |

All data in simulations is SYNTHETIC. Simulation results, search results and the pilot are reported separately.

## 1. Studies

| # | Study | Question | Method | Tool today |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Decision quality, main | Does the engine predict on-time return better than B0 to B3 on unseen later loans? | Frozen time-ordered holdout on `scale`, Brier, log loss, calibration, interval coverage, bootstrap intervals | harness built (M7); run waits for the freeze |
| 2 | Decision metrics | False trust and false suspicion rates; new against established users (NFR-Q-07) | Replay disputes, reviews and trust graph at the cutoff | not built |
| 3 | Ablations | What does each part add? | Remove in turn: uncertainty, indirect trust, detection, context policy | not built |
| 4 | Sensitivity | Do conclusions survive other parameters? | Half-life, decay, path cap, thresholds across `sensitivity_range` in `engine.json` | not built |
| 5 | Held-out attacks | Does detection work on attacks not used for tuning? | Separate module, own seed, fixed attack families, never imported by tuning code | iteration 3 |
| 6 | Public network | Does propagation behave on a real graph? | Epinions or Bitcoin OTC, propagation only (Student 1 chooses) | not built |
| 7 | Search | Hybrid against keyword | precision@5, recall@10, NDCG@10 over about 26 queries, two labellers, kappa reported | scoring built (M11); labels missing |
| 8 | Performance | Latency of requests and transitions | Local and deployed, P50 and P95 with config version | local test built (F8) |
| 9 | Pilot | Do residents understand and accept it? | Task completion, SUS, perceived fairness; consent and withdrawal | not started |

## 2. Rules fixed in advance

1. The protocol version, config version, commit and data checksum are recorded with every result.
2. A run is made once on the frozen setting. A bug found afterwards means a fix and a rerun, with both reported and the reason.
3. A result showing no gain is reported as measured. Targets are set after the first baseline, before the FYP-2 runs.
4. Scenario passes prove conformance only, not decision quality.

## 3. Open points for the team (from the protocol, section 9)

E1 predicted target; E2 cutoff percentile (70th proposed); E3 p* (0.75 proposed); E4 success targets, restated for a probability (for example Brier below B0 with a non-overlapping interval); E5 whether decision metrics are in the first result; E6 public network; S-E1 second labeller; S-E3 relevance threshold; S-E4 deployed or local search run.
