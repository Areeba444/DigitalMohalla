# Dataset card: custom-dataset1

| Field | Value |
| :--- | :--- |
| Short name | `custom-dataset1` |
| Full name | Search and matching evaluation set (listings, requests, pooled results, relevance labels, owner trust histories) |
| Source type | simulation. **Origin to confirm** |
| Status | obtained |
| Added by | team (files in `raw/custom-dataset1/`); card written 2026-10-12 |
| Last updated | 2026-10-12 |

**This is not trust-engine data.** It looks like the evaluation set for Module 4 (search, discovery and matching), which is supporting scope, not the CCP. It is in the data folder with the others, so it is catalogued here.

## 1. Where it comes from

| Field | Value |
| :--- | :--- |
| Original publisher or authors | **Unknown.** Nothing in the folder says who built it, how, or with what script. The user noted that "it has some stuff I don't remember". Fill in after asking whoever made it |
| What I could infer | The structure matches the plan for evaluating search: the Overview asks for hand-labelled queries (Precision@5, Recall@10, NDCG@10) and NFR-Q-05 asks for 20 to 30 hand-labelled queries; this set has 25 requests. It has results pooled from two baselines (`b1`, `b2`) and a proposed method (`p`), relevance labels from two labellers, and "cold start" owners. This is inferred, not confirmed |
| Link to a generator script | none found |
| File(s) in `raw/custom-dataset1/` | `listings.csv`, `requests.csv`, `pooled_results.csv`, `labels_student1.csv`, `labels_student2.csv`, `final_labels.csv`, `trust_histories.csv` |
| Checksum (first 16 hex of SHA-256) | listings 623b854b2d6f1fe4 · requests 5079bb7e463d9ad0 · pooled_results 4d345f340756b2bd · labels_student1 daadb02842cdecd5 · labels_student2 5ffd3fa5e42c2faf · final_labels a5b1be9775c4c825 · trust_histories f0d9a5d4f3ad849f |

## 2. Licence and permitted use

Unknown. Presumably ours (it appears to be team-built). Confirm, and confirm that it is synthetic.

## 3. What is in it

| File | Rows | Fields |
| :--- | :--- | :--- |
| `listings.csv` | 184 | `listing_id, owner_id, category, description, availability, lat, lon, condition, transaction_type, restrictions` |
| `requests.csv` | 25 | `request_id, requester_id, category, keywords, max_distance_km, requester_lat, requester_lon, required_transaction_type, is_edge_case` |
| `pooled_results.csv` | 63 | `request_id, listing_id, appeared_in_b1, appeared_in_b2, appeared_in_p, p_explanation, labeler_1, labeler_2, final_label` (the labeller columns are empty here; they are filled in the label files) |
| `labels_student1.csv`, `labels_student2.csv` | 63 each | `request_id, listing_id, label` |
| `final_labels.csv` | 63 | `request_id, listing_id, label, labeler_1, labeler_2, agreed` |
| `trust_histories.csv` | 60 | `owner_id, completed_transactions, cancellations, disputes, return_on_time_rate, account_age_days, is_cold_start` |

### Measured properties (2026-10-12)

| Property | Value |
| :--- | :--- |
| Listings | 184 from 55 owners across 10 categories (Garden Equipment and Baby & Kids 29 each, Furniture 21, Musical Instruments 19, Kitchen Appliances 18, Sports Equipment 16, Books 15, Tools 14, Electronics 13, Camping Gear 10) |
| Transaction types | rent 65, swap 60, borrow 59. **No donation** |
| Condition | good 40, fair 40, worn 38, new 34, like_new 32 |
| Coordinates | latitude 33.469 to 33.725, longitude 72.888 to 73.209 (an Islamabad-area box) for every listing and request |
| Requests | 25; 3 flagged as edge cases; 23 have labelled pairs (**R03 and R15 have none**) |
| Labelled pairs | 63 over 23 requests and 53 listings. Final labels on a 0 to 3 scale: 0: 6, 1: 18, 2: 21, 3: 18 |
| Every pair appears in all three result lists | `appeared_in_b1`, `appeared_in_b2` and `appeared_in_p` are True for all 63 pairs, so the pool does not show where the methods differ |
| Owner histories | 60 owners; 12 flagged cold start (all with 0 completed transactions, no on-time rate and an account 3 to 28 days old); completed transactions 0 to 37; 5 owners have a dispute |
| Labeller agreement | exact 29 of 63 (46.0%); Cohen's kappa 0.26; quadratic-weighted kappa 0.58; within one point 95.2% (computed by me from the labeller columns) |

## 3a. Known quality problems and mismatches with the project

1. **Weak labels.** Exact agreement is 46% and kappa 0.26 ("fair"). How disagreements were turned into a final label is not recorded (in the sample, the final label is sometimes the higher, sometimes the lower of the two). Any Precision@k or NDCG from these labels is weak evidence.
2. **Pool does not discriminate between methods.** All 63 pairs were returned by all three methods, so the data cannot show whether the proposed method beats the baselines.
3. **Scope.** Transaction types `rent` and `swap` are not in the project's scope (lending, borrowing and donation); there is no donation. Needs a decision (F8).
4. **Coordinates.** Every listing and request has latitude and longitude. The system itself must never store exact locations (NFR-PR-01). For a synthetic evaluation set this is acceptable only if the values are synthetic and labelled so. Confirm and label.
5. **Trust information is a summary, not events.** `trust_histories.csv` gives counts and an on-time rate per owner; it does not connect to the transaction, outcome or review records the trust engine uses, and its owner IDs (`O…`) do not match the community dataset (`U…`).
6. **Two requests have no labelled pairs** (R03, R15).
7. **Labeller names.** Files are named `labels_student1/2`. The team's own labelling is fine for a student project but must be described honestly as team labelling in the report, with the instructions the labellers followed (not found here).
8. Origin, licence and whether it is synthetic are all unconfirmed.

## 4. How it maps to what we need

| We need | Supplied? | How, or what is missing |
| :--- | :--- | :--- |
| NFR-Q-05: 20 to 30 hand-labelled queries for Precision@k and gain over a keyword baseline | Yes (25 queries) | With the label-quality caveats above |
| Trust-engine needs (D-01 to D-10) | No | Not an outcome, rating or dispute dataset |
| Cold-start fairness in matching | Partly | `is_cold_start` owners; the fair-matching claim would need more owners and a protocol |

## 5. How we use it

- **Intended use:** Module 4 search and matching evaluation only, when Module 4 is built (planned for iteration 3).
- **Not to be used for:** any claim about the trust engine.
- **Why this is allowed under the three-sources rule:** it is simulation, used for a different module's claims.

## 6. Transformations

None yet.

| Step | What was done | Script and version | Input | Output | Seed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | |

## 7. Results and notes

- Counts and agreement figures were computed from the files on 2026-10-12.

## 8. Decision

- **Verdict:** keep, do not use yet. First confirm its origin and licence, decide on `rent`/`swap` and the coordinates, and improve the labels.
- **Reviewed by:** Fatima Khursheed, Areeba Javed, Minahil Kashif
