# Data

Everything about the data for Digital Mohalla lives here: what the project needs, which datasets we have, where each came from, how we turn them into the data we need, and the files themselves.

| Field | Value |
| :--- | :--- |
| Owner | Student 3 (Module 10, analytics and evaluation), with Student 2 for the engine's data needs |
| Status | Updated 2026-10-13. Five dataset cards written from the actual files (2026-10-12); the first derived dataset, `neighborhood-sim`, built by `generators/` and validated (2026-10-13) |
| Related documents | `docs/DigitalMohalla_Project_Context.md` §2 (data and ethics), §6.6 (data structures), §16 (iteration 4 evaluation); `docs/design/01_requirements/Digital_Mohalla_Project_Overview_Ver1.md` ("Datasets and Evaluation Data"); `docs/design/06_data_model/` |

## 1. Datasets at a glance

All numbers below were measured from the files in `raw/` on 2026-10-12, not copied from the READMEs. Cards with the details are in `datasets/`.

| Dataset | Source type | What it is | Size (measured) | Feeds | Card |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `epinions` | public trust network | User-to-user trust and distrust statements, article metadata, review-helpfulness ratings | 841,372 trust edges, 131,828 users; 1,560,144 articles; `rating.txt` has 13,668,320 lines and **is truncated** | k-hop validation, baseline comparison | [epinions](datasets/epinions.md) |
| `bitcoin-otc` and `bitcoin-alpha` | public trust network | Signed, weighted (-10 to +10) trust ratings with timestamps | OTC: 35,592 edges, 5,881 users. Alpha: 24,186 edges, 3,783 users | k-hop validation, distrust signals | [bitcoin-otc-alpha](datasets/bitcoin-otc-alpha.md) |
| `community-neighborhood` | simulation (own generated, seed 42) | Synthetic Islamabad neighbourhood: users, borrow/lend transactions, ratings, disputes, hidden ground truth | 60 users, 250 transactions, 484 ratings, 16 disputes | Trust estimation, sparse evidence, indirect trust, scenarios | [community-neighborhood](datasets/community-neighborhood.md) |
| `fraud-scenarios` | simulation (own generated, seed 42) | Hand-made attack patterns plus a clean "legitimate dense group" baseline | 82 rows: 74 attack, 8 legitimate | Manipulation detection | [fraud-scenarios](datasets/fraud-scenarios.md) |
| `custom-dataset1` | simulation, **origin to confirm** | A search and matching evaluation set: listings, requests, pooled results, two people's relevance labels, owner trust histories | 184 listings, 25 requests, 63 labelled pairs, 60 owner histories | Module 4 (search and matching), not the trust engine | [custom-dataset1](datasets/custom-dataset1.md) |
| `neighborhood-sim` | **derived**, synthetic (own generator, seed 20261001) | Schema-shaped test data with ground truth: loans as lifecycle event streams, outcomes, trust edges, reviews, disputes, 20 scenario cases, a development attack set. Shape statistics measured from the public networks | `mini`: 63 users, 190 loans. `standard`: 90 users, 286 loans, 18 months. `scale`: about 2,000 users, 12,000 loans (not committed) | CI tests, scenario suite, calibration (C1 on `scale`), claims C3 and C5 | [neighborhood-sim](datasets/neighborhood-sim.md) |

Also in the data folder: `Digital_Muhalla_Algorithms_and_Datasets_Deep_Dive.md` (the team's earlier implementation guide, see section 4) and `raw/Datasets/README.md` (the dataset collection's own README).

## 2. The rule that governs everything

The project uses three kinds of data and **they are never mixed**:

| Source | Used for | Never used for |
| :--- | :--- | :--- |
| **Simulation** (our own generated data) | All claims about the algorithms: accuracy, calibration, ablations, manipulation detection, sparse evidence, cold start | Claims about real-world behaviour |
| **Public trust network** (Epinions, Bitcoin OTC and Alpha; YelpChi if added) | Validating propagation (k-hop indirect trust) and robustness as an external benchmark | Anything about Pakistani neighbourhood borrowing |
| **Real pilot** (consenting participants, later) | Acceptance and usability only | Tuning or training |

