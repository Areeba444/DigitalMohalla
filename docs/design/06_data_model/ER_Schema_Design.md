# Digital Mohalla: ER Diagram and Schema (design step A6)

| Field | Value |
|---|---|
| Document | Design step A6: ER diagram and physical schema (append-only event store, projections, bookings, assessments, cases) |
| Owner | Student 1 |
| Version | 2.3, 11 October 2026: integration decisions D10–D14 (ADR-0007, ADR-0008): `assessment.manipulation_level`, `manipulation_corroborated`, `rule_fired` and the decision-table check; three value bands. v2.2: team decisions D1–D9 and A11. v2.0 replaced v1.0 (`archive_v1/`). |
| Status | `payload` and the internal event types agreed (ADR-0005). Awaiting second-member review (A14). |
| Baseline | Use Cases v1.3 §2, FR/NFR v1.3, ADR-0001 to ADR-0005 (accepted), ADR-0007 and ADR-0008 (accepted for integration), `07_state_machines/State_Machine_Design.md` v2.2 |
| DBMS | PostgreSQL 14+ **with the `btree_gist` contrib extension** (ADR-0002). Tested on PostgreSQL 16.6. |
| Author note | Drafted with Claude (GenAI); to be disclosed on Form 13 and in the AI usage log. |

## Files

| File | What it is |
|---|---|
| `er_diagram.drawio` | Crow's-foot ER diagram, generated from the live PostgreSQL catalogue |
| `schema.sql` | The schema: 22 tables, 217 columns, triggers, functions, views, transition seed, privileges |
| `test_schema.py` | 44 checks against a real PostgreSQL (traceable to FRs, NFRs, ADRs and review findings R1–R4) |
| `Data_Dictionary.md` | A4 data dictionary: every column with type, key, meaning and source; enums; config parameters |
| `generate_data_dictionary.py` | Generates it from the catalogue; fails if a column lacks a meaning |
| `test_results.txt` | Last run: **44/44 passed** on PostgreSQL 16.6 |
| `generate_erd.py` | Reads the catalogue and writes `er_diagram.drawio`, so the diagram cannot disagree with the SQL |

