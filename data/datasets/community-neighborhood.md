# Dataset card: community-neighborhood

| Field | Value |
| :--- | :--- |
| Short name | `community-neighborhood` |
| Full name | Custom Pakistani neighbourhood dataset (synthetic) |
| Source type | simulation (own generated) |
| Status | obtained |
| Added by | team; generator `generate_custom_neighborhood.py`. Card written 2026-10-12 |
| Last updated | 2026-10-12 |

**All records are synthetic.** The names are first names only and the "sectors" are Islamabad sector names used as neighbourhood labels. No real person or address is represented.

## 1. Where it comes from

| Field | Value |
| :--- | :--- |
| Original publisher or authors | The team. Who wrote the generator is not recorded in the file; fill in |
| How it was made | `raw/Datasets/community-neighborhood/generate_custom_neighborhood.py`. Settings in the file: `N_USERS = 60`, `N_TRANSACTIONS = 250`, `SEED = 42`. It uses pandas. Run from its folder: `python generate_custom_neighborhood.py` (writes `community_data/`) |
| Design source | Deep Dive, Part 2, "Dataset 1: Custom Pakistani Neighborhood Dataset", and the Overview's "Primary Dataset" (50 to 100 users, 200 to 300 transactions) |
| Date generated | Files dated 2026-10-12 in the folder; the data's own dates run 2025-10-17 to 2026-10-11 |
| Whether the generator output is exactly reproducible | **No, not exactly.** The seed is fixed but every date is computed from the time the script is run (`datetime.now() - timedelta(...)` for account creation and for borrow dates), so a re-run shifts all dates. Record the run date with each derived copy, or change the generator to a fixed reference date |
| File(s) in `raw/Datasets/community-neighborhood/community_data/` | `users.csv`, `users_eval.csv`, `transactions.csv`, `ratings.csv`, `disputes.csv` |
| Checksum (first 16 hex of SHA-256) | users b155eae4b22242d7 · users_eval 1b7f7c7d0750fcf7 · transactions 556131557523d230 · ratings dc4900146906c552 · disputes 9bb28ccc17636f9d · generator 1f91e1de7684a938 |

## 2. Licence and permitted use

Ours. Synthetic data, so no personal-data issue. Label it synthetic in every use. May be committed once finalised (small), under `derived/`.

## 3. What is in it

| File | Rows | Fields |
| :--- | :--- | :--- |
| `users.csv` | 60 | `user_id, name, neighborhood, account_created, role_flags, account_status` |
| `users_eval.csv` | 60 | the same plus `_trustworthiness` (hidden ground truth, 0.558 to 0.98). **Evaluation only; never shown to a model during training** |
| `transactions.csv` | 250 | `transaction_id, borrower_id, lender_id, item_name, item_value_pkr, category, borrow_date, expected_return_date, actual_return_date, item_condition_returned, outcome, dispute_filed` |
| `ratings.csv` | 484 | `rating_id, rater_id, target_id, transaction_id, role_being_rated, metric, rating_value, rating_text, timestamp, helpful_votes` |
| `disputes.csv` | 16 | `dispute_id, transaction_id, filed_by, filed_against, dispute_type, description, resolution, moderator_notes` |

### Measured properties (2026-10-12)

| Property | Value |
| :--- | :--- |
| Neighbourhoods | E7 12, G7 11, G9 11, F11 11, F10 9, G8 6 users |
| Account creation | 2025-05-10 to 2026-08-20; all 60 active |
| Transaction dates | 2025-10-17 to 2026-10-11 (about a year) |
| Outcomes | on time 196 (78%), late 38 (15%), disputed 16 (6%). Every disputed transaction has `dispute_filed = Y`; no others do |
| Item value (PKR) | 600 to 15,000, median 3,250 |
| Project value bands | LOW 185, MEDIUM 65, **HIGH 0** |
| Categories | appliances 51, tools 48, outdoor 41, electronics 34, sports 31, furniture 26, media 19 |
| Ratings | borrower role 250, lender role 234; 234 transactions have two ratings, 16 have one |
| Review texts | **17 distinct texts across 484 ratings** (the most common, 60 times each) |
| Disputes | item_condition 6, missing_item 4, money_dispute 4, other 2; **all 16 have a resolution** (none open) |
| Activity per user | each user is in 3 to 17 transactions (median 8); 59 borrowers, 59 lenders; 6 of 244 borrower-lender pairs repeat |
| Roles | `role_flags` also include organizer and vendor, but there is no event or vendor data |

### Evidence available when replayed in time order

Counting, for each transaction, how many earlier transactions the borrower had as a borrower: 59 of 250 (24%) have none, 159 of 250 (64%) have two or fewer, and 223 of 250 (89%) have four or fewer. This is a useful spread for sparse-evidence and cold-start tests.