Public datasets are not "what we need". Their job is to be a source of real structure (graphs, rating patterns, timing) that we use to make our simulated dataset more realistic, or to benchmark on separately. A derived dataset must always say which source it came from and must be labelled **synthetic** if any of it was generated.

## 3. What is solid, and what needs attention

This is the honest state after reading the files. Details and evidence are on each card; the main ones:

| # | Finding | Why it matters | Where |
| :--- | :--- | :--- | :--- |
| F1 | Epinions `rating.txt` is almost certainly an **incomplete download**: it is exactly 716,800,000 bytes, and its last row is cut off (the final field is empty and there is no line ending). The READMEs say "about 3M+" ratings; the file has 13,668,320 lines. I could not check the original file size, so how much is missing is unknown | Results from it would silently use an arbitrary slice. The trust file (`user_rating.txt`) looks complete (every row has four fields) | epinions card |
| F2 | Epinions loader examples in the Deep Dive use other file names (`ratings_data.txt`, `trust_data.txt`) and numbers (131K users, 5.9K trust relationships) from a different release. The actual Kaggle files are `user_rating.txt` (tab separated), `mc.txt` (**pipe** separated) and `rating.txt` | The Deep Dive loader will fail or load the wrong thing | epinions card |
| F3 | The community dataset has **no high-value items**: every item is LOW (185) or MEDIUM (65) under the project's bands (LOW up to 5,000 PKR, MEDIUM up to 15,000, HIGH above); the maximum value is exactly 15,000 | Scenario ES-06 and the high-value rule cannot be tested on it | community-neighborhood card |
| F4 | No open disputes: all 16 disputes have a resolution | The `ACTIVE_DISPUTE` state (ES-03 open variant, ES-07, ES-08) cannot be tested | community-neighborhood card |
| F5 | Only 17 distinct review texts across 484 ratings (templated). Legitimate reviews are therefore already near-identical | The review-similarity check cannot be calibrated on this data and would see natural high similarity. The "identical text" attack is not distinguishable from normal | community-neighborhood and fraud-scenarios cards |
| F6 | `sybil_vouching` models manual **vouches**, but the project derives trust edges only from verified outcomes and has no vouch feature. `device_sharing` needs device IDs, which the design allows only "where legitimately available". Burst-velocity and new-account signals are not in iteration 1 (iteration 1 builds reciprocal clustering, review similarity and the retaliation check) | Not every scenario maps to an engine signal we are building now | fraud-scenarios card |
| F7 | `custom-dataset1` labeller agreement is low: exact agreement 46% (29 of 63), Cohen's kappa 0.26, quadratic-weighted kappa 0.58, agreement within one point 95% | Weak relevance labels weaken any search evaluation. The way disagreements were resolved is not recorded | custom-dataset1 card |
| F8 | `custom-dataset1` includes latitude and longitude for every listing and request, and transaction types `rent` and `swap`, which are not in the project's lending, borrowing and donation scope | Coordinates are fine only if they are synthetic and labelled so (the system itself stores no exact location). `rent` and `swap` need a scope decision | custom-dataset1 card |
| F9 | Several files describe themselves as "fraud". The project's wording is manipulation and anomaly, never an accusation, and controlled scenarios must be labelled synthetic | Wording in the report and screens | fraud-scenarios card |
| F10 | The Deep Dive and the dataset README use "Beta-Binomial". The project's term is "recency-weighted Beta posterior" | Terminology marks in the report | section 4 below |
| F11 | The success targets quoted in the dataset README (fraud recall at least 90%, false positives under 5%) are not agreed: the proposal says at least 70% accuracy and under 5% false positives, and NFR-Q-03 is still to be decided | Do not quote them as project targets yet | REQUIREMENTS.md, Q8 |
| F12 | **Both generators compute dates from the current time** (`datetime.now()`). The seed (42) fixes the content but every re-run shifts all dates, so the files are not exactly reproducible | A figure regenerated later will not match byte for byte. The attack timestamps would also not line up with the community timeline | community-neighborhood and fraud-scenarios cards |
| F13 | In the community dataset **111 of 250 transactions (44%) are dated before the borrower's or lender's account was created** (65 before the borrower's, 63 before the lender's) | Account-age and new-account signals, and any replay that assumes users exist before their first transaction, give wrong results on this data | community-neighborhood card |
| F14 | `raw/Datasets.zip` (110 MB) holds the same files as `raw/Datasets/` | Wasted space, confusion over which is current. Nothing was deleted | |

