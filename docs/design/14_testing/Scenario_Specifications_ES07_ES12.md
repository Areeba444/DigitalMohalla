# Scenario specifications ES-07 to ES-12 (iteration 2, DA-04)

| Field | Value |
| :--- | :--- |
| Version | 0.1 draft |
| Date | 2026-11-07 |
| Author | Minahil Kashif (Student 3), drafted with Claude Code; review: Areeba Javed (Student 2) pending |
| Status | Draft for the design gate (10 November). Expected results come from the running engine at config `1.3.0-iteration1-draft`; the questions in section 9 must be settled by Student 2 before these become CI fixtures |
| Files | `14_testing/generate_fixtures_iteration2.py` (runs the real engine) writes `14_testing/scenario_fixtures_iteration2.json`; this file works the same numbers by hand |

**All data here is SYNTHETIC.** No real people, items or places.

## 1. Why these six, and how the numbers were made

Iteration 1 built ES-01 to ES-06 and ES-13 (`14_testing/scenario_fixtures_iteration1.json`). The other six need disputes, locality holds and reversals, which iteration 2 builds (build items M2, M3 and F4). Each case below gives the evidence, the lifecycle path, the engine inputs, the hand calculation, the rule trace, the expected result and the explanation facts a test must check. Every number was produced by `AssuranceEngine.assess` through the generator and then checked by hand (section 8). None was typed in.

**How to read the arithmetic.** Each case uses past loans of the same kind as the request (same category, value band and length), so similarity is 1. Each loan's weight is therefore just its recency weight w = 2^(−age/180). alpha = 1 + (sum of on-time weights) and beta = 1 + (sum of late or missing weights), starting from the prior Beta(1, 1). The mean is alpha/(alpha + beta), and n_eff is the sum of the weights. When beta = 1, the 5% quantile of Beta(alpha, 1) has the closed form 0.05^(1/alpha), so most lower bounds can be checked on a calculator. Thresholds (engine config): tau_mu 0.75, tau_L 0.60, n_min 3, rho_sup 0.3, similarity floor 0.5. "As of" is 2026-10-01 08:00 UTC, as in iteration 1.

**Rule order** (`backend/app/domain/assurance/policy/decision.py`, the first rule that holds decides): R1 open dispute → R2 corroborated manipulation → R3 no history and rho below 0.3 → R4 high value and weak or dissimilar evidence → R5 risk level 3 → R6_DISPUTE a resolved dispute in 12 months → R6_SPARSE n_eff below 3 and rho below 0.3 → R7, R8 strong evidence → R9 everything else.

## 2. ES-07: Conflicting condition reports

**Story.** Borrower V has eight on-time loans, 15 to 120 days old (LOW value). On V's current loan the lender reports damage at return and V disagrees. V raises a dispute from RETURN_INITIATED with reason CONDITION_MISMATCH (T23). While the dispute is open, V asks another lender for a LOW-value item.

**Lifecycle path.** Current loan: RETURN_INITIATED → `dispute_opened` → DISPUTED, with the case OPEN (C01). The moderator records that V is at fault and possession is RETURNED (ADR-0009, proposed), so `dispute_resolved` gives COMPLETED (T25c). New request: REQUEST_CREATED → LOCALITY_CHECKED → ASSESSED.

| Step | alpha | beta | mean | 90% interval | n_eff | Rule | State | Lifecycle |
| :--- | ---: | ---: | ---: | :--- | ---: | :--- | :--- | :--- |
| Counterfactual: no dispute | 7.223 | 1 | 0.878 | 0.661 to 0.993 | 6.223 | R7 | SUFFICIENT_EVIDENCE | ASSESSED |
| **While the dispute is open** | 7.223 | 1 | 0.878 | 0.661 to 0.993 | 6.223 | **R1** | **ACTIVE_DISPUTE** | ASSESSED |
| After resolution (2 days ago) | 8.215 | 1 | 0.892 | 0.694 to 0.994 | 7.215 | R6_DISPUTE | REVIEW_RECOMMENDED | ASSESSED |

