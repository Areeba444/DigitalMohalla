# Team decisions, 13 October 2026 (Slice B kickoff)

| Field | Value |
|---|---|
| Recorded by | Student 2 (Areeba Javed) |
| Participants | Student 1 (Fatima Khursheed), Student 2 (Areeba Javed), Student 3 (Minahil Kashif), in person |
| Purpose | Close the points Slice B's code depends on (`Slices_B_C_Branch_and_Commit_Plan.md` §2, P1 to P5) |
| Use | Report Appendix F (meeting records); evidence for Form 2 "design evolution" |

Numbering continues from `Team_Decisions_2026-10-11.md` (D1 to D9). Supervisor review is still pending.

| # | Decision | Outcome | Applied in |
|---|---|---|---|
| D10 | Trust-edge weight rule (P1) | **ADR-0006 accepted as experimental.** `weight = (1 + s_w) / (2 + s_w + f_w)` with the direct estimator's prior and 180-day half-life, no similarity weighting on edges, edges inside a flagged cluster excluded. Its effect is evaluated in iteration 4 and it may change then | ADR-0006 status and sign-off; `feature/trust-edges` |
| D11 | Outcome mapping (P2) | Borrower: ON_TIME_RETURN, CONDITION_AGREED, DISPUTE_FREE. Lender: CONDITION_AGREED (item as described), DISPUTE_FREE. A party found at fault by the moderator fails the relevant metrics; "no fault" counts as success; a metric that does not apply (for example on-time return when the handover never happened) is not recorded. This confirms assumption A1 of `data/generators/README.md` | `feature/outcome-extraction`; assumption A1 |
| D12 | SUFFICIENT_EVIDENCE thresholds (P3) | Keep the values in `backend/config/engine.json` 1.1.0-iteration1-draft: posterior mean ≥ 0.75, lower 90% bound ≥ 0.60, n_eff ≥ 3, ρ_sup = 0.3. They are initial hypotheses, changed later only through a new `config_version` | `feature/decision-policy`; context document §15 open item closed for iteration 1 |
| D13 | ES-05 expected result (P4) | Follow the hand-checked fixture and Test Plan TC-44: rule R8, SUFFICIENT_EVIDENCE with safeguards, because the retaliatory review is detected and down-weighted. The requirements table is corrected | `data/REQUIREMENTS.md` §3; scenario suite |
| D14 | ES-13 expected result (P5) | Rule R9, REVIEW_RECOMMENDED, as ADR-0008 states; without the community paths the same request is R6_SPARSE, INSUFFICIENT_EVIDENCE | Scenario suite; context document §15 open item closed |
| D15 | Device scope for testing | Android only; no iOS device is targeted or tested in iteration 1 | Test Plan v1.3 (suites 15 and 19, TC-73) |
| D17 | Similarity of a past loan to the request (FR-T-03, Overview §5.12) | Decided by Student 2 during B2: similarity = 0.4 × value-band closeness (same 1.0, adjacent 0.5, two apart 0.0) + 0.4 × same category + 0.2 × duration closeness (shorter ÷ longer); each outcome's weight uses at least the 0.5 floor; rule R4's request similarity is the recency-weighted mean of the unfloored values. Stored in engine config 1.2.0-iteration1-draft | `backend/config/engine.json`; `feature/beta-posterior` |
| D16 | Test plan use | Test Plan v1.3 is a guide: tools are added only when a test first needs them; suites 6 to 14, 16, 17 and 19 are written inside the slices, suite 15 and the alpha session at the freeze | Test Plan v1.3; branch plan §1 and §5 |

**Still open after this meeting:** the hosting decision and its ADR number (P6, when CD starts), the locality method (D-11 gate), the mid-eval date.
