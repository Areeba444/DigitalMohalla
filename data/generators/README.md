# Synthetic-data generator

Builds the **synthetic** test dataset for Digital Mohalla: people, communities, items, loans as lifecycle
event streams, outcomes, trust edges, reviews, disputes and moderator decisions, plus the hidden ground truth.
The same files are used by CI and on a laptop. Python standard library only: no new dependency.

| Field | Value |
| :--- | :--- |
| Owner | Student 3 (Module 10), with Student 2 for the engine's data needs |
| Status | Built 2026-10-13 and loaded into PostgreSQL 16 against the real schema the same day (section 5a). Reviewed by Fatima Khursheed, Areeba Javed; assumptions in section 6 signed off |
| Generator version | 1.0.0 (`common.py`) |
| Seed and reference date | seed `20261001`; "today" is `2026-10-01 08:00 UTC` (`common.py`) |
| Target | `data/REQUIREMENTS.md`: needs D-01 to D-10, claims C1/C3/C5, scenarios ES-01 to ES-13 |

Everything it writes is **synthetic**: users are `@synthetic.invalid` and `is_synthetic = true`, the communities are
called "(synthetic)", and attack data is labelled as a controlled scenario, never as real fraud.

## 1. Run it

From the repository root:

```bash
python -I data/generators/build.py --tier standard      # writes data/derived/standard
python -I data/generators/validate.py data/derived/standard
```

| Command | What it does |
| :--- | :--- |
| `build.py --tier mini` | The scenario cast and the development attack set only. Writes `data/derived/mini`. Committed |
| `build.py --tier standard` | `mini` plus ordinary background life. Writes `data/derived/standard`. Committed |
| `build.py --tier scale [--users N --loans N]` | Background life only, default 2,000 users and 12,000 loans. Writes `data/interim/scale` (about 51 MB, **not committed**). Use it for latency and k-hop tests and for calibration (C1) |
| `validate.py <folder>` | Re-reads the CSV files only and runs every check (about 45,000 on `standard`). Exit 0 = all passed. Also writes `COVERAGE.md` |
| `measure_public.py` | Re-measures `data/derived/public_graph_stats.json` from the raw Epinions and Bitcoin files (about 4 minutes; needs `data/raw/`) |
| `graph_shape.py <folder>` | Compares the generated lending graph with the public networks |

Measured sizes (rebuilt 2026-10-13 for B5): `mini` 63 users, 193 loans, 1,392 events, 0.9 MB. `standard` 90 users, 289 loans, 2,074 events, 1.3 MB
(the plan said 50 to 100 users and 200 to 300 loans). `scale` about 2,000 users and 12,000 loans (see section 5a for the exact load).
Build times on a laptop: `mini` and `standard` a few seconds each, `scale` under two minutes.

The generator is **deterministic**: the same seed and reference date give byte-identical files. The tests prove it.
Dates are spread over 18 months (2025-05 to 2026-10) with weekday, month and time-of-day variation, so the data does
not share one timestamp. The only intentional cluster is the 20 "request under test" rows, which sit 1.5 to 6 hours
before the reference moment because they are the requests waiting for the engine "now".

## 2. What is in the output

CSV files in the shapes of `docs/design/06_data_model/schema.sql` (NULL is the empty field, booleans are `true`/`false`,
JSON columns hold JSON text, timestamps are UTC ISO 8601, periods are `[start,end)` range literals, durations are `N days`).
They can be loaded with PostgreSQL `COPY ... CSV` (identity columns need `OVERRIDING SYSTEM VALUE`).

