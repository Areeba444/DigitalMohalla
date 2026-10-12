# What data the project needs

This is the target. Judge every candidate dataset against it. Everything below is taken from the project documents (sources are named); where something is a proposal rather than a decision, it says so.

| Field | Value |
| :--- | :--- |
| Status | Draft 2026-10-12; updated the same day with a coverage check against the datasets now in `raw/` (section 9). Updated 2026-10-13: the derived dataset `neighborhood-sim` was built against this document, coverage in section 10; questions Q2 to Q6 and Q10 have notes. For the team to review and correct |
| Sources | Overview ("Datasets and Evaluation Data", §5 engine, evaluation scenarios); `docs/DigitalMohalla_Project_Context.md` §2, §6, §8, §16; `docs/design/06_data_model/schema.sql` v2.3; `docs/design/14_testing/scenario_fixtures_iteration1.json`; `docs/design/11_assurance_engine/Assurance_Engine_Config_Draft.json` |

## 1. The primary dataset: a custom neighbourhood dataset (simulation)

The Overview names this as the primary dataset. It is built by us, labelled synthetic, and used for all algorithmic claims.

**Planned size** (Overview; module roadmap, iteration 2): about 50 to 100 users and about 200 to 300 borrowing transactions, with the simulator built in iteration 2 and the held-out attack generator in iteration 3.

**What it must contain:**

| ID | Need | Why (what it evaluates) |
| :--- | :--- | :--- |
| D-01 | Users in communities, with community membership | Network structure for indirect trust; community-bounded moderation |
| D-02 | Community relationship and network information | k-hop propagation needs paths between people |
| D-03 | Items with a category and a value band (LOW up to 5,000 PKR, MEDIUM up to 15,000, HIGH above) | Similarity weighting and the high-value rule |
| D-04 | Borrowing transactions with their lifecycle events | Replay, outcomes, timing |
| D-05 | Transaction outcomes (see section 2) | The direct evidence the Beta posterior learns from |
| D-06 | Ratings and reviews, with reviewer, reviewee and role | Reciprocal-clustering, similar-review and retaliation checks |
| D-07 | Dispute scenarios (damage, non-return, condition mismatch, no-show, other) with a resolution | Disputed outcomes are excluded until resolved; resolved outcomes then count |
| D-08 | Controlled manipulation scenarios (section 4) | Manipulation detection, with ground truth |
| D-09 | Timestamps spread over a long enough period | Recency weighting uses a 180-day half-life, so outcomes need real age differences (weight is about 0.96 at 10 days and 0.25 at 360 days) |
| D-10 | A mix of evidence levels: none (cold start), sparse, rich, and old | The claims below are about low evidence |

**What it is used to evaluate** (Overview): sparse evidence, indirect trust, cold-start behaviour and manipulation detection.

### Claims the data must be able to test

| Claim | Meaning | What the data needs |
| :--- | :--- | :--- |
| C1 | Uncertainty reporting beats plain averages when evidence is low | Many borrowers with few outcomes, and a known "true" reliability to compare against |
| C3 | Low false-positive rate on legitimate dense clusters | Legitimate tight groups (for example a family-style group that reviews each other a lot) that must not be flagged |
| C5 | Newcomers are not excluded | Newcomers with no history who behave reliably |
| (indirect trust) | k-hop helps when a borrower has history, but none with this lender | Borrowers with outcomes with other members and community paths to the lender (scenario ES-13) |

(Claims C2, C4 and C6 to C9 are mentioned in the project instructions but are not defined in any file.)

### Evaluation set-up that the data must support

From the module roadmap, iteration 4: time-ordered holdout (train on earlier, test on later); baselines (global average, role-specific average, recency-weighted average, Beta without indirect, direct only, direct plus uncertainty, direct plus k-hop, full system); ablations (without uncertainty, without indirect trust, without detection, without context policy); metrics (Brier score, log loss, interval coverage and calibration, false-positive and false-negative rates, escalation precision and recall, coverage and latency at k = 1 to 4, fairness between new and established members).

