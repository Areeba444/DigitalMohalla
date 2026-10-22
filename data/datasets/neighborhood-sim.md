# Dataset card: neighborhood-sim

| Field | Value |
| :--- | :--- |
| Short name | `neighborhood-sim` (tiers `mini`, `standard`, `scale`) |
| Full name | Synthetic Digital Mohalla neighbourhood, version 2: schema-shaped test data with ground truth |
| Source type | own generated (simulation), **SYNTHETIC**. Shape statistics measured from public trust networks |
| Status | derived. `mini` and `standard` committed in `derived/`; `scale` built on demand into `interim/` |
| Added by | Claude Code for Student 3, 2026-10-13; reviewed by Fatima Khursheed, Areeba Javed |
| Last updated | 2026-10-13 |

## 1. Where it comes from

| Field | Value |
| :--- | :--- |
| Original publisher or authors | Our own generator, `data/generators/` (version 1.0.0). Names, item list and some wording reused from the earlier community generator (`raw/community-neighborhood/`) |
| Download link | none (built from the repository) |
| Date built | 2026-10-13 |
| Version or release | generator 1.0.0, seed 20261001, reference date 2026-10-01 08:00 UTC |
| Citation | Shape statistics come from Epinions and Bitcoin OTC/Alpha; cite the papers on their cards when the report describes them |
| Inputs | `derived/public_graph_stats.json` (aggregates only), `backend/config/engine.json`, `backend/app/domain/lifecycle/transition_leaves.csv`, `docs/design/14_testing/scenario_fixtures_iteration1.json` |
| Checksums | In each tier's `MANIFEST.json` (SHA-256 of every file) |

## 2. Licence and permitted use

| Field | Value |
| :--- | :--- |
| Licence or terms of use | Ours. No third-party rows are included |
| May we redistribute it in the repository? | yes, `mini` and `standard` (958 KB and 1.4 MB) |
| Attribution required? | none for the data; the public datasets behind `public_graph_stats.json` should be cited where their statistics are discussed |
| Restrictions | Must stay labelled synthetic. Attack accounts are controlled scenarios, never real fraud data |
| Personal data in it? | None. Names are random first name and surname pairs; emails end `@synthetic.invalid`; there are no addresses, coordinates or CNICs |
| Checked with supervisor? | no |

## 3. What is in it

| Field | Value |
| :--- | :--- |
| Format | CSV in the shapes of `schema.sql`, plus `labels/` (ground truth) and `MANIFEST.json` |
| Size (measured) | `mini`: 63 users, 190 loans, 1,378 events, 813 outcomes. `standard`: 90 users, 286 loans, 2,076 events, 1,192 outcomes, 361 reviews, 28 disputes. `scale`: about 2,000 users and 12,000 loans |
| Time span | 2025-05 to 2026-10-01 (18 months) |
| What one row represents | Per table as in the schema: a user, an item, a loan, one lifecycle event, one verified outcome, and so on |

Files, record shapes, what is left out, and the assumptions: `../generators/README.md` sections 2 and 6.

## 3a. Known quality problems

- Background life is small in `standard` (26 sampled users); calibration needs `scale`.
- Activity is concentrated in recent months; the heavy tail of the public graphs is lighter here (99th-percentile out-degree 4.9 times the mean against 15.6 and 11.4).
- Review text is composed from phrase banks; the similarity check in `validate.py` is a proxy for the engine's signal.
- Assumptions A1 to A9 (outcome mapping, payload contents, trust-edge formula, and others) need owner confirmation.
- ES-05: the fixture and the requirements table disagree on the expected state (R8 against REVIEW_RECOMMENDED).
- ES-09 and ES-10 are not built (locality method open). Shared-device linkage and location spoofing cannot be expressed in the schema.

## 4. How it maps to what we need

Compare with `../REQUIREMENTS.md`; the counted evidence is in each tier's `COVERAGE.md`.