| File | Rows (standard) | Notes |
| :--- | ---: | :--- |
| `app_user`, `community`, `membership`, `category`, `item` | 90 / 3 / 92 / 7 / 108 | One moderator per community and one admin. A few members belong to two communities |
| `borrowing_transaction`, `lifecycle_event` | 289 / 2,074 | Every event is checked against `backend/app/domain/lifecycle/transition_leaves.csv`; the projection columns equal a replay of the events. `request_created` carries the item and period, moderator events carry the decision id, as the schema's triggers require |
| `booking`, `locality_verification` | 251 / 92 | Projections and baseline rows the database would hold: a booking per acceptance (released when the loan ends); one VERIFIED locality result per member (assumption A10) |
| `condition_report` | 954 | Handover and return reports; `condition_agreed = false` is a disagreement |
| `outcome` | 1,172 | Written only at `transaction_closed` or `dispute_resolved`. 5 are `FLAGGED_FOR_REEVALUATION` (ES-11) |
| `trust_edge` | 670 | Derived from valid outcomes, never entered by hand |
| `review` | 344 | `retaliation_flag` and `similarity_flag` stay `false`: they are the detectors' output |
| `escalation_case`, `moderator_decision` | 40 / 37 | 27 disputes (22 decided, 3 open, 1 withdrawn, 1 reversed) and 13 high-value holds. Reason text and priority are what the database trigger would write |
| `labels/user_truth.csv` | | Hidden true reliability, group, attack flag, evidence level, whether the history was `sampled` or `scripted` |
| `labels/transaction_truth.csv`, `review_truth.csv` | | Which loans and reviews belong to an attack or a legitimate dense group |
| `labels/item_value_pkr.csv` | | Item value in PKR (the schema stores only the band) |
| `labels/scenario_manifest.csv` | 20 | One request waiting at `LOCALITY_CHECKED` per case, with the expected engine result and where that expectation comes from |
| `MANIFEST.json`, `COVERAGE.md` | | Checksums of every file; coverage of D-01 to D-10, C1/C3/C5, ES-01 to ES-13 |