**Update 2026-10-13.**

- F1: the team downloaded the Epinions files again; the new `rating.txt` is byte-identical to the first (same size, same checksum, same cut-off last line), so it is still incomplete. Measured: its rows cover creation years 2001 (12,779,772 rows) and 2002 (888,547 rows) only, while the trust statements run to 2003-08-12, which supports the incompleteness finding. Licence and citation are now recorded on the Epinions and Bitcoin cards.
- F3, F4, F5, F12, F13 are fixed in the new dataset `neighborhood-sim` (high-value items, open disputes, hundreds of distinct review texts, fixed reference date, accounts always older than their first loan). The original `community-neighborhood` files are unchanged. F6 is handled by dropping the vouching pattern and adding retaliation, trivial-exchange and false-claim patterns.
- F15: the hand-checked fixture for ES-05 expects SUFFICIENT_EVIDENCE (rule R8) but `REQUIREMENTS.md` section 3 lists REVIEW_RECOMMENDED. The team must choose; the manifest follows the fixture.
- F16: the generated lending graph has a lighter tail than the public graphs (99th-percentile out-degree 4.9 times the mean against 15.6 for Epinions and 11.4 for Bitcoin OTC). Do not use it for claims about hub behaviour.
- F18: **the schema cannot accept history through its normal rules.** Its triggers stamp each event with the current time, reject requests with past dates, and demand locality and assessment rows. History is therefore loaded by `scripts/load_dataset.py` with the schema's user triggers off, then verified (`verify_event_chain()`, `replay_state()`, the backend's Python replay). This also means anyone who wants realistic history in a demo database must use the loader.
- F17: `neighborhood-sim` rests on assumptions A1 to A10 (`generators/README.md` section 6), notably the outcome mapping (Student 2) and the trust-edge formula of ADR-0006 (still unsigned).

What looks good: the community dataset has real structure for sparse-evidence testing (replaying it in time order, 24% of borrows happen with no earlier borrowing by that person and 64% with two or fewer), about a year of timestamps (2025-10-17 to 2026-10-11) so recency weighting matters, and a hidden ground-truth column for evaluation. The Bitcoin graphs and Epinions trust file are complete and large enough for k-hop and latency tests.

## 4. How the Deep Dive document relates to the design

`Digital_Muhalla_Algorithms_and_Datasets_Deep_Dive.md` is an earlier implementation guide. It has three parts: algorithm code (Beta trust, k-hop, multi-signal detection), a dataset construction guide, and implementation tips. Treat it as a **reference, not the baseline**:

- Where it and the design baseline disagree, the design wins (`docs/design/11_assurance_engine/`, ADRs, config 1.1.0). The Deep Dive's Beta code has no recency weighting, uses the name "Beta-Binomial", and uses a different k-hop and detection structure.
- Its weekly plan (Members A, B, C; 16 weeks) is not the project plan (S1, S2, S3; the iteration 1 plan).
- Its database tip (`users`, `transactions`, `trust_cache`) is not the schema; the schema is `docs/design/06_data_model/schema.sql`.
- The dataset ideas in Part 2 are the origin of the community and fraud generators and are consistent with them.

## 5. Plans for each dataset

These are proposals from the team's notes plus the findings above. None is decided; the open questions are in `REQUIREMENTS.md` section 8.