## 2. Record shapes (so generated data loads straight into the system)

These come from the database schema and the engine design. **Proposal:** write generated data in these shapes, so the same evaluation harness can load simulated data and the fixtures. The event schema is frozen; do not invent event fields.

| Record | Fields | Notes |
| :--- | :--- | :--- |
| Outcome (OutcomeEvent) | `event_id, subject_id, observer_id, role, metric, success, occurred_at, transaction_id`; the schema also stores `category`, `value_band`, `loan_duration` and a status | Metrics: `ON_TIME_RETURN`, `CONDITION_AGREED`, `DISPUTE_FREE`. Only confirmed outcomes count; disputed ones are excluded until resolved |
| Trust edge | `source_id, target_id, role, metric, weight, evidence_count, updated_at` | **Derived from verified outcomes**, never entered by hand or as a vouch |
| Review | `transaction_id, reviewer_id, reviewee_id, reviewee_role, ratings (object), comment, retaliation_flag, similarity_flag` | Seeded for the manipulation scenarios |
| Lifecycle event | `event_id, stream_id, stream_seq, event_type, actor_id, occurred_at, previous_state, new_state, evidence_refs, authorisation, payload` | Frozen schema. `stream_seq` orders events within one transaction only |
| Scenario fixture | inputs plus an expected assurance state, rule fired, lifecycle state and explanation facts | The seven iteration-1 fixtures are in `docs/design/14_testing/scenario_fixtures_iteration1.json` |

## 3. The scenarios the data must cover

From the Overview's evaluation scenarios (expected states are the team's starting position, confirmed in design step A5):

| ID | Scenario | Expected assurance state |
| :--- | :--- | :--- |
| ES-01 | New user, no history | INSUFFICIENT_EVIDENCE |
| ES-02 | Consistently reliable | SUFFICIENT_EVIDENCE |
| ES-03 | Reliable with one recent dispute | REVIEW_RECOMMENDED (ACTIVE_DISPUTE if still open) |
| ES-04 | Colluding participants | REVIEW_RECOMMENDED |
| ES-05 | Retaliatory review | REVIEW_RECOMMENDED |
| ES-06 | High-value request with weak evidence | REVIEW_RECOMMENDED |
| ES-07 | Conflicting condition reports | ACTIVE_DISPUTE |
| ES-08 | Failure to return | ACTIVE_DISPUTE |
| ES-09 | Location mismatch | REVIEW_RECOMMENDED |
| ES-10 | Location-permission refusal | INSUFFICIENT_EVIDENCE |
| ES-11 | Moderator reversal | REVIEW_RECOMMENDED |
| ES-12 | Sparse or old history | INSUFFICIENT_EVIDENCE |
| ES-13 | History with others, none with this lender, reachable by community paths | REVIEW_RECOMMENDED (rule R9) |

Iteration 1 builds ES-01 to ES-06 and ES-13. The full set is needed by the end of iteration 3.

## 4. Controlled manipulation scenarios

From the Overview: reciprocal rating rings; new-account rating bursts; highly similar reviews; coordinated account behaviour; shared infrastructure where legitimately available. The threat model also lists retaliatory reviews, trivial exchanges, sudden high-value requests, false damage claims, location spoofing and moderator misuse.

Rules for these:

- They are labelled as controlled or synthetic everywhere and are never presented as real fraud data.
- Each needs **ground truth** (which records are attack records) so detection can be scored.
- **Separation of duties:** attack strategies used for final evaluation are held out from tuning. The detector's author does not write the attack generator (Module 10 sits with S3 for this reason).

## 5. The secondary source: a public trust network

The Overview names Epinions as the external benchmark; the proposal names Bitcoin OTC; the context document also lists YelpChi for robustness. **We now hold Epinions and Bitcoin OTC and Alpha** (not YelpChi), so the Epinions-or-Bitcoin choice may become "use both". Whether to also obtain YelpChi is open for iteration 2.

What the project needs from one:

