# Search evaluation data (DA-25): SYNTHETIC

Built by `data/generators/search_catalogue.py` (fixed seed; run `python -I data/generators/search_catalogue.py`).
Do not edit the CSV files by hand: change the generator and rebuild. `MANIFEST.json` holds the SHA-256 of each file.

| File | What it is |
| :--- | :--- |
| `catalogue.csv` | 150 synthetic items in the evaluator's community (several per need; 56 with a Roman Urdu other name in `search_terms`; lenders L01 to L08 have history, L09 to L20 are new) and 20 decoys (`decoy` = OTHER_COMMUNITY, DRAFT, BLOCKING_LENDER) that must never be returned |
| `queries.csv` | 26 test queries in the six types of DA-25 section 3, each with the `need` the labellers judge |
| `practice_queries.csv` | 5 calibration queries, not part of the test set |
| `MANIFEST.json` | Counts, seed and checksums. `frozen` turns true when the team signs off DA-25 step 1 |

## Status (15 November 2026)

| Step (DA-25 section 6) | State |
| :--- | :--- |
| 1. Catalogue, queries and guide written | Done as a draft by Minahil (Student 3). **The team must check every Roman Urdu word (open point S-E2) and then set `frozen` to true** |
| 2. Labelling and agreement | **Not done.** Needs two people labelling alone. The pool (top 10 of keyword-only and of hybrid, shuffled, systems hidden) can only be built once meaning-based search (A9) runs on this catalogue. `search_agreement.py` computes exact agreement, Cohen's kappa and quadratic kappa from the two label files |
| 3 to 5. Runs, metrics, targets | Plan item M11 (Slice 3) |

No label in this folder has been made up: there are none yet.

## Labelling guide (from DA-25 section 4)

Judge the **need** in `queries.csv`, not whether the words match.

| Label | Meaning | Example for "something to make holes in a brick wall" |
| :--- | :--- | :--- |
| 2 | Meets the need | Hammer drill |
| 1 | Partly meets it: a workable substitute | Cordless drill driver (light walls only), masonry drill bit set (needs a drill) |
| 0 | Does not meet it | Hand saw |

1. Label the five practice queries together with the other labeller, compare, and fix this guide where you disagreed.
2. Then label the test pool **alone**, without discussing it. Each labeller writes `query_id,item_key,label`.
3. Run `python -I data/generators/search_agreement.py labels_a.csv labels_b.csv` and record the result **before** resolving disagreements.
4. Settle each disagreement, record the final label and the reason; keep both raw files.
5. A "no answer" query (Q25, Q26) has no relevant item: label everything shown 0. These queries are left out of recall and NDCG and reported on their own.
