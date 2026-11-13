# Borrowing Lifecycle State Machine, Version 3 (iteration 2, DA-06)

| Field | Value |
|---|---|
| Owner | Fatima Khursheed (Student 1, Module 3) |
| Version | 3.1 draft, 12 November 2026 (v3.0 of 3 November aligned to ADR-0009 as recorded in `../03_architecture/DigitalMohalla_ADRs_Ver1.md`: T25a, T25b, T25c and four possession values) |
| Status | Draft for the iteration 2 design gate (10 November). ADR-0009 needs Minahil's sign-off; the three new event types (ADR-0015) need all three students (frozen event schema, FR-B-09) |
| Replaces | `State_Machine_Design.md` v2.2 (lifecycle part), which stays as the iteration 1 baseline until the backend moves to v3 (build F1) |
| Source of truth | `../_tools/lifecycle_model_v3.py` v3. The diagram, `transition_table_v3.csv`, `transition_table_v3.md`, `../14_testing/transition_test_matrix_v3.csv` and the `allowed_transition` rows in `../06_data_model/migration_0002_schema_v2_4.sql` are all generated from it or checked against it |
| Files | `borrowing_lifecycle_state_machine.drawio` (UML state machine), `generate_state_machine_v3.py`, `transition_table_v3.csv`, `transition_table_v3.md` |
| GenAI | Drafted with Claude (Claude Code); decisions and review by the owner. To be logged in `docs/ai-usage-log.md` and on Form 13 |

## 1. What changed and why

Version 3 keeps all 14 states and every iteration 1 transition. It splits T25 into three and adds T29, plus two internal ones.

| Change | Transitions | Reason | Source |
|---|---|---|---|
| A dispute now closes by **where the item is**, not always as COMPLETED | T25 split into T25a, T25b and T25c | The mid-evaluation review (DM14) found that `moderation/decisions.py` always moved a dispute to COMPLETED, and the database then released the booking. A dispute raised before handover therefore recorded a closed loan that never happened, and a dispute on a loan still out freed an occupied item | ADR-0009 |
| Counter-offer | T29 added; I07, I08 internal | FR-B-10 and UC-B6 extension 3b require it. It was left out of iteration 1 | ADR-0015 |
| Response window restarts on a counter-offer | T15 guard | Otherwise a lender who proposes new dates on day 2 of a 3-day window could see the request expire before the borrower answers | ADR-0015 |

Counts: 14 states, 24 event types (21 plus three), 29 transitions plus 8 internal ones, **39 leaf rows** (34 in v2.2). The invalid-pair matrix grows from 294 to **336 pairs**: 34 valid (state, event) pairs and 302 that must be rejected and logged.

## 2. Dispute exits by item possession (ADR-0009)

The moderator's decision records the item's possession in `moderator_decision.resolved_outcome` (key `possession`), and `dispute_resolved` copies it into its payload (ADR-0005). The event trigger chooses the only allowed next state from it, so the decision cannot contradict the item's whereabouts. The table follows ADR-0009.

| Dispute raised from | `possession` | Next state | Transition | Booking | Outcome evidence |
|---|---|---|---|---|---|
| ACCEPTED | `NOT_HANDED_OVER` | NO_SHOW | T25a | Released | The at-fault finding only (D11); no return outcome |
| ACTIVE or RETURN_INITIATED | `WITH_BORROWER` | ACTIVE (the loan continues; due date unchanged) | T25b | Stays held | The at-fault finding only; the return is judged when it happens |
| ACTIVE or RETURN_INITIATED | `RETURNED` | COMPLETED | T25c | Released | At-fault finding and the return outcome, as in iteration 1 |
| ACTIVE or RETURN_INITIATED | `LOST` | COMPLETED | T25c | Released; item set to PAUSED for the lender | At-fault finding; the borrower fails ON_TIME_RETURN and CONDITION_AGREED |

Rules the trigger enforces (draft in the migration, function `event_validate_v3`):

- `resolved_outcome.possession` must be present on every `DISPUTE_RESOLVED` decision, and `payload.possession` must copy it.
- `NOT_HANDED_OVER` is allowed only when the dispute was opened from ACCEPTED; `WITH_BORROWER`, `RETURNED` and `LOST` only from ACTIVE or RETURN_INITIATED.
- `WITH_BORROWER` always leads to ACTIVE, also from RETURN_INITIATED: the return that was started did not happen, so the borrower starts it again.
- The booking is released on NO_SHOW and COMPLETED, as before. T25b never releases it, so an occupied item stays blocked.
- `allowed_transition` is append-only, so the v2.3 row for T25 keeps its reference `T25`; it is the row of T25c.