| ID | Need | Used for |
| :--- | :--- | :--- |
| P-01 | A directed (ideally weighted) graph of who trusts or rates whom | Validating bounded k-hop path search and the effect of k |
| P-02 | Some form of held-back ground truth (for example held-out edges or ratings) | Checking whether propagated trust predicts anything |
| P-03 | Timestamps on edges, if available | Time-ordered evaluation |
| P-04 | Review or rating text with spam labels, if available (YelpChi-style) | Robustness of the manipulation checks |

It is used only for **propagation validation and comparison**, never for claims about neighbourhood borrowing and never mixed into the simulated dataset's results.

## 6. Which source may supply what

| Need | Simulation | Public trust network | Real pilot |
| :--- | :--- | :--- | :--- |
| Algorithm accuracy and calibration claims | **Yes** | No | No |
| Cold-start and sparse-evidence behaviour | **Yes** | No | No |
| Manipulation detection (with ground truth) | **Yes** | Robustness check only | No |
| k-hop propagation validation | Yes | **Yes (benchmark)** | No |
| Realistic graph structure and rating patterns to copy into the simulator | Receives them | **Can provide the pattern** | No |
| Acceptance and usability | No | No | **Yes** |

## 7. How public datasets can help build the custom dataset (ideas to check, not decisions)

Public data cannot be used directly because it is about other things (ratings, purchases, bitcoin trades). It may still help us make the simulator realistic. Each idea below must be checked against the dataset's licence and card before use:

- **Graph shape:** degree distribution, clustering, reciprocity and community structure of a real trust network, to shape the simulated community graph.
- **Rating behaviour:** how ratings are distributed, how often people rate back, how long reviews take to arrive.
- **Timing:** gaps between interactions and burst patterns, to make the simulated timeline and the "new-account burst" attack more realistic.
- **Review text similarity:** how similar legitimate reviews naturally are, to set the threshold for the "highly similar reviews" check.
- **Scale:** testing the k-hop search and latency on a graph far larger than 100 users.

What not to do: relabel public data as neighbourhood borrowing data, or report a result from a public dataset as if it described our users.

## 8. Open questions for the team

| # | Question | Who decides |
| :--- | :--- | :--- |
| Q1 | Do we use Epinions, Bitcoin OTC and Alpha, or all three as trust benchmarks? And do we obtain YelpChi for review-spam robustness? | Team, with supervisor (iteration 2) |
| Q2 | Size and time span of the first simulated dataset we actually use. The current community set has 60 users, 250 transactions and about one year; the plan says 50 to 100 users and 200 to 300 transactions. **Note 2026-10-13:** `neighborhood-sim/standard` has 90 users, 296 loans, 19 months; `mini` 63 users, 190 loans; `scale` 2,026 users on demand. Student 3 agreed to the three tiers | S3 with S2 |
| Q3 | What ground-truth labels are stored? The community set has a hidden `_trustworthiness` per user and the fraud set has an `is_fraud` row flag; per-account attack labels are missing. **Note 2026-10-13:** `neighborhood-sim/labels/` stores true reliability and attack group per user, attack and fault per loan, attack kind per review, and the expected engine result per scenario case | S2 and S3 |
| Q4 | Output format of the simulator: the database table shapes in section 2, CSV, or JSON? (Proposal: the table shapes.) The current files are CSV in their own shapes and need a mapping. **Answered 2026-10-13 by Student 3:** CSV in the shapes of `schema.sql`, labels in separate files | S3 |
| Q5 | Fixed reference date and seeds for generated data. Both generators currently use the run time, so dates shift on every run. **Answered 2026-10-13:** reference date 2026-10-01 (08:00 UTC), seed 20261001, dates spread over 19 months | S3 |
| Q6 | Who writes the held-out attack generator? It must not be the detectors' author. **Note 2026-10-13:** Student 3 states they are S3, the owner of Module 10; the held-out set is theirs. Only the development attack set exists (`generators/attacks_dev.py`) | Team |
| Q7 | Do we collect any real pilot data, and with what consent and privacy protection? | Team, supervisor |
| Q8 | Success targets. The dataset README quotes fraud recall of at least 90% and false positives under 5%; the proposal says at least 70% accuracy and under 5% false positives; NFR-Q-03 is still to be decided | FYP-2 evaluation plan |
| Q9 | Who built `custom-dataset1`, how, and is it synthetic? Do we keep `rent` and `swap`, and the latitude and longitude columns? | Whoever built it; team for scope |
| Q10 | Re-download Epinions `rating.txt` (the current file is cut off). **Note 2026-10-13:** a second download is byte-identical (same size and checksum); the team is looking for a complete copy | Whoever holds the original download |