Run: `set DM_TEST_DSN=postgresql://postgres@localhost:5432/postgres`, then `python test_schema.py` (loads and tests the schema) and `python generate_erd.py`. The embedded `pgserver` package used for v1.0 lacks `btree_gist`; use the official `postgres` Docker image (the project's Docker Compose target) or the EDB binaries.

## 1. Why v2.0

v1.0 implemented the v1.1 state machine (old vocabulary) and prevented double booking with a per-item lock (its DS-4 rejected an exclusion constraint). The baseline now fixes the state list and field names (Use Cases §2, FR-B-09) and ADR-0002 requires the exclusion constraint, so v1.0 conflicts on both counts.

| Change | Reason |
|---|---|
| `transaction_event` → `lifecycle_event` with `stream_id`, `stream_seq`, `schema_version`, `actor_id`, `evidence_refs`, `config_version` | Frozen event record, Use Cases §2 / FR-B-09 |
| `txn_state` (18 values) → `lifecycle_state` (14); `txn_event_type` (31) → `event_type` (17 + 4 internal, ADR-0005) | Use Cases §2; ADR-0003, ADR-0004 |
| `actor_role` column removed; role derived from `authorisation` | Only `actor_id` and `authorisation` are frozen fields |
| New `booking` table with `EXCLUDE USING gist (item_id WITH =, period WITH &&) WHERE (status = 'HELD')` | ADR-0002 |
| `dispute` → `escalation_case` (dispute and non-dispute holds), `dispute_statement` → `case_statement` | UC-D6, UC-I4, FR-T-10 |
| `assurance_result.requires_moderator` → `assessment.hold_reason` + `policy_decision`, with `config_version` NOT NULL | ADR-0003, FR-T-06, NFR-D-01 |
| `evidence_record` → `outcome` (Overview §5.10 OutcomeEvent: subject, observer, role, metric, success) | Overview §5.10, FR-T-03 |
| `trust_edge` keyed by (source, target, role, metric) | Overview §5.10 TrustEdge, FR-T-04 |
| `request` table merged into `borrowing_transaction`; `invitation`, `availability_block`, `community.boundary_geojson` removed | A2 class list has no separate Request; the locality method and the calendar (B2) are not chosen / not built in iteration 1 |
| `locality_outcome` reduced to VERIFIED, INCONCLUSIVE, CONFLICTING | FR-A-08 three-valued outcome |
| `app_user.is_synthetic` added | Plan evidence checklist: synthetic data labelled |

## 2. Tables by module

| Module | Table | Domain class (A2) | Notes |
|---|---|---|---|
| 1 | `app_user`, `user_block`, `community`, `membership`, `invitation`, `locality_verification` | User, Community, Membership, LocalityResult | A11 geofence + invitation: coarse signal and outcome only; the outcome must follow the decision table (`locality_rule_ck`); invitations single-use (`locality_guard`) |
| 3 | `category`, `item` | Item | Seeded in iteration 1 |
| 3 | `borrowing_transaction` | BorrowingTransaction | Projection; only `event_apply` changes `current_state`, `stream_version`, `hold_reason`, `due_at` |
| 3 | `lifecycle_event` | LifecycleEvent | Append-only, hash-chained; `UNIQUE (stream_id, stream_seq)`; composite FK to `allowed_transition` |
| 3 | `allowed_transition` | (A3 transition table) | 34 rows generated from `_tools/lifecycle_model.py` |
| 3 | `booking` | Booking | Exclusion constraint on HELD bookings; held until COMPLETED or NO_SHOW (ADR-0002 as amended) |
| 3 | `condition_report`, `attachment` | ConditionReport | Each party's confirmation; photos must have metadata stripped |
| 5 | `assessment`, `outcome`, `review` | Assessment, Outcome, Review | Field list owned by Student 2; structure agreed for integration |
| 5 | `trust_edge` | TrustEdge | Student 1 (indirect trust) |
| 9 | `escalation_case`, `case_statement`, `moderator_decision`, `audit_log` | EscalationCase, ModeratorDecision | One live case per transaction; decisions need a reason |

## 3. How the database enforces the design

| Mechanism | Rule | Proven by test |
|---|---|---|
| `event_validate` trigger: lock the stream row, `stream_seq = version + 1`, `previous_state` = current | Optimistic concurrency, no gaps | "Stale command" |
| Composite FK + `allowed_transition` lookup + role check | Transition table T01–T26 (FR-B-08, NFR-R-02) | 34-row model check; CSV check; invalid-transition checks; no dispute from RETURNED |
| Party / moderator / admin identity checks; moderator must be of the item's community and not a party | NFR-S-02, NFR-S-03 | Impersonation, other-community moderator |
| Every moderator transition must reference a `moderator_decision` with a reason on the live case | FR-T-11 | Moderator rules |
| Guards: locality outcome recomputed from stored evidence; hold reason matches; assessment reference and `config_version` match; dual confirmation; deposit recorded; on-time vs late; dates-taken only after an overlapping booking; withdraw restores `previous_state` | FR-B-07, FR-B-11, FR-B-13, FR-B-17, ADR-0001/0003/0004 | One check per guard |
| `booking_no_overlap` exclusion constraint, written by `event_apply` in the same transaction as `request_accepted` | ADR-0002, FR-B-05, NFR-R-01 | Overlap refused; 3-connection race × 5 rounds → exactly one commit each time |
| Append-only triggers, revoked privileges, per-stream hash chain, `verify_event_chain()` | FR-M-05, NFR-S-05 | Append-only; tamper detection with triggers disabled; app role |
| `replay_state()` rebuilds the state from events only; `request_created` must carry the item and dates, so the whole transaction is recoverable from the log | FR-B-09, NFR-R-03 | Happy path: replay = projection; creation data in the event |
| A moderator event must match the kind of its recorded decision (CLEARED / SAFEGUARDS_IMPOSED → `hold_cleared`, RESTRICTED → `request_declined`, DISPUTE_RESOLVED → `dispute_resolved`) | FR-T-11, ADR-0003 | Decision kind |
| The borrower's confirmation counts only after the lender's latest checklist | UC-B7 step 3, UC-B8 steps 2–3 | Confirmation order |
| View `v_pending_outcomes`: closing events with no outcome yet (catch-up for the engine) | FR-B-15, NFR-R-04 | Pending outcomes |
| Case opened by `held_for_review` / `dispute_opened`; DECIDED by the moderator event; WITHDRAWN by cancel, withdraw or dates-taken | UC-D6, C01/C06/C07 | Hold, dispute and cancel checks |
| `assessment_level_ck` and `assessment_rule_ck`: the risk level follows the bands and the corroboration rule; each `rule_fired` fixes the assurance state, policy decision and hold reason of the A5 decision table, so level 4 is always held unless an open dispute takes precedence | FR-T-06, ADR-0007, ADR-0008, D12 | Risk check; decision-table check |

What the database does not enforce: wall-clock timers (scheduler, iteration 2), the decision policy itself (Student 2's engine), notification delivery and file storage.

## 4. Location privacy (Student 1)

No table has a coordinate, address or CNIC column (a test scans the catalogue). `locality_verification` stores the method and the coarse outcome; a refused permission can only be INCONCLUSIVE. The request-time check `locality_outcome_for()` reads stored results only; this is the iteration-1 locality stub of plan item B5. Attachments are refused unless `metadata_stripped` is true. Retention of coarse results is open (NFR-PR-02).

## 5. Open inputs

| # | Input | Placeholder | Owner |
|---|---|---|---|
| ER-1 | `payload` column and hash columns | **Resolved:** ADR-0005 | — |
| ER-2 | Final fields of `assessment`, `outcome`, `review`; value-band thresholds; outcome metrics | **Mostly resolved (D14):** value bands and the engine-contract mapping in `Assurance_Data_Dictionary.md` §5; Student 2 to confirm the metric list | Student 2 |
| ER-3 | Trust-edge weight rule | Posterior mean, ADR-0006 (proposed) | Student 2 to confirm |
| ER-4 | Retention periods (coarse locality results, photos) | Not enforced; attachments deletable | Team / supervisor |
| ER-5 | Locality method and its tables | **Resolved (A11):** `invitation`, `community.boundary_polygon`, `geofence_signal`, decision-table constraint | — |
| ER-6 | Booking hold period | **Resolved (D6):** ADR-0002 amended to "until COMPLETED or NO_SHOW" | — |
| ER-7 | Request table | **Resolved (D7):** merged into BorrowingTransaction | — |
