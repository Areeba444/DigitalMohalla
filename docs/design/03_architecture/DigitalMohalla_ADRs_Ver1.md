# Digital Mohalla: Architecture Decision Records (ADR-0001 to ADR-0008)

| Field | Value |
| :--- | :--- |
| Document | Architecture Decision Records, design step A1 |
| Version | 1.2 |
| Date | 2026-10-11 (v1.0: 2026-10-10; v1.1 and v1.2: 2026-10-11) |
| Authors | Team Digital Mohalla (drafted with Claude; reviewed by: ______) |
| Status | ADR-0001 to ADR-0005 Accepted on 2026-10-11 after team discussion; ADR-0006 Accepted as experimental on 2026-10-13 (see `00_management/Team_Decisions_2026-10-13.md`, D10); ADR-0007 and ADR-0008 Accepted for integration on 2026-10-11 by Student 1 as integration lead, awaiting the initials of Students 2 and 3 (see `00_management/Integration_Decisions_2026-10-11.md`). Members initial the sign-off table. |
| Applies to | `01_requirements/DigitalMohalla_Use_Cases_Ver1.md` v1.3, `01_requirements/DigitalMohalla_FR_NFR_Ver1.md` v1.3 |

An ADR records one design decision, the reason for it and what it changes. Later ADRs may supersede earlier ones, but none is edited after acceptance.

---

## ADR-0001: Soft hold on requested dates

**Status:** Accepted, 2026-10-11 (proposed 2026-10-10)

**Context.** UC-B5 said a new request "holds the dates". UC-B6 step 5, however, declines other pending requests for the same dates when the lender accepts one, and such requests cannot exist if the first request blocks the dates. FR-B-05 only requires that Accepted and Active bookings never overlap.

**Decision.** A pending request marks its dates as *requested* but blocks nothing. Several pending requests may overlap. Dates are blocked only when a lender accepts a request (ADR-0002). At that moment every other pending request that overlaps is DECLINED with the reason "dates taken".

**Consequences.**
- Lenders can choose between competing requests, and borrowers are not locked out by an unanswered request.
- The race moves from request creation to acceptance, where ADR-0002 handles it.
- Changed: UC-B5 step 3, post-conditions and extension 3c; UC-B6 step 5; FR-B-06; FR-B-05 and its acceptance criterion.
- Tests: two overlapping pending requests are both created; accepting one declines the other.

---

## ADR-0002: Overlap constraint enforced by the database at acceptance

**Status:** Accepted, 2026-10-11, with the wording amendment below (proposed 2026-10-10)

**Context.** UC-B5 extension 3c resolved simultaneous requests by keeping "the one with the lower `stream_seq`". `stream_seq` numbers the events inside one transaction's stream, so two competing requests (two streams) both start at 1 and cannot be ordered by it. Checking availability in application code also fails under concurrency: two acceptances can both read "dates free" before either writes.

**Decision.** Store each accepted booking's date range and enforce, in PostgreSQL, that no two **held** bookings for the same item have overlapping date ranges (an exclusion constraint on a date range). A booking is held from acceptance until the transaction reaches COMPLETED or NO_SHOW, so the dates stay blocked through ACTIVE, RETURN_INITIATED, RETURNED and DISPUTED, while the item is not yet back. *(Amended 2026-10-11: v1.0 said "with status ACCEPTED or ACTIVE", which would have released the dates during a return or a dispute.)* The state transition, the booking write and the `request_accepted` event are committed in one database transaction. If the constraint refuses the write, nothing is committed, the lender is told the dates are taken, and that request ends DECLINED with reason "dates taken". The unique key on (`stream_id`, `stream_seq`) additionally stops two writers appending to the same stream at once.

**Consequences.**
- Double booking becomes impossible regardless of timing, which is what NFR-R-01 measures.
- The check depends on PostgreSQL; if the database changes, an equivalent constraint or a serialised check is needed.
- Changed: UC-B5 extension 3c (removed; the case now lives in UC-B6 extension 3c), UC-B6 step 4, FR-B-05, FR-B-10, NFR-R-01, FR-B-05 acceptance criterion. The ERD (step A6) shows the bookings table with the constraint.
- Tests: test suite 3 (double booking) runs N parallel acceptances for overlapping dates and expects exactly one commit, every run.

---

## ADR-0003: Exits from HELD_FOR_REVIEW depend on the hold reason

**Status:** Accepted, 2026-10-11 (proposed 2026-10-10)

**Context.** A request can enter HELD_FOR_REVIEW at two different points: before assessment (locality inconclusive or conflicting) or after it (manipulation risk ≥ 60, high value with low confidence), plus on engine failure, where no assessment exists. UC-I4 lists the moderator outcomes (cleared, safeguards imposed, restricted) but not the state each one leads to. "Cleared" cannot go straight to ASSESSED when there is no assessment yet.