Why not a new terminal state such as CLOSED_BY_DECISION: NO_SHOW already means "the handover never happened, dates released", and the review itself names NO_SHOW as the expected regression ("ACCEPTED NO_SHOW"). A new state would add 24 more invalid pairs and change every screen that lists states, for no difference in meaning.

## 3. Counter-offer (ADR-0015)

```text
ASSESSED --counter_offered [lender; none open] (I07)--> ASSESSED       payload.proposed_period
ASSESSED --counter_declined [borrower; one open] (I08)--> ASSESSED     original dates stay
ASSESSED --counter_accepted [borrower; one open; dates free] (T29)--> LOCALITY_CHECKED
         then T05 to T08 run the assessment again on the new dates
```

- At most one counter-offer is open at a time. It is open from `counter_offered` until the next `counter_accepted`, `counter_declined`, `request_accepted`, `request_declined`, `request_cancelled` or `request_expired` on the stream.
- On T29 the trigger copies `payload.proposed_period` into `borrowing_transaction.requested_period`. The event carries the period, so replay rebuilds it from the log (FR-B-09).
- T29 returns to LOCALITY_CHECKED, not ASSESSED. Loan length is part of the similarity weighting (decision D17), so an assessment made for other dates is stale. Locality is not re-checked: it reads the member's stored result, which the new dates do not change.
- Proposed dates must not overlap a held booking. Pending requests still block nothing (ADR-0001).

## 4. Iteration 2 transitions the scheduler fires

These were designed in iteration 1 and are built now (Fatima, F4 and F5). The scheduler (ADR-0012) appends them as `system:scheduler`.

| Job | Transition | Guard value (config, to be set in FR/NFR v1.4) |
|---|---|---|
| Request expiry | T15 ASSESSED → EXPIRED | response window, initial 72 h, restarted by `counter_offered` |
| Handover reminder | I01 in ACCEPTED | at the agreed handover time |
| No-show | T19 ACCEPTED → NO_SHOW | handover time plus a grace period, initial 24 h |
| Return reminders | I02 in ACTIVE | 24 h before the due date, and at the due date |
| Overdue escalation | T24 ACTIVE → DISPUTED, reason `NON_RETURN` | due date plus an overdue limit, initial 72 h, after at least two reminders |
| Confirmation reminder | I06 in RETURN_INITIATED | 24 h after `return_initiated` with no confirmation |

The values are initial hypotheses. They go into the versioned config with every other parameter (NFR-D-01) and are not hard-coded.

## 5. Effect on other artefacts

| Artefact | Change | Owner |
|---|---|---|
| `../06_data_model/migration_0002_schema_v2_4.sql` | Three event types, five `allowed_transition` rows, a check on `moderator_decision.resolved_outcome`, guards in `event_validate_v3`, item handling in `event_apply_v3` | Fatima |
| Escalation-case state machine | C06 records possession with the decision | Minahil (DA-07) |
| `../14_testing/transition_test_matrix_v3.csv` | Regenerated: 336 pairs | Fatima |
| Backend `transition_leaves.csv` and `transition_table.py` | Regenerate from this model when migration 0002 is built (F1) | Fatima |
| `moderation/decisions.py` | `plan()` maps possession to the next state instead of always COMPLETED | Minahil (M1) |
| Sequence (c), dispute activity diagram | Possession branch | Minahil |

## 6. Tests this version adds (test suite 1, suite 25)

- Every one of the 336 pairs: valid ones pass, invalid ones are rejected and logged.
- A dispute opened from ACCEPTED and resolved as `NOT_HANDED_OVER` ends in NO_SHOW and releases the booking; no return outcome exists.
- A dispute opened from ACTIVE or RETURN_INITIATED and resolved as `WITH_BORROWER` goes to ACTIVE; the booking is still HELD and another request for the same dates is refused.
- `RETURNED`, `LOST` and `WITH_BORROWER` from ACCEPTED are refused by the trigger; `NOT_HANDED_OVER` from ACTIVE is refused.
- A second `counter_offered` while one is open is refused; `counter_accepted` with taken dates is refused; after T29 the next event is an assessment event and the stored assessment uses the new loan length.
