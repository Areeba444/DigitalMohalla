# Dataset card: fraud-scenarios

| Field | Value |
| :--- | :--- |
| Short name | `fraud-scenarios` |
| Full name | Controlled manipulation scenarios (the files call them "fraud scenarios") |
| Source type | simulation (own generated) |
| Status | obtained |
| Added by | team; generator `generate_fraud_scenarios.py`. Card written 2026-10-12 |
| Last updated | 2026-10-12 |

**All records are synthetic controlled test cases.** They must never be presented as real fraud data, and the project's wording is "manipulation" or "anomaly", never an accusation (Overview, "Controlled Manipulation Scenarios").

## 1. Where it comes from

| Field | Value |
| :--- | :--- |
| Original publisher or authors | The team. Who wrote the generator is not recorded; fill in |
| How it was made | `raw/Datasets/fraud-scenarios/generate_fraud_scenarios.py` (`SEED = 42`). Run from its folder: `python generate_fraud_scenarios.py` (writes `fraud_scenarios/`). The script also contains an `evaluate_detection` helper |
| Design source | Deep Dive Part 2 "Dataset 3: Fraud Scenarios"; Overview "Controlled Manipulation Scenarios" |
| Date generated | Files dated 2026-10-12. Row timestamps are offsets from the moment the script ran (the times in these files all end in 22:52:32 on dates between 2026-07-18 and 2026-10-12), so **re-running the script shifts every timestamp**. The seed fixes the content but not the dates |
| File(s) in `raw/Datasets/fraud-scenarios/fraud_scenarios/` | `all_scenarios_combined.csv` and one file per scenario, plus `clean_baseline.csv` |
| Checksum (first 16 hex of SHA-256) | combined acee724519ffa089 · rating_ring 0e5046220bbdef0d · device_sharing e902cf4a2f052d0f · burst_velocity 005a4054eb80a3c6 · identical_text f4889cec61b9e1f7 · sybil_vouching 89824b398cf6656f · clean_baseline da81bbbbe5aeb539 · generator ce1929f5434672f4 |

## 2. Licence and permitted use

Ours, synthetic. Small; may be committed under `derived/` once finalised.

## 3. What is in it

All files share these fields: `rating_id, rater_id, target_id, transaction_id, role_being_rated, metric, rating_value, rating_text, timestamp, account_age_days, device_id, scenario, is_fraud` (13 columns).

| Scenario file | Rows | Pattern | Signal the team's README names |
| :--- | :--- | :--- | :--- |
| `scenario_rating_ring.csv` | 6 | Ring_A, Ring_B, Ring_C rate each other in a circle with top ratings | reciprocal rating density above 0.7 |
| `scenario_device_sharing.csv` | 20 | Five Sybil accounts that all use device ID `DEV_SHARED_XYZ123` | device sharing count above 1 |
| `scenario_burst_velocity.csv` | 30 | A 2-day-old account submits 30 ratings in a day | velocity spike above 5 times average |
| `scenario_identical_text.csv` | 10 | One account posts the same review 10 times | text similarity above 90% |
| `scenario_sybil_vouching.csv` | 8 | A 1-day-old account (`NewUser123`) is rated highly by eight accounts in two days | new-account burst above 5 |
| `clean_baseline.csv` | 8 | Legitimate tight-knit friend groups (should **not** be flagged) | none |
| `all_scenarios_combined.csv` | 82 | All of the above: **74 attack rows (`is_fraud = True`) and 8 legitimate** | |

Measured on 2026-10-12: 6 + 20 + 30 + 10 + 8 = 74 attack rows, 8 clean rows.

## 3a. Known quality problems and mismatches with the project

1. **Not every scenario matches what iteration 1 builds** (F6). Iteration 1 implements reciprocal clustering (rating ring), review similarity (identical text) and the retaliation check, plus a guard that a legitimate dense group stays below the review threshold (ADR-0007, test suites 9 and 12). Burst velocity and new-account signals are later; device sharing needs device IDs, which the design allows only "where legitimately available".
2. **`sybil_vouching` does not fit the design.** The project has no manual vouching: trust edges are derived only from verified outcomes. The scenario can be reinterpreted as a new-account burst of positive ratings, but the name and the "vouch" idea should be changed or dropped before it is used.
3. **No retaliation scenario.** The retaliatory-review check (ES-05) has no matching attack here.
4. **Scenario accounts are separate from the community dataset.** IDs such as `Ring_A`, `Voucher_1` and `Clean_A1`, and transaction IDs such as `FT5_001`, do not appear in `community-neighborhood`. "Inject into clean data" needs an explicit protocol (which users, which transactions, which timestamps), and the timestamps (relative to when the script ran, not tied to the community dataset's 2025-10-17 to 2026-10-11 timeline) would need re-dating.
5. **Ground truth is only a row flag.** `is_fraud` says a row belongs to an attack. For scoring a detector per account (the engine reports risk per request) a per-account label is also needed.
6. **Tiny.** One instance of each pattern. A detector can be tuned to these exact rows. This is why the held-out attack generator (written by someone other than the detector's author) is planned for iteration 3.
7. **The "evaluation targets" in the dataset README** (recall at least 90%, false positives under 5%) are the Deep Dive's numbers, not agreed project targets (F11).
8. **Wording** (F9): the files and the evaluation helper say "fraud". Use "controlled manipulation scenarios" in the report and any screen.

## 4. How it maps to what we need

| We need | Supplied? | How, or what is missing |
| :--- | :--- | :--- |
| D-08 Controlled manipulation scenarios | Partly | Five patterns with labels. Missing: retaliation, trivial exchanges, sudden high-value request, false damage claim, location spoofing |
| C3 Legitimate dense clusters | Partly | `clean_baseline.csv` has 8 rows; the design fixtures PU-02 (family group) cover this in iteration 1 |
| Held-out attack set | No | These scenarios are the visible set; the held-out generator is separate and later |

## 5. How we use it

- **Intended use:** unit-level checks of the iteration 1 detectors (rating ring, identical text) and the dense-group guard. Later, one input of the manipulation evaluation.
- **Not to be used for:** presenting any result as real fraud performance, or for tuning detector thresholds that are then reported on the same rows.
- **Why this is allowed:** simulation, labelled controlled.

## 6. Transformations

None yet.

| Step | What was done | Script and version | Input | Output | Seed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | |

## 7. Results and notes

- Counts were measured from the files on 2026-10-12.

## 8. Decision

- **Verdict:** use with changes (relabel, decide which scenarios match iteration 1, add a retaliation case, define the injection protocol).
- **Reviewed by:** ______
