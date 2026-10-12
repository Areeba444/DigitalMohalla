# Trust-edge weight rule: confirmation with Student 2

| Field | Value |
|---|---|
| From | Student 1 (indirect trust) |
| To | Student 2 (estimation, policy, detection) |
| Version | 1.1, 11 October 2026 (integration notes added; signatures still open) |
| Date | 11 October 2026 |
| Decision record | ADR-0006 in `03_architecture/DigitalMohalla_ADRs_Ver1.md` (status: Proposed until this page is signed) |
| Due | Before the A5 deadline (D-17); it feeds test suite 7 and Slice B |

## Proposal (one paragraph)

An edge A→B for role r and metric m is weighted by the **recency-weighted Beta posterior mean** of the outcomes A has confirmed about B: `(1 + s_w) / (2 + s_w + f_w)`. Here s_w and f_w are the recency-weighted successes and failures, using your estimator with the same config (prior Beta(1, 1), 180-day half-life). One success gives 0.67, five give 0.86, one failure gives 0.33. The k-hop search then applies decay (0.7 per extra hop), noisy-OR, path diversity and the 0.6 cap. Worked example: `khop_worked_example.drawio`.

## Questions (Student 1's proposed answer in brackets)

1. **Shared estimator.** Can the edge weight call your posterior function with the same config values, so there is one implementation? *(Yes: one function in Module 5, e.g. `beta_posterior(successes_w, failures_w, config)`, used by both.)*
2. **Which outcomes count.** All VALID outcomes where A is the observer and B the subject in role r and metric m, from `transaction_closed` or `dispute_resolved`; flagged outcomes excluded. Do you apply similarity weighting (category, value band, duration) to direct evidence, and should edges use it too? *(Edges: no similarity weighting, since they describe a relationship and path decay already discounts them; similarity stays in your direct estimate.)*
3. **Manipulation.** If your reciprocal-clustering check flags a group of accounts, should edges between them be dropped from k-hop paths, so manipulation cannot spread through the graph (Overview §5.5)? *(Yes: exclude an edge when both ends are in the same flagged cluster; show the exclusion in the explanation.)*
4. **t_v and b.** I need the borrower's direct posterior mean (t_v) and the role/metric population baseline (b) as inputs. How will you compute b? *(Your call; for example the mean outcome rate over all users with at least one outcome in that role and metric, from the same config version.)*
5. **Refresh.** Edges are recomputed when outcomes arrive; a scheduled refresh for recency drift comes with the scheduler in iteration 2. Acceptable for iteration 1? *(Yes: drift is under 2% in 5 days.)*
6. **Decision table.** Which row of your A5 decision table uses ρ, and what must the ES-13 explanation show? *(For example, indirect evidence with ρ ≥ some threshold moves INSUFFICIENT_EVIDENCE to REVIEW_RECOMMENDED but never to SUFFICIENT_EVIDENCE, and the explanation lists the paths.)*

## How to confirm (about 15 minutes)

1. Send this page and `khop_worked_example.drawio` to Student 2.
2. Go through questions 1–6 together; write the agreed answer under each, or "changed: …".
3. If anything changes the formula, Student 1 updates `generate_khop_example.py` and regenerates the example (`python 11_assurance_engine/generate_khop_example.py`) so the example and the test fixture match.
4. Both sign below; then change ADR-0006's status to Accepted and record it in the next team-decisions note.

## Integration notes (11 October 2026; not a signature)

Student 2's own artefacts already answer two questions; please confirm them when signing.

- **Q4.** The engine config sets `indirect_trust_alg2.baseline.default_population_baseline = 0.5`, and the Algorithm doc §4 uses t_v = the borrower's direct mean, or b when there is none (prior-backed).
- **Q6.** Answered by ADR-0008 (decision D11): rule R6_SPARSE (n_eff < 3 and ρ < 0.3 → INSUFFICIENT_EVIDENCE); with ρ ≥ 0.3 the request is REVIEW_RECOMMENDED (R9), never SUFFICIENT_EVIDENCE. The ES-13 explanation lists the selected paths with their weights, I, ρ and t_indirect.
- **Q1.** The Algorithm doc §2 defines `TrustEdge.weight` as "derived from source's verified direct evidence", which is consistent with ADR-0006. It does not yet name the formula.

## Agreed answers

| Q | Agreed answer |
|---|---|
| 1 | |
| 2 | |
| 3 | |
| 4 | |
| 5 | |
| 6 | |

| Student 1 | Student 2 | Date |
|---|---|---|
| | | |