**By hand.** The weights are 2^(−15/180) = 0.944, 0.891, 0.841, 0.794, 0.749, 0.707, 0.667 and 0.630, which sum to 6.223. That gives alpha = 7.223, a mean of 7.223/8.223 = 0.878, and a lower bound of 0.05^(1/7.223) = 0.661 ≥ 0.60. The evidence is strong, so without the dispute R7 fires (LOW value).

**Rule trace while open.** R1 fires first: an open dispute wins whatever the evidence says (decision D12). R1 has no hold reason, so the request still reaches the lender (FR-B-07, UC-D3 ext 5a).

**After resolution.** The return was on time, so D11 adds an ON_TIME_RETURN success of weight 2^(−2/180) = 0.992, and alpha becomes 8.215. The condition finding against V is recorded as CONDITION_AGREED and DISPUTE_FREE failures, which the borrower estimate (ON_TIME_RETURN only) does not read. The resolved dispute still counts, so R6_DISPUTE gives REVIEW_RECOMMENDED with safeguards `condition_photos_checklist`, `deposit_record` and `explicit_return_reminder`.

**Explanation facts.**
- While open: "A dispute involving a party is still open" and "An open dispute must be resolved first".
- After resolution: "Resolved disputes in the last 12 months: 1."
- No disputed evidence is counted before it is resolved (FR-B-15 And).

## 3. ES-08: Failure to return

**Story.** Borrower V has six on-time MEDIUM loans, 30 to 180 days old. The current loan is ACTIVE and passes its due date. Reminders go out, and 72 h after the due date (overdue limit, proposed in FR/NFR v1.4) the scheduler opens a dispute with reason NON_RETURN (T24, ADR-0012). While it is open, V asks for another MEDIUM item. The moderator later finds V at fault with possession LOST, so `dispute_resolved` gives COMPLETED (T25c) and the item is set to PAUSED.

| Step | alpha | beta | mean | 90% interval | n_eff | Rule | State | Lifecycle |
| :--- | ---: | ---: | ---: | :--- | ---: | :--- | :--- | :--- |
| **While the dispute is open** | 5.083 | 1 | 0.836 | 0.555 to 0.990 | 4.083 | **R1** | **ACTIVE_DISPUTE** | ASSESSED |
| After resolution (2 days ago) | 5.083 | 1.992 | 0.718 | 0.425 to 0.939 | 5.075 | R6_DISPUTE | REVIEW_RECOMMENDED | ASSESSED |

**By hand.** The weights are 2^(−30/180) = 0.891, 0.794, 0.707, 0.630, 0.561 and 0.500, which sum to 4.083. At stage ACTIVE with reason NON_RETURN, D11 adds an ON_TIME_RETURN **failure** of weight 0.992, so beta = 1.992 and the mean is 5.083/7.075 = 0.718. The lower bound needs the Beta quantile (beta is not 1): SciPy gives 0.425.

**Explanation facts.**
- While open: "A dispute involving a party is still open".
- After resolution: the estimate falls to 0.72, and "Resolved disputes in the last 12 months: 1."
- The open dispute is also shown on V's other requests (UC-B12 post-condition).

**Workflow checks (not engine).**
- The automatic dispute is opened once even if the scheduler runs twice (NFR-R-05).
- The dates of the lost item stay held until COMPLETED.

## 4. ES-09: Location mismatch

**Story.** Borrower V's stored membership locality result is CONFLICTING: the geofence signal was OUTSIDE at join and a moderator approved the membership anyway (`locality_outcome_for`, decision D13). V has four on-time LOW loans, 10 to 130 days old.

**Lifecycle path.**
1. REQUEST_CREATED → `held_for_review` → HELD_FOR_REVIEW with hold reason `locality_conflict` and a flag (T04, UC-B5 ext 4b). **No assessment exists yet**: the engine runs only after the locality check passes or a moderator clears the hold.
2. The moderator records CLEARED with a reason. `hold_cleared` → LOCALITY_CHECKED (never directly ASSESSED, FR-B-08 And).
3. The engine runs → ASSESSED.

| Step | alpha | beta | mean | 90% interval | n_eff | Rule | State | Lifecycle |
| :--- | ---: | ---: | ---: | :--- | ---: | :--- | :--- | :--- |
| At request | — | — | — | — | — | — | none | HELD_FOR_REVIEW (`locality_conflict`) |
| After the hold is cleared | 4.100 | 1 | 0.804 | 0.482 to 0.988 | 3.100 | R9 | REVIEW_RECOMMENDED | ASSESSED |

