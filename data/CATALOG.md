# Dataset catalogue

One row per dataset. Details go on the dataset's own card in `datasets/`. Leave a field as "unknown" until you have checked it. Updated 2026-10-12; sizes were measured from the files in `raw/`.

**Status values:** `candidate` (idea, not yet obtained) · `obtained` (file in `raw/`) · `in use` · `derived` (we built it) · `rejected` (not usable, see card)

**Source type** (see `README.md`): `simulation` · `public trust network` · `real pilot` · `other public` · `own generated`

| Short name | What it is | Source type | Status | Licence / terms | Size | Card | Intended use |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `epinions` | Epinions trust and distrust statements, article metadata, helpfulness ratings (from Kaggle, per the team's README) | public trust network | obtained; **`rating.txt` incomplete** | Kaggle "Other"; page asks for citation only (TrustRec paper); no redistribution permission shown | `user_rating.txt` 841,372 edges and 131,828 users; `mc.txt` 1,560,144 rows; `rating.txt` 13,668,320 lines, cut off. About 783 MB in total | [epinions](datasets/epinions.md) | k-hop validation and baseline comparison (the Overview's named external benchmark) |
| `bitcoin-otc` | Bitcoin OTC signed trust ratings, -10 to +10, with timestamps (from Stanford SNAP, per the README) | public trust network | obtained | none stated on the SNAP page text; cite Kumar et al. 2016 and 2018; no redistribution permission shown | 35,592 edges, 5,881 users, 3,563 negative; 2010-11-08 to 2016-01-25 | [bitcoin-otc-alpha](datasets/bitcoin-otc-alpha.md) | k-hop validation; distrust signals (the proposal's named benchmark) |
| `bitcoin-alpha` | Bitcoin Alpha signed trust ratings, same format | public trust network | obtained | as OTC (Alpha page not seen) | 24,186 edges, 3,783 users, 1,536 negative; 2010-11-08 to 2016-01-22 | [bitcoin-otc-alpha](datasets/bitcoin-otc-alpha.md) | As above; a second graph for robustness |
| `community-neighborhood` | Synthetic Islamabad neighbourhood: users, transactions, ratings, disputes, hidden ground truth | simulation (own generated) | obtained | ours; synthetic | 60 users, 250 transactions, 484 ratings, 16 disputes; 2025-10-17 to 2026-10-11 | [community-neighborhood](datasets/community-neighborhood.md) | Primary data for trust estimation, sparse evidence, indirect trust and the evaluation scenarios. Gaps listed on the card |
| `fraud-scenarios` | Hand-made attack patterns (rating ring, device sharing, burst, identical text, vouching) plus a legitimate baseline | simulation (own generated) | obtained | ours; synthetic | 82 rows: 74 attack, 8 legitimate | [fraud-scenarios](datasets/fraud-scenarios.md) | Manipulation-detection tests and the false-positive guard. Some scenarios do not match iteration 1 signals |
| `neighborhood-sim` | Synthetic neighbourhood v2: schema-shaped loans, events, outcomes, reviews, disputes with ground truth, 20 scenario cases, development attack set | derived (own generated, simulation) | derived | ours; synthetic | `mini` 63 users/190 loans; `standard` 90 users/296 loans; `scale` 2,026 users/12,171 loans (on demand) | [neighborhood-sim](datasets/neighborhood-sim.md) | CI tests, scenario suite, calibration, claims C3 and C5 |
| `custom-dataset1` | Search and matching evaluation set: listings, requests, pooled results, relevance labels, owner trust histories | simulation, **origin to confirm** | obtained | unknown (ours?) | 184 listings, 25 requests, 63 labelled pairs, 60 owner histories | [custom-dataset1](datasets/custom-dataset1.md) | Module 4 search and matching evaluation (NFR-Q-05). Not trust-engine data |

## Datasets the project documents mention that we do not have yet

| Name | Mentioned in | What the document says it is for | Open point |
| :--- | :--- | :--- | :--- |
| YelpChi | Context doc §15 | Robustness check for manipulation detection (review spam) | Decide in iteration 2; would help with F5 (no realistic review text in our data) |
| A public classifieds or e-commerce dataset (OLX-style dump, RetailRocket click and purchase data) | Overview §5 (search and matching, Tier 2) | Only for the later learning-to-rank work in Module 4; not part of the trust engine | Out of scope for iteration 1 |
| Real pilot data | Overview, Context doc §2 | Acceptance and usability only | Needs consent and privacy protection; not before the pilot |

## Derived datasets (ours)

| Name | Built from | Script | Version | Seed | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `public_graph_stats` | `epinions`, `bitcoin-otc`, `bitcoin-alpha` (aggregates only) | `generators/measure_public.py` | 1.0.0 | 20261001 | `derived/public_graph_stats.json` |
| `neighborhood-sim/mini` | statistics above, engine config, fixtures | `generators/build.py --tier mini` | 1.0.0 | 20261001 | committed in `derived/mini` |
| `neighborhood-sim/standard` | as above | `generators/build.py --tier standard` | 1.0.0 | 20261001 | committed in `derived/standard` |
| `neighborhood-sim/scale` | as above | `generators/build.py --tier scale` | 1.0.0 | 20261001 | built on demand into `interim/scale`; not committed |

The generators for the two original synthetic sets use seed 42; see their cards.

## Files in the data folder that are not datasets

| File | What it is |
| :--- | :--- |
| `Digital_Muhalla_Algorithms_and_Datasets_Deep_Dive.md` | The team's earlier implementation guide (algorithm code, dataset construction guide, tips). A reference; the design baseline wins where they differ. See `README.md` section 4 |
| `raw/Datasets/README.md` | The dataset collection's own README (module mapping, loading examples, evaluation targets) |
| `raw/Datasets.zip` | A 110 MB zip holding the same files as `raw/Datasets/` |
