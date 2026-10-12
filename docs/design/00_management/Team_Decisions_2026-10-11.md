# Team decisions, 11 October 2026 (design steps A1 and A4)

| Field | Value |
|---|---|
| Recorded by | Student 1 |
| Participants | Student 1, Student 2, Student 3 (team discussion) |
| Purpose | Close the open points of the Student 1 design review before the A4 deadline (D-19) |
| Use | Report Appendix F (meeting records); evidence for Form 2 "design evolution" |

Each member should add their initials against this record. Supervisor review is still pending.

| # | Decision | Outcome | Applied in |
|---|---|---|---|
| D1 | Event-specific data (FR/NFR issue N-6) | Add `payload` (JSON object, contents per event type) to the frozen event record; `prev_hash` and `row_hash` are storage-level columns. Recorded as **ADR-0005**. | ADRs v1.1; Use Cases v1.2 §2; FR-B-09; `schema.sql`; ERD; class diagram |
| D2 | Internal event types | `reminder_sent`, `extension_requested`, `extension_approved` and `extension_declined` are named now and built in iteration 2 | Use Cases v1.2 §2; event catalogue; `schema.sql` |
| D3 | ADR-0001 to ADR-0004 | **Accepted** (closes N-5) | ADR sign-off table |
| D4 | Disputes in RETURNED (UC-B12 vs UC-B8) | No dispute from RETURNED; a disagreement at return is raised in RETURN_INITIATED (UC-B8 ext 3a). Two leaf transitions removed (34 rows remain). | UC-B12 pre-condition; FR-B-16; T23, T26; `allowed_transition`; new schema test |
| D5 | "RESUME" dispute resolution (accepted at the Step-0 meeting) | Dropped; ADR-0004 replaces it | ADR-0004 status note |
| D6 | ADR-0002 wording | Bookings are held from acceptance until COMPLETED or NO_SHOW (not only while ACCEPTED or ACTIVE) | ADR-0002; FR-B-05; UC-B5 step 2, ext 2a |
| D7 | Separate Request table (Step-0) | Merged into BorrowingTransaction, following the A2 class list | Schema v2.0 (already so) |
| D8 | Borrower cancellation | Allowed from any pending state; an open case is withdrawn | UC-B6 ext *a; T16 (already so) |
| D9 | Escalation case state WITHDRAWN | Accepted (case closed without a decision when the lifecycle leaves the hold or dispute) | Escalation case C07 (already so) |

**Still open after this meeting** (not part of these decisions): the locality method (A11, D-11 gate), the trust-edge weight rule (Student 1 with Student 2, A5), N-7 and Student 2's fields and thresholds (A5), the timer values (iteration 2), the frontend and backend stack (D-15 gate), and whether the A2 domain model keeps LocalityResult, ConditionReport and Booking (A2 sitting).
