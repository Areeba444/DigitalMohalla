# Dataset card: bitcoin-otc-alpha

Two related datasets with the same format (Bitcoin OTC and Bitcoin Alpha), described together.

| Field | Value |
| :--- | :--- |
| Short name | `bitcoin-otc`, `bitcoin-alpha` |
| Full name | Bitcoin OTC and Bitcoin Alpha web-of-trust (signed, weighted) networks |
| Source type | public trust network |
| Status | obtained |
| Added by | team (files in `raw/Datasets/bitcoin-otc/`); card written 2026-10-12 |
| Last updated | 2026-10-12 |

## 1. Where it comes from

| Field | Value |
| :--- | :--- |
| Original publisher or authors | Stanford SNAP (per the team's README). Authors of the data papers: S. Kumar, F. Spezzano, V.S. Subrahmanian, C. Faloutsos (ICDM 2016) and S. Kumar, B. Hooi, D. Makhija, M. Kumar, C. Faloutsos, V.S. Subrahmanian (WSDM 2018), per the Bitcoin OTC page text pasted by the team on 2026-10-12 |
| Download link (exact page) | SNAP page "Bitcoin OTC trust weighted signed network" (text pasted by the team; URL not recorded, add it). The Bitcoin Alpha page was not pasted; it is linked from the OTC page as a similar network |
| Date downloaded | unknown |
| Version or release | unknown |
| Citation | The OTC page asks users to cite two papers: (1) S. Kumar, F. Spezzano, V.S. Subrahmanian, C. Faloutsos, "Edge Weight Prediction in Weighted Signed Networks", IEEE ICDM 2016, pp. 221-230; (2) S. Kumar, B. Hooi, D. Makhija, M. Kumar, C. Faloutsos, V.S. Subrahmanian, "REV2: Fraudulent User Prediction in Rating Platforms", ACM WSDM 2018, pp. 333-341. Whether the Alpha page asks for the same two is not confirmed; assume so until checked |
| File(s) in `raw/Datasets/bitcoin-otc/` | `soc-sign-bitcoinotc.csv` (+ `.csv.gz`), `soc-sign-bitcoinalpha.csv` (+ `.csv.gz`) |
| Checksum (first 16 hex of SHA-256) | otc csv 76bd9d8f1d3ff9a1 · otc gz 6424ac981dad3a01 · alpha csv 1b2a970f327d0ceb · alpha gz 3a178611b9c2f39c |

## 2. Licence and permitted use

| Field | Value |
| :--- | :--- |
| Licence or terms of use | None stated in the page text the team pasted (it gives a citation request only) |
| Where I read it | SNAP Bitcoin OTC page text pasted by the team on 2026-10-12. Not seen: the SNAP site's general terms, and the Alpha page |
| May we redistribute it in the repository? | **No permission shown, so treat as no** until the SNAP terms are checked. The files are small (1.0 MB and 0.5 MB). `raw/` is gitignored. Statistics measured from them can go in the docs |
| Attribution required? | Yes, cite the two papers above |
| Restrictions | None stated. Use is academic evaluation |
| Personal data in it? | Numeric user IDs only. Do not attempt re-identification |
| Checked with supervisor? | no |

## 3. What is in it

| Field | Value |
| :--- | :--- |
| Format | CSV, no header: `SOURCE, TARGET, RATING, TIME` |
| Size (measured) | OTC: 35,592 edges, 5,881 users. Alpha: 24,186 edges, 3,783 users |
| Time span | Both from 2010-11-08. OTC to 2016-01-25, Alpha to 2016-01-22 (Unix timestamps, converted by me) |
| What one row represents | One user's rating of another user, from -10 (total distrust) to +10 (total trust) |

### Fields

| Field | Meaning | Type | Missing? |
| :--- | :--- | :--- | :--- |
| `SOURCE` | Rater | integer ID | no |
| `TARGET` | User being rated | integer ID | no |
| `RATING` | -10 to +10 (measured range: -10 to 10) | integer | no |
| `TIME` | Unix epoch seconds | number | no |

### Graph structure

| Question | Answer |
| :--- | :--- |
| Nodes are | Platform members |
| Edges are | Directed, signed, weighted |
| Negative edges (measured) | OTC: 3,563 of 35,592 (10%). Alpha: 1,536 of 24,186 (6%) |
| Timestamps on edges? | Yes, to the second |

## 3a. Known quality problems

- Not yet checked for duplicate edges (the same pair rated more than once), self-loops, or how heavily ratings concentrate on few users. Check before building a benchmark. I did not check these.
- The domain is anonymous cryptocurrency trading, so the ratings reflect payment reliability, not borrowing behaviour.
- The team's README suggests rescaling -10..+10 to 1..5 for comparison with Epinions. A rescaling changes what "trust" means; record the exact formula whenever it is used.

## 4. How it maps to what we need

| We need | Supplied? | How, or what is missing |
| :--- | :--- | :--- |
| P-01 Directed graph of who trusts whom | Yes | Positive ratings as trust edges; weights available |
| P-02 Held-back ground truth | Partly | Time-ordered hold-out of later edges; needs a protocol |
| P-03 Timestamps on edges | Yes | `TIME` |
| P-04 Review text with spam labels | No | No text. Negative edges can serve as distrust signals only |
| Proposal's benchmark choice | Yes | Proposal §11.4 (via the context doc) names Bitcoin OTC |

## 5. How we use it

- **Intended use:** a larger graph for k-hop validation and latency, and distrust signals for robustness. Also an option for the benchmark choice (Epinions or Bitcoin OTC, open for iteration 2); having both may remove the need to choose.
- **Not to be used for:** claims about neighbourhood borrowing, or tuning the engine.
- **Why this is allowed:** separate public-trust-network source, reported separately.

## 6. Transformations

None yet.

| Step | What was done | Script and version | Input | Output | Seed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | |

## 7. Results and notes

- Counts, rating range and dates were measured by reading the files on 2026-10-12.
- Checked against the SNAP page text: edges (35,592) match. The page says 89% of OTC edges are positive; the file gives 32,029 of 35,592 = 89.99% (no zero ratings), so the page figure is rounded down. Alpha: 22,650 of 24,186 = 93.65% positive (no page figure seen).

## 8. Decision

- **Verdict:** use (after the licence is checked).
- **Reviewed by:** ______