**Decision.** Every `held_for_review` event records a hold reason: `locality_inconclusive`, `locality_conflict`, `manipulation_risk`, `high_value_low_confidence` or `engine_failure`. The moderator's decision is recorded as `hold_cleared` (with any safeguards) or `request_declined` (restriction, by human decision only). The exits are:

| Hold reason | Cleared | Safeguards imposed | Restricted |
| :--- | :--- | :--- | :--- |
| `locality_inconclusive`, `locality_conflict` | `hold_cleared` → LOCALITY_CHECKED; the assessment then runs | Same, with the safeguards attached | `request_declined` → DECLINED |
| `manipulation_risk`, `high_value_low_confidence` | `hold_cleared` → ASSESSED; the existing assessment plus the moderator's note reach the lender | `hold_cleared` → ASSESSED with the added safeguards | `request_declined` → DECLINED |
| `engine_failure` | `hold_cleared` → LOCALITY_CHECKED; the assessment is re-run | Not available: no assessment exists to attach safeguards to | `request_declined` → DECLINED |

A request that is held again after clearance (for example, the re-run assessment finds manipulation risk) re-enters HELD_FOR_REVIEW with the new reason; it is not cleared automatically.

**Consequences.**
- The state machine (step A3) draws these as separate guarded transitions, and the transition table tests each one.
- No request reaches the lender without an assessment, which keeps FR-T-01 ("exactly one assurance state") and FR-T-07 ("no default state") true.
- New event type: `hold_cleared`.
- Open point, decided in the A5 decision table: when a high-value request with weak evidence is *held* for a moderator versus sent to the lender as REVIEW_RECOMMENDED with safeguards (UC-B5 extension 5c, ES-06).
- Event-specific data such as the hold reason, the decision or the dates is stored in `payload` (ADR-0005, closes N-6).
- Changed: Use Cases §2, UC-I4 post-conditions, FR-B-08, FR-T-11.

---

## ADR-0004: Distinct event types for closing or withdrawing a dispute

**Status:** Accepted, 2026-10-11 (proposed 2026-10-10). Supersedes the optional "RESUME" dispute resolution accepted at the Step-0 meeting: a moderator's decision always closes the dispute through `dispute_resolved` → COMPLETED.

**Context.** Both a clean completion and a moderator-closed dispute entered COMPLETED through `transaction_closed`, so a replay of the event log could not tell them apart without reading the evidence. FR-B-17 also lets the raising party withdraw a dispute and restore the previous state, but no event type existed for that.

**Decision.** Add two event types:
- `dispute_resolved`: DISPUTED → COMPLETED, actor is the moderator, evidence includes the decision and reason. The resolved outcome is then sent to the assurance engine as evidence.
- `dispute_withdrawn`: DISPUTED → the state stored in the `dispute_opened` event's `previous_state`, actor is the raising party.

`transaction_closed` is used only for a normal completion (RETURNED → COMPLETED).

**Consequences.**
- Replay, the audit log (UC-I6) and the evaluation harness can count moderator closures directly.
- Event types are part of the frozen schema, so this needs sign-off from all three students.
- Changed: Use Cases §2, UC-B12 extension 5b, UC-I4 post-conditions, FR-B-08, FR-B-17, FR-T-11 and its acceptance criterion.

---

## ADR-0005: Event-specific data in a `payload` field

**Status:** Accepted, 2026-10-11 (closes FR/NFR issue N-6)

**Context.** The frozen event record (`event_id, stream_id, stream_seq, event_type, schema_version, actor_id, occurred_at, previous_state, new_state, evidence_refs, authorisation`, and `config_version` on assessment events) has no place for data that only some event types carry: the requested dates, the hold reason (ADR-0003), the moderator's decision, the dispute reason, the on-time or late outcome. The transition guards and replay need these values, and missing fields cannot be reconstructed later (Overview §11). The Step-0 meeting of 9–10 October had accepted a `payload` field in the state-machine design v1.1; the v1.1 requirements left the question open as N-6.

**Decision.**
- Add one field to the frozen record: `payload`, a JSON object. Its contents are defined per `event_type` in the event catalogue (`07_state_machines/State_Machine_Design.md` §5); validation checks the keys each event type needs.
- `evidence_refs` stays a set of references only (assessment, decision, condition reports, attachments).
- Two storage-level columns, `prev_hash` and `row_hash`, hold a per-stream hash chain for tamper evidence (FR-M-05, NFR-S-05). They are not event content and are not part of the published event schema.
- The four internal event types `reminder_sent`, `extension_requested`, `extension_approved` and `extension_declined` are added to the event-type list now (Use Cases §2 already describes them as events inside ACTIVE), and are built in iteration 2.

