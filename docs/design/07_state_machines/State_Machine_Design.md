# Digital Mohalla: State Machines and Transition Table (design step A3)

| Field | Value |
|---|---|
| Document | Design step A3 (borrowing lifecycle and escalation case) with the event catalogue of step A4 |
| Owner | Student 1 (lifecycle, indirect trust, locality) |
| Version | 2.2, 11 October 2026: integration decisions applied (`00_management/Integration_Decisions_2026-10-11.md`): guards of T05 to T07 name the A5 rules (T06 = corroborated level 4, ADR-0007), T01 checks held bookings (D6). v2.1: team decisions D1–D9. v2.0 replaced v1.1 of 10 October (kept in `archive_v1/`). |
| Status | Event types and `payload` agreed (ADR-0005). Awaiting second-member review (A14). |
| Baseline | `01_requirements/DigitalMohalla_Use_Cases_Ver1.md` v1.3 §2, `01_requirements/DigitalMohalla_FR_NFR_Ver1.md` v1.3, `03_architecture/DigitalMohalla_ADRs_Ver1.md` (ADR-0001 to ADR-0005 accepted; ADR-0007 for T06), Iteration 1 plan step A3 |
| Author note | Drafted with Claude (GenAI); to be disclosed on Form 13 and in the AI usage log. |

## Files

| File | What it is |
|---|---|
| `borrowing_lifecycle_state_machine.drawio` | UML state machine of `BorrowingTransaction`: 14 states, T01 to T26 |
| `escalation_case_state_machine.drawio` | UML state machine of `EscalationCase`: C01 to C11 |
| `transition_table.md` | Transition table: state × event → next state, guard, action, actor, source, FRs |
| `transition_table.csv` | The same table at leaf level (34 rows): the invalid-transition test matrix (test suite 1) |
| `generate_state_machines.py` | Regenerates all four from `../_tools/lifecycle_model.py` |

The model file is the single source of truth. `schema.sql` seeds `allowed_transition` from it, and `06_data_model/test_schema.py` fails if the database rules, the CSV and the model differ.

## 1. Why this is drawn again (audit of v1.1)

v1.1 was drawn before the team agreed the single state list (Use Cases §2, recorded as "Agreed" in the Iteration 1 plan) and before ADR-0001 to ADR-0004. Its vocabulary conflicts with the baseline, so v2.0 replaces it.

| v1.1 (archived) | v2.0 (baseline) | Reason |
|---|---|---|
| REQUESTED, ASSESSING, MODERATOR_REVIEW, AWAITING_LENDER | REQUEST_CREATED, LOCALITY_CHECKED, HELD_FOR_REVIEW, ASSESSED | Use Cases §2 state list (FR-B-08) |
| AWAITING_HANDOVER, AWAITING_RECEIPT | ACCEPTED (both confirmations are data, not states) | Use Cases §2; UC-B7 |
| ON_LOAN, OVERDUE | ACTIVE (reminders and extensions are internal events) | Use Cases §2 "events inside ACTIVE" |
| RETURN_PENDING, no RETURNED | RETURN_INITIATED, RETURNED | Use Cases §2 |
| RESOLVED (separate closed state), RESUME resolution | COMPLETED via `dispute_resolved` | ADR-0004 |
| INELIGIBLE | removed: a non-member cannot create a request (G1 rejection, UC-B5 pre-condition) | UC-B5 |
| `requiresModerator` flag decides T04/T05 | hold reason recorded on `held_for_review`; exits by hold reason | ADR-0003 |
| 31 UPPER_CASE event types, fields `transaction_id`, `sequence_no`, `actor`, `evidence` | 17 lower-case event types (+4 internal, ADR-0005), fields `stream_id`, `stream_seq`, `actor_id`, `evidence_refs`, `schema_version`, `config_version` | Use Cases §2 frozen schema, FR-B-09 |
| Tentative hold, per-item lock | Soft hold; exclusion constraint at acceptance | ADR-0001, ADR-0002 |

What survives from v1.1: one aggregate per request (the request is the creation event of the transaction), lifecycle state kept separate from assurance state, validation order authorisation → state → guard, append-only events with replay, system-opened dispute on non-return.

## 2. Borrowing lifecycle: states