| We need | Supplied? | How, or what is missing |
| :--- | :--- | :--- |
| D-01, D-02 communities and paths | Yes | 3 communities (2 in `mini`), 3 members in two communities, 1,078 two-hop paths with no direct edge |
| D-03 items and bands | Yes | LOW 77, MEDIUM 23, HIGH 8 (the HIGH items close finding F3) |
| D-04 lifecycle event streams | Yes | 17 of the 21 event types; every path checked against the transition table and loaded into the real schema |
| D-05 outcomes | Yes, under A1 | 3 metrics, both roles, 5 flagged for re-evaluation |
| D-06 ratings and reviews | Yes | 316 distinct comments in 361 reviews (finding F5 closed) |
| D-07 disputes | Yes | 28 disputes: decided 23, open 3, withdrawn 1, reversed 1 (finding F4 closed) |
| D-08 manipulation scenarios | Partly | Ring, burst, similar-review farm, trivial exchanges, false claims (development set). No device or spoofing patterns; no held-out set |
| D-09 time spread | Yes | 18 months; accounts always older than their first loan (finding F13 closed); fixed reference date (finding F12 closed) |
| D-10 evidence levels | Yes | none 20, sparse 24, moderate 32, rich 7, old 3 (borrower side) |
| C1 | Partly | `standard` has only 26 sampled users, 15 with two or fewer outcome loans; use `scale` |
| C3 | Yes | Family cluster of five accounts, 16 loans and 31 mutual reviews in 80 days |
| C5 | Partly | `standard` has 4 non-attack accounts under 30 days old (all reliable) plus the 58-day-old `c5.newcomer`; `scale` has many more |
| ES-01 to ES-08, ES-11 to ES-13 | Yes | One request waiting for the engine per case, in `labels/scenario_manifest.csv` |
| P-01 to P-04 | No | Public data only (separate cards) |

## 5. How we use it

- **Intended use:** test the lifecycle replay, the estimator, the k-hop search, the manipulation checks and the decision policy; run the scenario suite in CI; calibrate claims C1, C3 and C5 (on `scale` for C1).
- **Not to be used for:** claims about real neighbourhood behaviour; the final manipulation-detection numbers (the development attack set is for tuning, the held-out set is separate); tuning on `labels/` inside the engine.
- **Why this use is allowed under the "three sources are never mixed" rule:** it is simulation. Public-network structure enters only as aggregate shape statistics, and results on the public networks are reported separately.

## 6. Transformations

| Step | What was done | Script and version | Input | Output | Seed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Measured degree, reciprocity, clustering, timing-gap and rating-spread statistics | `measure_public.py` 1.0.0 | `raw/epinions/*`, `raw/bitcoin-otc/*` | `derived/public_graph_stats.json` | 20261001 |
| 2 | Simulated people, items, loans, events, outcomes, reviews, disputes, scenarios, attacks | `build.py` 1.0.0 | step 1, engine config, transition table, fixtures | `derived/mini`, `derived/standard`, `interim/scale` | 20261001 |
| 3 | Checked the files | `validate.py` 1.0.0 | each tier | `COVERAGE.md` | none |
| 4 | Loaded into PostgreSQL 16 and verified | `scripts/load_dataset.py` | a tier, the Alembic schema `dm` | a `*_test` database | none |

## 7. Results and notes

- Checks run on 2026-10-13: `mini` 31,928 passed and `standard` 47,988 passed, 0 failed. Two real defects were found by an earlier full-size run and fixed (cross-community membership timing; item double booking).
- Two identical builds are byte-identical; the committed files equal a fresh build (`test_dataset_generator.py`).
- **Loaded into PostgreSQL 16** (the project's real schema): reading the schema's triggers showed the first version broke several of its rules (missing event payloads, wrong order of return checklists, borrower verification level, missing booking and locality rows); all fixed. Now `mini` and `standard` load with foreign keys and CHECK constraints on and every verification passes (`replay_state()`, hash chains, the backend's own replay), and a request made through the real lifecycle service on top of the loaded data completes (`test_dataset_load.py`).
- The engine has not been run on this data yet.

## 8. Decision

- **Verdict:** use with changes.
- **Reason:** structurally sound and reproducible; assumptions need the engine owners' sign-off before any number from it goes in the report.
- **Reviewed by:** Fatima Khursheed, Areeba Javed, Minahil Kashif