**Consequences.**
- Every event can be validated and replayed without joining other tables; `schema_version` covers later changes to a payload's contents.
- A payload is not type-checked by the database column itself; guards check the keys they depend on, and the event catalogue is the contract.
- Changed: Use Cases §2 event record, FR-B-09, N-6 (resolved), `schema.sql` (`lifecycle_event.payload`, hash columns), ER diagram, class diagram.

---

## ADR-0006: Trust-edge weight is the recency-weighted Beta posterior mean

**Status:** Accepted as experimental, 2026-10-13 (team decision D10). Proposed 2026-10-11 by Student 1. The rule is used in iteration 1 and its effect is evaluated in iteration 4; it may change then.

**Context.** FR-T-04 and Overview §5.5 define bounded k-hop indirect evidence over a graph whose edges carry "verified evidence strength for the same role and metric", derived from the source user's evidence, but not how outcomes become an edge weight. Test suite 7 and the ES-13 demo need a fixed rule.

**Decision.** `weight(A→B, role, metric) = (α0 + s_w) / (α0 + β0 + s_w + f_w)`, where s_w and f_w are the recency-weighted successes and failures among the VALID outcomes A has confirmed about B in that role and metric, using the same estimator and config (α0 = β0 = 1, 180-day half-life) as direct evidence. An edge exists only when at least one such outcome exists, and is recomputed when outcomes arrive or are flagged.

**Alternatives considered.** (a) Lower bound of the 90% credible interval: robust to thin evidence but weights so low that indirect evidence would rarely change a decision. (b) Posterior mean × min(1, n_eff / 3): damps thin edges but adds a parameter to validate. Thin edges are already limited by path decay, the diversity factors and the 0.6 cap.

**Consequences.** One formula and parameter set for direct and indirect evidence; easy to explain in the ES-13 explanation; a single success gives weight 0.67 (accepted, bounded by the cap). Changed: `11_assurance_engine/KHop_Indirect_Trust_Design.md`, the worked example (weights now derived from outcome counts), class diagram (TrustEdge).

---

## ADR-0007: A manipulation hold needs corroborated evidence; S4 is active in iteration 1

**Status:** Accepted for integration, 2026-10-11 (decision D10 in `00_management/Integration_Decisions_2026-10-11.md`). Student 2 and Student 3 to initial.

**Context.** FR-T-06, UC-B5 extension 5b, UC-D3/4/5 extension 4a, transition T06 and the database check `assessment_risk_hold_ck` said that a manipulation risk of 60 or more *always* holds the request. Student 2's Algorithm 3 adds a false-positive guard: level 4 needs at least two signals with a normalised value of 0.5 or more, and an uncorroborated score is capped at level 3 (request verification). That guard is what keeps a dense family or friend group, which naturally produces reciprocal ratings, out of moderator review (test suite 12, Overview §5.6). The two rules contradict each other. In addition, iteration 1 activated only S1 (reciprocal clustering) and the retaliation check, so with the guard no request could ever reach level 4. ES-04 (colluding group → HELD_FOR_REVIEW) could not pass. The ES-04 fixture had quietly used S4 as well, and its score was miscalculated (86.8 instead of 96.8).

**Decision.**
- Manipulation **level 4** is a score of 60 or more **and** corroboration by at least two signals with value ≥ 0.5. Only level 4 holds the request (rule R2, HELD_FOR_REVIEW with hold reason `manipulation_risk`, case opened). A score of 60 or more from a single signal is level 3: the request reaches the lender as REVIEW_RECOMMENDED with a verification safeguard (rule R5). Nothing is restricted automatically in either case.
- Iteration 1 activates **S1 reciprocal-rating clustering, S4 review-text similarity** (character n-gram TF-IDF cosine, which also works for Roman Urdu) and the retaliation check. S2, S3 and S5 stay in iteration 2. Weights are renormalised over the available signals, as Algorithm 3 already specifies.
- The assessment row stores `manipulation_level`, `manipulation_corroborated` and `rule_fired`. The database checks that the level follows the bands and the corroboration rule, and that level 4 is held unless an open dispute takes precedence (rule R1, decision D12).

**Alternatives considered.** (a) Keep "score ≥ 60 always holds" and drop the guard: ES-04 passes with S1 alone, but a family group with S1 ≈ 0.83 scores about 83 under renormalisation and would be held, failing test suite 12. (b) Keep the guard and the plan's two checks: ES-04 cannot be held in iteration 1, and the Mid-1 gate falls to 6 of 7 scenarios.