| State | Group | Meaning | Entered by |
|---|---|---|---|
| REQUEST_CREATED | PENDING | Request submitted; dates marked as requested (soft hold, blocks nothing) | `request_created` |
| LOCALITY_CHECKED | PENDING | Coarse locality verified, or a locality / engine-failure hold cleared | `locality_checked`, `hold_cleared` |
| HELD_FOR_REVIEW | PENDING | Waiting for a moderator; hold reason recorded; never an automatic rejection | `held_for_review` |
| ASSESSED | PENDING | Assurance state and evidence summary attached; lender decides | `assessment_generated`, `hold_cleared` |
| ACCEPTED | IN_PROGRESS | Lender accepted; booking HELD; handover pending | `request_accepted` |
| ACTIVE | IN_PROGRESS | Both parties confirmed handover | `handover_confirmed` |
| RETURN_INITIATED | IN_PROGRESS | Borrower started the return | `return_initiated` |
| RETURNED | IN_PROGRESS | Both parties confirmed the return condition | `return_confirmed` |
| COMPLETED | terminal | Closed normally or by moderator; outcome sent to the engine | `transaction_closed`, `dispute_resolved` |
| DECLINED | terminal | By lender, by moderator (restriction) or by system ("dates taken") | `request_declined` |
| CANCELLED | terminal | Borrower withdrew before acceptance | `request_cancelled` |
| EXPIRED | terminal | Lender did not answer in the response window | `request_expired` |
| NO_SHOW | terminal | Handover did not happen within the grace period | `no_show` |
| DISPUTED | side | Dispute open; deposit record and other transitions frozen | `dispute_opened` |

PENDING and IN_PROGRESS are composite states drawn only to group shared exits (T16, T17, T23). Events record leaf states, never composite names.

## 3. Transition table

See `transition_table.md` (26 transitions + 6 internal; 34 leaf rows in the CSV). The rules that are easiest to get wrong:

- **Locality before assessment (FR-B-07).** REQUEST_CREATED leaves only through the coarse locality result: verified → LOCALITY_CHECKED (T02); inconclusive or conflicting → HELD_FOR_REVIEW with the matching hold reason (T03, T04). The result is read from stored coarse evidence, never from coordinates.
- **Assessment as one engine call.** LOCALITY_CHECKED calls `assess(request)` once. The choice on its result appends either `assessment_generated` → ASSESSED (T05) or `held_for_review` with reason `manipulation_risk`, `high_value_low_confidence` or `engine_failure` (T06 to T08). Manipulation and high-value holds reference the stored assessment and its `config_version`; an engine-failure hold has no assessment and no assurance state (FR-T-07).
- **Exits from HELD_FOR_REVIEW (ADR-0003).** Locality and engine-failure holds clear to LOCALITY_CHECKED, so the assessment runs (again); manipulation and high-value holds clear to ASSESSED with the moderator's note and safeguards; any hold can end DECLINED by moderator restriction. Safeguards cannot be imposed on an engine-failure hold (UC-I4 3c). A cleared request that is held again opens a new case (UC-I4 4d).
- **Soft hold and overlap (ADR-0001, ADR-0002).** Pending requests block nothing. `request_accepted` inserts the booking in the same database transaction; the exclusion constraint refuses an overlapping acceptance and nothing is committed. Every other overlapping pending request is then declined by the system with reason `dates_taken` (T17).
- **Dual confirmation.** Each party's handover or return confirmation is a `condition_report` row. The lender's checklist comes first; the borrower's confirmation counts only if made after the lender's latest checklist, so the borrower always agrees to what was recorded. The transition event is appended when the pair is complete (T18, T21). Disagreement is not a transition: it becomes a dispute (T23).
- **Disputes (ADR-0004).** `dispute_opened` stores `previous_state`. `dispute_resolved` closes to COMPLETED and its decision becomes evidence; `dispute_withdrawn` (raising party only) restores exactly the stored previous state, drawn as the history pseudostate H of IN_PROGRESS. A dispute cannot be opened from RETURNED (decision D4), so H returns to ACCEPTED, ACTIVE or RETURN_INITIATED.

### 3.1 Invalid transitions and what the system does

Anything not in the table is invalid: 294 (state, event type) pairs exist and 34 rows are valid. Validation runs in the order authorisation → state → guard, both in the application (`TransitionValidator`, for clear messages) and in the database (`event_validate`, as the guarantee). A rejected command appends no event, returns 403 (not authorised) or 409 (invalid transition, stale `stream_seq`, failed guard, dates taken), and is written to `audit_log` with outcome REJECTED and its reason (FR-B-08, FR-M-05).