## 9. How well the datasets we have cover these needs

Checked 2026-10-12 against the files in `raw/`. "Yes" means the data can supply it now; the dataset cards give the evidence. F-numbers refer to the findings list in `README.md` section 3.

### Needs from section 1

| Need | Best source we have | Covered? | Gap |
| :--- | :--- | :--- | :--- |
| D-01, D-02 Users, communities, network structure | `community-neighborhood` | Partly | No membership or relationship table; the graph must be derived from transactions. Neighbourhood labels exist |
| D-03 Items with category and value band | `community-neighborhood` | Partly | No HIGH items (F3) |
| D-04 Transactions with lifecycle events | `community-neighborhood` | Partly | Rows, not event streams; dates inconsistent with account creation (F13) and not reproducible (F12) |
| D-05 Outcomes | `community-neighborhood` | Derivable | Mapping to the three outcome metrics needs S2's confirmation |
| D-06 Ratings and reviews | `community-neighborhood`, `fraud-scenarios` | Partly | Templated text (F5); no retaliation or similarity flags |
| D-07 Disputes | `community-neighborhood` | Partly | All resolved (F4); the `missing_item` disputes contradict their transactions |
| D-08 Controlled manipulation scenarios | `fraud-scenarios` | Partly | Five patterns; no retaliation, high-value, false-damage or spoofing cases; some do not match iteration 1 signals (F6); tiny |
| D-09 Long enough time spread | `community-neighborhood` | Yes | About one year (but see F12 and F13) |
| D-10 Mix of evidence levels | `community-neighborhood` | Yes | 24% of borrows have no earlier borrowing by that person, 64% have two or fewer |
| P-01 to P-03 Public trust graph | `epinions` (`user_rating.txt`), `bitcoin-otc`, `bitcoin-alpha` | Yes | Licences unchecked |
| P-04 Review text with spam labels | none | No | YelpChi would be needed |

### Claims

| Claim | Testable on current data? | Why |
| :--- | :--- | :--- |
| C1 Uncertainty beats averages at low evidence | Yes, on simulation | Many early-history borrows and a hidden true reliability. Fix the date issue (F13) first |
| C3 Few false positives on legitimate dense clusters | Weakly | Only 8 legitimate rows in `fraud-scenarios`, and legitimate reviews in the community set are near-identical (F5) |
| C5 Newcomers not excluded | Yes, on simulation | Newcomers appear naturally in a time-ordered replay |
| Indirect trust (ES-13) | Yes, on simulation and on the public graphs | The community graph is sparse (6 of 244 borrower-lender pairs repeat), which suits it |

### Scenarios

| Scenario | Covered by current data? |
| :--- | :--- |
| ES-01 new user, ES-02 reliable, ES-12 sparse or old history | Yes (replay of the community set) |
| ES-03 recent resolved dispute | Yes. The open-dispute variant: no (F4) |
| ES-04 colluding group | Partly (rating ring in `fraud-scenarios`) |
| ES-05 retaliatory review | No |
| ES-06 high-value request | No (F3) |
| ES-07, ES-08 conflicting reports, failure to return | No (no open disputes) |
| ES-09, ES-10 location mismatch and refusal | No (locality is not in these datasets) |
| ES-11 moderator reversal | No |
| ES-13 community paths | Yes |