| Dataset | Plan from the team's notes | Needed before it can be used |
| :--- | :--- | :--- |
| `community-neighborhood` | Primary data for trust estimation and the evaluation scenarios; replay in time order; the hidden `_trustworthiness` column is for evaluation only | Superseded for testing by `neighborhood-sim` (second version with a fixed reference date, accounts before first transactions, high-value items, open disputes, diverse review text). Keep the original as the earlier reference; its card still lists its own problems |
| `fraud-scenarios` | Inject into the clean data and check the detectors; legitimate dense groups test the false-positive rate | Patterns rebuilt as the **development** attack set in `neighborhood-sim`. The held-out attack generator is still to be written separately (Student 3, not the detectors' author) |
| `epinions` | Build a social graph from positive trust edges and run k-hop on a 300-user subset; time-based 80/20 split for ratings | Find a complete `rating.txt` (a second download was identical); fix the loader; decide the subset method and the seed. Aggregate shape statistics are already in `derived/public_graph_stats.json` |
| `bitcoin-otc` and `bitcoin-alpha` | Larger graph for k-hop validation; negative ratings as distrust signals; compare with published results (the README names REV2) | Citations recorded on the cards; no redistribution permission shown, so keep raw files out of Git; decide whether Bitcoin OTC replaces or complements Epinions as the benchmark (open decision for iteration 2) |
| `custom-dataset1` | Module 4 search and matching evaluation (Precision@k, NDCG; NFR-Q-05 asks for 20 to 30 hand-labelled queries) | Confirm who built it and how; decide on `rent` and `swap`; improve label agreement; decide whether the coordinates are kept |

## 6. Other rules

- **Every record we generate is labelled synthetic** (files, columns, screens, report). Controlled attack scenarios are never presented as real fraud data.
- **Nothing here may contain exact addresses, coordinates of real places, CNICs or real names.** Public datasets are used only in the form they were released. Do not try to re-identify anyone. The synthetic datasets use first names and sector names only; keep it that way.
- **Check the licence before relying on a dataset** and record it on the card. If the licence forbids redistribution, the file stays out of Git (see below) and only its card is committed.
- **Attack data is kept apart from detector tuning.** The held-out attack generator (iteration 3) is written by someone other than the author of the detectors, and detector parameters are set without looking at it.
- **Every figure in the report must be regenerable.** Record the exact input files, versions, random seeds and scripts for each derived dataset (see the card template).
- Don't invent numbers about a dataset. Write "unknown" until you have checked, and say where you checked.

## 7. Folder map

```text
data/
  README.md               this file
  CATALOG.md              one row per dataset
  REQUIREMENTS.md         the data the project needs, and how well the current datasets cover it
  Digital_Muhalla_Algorithms_and_Datasets_Deep_Dive.md   earlier implementation guide (reference)
  datasets/
    _TEMPLATE.md          copy this to start a dataset card
    epinions.md  bitcoin-otc-alpha.md  community-neighborhood.md  fraud-scenarios.md  custom-dataset1.md  neighborhood-sim.md
  generators/             the synthetic-data generator, validator and its README (Python standard library only)
  raw/                    original files, never edited. NOT committed (see .gitignore)
    Datasets/             epinions/, bitcoin-otc/, community-neighborhood/, fraud-scenarios/, README.md
    custom-dataset1/      the search and matching set
    Datasets.zip          duplicate of Datasets/ (110 MB)
  interim/                cleaned or converted intermediate files. NOT committed
  derived/                the datasets we build for the project (small, synthetic, labelled). Committed
    public_graph_stats.json   aggregate shape statistics from the public networks
    mini/  standard/          schema-shaped CSV, labels/, MANIFEST.json, COVERAGE.md
```

`raw/` and `interim/` stay out of Git because they are large (Epinions alone is about 780 MB) and may be licensed for our use only. Each card says where to get the files and where to put them.

## 8. Workflow for adding or changing a dataset

1. Copy `datasets/_TEMPLATE.md` to `datasets/<short-name>.md` and fill in what you know. Leave unknowns as "unknown".
2. Add a row to `CATALOG.md` and, if useful, to the table in section 1.
3. Put the original file(s) in `raw/<short-name>/` and note the download date and a checksum on the card.
4. Check the licence and terms. Record them. If unclear, ask the supervisor before using it.
5. Decide, against `REQUIREMENTS.md`, which needs it can feed. Record that on the card ("How it maps to what we need").
6. If you transform it, keep the script in `generators/` (or `scripts/`), write the output to `interim/` or `derived/`, and record the steps and seed on the card.
7. If a dataset turns out to be unusable, keep the card, set its status to "rejected" and say why. A negative result is a finding.

## 9. Academic integrity

Data work done with AI assistance goes in `docs/ai-usage-log.md`. Cite dataset sources properly in the report, and say whether an algorithm or data pipeline was reproduced, adapted or modified. Do not fabricate datasets, references or results. The generators' and the Deep Dive's code came from the team's earlier work; say in the report who wrote and who reviewed each.