**Not generated:** `assessment` (the engine's own output, so `assessment_generated` and engine holds carry no `assessment_id`), `invitation`,
`attachment`, `case_statement`, `audit_log`, `user_block`, and the hash columns `prev_hash` and `row_hash` (`scripts/load_dataset.py` computes
them with the schema's own `event_hash()` when it loads the events). `ES-09` and `ES-10` (location mismatch and refusal) are not built because the
locality method is still open.

## 3. Where each part comes from

| Part | Source | How it is used |
| :--- | :--- | :--- |
| Uneven activity: a few busy members, many quiet ones | Epinions trust file (out-degree shape) | Each member's activity level is drawn from the measured quantile table (`public_graph_stats.json`) |
| Uneven lender popularity | Epinions (in-degree shape) | Lender choice is weighted the same way |
| Give-and-take between neighbours | Epinions reciprocity 0.35, halved to 0.17 | Chance that a lender later borrows back |
| Bursts and long quiet gaps in time | Bitcoin OTC (one rater's gaps divided by their own median) | Spacing of each member's loans |
| New-account burst size | Bitcoin OTC and Alpha (ratings in the first 7 days) | Median 1, 90th percentile 4, 99th percentile 10, used to design the burst attack (8 in 2 days) |
| Skew of star ratings | Epinions `rating.txt` (77% five stars, 15% four, 6% three, 2% two) | Spread of ratings after a good loan (the file is cut off, covers 2001 and 2002 only) |
| People, item mix, review phrases, dispute wording | The earlier community generator (our own work) | Names and item list reused; new phrase banks, so there are hundreds of distinct review texts instead of 17 |
| Attack patterns | The earlier fraud generator (our own work) | Ring and identical-text patterns rebuilt in the schema's shapes; vouching dropped (no vouch feature) |
| Scenario histories | The design: engine config, fixtures, algorithm document | Hand-written so a test knows exactly what evidence exists |
| Dispute wording | Written by us | **No e-commerce complaint corpus is used.** None is held, and downloading one needs a licence check and your approval. It could make dispute text more varied, not the data more correct |

Row-level data from Epinions and Bitcoin is **never copied**: only aggregates (`public_graph_stats.json`), because their licences
show no redistribution permission.

Measured against the public graphs (`graph_shape.py`, scale tier): reciprocity 0.27 (Epinions 0.35, Bitcoin OTC 0.79), clustering
0.35 (0.28 and 0.29). The generated graph has a **lighter tail**: the 99th-percentile out-degree is 4.9 times the mean against 15.6
(Epinions) and 11.4 (Bitcoin OTC), because weights are capped and communities are small. Do not use it to claim realistic hub behaviour.

## 4. The three layers and the development attack set

1. **Background life** (`population.py`): archetypes (reliable veteran, steady average, unreliable, sparse, newcomer, old and inactive,
   lender only) with a hidden true reliability. Outcomes are sampled from it, so a test can compare an estimate with the truth (claim C1).
2. **Scenario cast** (`scenarios.py`, `cast.py`): ES-01 to ES-08, ES-11 to ES-13, C3 (a family of five who lend to each other 16 times
   and must not be flagged), C5 (a reliable newcomer), plus counter-cases ES-03b (open dispute), ES-06b (strong evidence for a high-value
   request) and ES-13b (no community path).
3. **Development attack set** (`attacks_dev.py`): reciprocal rating ring (ES-04), new-account burst, similar-review farm, trivial
   exchanges followed by a high-value request, false damage claims. All have `split = dev`.

**Separation of duties.** The development set is for building and tuning. The held-out set for final evaluation must be a different
set of strategies, written in its own module with its own seed namespace by someone other than the detectors' author (Student 3,
who owns Module 10), and never imported by tuning code. Nothing in this folder is the held-out set. Not built, because the schema
cannot express them without inventing a field: shared device or network linkage; location spoofing (locality method open).

## 5. Checks (`validate.py`)

Foreign keys; the transition table and roles for every event; schema constraints (projection columns, closed-at, hold reason, one live
case per loan, unique reviews and outcomes); no event before an account existed; no double booking of an item; outcomes only from closed
loans or resolved disputes, with both parties' `DISPUTE_FREE`; trust edges recomputed from outcomes; no privacy-suggesting columns; review
text (character 3-gram cosine, a **proxy** for the engine's S4 signal): at least 80% distinct legitimate texts, at most 5% of legitimate
reviews with a look-alike about the same person (measured 3.3% on `mini`), and attack groups with mean cosine of 0.8 or more.

`backend/tests/unit/test_dataset_generator.py` runs all of it in CI (and `backend/tests/integration/test_dataset_load.py` loads `mini` into PostgreSQL), checks determinism and that the committed files in `data/derived/`
equal what the generator produces now, and checks that the validator **fails** on broken data.

## 5a. Loaded into PostgreSQL (the real check)

`scripts/load_dataset.py` loads a tier into PostgreSQL 16 and verifies it. It was run on 2026-10-13 against the project's own migration
(`alembic/versions/0001`, schema `dm`) with these results: `mini` and `standard` load with foreign keys, CHECK and booking-exclusion
constraints on, and every verification passes (row counts; `verify_event_chain()` on every stream; `replay_state()` equals the stored state;
the backend's Python `BorrowingTransaction.replay()` agrees; projections equal the last event; views `v_pending_outcomes`, `v_item_calendar`,
`v_moderation_queue` are consistent). On top of the loaded history a new request then runs end to end through the real lifecycle service
under the live triggers.

The full `scale` tier was also loaded into a scratch database the same day: 2,026 users, 12,229 loans, 88,573 events,
49,075 outcomes, all verifications passed, in about 4 minutes (build about 5 minutes, `validate.py` 2,000,839 checks, 0 failed).

**Why the triggers are switched off for the load.** The schema stamps every event with the current clock time and refuses a request whose dates
are past, so history cannot go through the normal rules. The loader turns off only the schema's *user* triggers (foreign keys stay on),
computes the hash chain, and turns them back on (the test checks all 28 are enabled afterwards).

**What the load taught us.** Reading the triggers showed the first version of the data broke the schema's rules in several places, all fixed:
`request_created` must carry `item_id` and `requested_period`; `dispute_opened` must carry a `reason`; a moderator's event must carry the id of
a matching decision (`evidence_refs.decision_id`); the borrower must confirm a return AFTER the lender's checklist; borrowers must be verified to the
level the item requires; a lender's decline for taken dates is made by the system; `booking` and `locality_verification` rows are needed. `validate.py`
now re-implements these rules, so the unit tests catch them without a database.

Still not provable by a load: that the engine reaches the expected results (it has not been run on this data), and the live rule that
`assessment_generated` needs an assessment row (history is loaded without assessments).

## 6. Assumptions that need confirmation

Nothing below is measured. Each is a choice made so the data can load; the owner decides whether it stays.

| # | Assumption | Owner |
| :--- | :--- | :--- |
| A1 | **Outcome mapping.** Borrower: `ON_TIME_RETURN` (returned by the due time), `CONDITION_AGREED`, `DISPUTE_FREE`. Lender: `CONDITION_AGREED` (item as described), `DISPUTE_FREE`. A party found at fault gets failures on the relevant metrics; "no fault" gives successes; a metric that does not apply (for example on-time return when the handover never happened) is skipped | Student 2 |
| A2 | A condition disagreement at return or handover always leads to a dispute | Student 2 |
| A3 | Event payloads follow the schema's trigger rules and what the lifecycle service writes (`request_created`: item and period; `locality_checked`; `held_for_review`: hold reason; `dispute_opened`: reason and description; `transaction_closed`: outcome); all others are `{}`. `evidence_refs` carries only `decision_id` on moderator events; no `assessment_id` because no assessment rows exist. The event-specific data field (N-6) is still open | team |
| A4 | `moderator_decision.resolved_outcome` is `{"at_fault": "borrower" or "lender" or "none"}` | Student 2 |
| A5 | Trust-edge weight is the recency-weighted Beta posterior mean `(1 + s) / (2 + s + f)` with a 180-day half-life (ADR-0006, still unsigned) | Students 1 and 2 |
| A6 | In the background world a high-value request from someone with fewer than 3 outcomes is held 90% of the time and cleared 60% of the time. This is a simulator choice for lifecycle variety, not engine output | Student 2 |
| A7 | Archetype mix, reliability ranges, month and weekday weights, time of day, loan lengths, review probability and delay (median 20 hours) | Student 3 |
| A8 | Expected results in `scenario_manifest.csv`: copied from the hand-checked fixtures for ES-01 to ES-06 and ES-13; from the requirements table for the rest (marked unconfirmed); blank where nothing is defined | Student 2 |
| A9 | `NO_SHOW` and `EXPIRED` appear (iteration 2 transitions in the table); reminders and extensions do not | team |
| A10 | Every member has one `MODERATOR_APPROVAL` locality result approved by the platform admin, valid until 120 days after the reference date. Locality design A11 is in the schema, but the context document still lists the locality method as an open item | Student 1 |

## 7. Known limitations

- `standard` has only 26 background users with **sampled** reliability, so it is too small for calibration (claim C1). Use the
  `scale` tier (`labels/user_truth.csv` marks `history_basis = sampled`). Scripted users carry nominal reliability labels only.
- Most background activity is recent (September 2026 holds about a quarter of the requests, partly the attack and scenario cast): a growing
  neighbourhood. A time-ordered split works, but the early months are thin.
- Heavy tails are lighter than the public graphs (section 3).
- Review text is composed from phrase banks. It is varied, not natural language.
- The ES-05 case follows the hand-checked fixture (expected SUFFICIENT_EVIDENCE, rule R8) but `data/REQUIREMENTS.md` lists
  REVIEW_RECOMMENDED. The two documents disagree; the team must choose.
- The engine has not been run on this data yet, so no expected result has been checked against real engine output.
- History is loaded with the schema's user triggers off; assessment rows do not exist (see section 5a).

## 8. Files

`common.py` (constants, ids, CSV writer) · `world.py` (people, loans, events, outcomes) · `population.py` (background life) ·
`cast.py`, `scenarios.py` (scenario cast) · `attacks_dev.py` (development attacks) · `texts.py` (phrase banks) · `build.py` ·
`validate.py` · `measure_public.py` · `graph_shape.py`; the loader is `scripts/load_dataset.py`.

To add a scenario: create its people with `cast_user`, give them history with `hist_loan` (days before the reference date), end with
`request_under_test`, and register it with `add_manifest`. Rebuild, run `validate.py`, and commit the changed files in `data/derived/`
(the test fails until you do).