The seven iteration 1 scenario fixtures in `docs/design/14_testing/scenario_fixtures_iteration1.json` are separate, hand-checked inputs and do not depend on these datasets.

### What to build next (proposal, for the team to confirm)

1. A second version of the community generator with a fixed reference date, accounts created before their first transaction, a few HIGH-value items, some open disputes, varied review text and per-account labels (closes F3, F4, F5, F12, F13).
2. Add retaliation and high-value-request scenarios to the manipulation set, drop or reinterpret the vouching scenario, and write the injection protocol (F6).
3. Re-download Epinions `rating.txt` and write a loader that matches the actual files (F1, F2).
4. Check licences and citations for Epinions and the Bitcoin sets.
5. Confirm the origin of `custom-dataset1` and decide what to do with it (Q9).

## 10. Coverage after building `neighborhood-sim` (2026-10-13)

Counted from the generated files (`data/derived/standard/COVERAGE.md`), not estimated. SYNTHETIC data. Assumptions A1 to A10 in
`data/generators/README.md` section 6 apply. The data also loads into the project's real PostgreSQL schema and passes the schema's own integrity
checks (section 5a of that README). Items marked "engine" are expectations that have not yet been checked against real engine output.

| Need | Covered by `standard`? | Evidence |
| :--- | :--- | :--- |
| D-01, D-02 communities and paths | Yes | 3 communities, 92 memberships, 3 members in two communities, 708 trust edges, 1,078 two-hop paths with no direct edge |
| D-03 items and value bands | Yes | LOW 77, MEDIUM 23, HIGH 8; 7 categories |
| D-04 loans as lifecycle events | Yes | 286 streams, 2,076 events, 17 of 21 event types, every transition checked against the backend table and loaded into the real schema; 20 requests waiting at LOCALITY_CHECKED, 5 ACCEPTED, 1 ACTIVE, 3 DISPUTED |
| D-05 outcomes | Yes (A1) | 1,192 outcomes over the three metrics and both roles; 5 flagged for re-evaluation |
| D-06 ratings and reviews | Yes | 361 reviews, 316 distinct comments; engine flags left unset |
| D-07 disputes | Yes | 28 disputes: 23 decided, 3 open, 1 withdrawn, 1 reversed; reasons DAMAGE, NON_RETURN, CONDITION_MISMATCH |
| D-08 manipulation scenarios | Partly | Development set: ring, new-account burst, similar-review farm, trivial exchanges then high-value request, false damage claims (23 attack accounts). Not built: shared device or network, location spoofing, moderator misuse, and the **held-out** set |
| D-09 time spread | Yes | 2025-05 to 2026-10, 18 months, all weekdays and time-of-day bands; accounts older than their first loan |
| D-10 evidence mix | Yes | none 20, sparse 24, moderate 32, rich 7, old 3 (borrower side) |
| C1 uncertainty vs averages | Partly | 26 sampled users in `standard` (15 with two or fewer outcome loans); use `scale` (about 2,000 users) |
| C3 false positives on dense clusters | Yes | Family of five: 16 loans, 31 mutual reviews in 80 days, varied text. One case only |
| C5 newcomers not excluded | Partly | 4 non-attack accounts under 30 days old plus a 58-day-old reliable newcomer; `scale` has many more |
| ES-01 to ES-08, ES-11, ES-12, ES-13 | Yes | One request per case in `labels/scenario_manifest.csv`, plus ES-03b, ES-06b, ES-13b counter-cases |
| ES-09, ES-10 location | **No** | Locality method is open |

Of the earlier "what to build next" list (section 9): item 1 is done (second generator version), item 2 is done in a different form (vouching
dropped; retaliation, high-value and false-claim cases added as separate scenarios rather than injected into the community set), items 3 and 5
are open (a complete Epinions `rating.txt`; the origin of `custom-dataset1`), item 4 is partly done (citations recorded; redistribution permission
still not shown for Epinions, Bitcoin OTC and Alpha).
