# Dataset card: epinions

| Field | Value |
| :--- | :--- |
| Short name | `epinions` |
| Full name | Epinions trust network and review ratings |
| Source type | public trust network |
| Status | obtained; **`rating.txt` is incomplete** (see section 3a) |
| Added by | team (files placed in `raw/Datasets/epinions/`); card written 2026-10-12 |
| Last updated | 2026-10-12 |

## 1. Where it comes from

| Field | Value |
| :--- | :--- |
| Original publisher or authors | Epinions.com (a consumer review site). The copy we hold is the Kaggle version prepared by the TrustRec authors (Hamedani, Ali, Hong and Kim), per the Kaggle description pasted by the team on 2026-10-12 |
| Download link (exact page) | Kaggle dataset page (exact URL not recorded; add it). The Deep Dive's trustlet.org source is a different release (see 3a) |
| Date downloaded | unknown (files placed in the folder on 2026-10-12) |
| Version or release | unknown |
| Citation | The Kaggle page asks users to cite: Masoud Reyhani Hamedani, Irfan Ali, Jiwon Hong and Sang-Wook Kim, "TrustRec: An Effective Approach to Exploit Implicit Trust and Distrust Relationships along with Explicit ones for Accurate Recommendations", Computer Science and Information Systems, Vol. 18, No. 1, Jan. 2020 (as given on the page; check the volume, issue and year against the publisher before using it in a report) |
| File(s) in `raw/Datasets/epinions/` | `user_rating.txt`, `mc.txt`, `rating.txt`, `NOTE.txt` |
| Checksum (first 16 hex of SHA-256) | `user_rating.txt` 8bc1b3e9469a5b7c · `mc.txt` 06d13b3e71256a7a · `rating.txt` 1ffcfce3eb7660bc · `NOTE.txt` 537781e67d4a795c |

## 2. Licence and permitted use

| Field | Value |
| :--- | :--- |
| Licence or terms of use | Kaggle licence field says "Other (specified in description)". The description (pasted by the team) specifies only a request to cite the paper above; it states no redistribution terms |
| Where I read it | Kaggle "About Dataset" text pasted by the team on 2026-10-12. The licence field itself and any terms behind it were not seen by me |
| May we redistribute it in the repository? | **No permission shown, so treat as no.** Do not commit it; it is also about 783 MB. `raw/` is gitignored. Statistics we measure from it (degree distribution, rating spread) can go in the docs; rows cannot |
| Attribution required? | Yes, cite the paper above (a request on the page) |
| Restrictions | None stated beyond citing. The page describes it as publicly available and meant for evaluating recommender systems |
| Personal data in it? | Numeric user IDs only, no names. Do not attempt re-identification |
| Checked with supervisor? | no |

## 3. What is in it

| Field | Value |
| :--- | :--- |
| Format | Plain text. `user_rating.txt` and `rating.txt` are **tab** separated, `mc.txt` is **pipe** (`|`) separated. No header rows |
| Size (measured) | `user_rating.txt`: 841,372 rows. `mc.txt`: 1,560,144 rows. `rating.txt`: 13,668,320 lines (last one cut off) |
| Time span | Trust statements dated 2001/01/10 to 2003/08/12 (day resolution, `YYYY/MM/DD`) |
| What one row represents | `user_rating.txt`: one user's trust (+1) or distrust (-1) statement about another user. `mc.txt`: one article and its author and subject. `rating.txt`: one member's 1 to 5 helpfulness rating of one article |

### Fields (from `NOTE.txt`, checked against the files)

| File | Fields in order | Meaning |
| :--- | :--- | :--- |
| `user_rating.txt` | `MY_ID`, `OTHER_ID`, `VALUE`, `CREATION` | Who trusts whom. VALUE is +1 (trust) or -1 (distrust). Measured: 717,667 trust and 123,705 distrust edges; 131,828 distinct users |
| `mc.txt` | `CONTENT_ID`, `AUTHOR_ID`, `SUBJECT_ID` | Article, who wrote it, what it is about |
| `rating.txt` | `OBJECT_ID`, `MEMBER_ID`, `RATING`, `STATUS`, `CREATION`, `LAST_MODIFIED`, `TYPE`, `VERTICAL_ID` | Helpfulness rating 1 to 5 (the note says a few 6s should be treated as 5). `LAST_MODIFIED` is empty in some rows |