**Consequences.** ES-04 scores 96.8 (S1 = 1.0, S4 = 0.92), is corroborated and held; a family group (S1 = 0.83, S4 = 0.10) scores 53.8, level 3, and is not held (fixture PU-02); a single strong signal (score 68) is level 3 (PU-01). Student 2's iteration-1 work grows by one signal, S4. Changed: FR-T-05/FR-T-06 and their acceptance criteria, Use Cases §2, UC-B5 5b, UC-D3/4/5 4a, T06, `schema.sql` v2.3, the engine config 1.1.0, the Algorithm doc §5, the fixtures v1.1, and test suites 9, 11 and 12. The plan's scope row now lists three manipulation checks.

---

## ADR-0008: Community paths lift sparse direct evidence from INSUFFICIENT to REVIEW_RECOMMENDED

**Status:** Accepted for integration, 2026-10-11 (decision D11). Student 2 to initial; closes Q6 of `11_assurance_engine/Edge_Weight_Rule_Student2_Confirmation.md`.

**Context.** In Student 2's decision table, ρ (indirect reliability) appeared only in rule R3: "no verified direct history **and** ρ < 0.3 → INSUFFICIENT_EVIDENCE". Under ADR-0006, an edge into the borrower exists only if someone has confirmed an outcome about the borrower. So a borrower who is reachable by any path always has direct history, R3 can never see ρ ≥ 0.3, and indirect evidence never changes a decision. That is the plan's named risk, "k-hop changes nothing". The ES-13 fixture (no direct history, yet two paths, prior_backed false, estimate 0.651) was impossible for the same reason. UC-D3/4/5 extension 1a also lists ES-12 (sparse or old history) under INSUFFICIENT_EVIDENCE, which no rule produced.

**Decision.** Add rule **R6_SPARSE** to the decision table after R6_DISPUTE: *sparse direct evidence (n_eff < n_min = 3) **and** ρ < ρ_sup (0.3) → REQUEST_VERIFICATION, INSUFFICIENT_EVIDENCE*. With ρ ≥ 0.3 the rule does not fire, so the request falls through to R9 (REVIEW_RECOMMENDED with safeguards). Rule R3 (no verified history at all) is unchanged, so FR-T-02 still holds for every newcomer, whatever the item value. Placing the rule after R4 to R6_DISPUTE keeps the high-value hold (ES-06), moderate manipulation (R5) and a recent dispute (ES-03) ahead of it. Indirect evidence alone still never gives SUFFICIENT_EVIDENCE (R7 and R8 need n_eff ≥ 3 from direct evidence).

**Consequences.**
- ES-13 is now possible and shows the effect. Borrower v has two confirmed loans, from a and from b (n_eff 1.77, mean 0.735, 90% CI [0.339, 0.982]), and none with lender u. ADR-0006 edge weights are u→a 0.801, u→b 0.777, a→v 0.658 and b→v 0.648. The two paths have q = 0.369 and 0.352, giving I = 0.591 and ρ = 0.394. The rule fired is R9 and the state REVIEW_RECOMMENDED. **Without the paths**, the same request gives R6_SPARSE and INSUFFICIENT_EVIDENCE. The explanation lists both paths (plan demo step 2.2).
- Borrowers with sparse history and no community support get INSUFFICIENT_EVIDENCE instead of REVIEW_RECOMMENDED (fixture PU-05, the ES-12 pattern). Both states reach the lender; neither is negative.
- Changed: Algorithm doc §6, the decision-policy activity diagram, `assessment.rule_fired` and its check, FR-T-04 and FR-T-06, UC-D3/4/5 extension 1a, the fixtures v1.1 (ES-13 rebuilt from outcomes, with a counterfactual) and `11_assurance_engine/KHop_Indirect_Trust_Design.md` §4.

---

## Sign-off

Agreed in team discussion on 2026-10-11 (recorded by Student 1). Each member should add their initials.

| ADR | Student 1 | Student 2 | Student 3 | Date accepted |
| :--- | :--- | :--- | :--- | :--- |
| ADR-0001 | agreed | agreed | agreed | 2026-10-11 |
| ADR-0002 (amended wording) | agreed | agreed | agreed | 2026-10-11 |
| ADR-0003 | agreed | agreed | agreed | 2026-10-11 |
| ADR-0004 | agreed | agreed | agreed | 2026-10-11 |
| ADR-0005 | agreed | agreed | agreed | 2026-10-11 |
| ADR-0006 (experimental) | agreed | agreed | agreed | 2026-10-13 |
| ADR-0007 | accepted (integration lead) | pending | pending | 2026-10-11 (for integration) |
| ADR-0008 | accepted (integration lead) | pending | pending | 2026-10-11 (for integration) |