| Attempt | Why it is rejected | Requirement |
|---|---|---|
| COMPLETED → `request_accepted` | Terminal state | FR-B-08 acceptance criterion |
| Accept in LOCALITY_CHECKED or HELD_FOR_REVIEW | No request reaches the lender without an assessment | FR-B-07, ADR-0003 |
| `hold_cleared` of a locality hold → ASSESSED | Must return to LOCALITY_CHECKED so the assessment runs | FR-B-08 acceptance criterion |
| ACCEPTED → ACTIVE on the lender's word alone | Both parties must confirm; deposit (record-only) if required | FR-B-11, UC-B7 3b |
| Lender initiates the return | Role not allowed for T20 | NFR-S-02 |
| Moderator of another community, or a party, decides | Community scope; conflict of interest | NFR-S-03, FR-T-11 |
| Dispute in a PENDING state, or a second open dispute | B12 pre-condition; one case per transaction | UC-B12, UC-B12 1a |
| Withdraw by the other party, or to a different state | Only the raiser; only the stored previous state | ADR-0004, FR-B-17 |
| Command based on an old `stream_seq` | Optimistic concurrency | ADR-0002 |

## 4. Escalation case (A3)

| ID | From | Trigger [guard] / action | To | Source |
|---|---|---|---|---|
| C01 | initial | `case_opened` by a hold or dispute [no open case for the transaction] / assemble evidence trail; priority, reason; assign community moderator, or Admin if none | OPEN | D6 steps 1–2, 1b, 2a; FR-T-10 |
| C02 | OPEN | `info_requested` [assigned moderator] / notify parties, set deadline | AWAITING_INFORMATION | I4 step 2; D6 1a |
| C03 | AWAITING_INFORMATION | `info_received` [party] / attach | OPEN | I4 step 2 |
| C04 | AWAITING_INFORMATION | `deadline_passed` / note non-response | OPEN | I4 2a; B12 5a |
| C05 | OPEN (internal) | `escalated_to_admin` [unresolvable, or a moderator is involved] / assignee := Admin | OPEN | I4 3a, 3b |
| C06 | OPEN | `decision_recorded` [authorised, not a party, reason, allowed for the hold reason, case still undecided] / issue `dispute_resolved`, `hold_cleared` or `request_declined` | DECIDED | I4 steps 3–4, 3c, 4a |
| C07 | OPEN, AWAITING_INFORMATION | lifecycle left the trigger state without a decision (`dispute_withdrawn`, `request_cancelled`, `request_declined` dates taken) / close without decision | WITHDRAWN | FR-B-17; B12 5b |
| C08 | DECIDED | `appeal_filed` [party, within window] (iteration 2) | APPEALED | I4 4b |
| C09 | APPEALED | `appeal_decided` upheld [second moderator ≠ first] (it. 2) | DECIDED | I4 4b |
| C10 | APPEALED | `appeal_decided` overturned (it. 2) / keep both, flag outcomes | REVERSED | I4 4b, 4c |
| C11 | DECIDED | `decision_reversed` [authorised, reason] (it. 2) / keep both, flag outcomes | REVERSED | I4 4c; ES-11 |

Case actions are not lifecycle event types (no change to the frozen schema): each one is an `audit_log` entry and the `escalation_case.status` column. In iteration 1 the schema opens the case inside the same database transaction as `held_for_review` or `dispute_opened`, and moves it to DECIDED or WITHDRAWN when the lifecycle event that settles it is appended.

## 5. Event catalogue (A4) and event-specific data (ADR-0005)

Event-specific data, which the guards and replay need (dates, hold reason, decision, outcome), is stored in `payload`, a JSON object whose contents per event type are this table (**ADR-0005, accepted 2026-10-11**, closes N-6). `evidence_refs` stays a set of references.

