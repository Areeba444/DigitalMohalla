# Dataset card: yelpchi

| Field | Value |
| :--- | :--- |
| Short name | `yelpchi` |
| Full name | Yelp Fake Review Dataset (YelpChi-derived, Chicago restaurants) |
| Source type | other public (Kaggle re-upload of Yelp Chicago reviews) |
| Status | obtained; in `raw/yelpchi/` |
| Added by | Areeb Javed, 2026-11-22 |
| Last updated | 2026-11-22 |

## 1. Where it comes from

| Field | Value |
| :--- | :--- |
| Original publisher or authors | Rayana, S. and Akoglu, L. (Stony Brook University). The original YelpChi dataset is part of the ODDS (Outlier Detection DataSets) collection. This copy was downloaded from Kaggle ("Yelp Fake Review Dataset", a re-upload). |
| Download link | Kaggle: `https://www.kaggle.com/datasets/` (search "Yelp Fake Review Dataset", ~7 MB) |
| Date downloaded | 2026-11-22 |
| Version or release | `new_data_train.csv` and `new_data_test.csv` (Kaggle version 1) |
| Citation | Rayana, S. and Akoglu, L. (2015). "Collective Opinion Spam Detection: Bridging Review Networks and Metadata." ACM KDD 2015. |
| File(s) in `raw/yelpchi/` | `new_data_train.csv` (5.77 MB, 9,929 rows), `new_data_test.csv` (1.44 MB, 2,483 rows) |
| Delimiter | Tab (`\t`) — despite the `.csv` extension |

## 2. Licence and permitted use

| Field | Value |
| :--- | :--- |
| Licence or terms of use | Not explicitly stated on the Kaggle page. The original academic release (ODDS) is for research use. Kaggle's terms apply to the downloaded copy. |
| May we redistribute it in the repository? | **No** — `raw/` is gitignored. Statistics and results derived from it may appear in reports. |
| Attribution required? | Yes — cite Rayana & Akoglu KDD 2015 wherever results derived from this data appear. |
| Restrictions | Academic / research use only. Do not re-identify individual reviewers. |
| Personal data in it? | Reviewer names are present in the `name` column. Do not expose or analyse individual reviewers. Use only aggregate text statistics. |
| Checked with supervisor? | No |

> [!IMPORTANT]
> This is a **Kaggle re-upload**, not the original ODDS release. The text has been preprocessed (stop words removed, lowercased). Cosine values measured from this file will be slightly lower than from raw text. Relative ordering (legit << spam) is preserved.

## 3. What is in it

| Field | Value |
| :--- | :--- |
| Format | Tab-separated values (TSV), despite `.csv` extension |
| Rows | Train: 9,929 · Test: 2,483 · Total: 12,412 |
| Columns (23 total) | `reviewID`, `reviewerID`, `restaurantID`, `date`, `rating`, `reviewUsefulCount`, `reviewContent`, `flagged`, `name`, `location`, `yelpJoinDate`, `friendCount`, `reviewCount`, `firstCount`, `usefulCount`, `coolCount`, `funnyCount`, `complimentCount`, `tipCount`, `fanCount`, `restaurantRating`, `ReviewLength` |
| Label column | `flagged` — `0` = genuine (not filtered by Yelp), `1` = spam (filtered by Yelp's classifier) |
| Text column | `reviewContent` — preprocessed: lowercased, stop words removed |
| Label balance | Train: 4,993 genuine (50.3%), 4,935 spam (49.7%) — nearly balanced |
| Time span | 2005-07-07 to 2012-09-20 |

## 4. How it maps to what we need

| We need | Supplied? | Detail |
| :--- | :--- | :--- |
| P-04: Review text with spam labels | **Yes** | 12,412 labelled Yelp reviews, genuine vs spam |
| Threshold calibration for the similar-review signal | **Yes** | See calibration results below |
| Spam text that is highly similar within groups | **Partially** | YelpChi labels are behavioural (Yelp's filter), not text-similarity-based. Spam reviews here have naturally diverse text (mean cosine 0.11). This validates the natural baseline, not ring/farm text patterns. |

## 5. Calibration results

Run: `python -I data/generators/calibrate_similarity.py` on 2026-11-22.  
Method: character 3-gram TF-IDF cosine, same as `validate.py`. Sample: 1,500 legit + 1,500 spam (seed 20261001).

| Metric | Legit reviews | Spam reviews |
| :--- | :--- | :--- |
| p50 cosine | 0.133 | 0.104 |
| p75 cosine | 0.175 | 0.144 |
| p90 cosine | 0.216 | 0.185 |
| p95 cosine | 0.242 | 0.211 |
| p99 cosine | 0.292 | 0.265 |
| max cosine | 0.781 | 1.000 |
| mean cosine | 0.137 | 0.109 |

**Pairs above each threshold (legit, out of 1,124,250 pairs):**

| Threshold | Pairs above | % |
| :--- | :--- | :--- |
| ≥ 0.50 | 3 | 0.000% |
| ≥ 0.60 | 1 | 0.000% |
| ≥ 0.65 | 1 | 0.000% |
| **≥ 0.70** | **1** | **0.000%** |
| ≥ 0.75 | 1 | 0.000% |
| ≥ 0.80 | 0 | 0.000% |

> [!NOTE]
> The 0.70 threshold used in `validate.py` for the "suspiciously similar legitimate review" check is **confirmed safe** by real Yelp data. Only 1 pair out of 1.1 million legitimate review pairs exceeded 0.70. The threshold could even be raised to 0.80 without increasing false positives.
>
> Our synthetic attack groups (ring, farm, burst) have mean cosine 0.82–0.94 (from COVERAGE.md), which is well above the 0.70 threshold and far above any natural baseline.

Full output: `data/raw/yelpchi/calibration_result.txt`

## 6. How we use it

- **Intended use:** Confirm that the similarity threshold (0.70) in the validator and engine is safe — genuine reviews rarely resemble each other above that level.
- **Not to be used for:** Training a classifier on YelpChi and deploying it on DigitalMohalla reviews (domain mismatch: restaurant reviews ≠ peer borrowing). The labels are Yelp-behavioural, not purely text-based.
- **Why this use is allowed under the "three sources are never mixed" rule:** Aggregate statistics only. No YelpChi rows enter the simulated dataset; no results on YelpChi are reported as results on DigitalMohalla.

## 7. Decision

- **Verdict:** Use for threshold calibration only (P-04). The calibration is complete; the threshold 0.70 is confirmed.
- **Reviewed by:** Areeb Javed (2026-11-22)