### Graph structure

| Question | Answer |
| :--- | :--- |
| Nodes are | Epinions members |
| Edges are | Directed, signed (+1 or -1), no weights beyond the sign |
| Edge meaning | A member's explicit trust or distrust of another member's reviewing |
| Timestamps on edges? | Day-level date only |

## 3a. Known quality problems

1. **`rating.txt` looks like an incomplete download.** It is exactly 716,800,000 bytes (a round number), and its last line is cut off: the final field is empty and there is no trailing newline. Every complete row has eight fields. The team's README says "~3M+" ratings; the file has 13.7M lines, so that figure is wrong as well. I could not check the original file size, so how much is missing is unknown. Fix: download it again, compare the size and checksum, and update this card. **Update 2026-10-12 (late):** the team re-downloaded the files; the new `rating.txt` has the same size (716,800,000 bytes) and the same checksum, with the same cut-off last line. So the source copy itself is cut off (or the same copy was fetched again). Still unresolved; the team is looking for the full version. **Measured 2026-10-13:** the rows cover creation years 2001 (12,779,772 rows) and 2002 (888,547 rows) only, while the trust statements in `user_rating.txt` run to 2003-08-12. Rating shares in the part we hold: 5 stars 77%, 4 stars 15%, 3 stars 6%, 2 stars 2.3%, 1 star 0.02% (the note says 6s count as 5). These shares are used only as a shape in `derived/public_graph_stats.json`.
2. **The Deep Dive describes a different release.** Its loader reads `ratings_data.txt` and `trust_data.txt`, space separated, and quotes "840K ratings, 131K users, 5.9K trust relationships" (trustlet.org). The files here are different. Code written from the Deep Dive will not load them. The team's README loader is closer (tab separated) but does not mention that `mc.txt` is pipe separated.
3. **Old data.** 2001 to 2003. Fine for graph structure, but not a stand-in for recency behaviour in 2026.
4. **Distrust edges are 15% of all edges** (123,705 of 841,372). Decide whether the k-hop benchmark uses only trust edges, as the team's notes suggest, or handles distrust.
5. The graph is far larger than our target scale (131,828 users). The notes propose a 300-user subset (users with at least 20 ratings); how the subset is drawn and which seed is used must be recorded when it is built.

## 4. How it maps to what we need

Compare with `../REQUIREMENTS.md`.

| We need | Supplied? | How, or what is missing |
| :--- | :--- | :--- |
| P-01 Directed graph of who trusts whom | Yes | `user_rating.txt`, signed, complete as far as checked |
| P-02 Held-back ground truth | Partly | Hold out a share of trust edges (time-ordered) and test whether propagation predicts them. Needs a defined protocol |
| P-03 Timestamps on edges | Yes (day level) | `CREATION` |
| P-04 Review text with spam labels | No | Ratings only, no text and no spam labels. YelpChi would be needed for that |
| D-06 Reviews and ratings for the manipulation checks | No | Not a source of reciprocal-rating or text-similarity ground truth |

## 5. How we use it

- **Intended use:** external benchmark for bounded k-hop propagation (accuracy, coverage and latency at k = 1 to 4), and comparison of the trust baseline. The Overview names Epinions as the secondary dataset for comparative evaluation.
- **Not to be used for:** claims about neighbourhood borrowing, tuning the engine parameters, or the simulated-data results.
- **Why this is allowed under the "three sources are never mixed" rule:** it stays a separate public-trust-network source, reported separately from simulation results.

## 6. Transformations

None yet. Planned (from the team's notes, to be confirmed): drop to positive edges or keep signs; select a subset of about 300 users with enough ratings; time-ordered 80/20 split. When built, record the script, seed and output here.

| Step | What was done | Script and version | Input | Output | Seed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | |

## 7. Results and notes

- Counts above were measured by reading the files on 2026-10-12.

## 8. Decision

- **Verdict:** use with changes. The trust file is usable now. Re-download `rating.txt` before using any rating statistics.
- **Reviewed by:** Fatima Khursheed, Areeba Javed, Minahil Kashif