| Event type | `payload` | `evidence_refs` | Actor | Status |
|---|---|---|---|---|
| `request_created` | `item_id`, `requested_period` (checked against the transaction, so it can be rebuilt from the log), message | — | Borrower | frozen |
| `locality_checked` | `locality_outcome` = VERIFIED | locality result id | System | frozen |
| `held_for_review` | `hold_reason` (5 values) | `assessment_id` for manipulation / high-value holds | System | frozen; `config_version` set when an assessment is referenced |
| `assessment_generated` | — | `assessment_id` | System | frozen; carries `config_version` |
| `hold_cleared` | note | `decision_id` | Moderator / Admin | frozen (ADR-0003) |
| `request_accepted` | handover time (optional) | — | Lender | frozen |
| `request_declined` | `reason` (lender text, `dates_taken`, restriction) | `decision_id` when a moderator restricts | Lender / System / Moderator | frozen |
| `request_cancelled`, `request_expired`, `no_show` | reason (optional) | — | Borrower / System | frozen |
| `handover_confirmed`, `return_confirmed` | — | both condition-report ids | Borrower or Lender | frozen |
| `return_initiated` | — | — | Borrower | frozen |
| `transaction_closed` | `outcome` = `on_time` / `late`, deposit release recorded | — | System | frozen (normal completion only) |
| `dispute_opened` | `reason` (DAMAGE, NON_RETURN, CONDITION_MISMATCH, NO_SHOW, OTHER), description | attachment ids | Party; System for NON_RETURN | frozen |
| `dispute_resolved` | decision | `decision_id` | Moderator / Admin | frozen (ADR-0004) |
| `dispute_withdrawn` | reason (optional) | — | Raising party | frozen (ADR-0004) |
| `reminder_sent` | kind | — | System | agreed (D2), iteration 2 |
| `extension_requested`, `extension_approved`, `extension_declined` | `new_due` | — | Borrower / Lender | agreed (D2), iteration 2 |

The four internal event types are needed by FR-B-14 and FR-B-18; they were named on 2026-10-11 (decision D2, Use Cases v1.2 §2) and are built in iteration 2.

## 6. Design decisions (for the viva)

- **DD-A. Choice pseudostates for the system steps.** Locality and assessment are single system actions whose result decides the event type appended. Drawing them as choices keeps one arrow per outcome instead of five parallel arrows.
- **DD-B. Confirmations are data, the transition is the pair.** UC-B7 and UC-B8 need both parties; the Use Cases §2 state list has no intermediate state. Recording each confirmation as a `condition_report` and appending the transition when the pair is complete gives the two-party guarantee without new states.
- **DD-C. History pseudostate for withdrawal.** ADR-0004 restores "the state stored in `previous_state`". IN_PROGRESS contains only simple states, so shallow history H returns to exactly that state; the database checks it against the stored value.
- **DD-D. Terminal states without final pseudostates.** Five terminal states are drawn with a bold border instead of five arrows to final nodes; the record stays in the event store.
- **DD-E. Case opened by the event.** A held or disputed request can never exist without its case, because both are written in one database transaction.

## 7. Open points

| # | Point | Current design | Who decides |
|---|---|---|---|
| SM-I1 | UC-B12 allowed disputes in RETURNED, but UC-B8 closes RETURNED immediately | **Resolved (D4):** no dispute from RETURNED; UC-B12 v1.2 updated; T23 and T26 exclude RETURNED | — |
| SM-I2 | Cancel from which pending states | **Resolved (D8):** any pending state; UC-B6 *a v1.2 updated | — |
| SM-I3 | Case whose trigger disappears | **Resolved (D9):** WITHDRAWN (C07) accepted | — |
| SM-I4 | Who appends `handover_confirmed` / `return_confirmed`, and in which order | **Resolved by design review (R2):** the lender records the checklist first; the borrower's confirmation counts only if made after it (UC-B7 step 3, UC-B8 steps 2–3); the completing party appends the event | — |
| SM-I5 | Step-0 `RESUME` resolution | **Resolved (D5):** dropped; ADR-0004 replaces it | — |
| SM-I6 | Timer values (response window, grace, overdue limit, dispute window, confirmation window) | Not in the v1.1 baseline; v1.1 proposals are archived; needed only when the scheduler is built (iteration 2) | Team, iteration 2 plan |
| SM-I7 | When a high-value request with weak evidence is held (T07) instead of sent as REVIEW_RECOMMENDED (T05) | Both paths drawn | Student 2, A5 decision table (N-7) |
| SM-I8 | UC-B8 3b "flagged for moderator attention" has no case trigger in FR-T-10 | Modelled as `reminder_sent` only (I06) | Team |