**By hand.** The weights are 0.962 + 0.825 + 0.707 + 0.606 = 3.100, so n_eff ≥ 3 and R6_SPARSE does not fire. The lower bound 0.05^(1/4.100) = 0.482 is below 0.60, so the evidence is not strong and R9 fires.

**What is checked.**
- Nothing is rejected automatically (ES-09, FR-A-08).
- The locality conflict does **not** lower the assurance state: the state after clearance comes from the evidence alone.
- No coordinates appear in the event, the assessment or the explanation (NFR-PR-01).

## 5. ES-10: Location-permission refusal

**Story.** Newcomer V refused location permission when joining. The stored result is INCONCLUSIVE (signal UNAVAILABLE), and the membership was approved by a moderator. V has no verified loans.

| Step | alpha | beta | mean | 90% interval | n_eff | Rule | State | Lifecycle |
| :--- | ---: | ---: | ---: | :--- | ---: | :--- | :--- | :--- |
| At request | — | — | — | — | — | — | none | HELD_FOR_REVIEW (`locality_inconclusive`, T03) |
| After the hold is cleared | 1 | 1 | 0.500 | 0.050 to 0.950 | 0 | R3 | INSUFFICIENT_EVIDENCE | ASSESSED |

**By hand.** With no outcomes the posterior is the prior Beta(1, 1). Its 5% and 95% quantiles are 0.05 and 0.95.

**Rule trace.** No open dispute and level 1, so R1 and R2 do not fire. R3 fires: zero direct events and rho 0 < 0.3. Its safeguards are `deposit_record`, `handover_photos` and `fixed_return_date`.

**Explanation facts.**
- "Insufficient verified history; lender review required."
- "This is not a negative finding about the borrower."
- Permission refusal is never treated as negative evidence (ES-10).

## 6. ES-11: Moderator reversal

**Story.** Borrower V has five on-time LOW loans, 20 to 100 days old. A sixth loan ended 30 days ago in a NON_RETURN dispute decided against V, which added an ON_TIME_RETURN failure. A moderator then reverses that decision with a reason (C11, `REVERSAL`): both decisions stay in the log and the failure is marked FLAGGED_FOR_REEVALUATION. V asks for a LOW item before and after the reversal.

| Step | alpha | beta | mean | 90% interval | n_eff | Rule | State |
| :--- | ---: | ---: | ---: | :--- | ---: | :--- | :--- |
| Before the reversal | 4.992 | 1.891 | 0.725 | 0.428 to 0.944 | 4.883 | R6_DISPUTE | REVIEW_RECOMMENDED |
| After the reversal (as built) | 4.992 | 1 | 0.833 | 0.549 to 0.990 | 3.992 | R6_DISPUTE | REVIEW_RECOMMENDED |
| After the reversal, if a reversed dispute were not counted | 4.992 | 1 | 0.833 | 0.549 to 0.990 | 3.992 | R9 | REVIEW_RECOMMENDED |

**By hand.**
- The weights are 0.926 + 0.857 + 0.794 + 0.735 + 0.680 = 3.992, and the failure at 30 days weighs 2^(−30/180) = 0.891.
- Before the reversal: beta = 1.891, mean = 4.992/6.883 = 0.725.
- After the reversal: the flagged outcome is skipped (`estimate` counts only VALID outcomes), so beta returns to 1, the mean is 0.833, and the lower bound is 0.05^(1/4.992) = 0.549.

**What the reversal changes.** The estimate and its interval change, and the next assessment counts five loans instead of six. The state stays REVIEW_RECOMMENDED. The dispute case is REVERSED, and the evidence source counts REVERSED cases among resolved disputes (`backend/app/infra/db/evidence.py`), so R6_DISPUTE still fires. If that count left reversed cases out, R9 would fire instead with the same state (row 3). The choice is Student 2's (question Q2).

**Workflow checks.**
- Both decisions are kept, and the second references the first (`decision_reversal_ck`).
- The loan is not rewound.
- Trust edges are refreshed without the flagged outcome.
- V's evidence screen shows the flagged loan as "under review" (UC-D2 ext 3a).

