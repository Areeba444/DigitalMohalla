# Search evaluation design (DA-25)

| Field | Value |
| :--- | :--- |
| Version | 0.1 draft |
| Date | 2026-11-07 |
| Author | Minahil Kashif (Student 3), drafted with Claude Code; review: Areeba Javed (Student 2) pending |
| Status | Draft. The catalogue, query set, labelling guide and metrics are **frozen before anyone measures** (checksums recorded), as for the trust evaluation (`14_testing/Evaluation_Protocol_v0.md`) |
| Realises | NFR-Q-05 (precision@k and gain over the keyword baseline), NFR-P-01, NFR-P-02 (latency recorded, no target yet), FR-S-05 (logs used later for learning to rank); build items M9 and M11; suite 31 |
| Separation | Student 1 builds retrieval and Student 2 builds ranking (DA-22). Student 3 builds the catalogue, the queries and the labels and scores both, so the scorer is not an author |

## 1. Why a new catalogue

Today's `standard` dataset has 108 items sharing 26 titles and no descriptions (iteration 2 plan). Meaning-based search cannot be judged on that: almost every query would match by title or not at all. The old `custom-dataset1` labels had exact agreement 46% and Cohen's kappa 0.26 (`data/README.md`, finding F7), which is too weak to rank two systems. This design fixes both problems before anything is measured.

## 2. Catalogue (about 150 items, SYNTHETIC)

| Property | Rule |
| :--- | :--- |
| Size | About 150 PUBLISHED items in the evaluator's community, plus about 20 decoys: other communities, DRAFT items, a blocking lender. The decoys test eligibility (suite 30) and must never appear in results |
| Coverage | Every category in `category`; several items per need (for example three ways to make a hole in a wall), so ranking has real choices |
| Descriptions | One to three plain sentences per item: what it is, its condition, what it is good for. Written by hand from a template list, not copied from any listing site |
| Names | English titles, and for about a third of the items a common Roman Urdu name in the title or description (for example *seerhi* for a ladder, *istri* for a clothes iron, *degchi* for a cooking pot). The team checks every Roman Urdu word, since an English-only model will miss these (NFR-U-05) |
| Lenders | Spread so some items have lenders with no history and some with history, letting suite 30 check that a new lender is not pushed down |
| Build | A generator with a fixed seed (`data/generators/`, build item M9) writes the catalogue as CSV for the loader; labelled SYNTHETIC; no address or coordinate fields |

## 3. Query set (20 to 30 queries)

Written **before** either system is run on the catalogue, and frozen with a checksum.

| Query type | Share | Example (illustrative; the real set is written in M9) |
| :--- | :--- | :--- |
| Exact name | about 20% | "drill machine" |
| Need, no shared word with the best item | about 30% | "something to make holes in a wall" |
| Roman Urdu or mixed | about 20% | "seerhi chahiye" |
| Misspelling or short form | about 10% | "lader" |
| Category-level | about 10% | "garden tools" |
| No good answer in the catalogue | about 10% | a need nothing in the catalogue meets; checks that results are not shown with false confidence |

Five more practice queries, not in the test set, are used only for labeller calibration (section 4).

## 4. Relevance labels

| Step | Rule |
| :--- | :--- |
| Scale | 0 = does not meet the need; 1 = partly meets it (a workable substitute); 2 = meets it |
| Pool | For each query, the union of the top 10 from keyword-only and the top 10 from hybrid, shuffled, with the system hidden. Unjudged items count as 0 and the pool depth is reported |
| Labellers | Two people, each labelling alone with the written guide. Proposed: Student 3 and one person outside the team who is not an author of retrieval or ranking. If no outsider is available, Student 1 with the conflict disclosed. Decided by the team |
| Calibration round | Both label the five practice queries, compare and fix the guide. Then they label the test set without discussing it |
| Agreement | Cohen's kappa and quadratic-weighted kappa on the test pool, reported before disagreements are resolved; exact agreement as a percentage |
| Resolution | Disagreements are discussed and settled; the final label and the reason are recorded. The raw labels of both labellers are kept |

## 5. Metrics

| Metric | Definition |
| :--- | :--- |
| Precision@5 | Share of the top 5 with label of at least 1 |
| Recall@10 | Items with label of at least 1 in the top 10, divided by all items with label of at least 1 in the pool for that query |
| NDCG@10 | Gain 2^label − 1, discount log2(rank + 1), normalised by the ideal order of the judged pool |
| Mean and noise | Mean over queries; 95% bootstrap interval over queries (1,000 resamples, fixed seed); paired difference hybrid − keyword with its interval |
| By query type | The same metrics per type in section 3, so a gain only on exact names is visible |
| Latency (no target) | Retrieval time and whole search time over 100 runs on the deployed and the local instance: median and P95 (NFR-P-01, NFR-P-02) |

Queries with no relevant item ("no good answer") are left out of recall and NDCG and reported on their own: what the top result was, and whether the reason line was honest.

## 6. Procedure

1. Freeze the catalogue, queries and labelling guide (checksums in the results file).
2. Run the labelling (section 4) and report agreement.
3. Run both systems on the frozen query set as a member of the evaluator's community (TC-164). Record the model name and size, the config version and the commit.
4. Compute the metrics once and report them from the results file.
5. Set the real targets for FYP-2 **after** this baseline and before FYP-2 runs. The overview's 60 to 70% precision and 30 to 40% gain are estimates (I-15), not targets.

## 7. Limits to state in the report

- The catalogue and queries are synthetic and written by the team, so absolute precision says little about real use. The comparison between the two systems on the same frozen set is the result.
- 20 to 30 queries give wide intervals; the bootstrap intervals show how wide.
- Learning to rank needs real pilot clicks (FR-S-05 logs), so it stays in FYP-2.

## 8. Open points

| # | Point | Owner |
| :--- | :--- | :--- |
| S-E1 | Second labeller | Team |
| S-E2 | Which Roman Urdu names to include; checked by the team | Team |
| S-E3 | Relevance threshold for precision and recall: at least 1 (proposed) or 2 | Students 3 and 2 |
| S-E4 | Whether the first measurement runs on the deployed instance or the local one (the deployed one may run keyword-only if the model does not fit, ADR-0016) | Students 1 and 2 |