## 3a. Known quality problems

1. **No high-value items** (F3). The maximum is exactly 15,000 PKR. ES-06 and the high-value hold rule cannot be tested.
2. **No open disputes** (F4). `ACTIVE_DISPUTE` (ES-03 open variant, ES-07, ES-08) cannot be tested, and there is no case of a dispute still unresolved when a new request arrives.
3. **Templated review text** (F5). 17 distinct comments in 484 ratings means legitimate reviews are already near-identical. The review-similarity check would see this as normal and cannot be calibrated here.
4. **A dispute type that contradicts its transaction.** All four `missing_item` disputes link to transactions that have an actual return date and a `damaged` condition, so an item that "never came back" was returned. Check how the generator builds disputes.
5. **The generator's own targets are not met.** The Deep Dive's rules say about 30% late returns and 10% condition disputes; the generated data has 15% late and 6% disputed. Neither set of numbers is a project requirement, but the Deep Dive's description does not match the data.
6. **The dispute README lists `late_return` as a dispute type;** the data has none.
7. **`money_dispute` (4) refers to kitty-party funds,** which is a stretch module outside the borrowing core.
8. The hidden `_trustworthiness` range (0.558 to 0.98) has no clearly unreliable user, so the data cannot show detection of a truly bad actor on its own. The fraud-scenarios set supplies the attackers.
9. **Dates are not consistent with account creation.** 111 of 250 transactions (44%) are dated before the borrower's or the lender's account was created (65 before the borrower's, 63 before the lender's), because account creation and borrow dates are drawn independently. Any new-account or account-age signal, and any replay that assumes a user exists before their first transaction, is wrong on this data. Ratings are never dated before the item's return (0 of 484), so rating order is fine.
10. The team's README says users get "authentic Pakistani names". Fine for synthetic data; keep it to first names.

## 4. How it maps to what we need

Compare with `../REQUIREMENTS.md`. The mapping below is a **proposal for S2 to confirm**, because the outcome metrics are S2's to fix.

| We need | Supplied? | How, or what is missing |
| :--- | :--- | :--- |
| D-01, D-02 Users and community structure | Yes | `users.csv` plus a community label. There is no explicit membership or relationship table; the project derives trust edges from outcomes, so edges come from `transactions.csv` |
| D-03 Items with category and value band | Partly | Category and value exist. Value bands must be derived (LOW up to 5,000, MEDIUM up to 15,000, HIGH above). **No HIGH items** |
| D-04 Transactions with lifecycle events | Partly | Dates and outcome exist. The full event stream (request, locality, assessment, handover and so on) does not; it would have to be generated from these rows |
| D-05 Outcomes | Derivable | `ON_TIME_RETURN` = returned on or before the expected date; `CONDITION_AGREED` = condition `good` and no dispute; `DISPUTE_FREE` = `dispute_filed = N`. Only confirmed outcomes count, so the 16 disputed ones are excluded until resolved and then counted by their resolution |
| D-06 Ratings and reviews | Partly | Ratings exist with role and metric. There are no reviewer-similarity or retaliation flags, and the text is templated |
| D-07 Disputes | Partly | Type mapping to the project's reasons: `item_condition` to CONDITION_MISMATCH or DAMAGE; `missing_item` to NON_RETURN; `money_dispute` and `other` to OTHER. All resolved |
| D-09 Timestamps over a long period | Yes | About one year, so the 180-day half-life matters |
| D-10 Mix of evidence levels | Yes | See the replay counts above |
| Ground truth for reliability | Yes | `_trustworthiness` (hidden) |

## 5. How we use it

- **Intended use:** the clean base for the trust-estimation and indirect-trust tests, replayed in time order, with the hidden column as the target. The base into which controlled manipulation scenarios are injected.
- **Not to be used for:** claims about real neighbourhoods, or tuning on the hidden column.
- **Why this is allowed under the three-sources rule:** it is simulation, used for algorithm claims, and it never mixes with the public sets.
- **Before it is used for the claims** (C1, C3, C5): fix or extend it for the gaps above (a second version with high-value items, open disputes and varied review text), and record the new seed.

## 6. Transformations

None yet. Planned: map to the project's outcome records and value bands; derive trust edges; build a time-ordered train and test split. Record every step, script and seed here.

| Step | What was done | Script and version | Input | Output | Seed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | |

## 7. Results and notes

- All counts above were measured from the files on 2026-10-12.

## 8. Decision

- **Verdict:** use with changes: a second generator version with a fixed reference date, account dates that precede first transactions, high-value items, open disputes and varied review text (gaps 1, 2, 3 and 9), and an explicit mapping to the project's records.
- **Reviewed by:** Fatima Khursheed, Areeba Javed, Minahil Kashif