## 7. ES-12: Sparse or old history

| Case | Evidence | alpha | n_eff | mean | 90% interval | Rule | State |
| :--- | :--- | ---: | ---: | ---: | :--- | :--- | :--- |
| ES-12 old | Six on-time LOW loans, 540 to 720 days old | 1.545 | 0.545 | 0.607 | 0.144 to 0.967 | R6_SPARSE | INSUFFICIENT_EVIDENCE |
| ES-12b sparse | Two on-time LOW loans, 10 and 20 days old | 2.888 | 1.888 | 0.743 | 0.354 to 0.982 | R6_SPARSE | INSUFFICIENT_EVIDENCE |

**By hand.**
- Old: the weights are 2^(−540/180) = 0.125, then 0.109, 0.095, 0.082, 0.072 and 0.063, which sum to 0.545. The lower bound is 0.05^(1/1.545) = 0.144.
- Sparse: 0.962 + 0.926 = 1.888.

**Rule trace.** Both have direct events, so R3 does not fire. n_eff < 3 and rho 0 < 0.3, so R6_SPARSE fires.

**Explanation facts.**
- "Not enough verified evidence to judge this request."
- The effective outcome count is shown: 0.5 for old, 1.9 for sparse.
- Six old loans count for less than two recent ones, which is the purpose of recency weighting (FR-T-03).

## 8. Checks done (7 November 2026)

| Check | Result |
| :--- | :--- |
| Generator run with `uv run python ../docs/design/14_testing/generate_fixtures_iteration2.py` | 14 assessments, all listed above |
| Hand check of every n_eff from 2^(−age/180) | All match to 3 decimals |
| Hand check of lower bounds with 0.05^(1/alpha) where beta = 1 (ES-07, ES-09, ES-11 after, ES-12, ES-12b) | All match to 3 decimals |
| Lower bounds with beta ≠ 1 (ES-08 after, ES-11 before) | From SciPy only; not checked by hand. The independent oracle `14_testing/verify_fixtures.py` should be extended to these (Student 3, before the fixtures enter CI) |
| Locality holds (ES-09, ES-10 at request) | From the lifecycle code path (`_locality_and_assessment`), not run against a database |
| Not run | No pytest suite yet; the ES-07 to ES-12 tests are written in Test Plan v2 (DA-16) and built with M2, M3 and F4 |

## 9. Questions for Student 2 (review)

| # | Question | Why it matters |
| :--- | :--- | :--- |
| Q1 | `data/REQUIREMENTS.md` §3 gives ES-09 REVIEW_RECOMMENDED and ES-10 INSUFFICIENT_EVIDENCE as states, but at the request both are HELD_FOR_REVIEW with no assessment. Proposed wording: "HELD_FOR_REVIEW (locality hold), then the state from the evidence once cleared". The fixtures above pick evidence that gives those states after clearance | The scenario table and the tests should say the same thing |
| Q2 | Should a REVERSED dispute still count in "resolved disputes in the last 12 months"? Today it does | Decides whether ES-11 after the reversal fires R6_DISPUTE or R9 (same state either way) |
| Q3 | The explanation after a reversal does not mention the outcome under re-evaluation. Should it say "1 loan is under review and not counted"? | UC-D2 ext 3a shows it to the member; the lender sees nothing |
| Q4 | ADR-0009 (proposed) records only the at-fault finding for WITH_BORROWER (the return is judged when it happens), and LOST also fails CONDITION_AGREED. `outcomes_for_resolved_dispute` does not read possession yet: for a dispute from RETURN_INITIATED it adds an ON_TIME_RETURN outcome whatever the possession. Agree that the function takes possession as an input once ADR-0009 is accepted? | ES-07 (RETURNED) and ES-08 (LOST) give the same ON_TIME_RETURN result either way; a WITH_BORROWER case needs the change first |

**ES-05 (settled).** The fixture, `data/REQUIREMENTS.md` §3, both scenario manifests and Test Plan TC-44 all say R8, SUFFICIENT_EVIDENCE with safeguards (team decision D13, 13 October). Checked again on 7 November; nothing is left to change.
