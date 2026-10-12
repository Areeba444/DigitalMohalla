# User Interface Wireframes & Architectural Annotations (Iteration 1)

**Deliverable ID:** Design Step A12  
**Applicable Documents:** Use Cases v1.1, FR/NFR v1.1, ADR-0001 to ADR-0004  
**Design Standard:** Mobile (iOS/Android 390×844), Mid-Fidelity Wireframes  
**Target Milestone:** FYP-1 Mid-Evaluation (Iteration 1 Design Gate A14)  
**Artifact Directory:** [`UI/Wireframes/Final-Pngs/`](file:///c:/Users/areeb/Documents/FYP/Supervisor-Evaluation/UI/Wireframes/Final-Pngs)

---

## 1. Overview and Core Design Principles

In accordance with Iteration 1 milestones (Step A12), eight comprehensive wireframe views (covering screens W1 through W7) were designed to specify the end-to-end peer lending workflow, mutual physical condition verification, dispute adjudication, and community governance.

The user interfaces enforce the following foundational software engineering requirements:
1. **NFR-U-01 (Explainable Trust & Multi-Dimensional Assurance):** No screen reduces peer trustworthiness to a single composite numerical score or star rating. Decision-makers are presented with the posterior Beta distribution 90% confidence interval bar alongside independent manipulation risk bands (FR-T-05, FR-T-06).
2. **ADR-0001 & ADR-0002 (Concurrency Management & Soft Holds):** Booking contention is explicitly surfaced in the UI. Overlapping pending requests are surfaced prior to confirmation, and optimistic lock collisions gracefully transition the request to `DECLINED` with reason `"dates taken"`.
3. **Bilateral Handover & Return Symmetry (FR-B-11 to FR-B-15):** Physical item exchange requires dual confirmation. Handover and return inspections are displayed side-by-side to highlight condition deltas immediately.
4. **NFR-S-03 (Multi-Tenant Community Isolation):** Community moderators are strictly bounded to their local mohalla. Cross-community cases are isolated at the database layer.
5. **ADR-0003 & ADR-0004 (Human-in-the-Loop Adjudication):** Machine algorithms flag holds and anomalies, but only authenticated human moderators possess the authority to restrict users or commit binding dispute resolutions.

---

## 2. Screen Specifications & Report Callout Annotations

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                Wireframe Catalog (A12)                                 │
├─────────┬──────────────────────────────────────────┬──────────────┬────────────────────┤
│ Screen  │ Description                              │ Viewport     │ Final PNG Asset    │
├─────────┼──────────────────────────────────────────┼──────────────┼────────────────────┤
│ W1      │ Lender Request with Evidence Summary     │ Mobile (390) │ W1_Lender_...png   │
│ W2      │ Lender Decision & Concurrency Conflict   │ Mobile (390) │ W2_Lender_...png   │
│ W3a     │ Handover Inspection (Lender View)        │ Mobile (390) │ W3a_Handover...png │
│ W3b     │ Handover Confirmation (Borrower View)    │ Mobile (390) │ W3b_Handover...png │
│ W4      │ Return Inspection Side-by-Side           │ Mobile (390) │ W4_Return_...png   │
│ W5      │ Dispute Submission & Case Progress       │ Mobile (390) │ W5_Dispute_...png  │
│ W6      │ Community Moderator Triage Queue         │ Mobile (390) │ W6_Moderator...png │
│ W7      │ Moderator Adjudication & Decision Table  │ Mobile (390) │ W7_Moderator...png │
└─────────┴──────────────────────────────────────────┴──────────────┴────────────────────┘
```

---

### Figure 4.1: Screen W1 – Lender Request with Assurance Summary
![Figure 4.1: Screen W1 – Lender Request with Assurance Summary](../../UI/Wireframes/Final-Pngs/W1_Lender_Request_Assurance%201.png)

*Source Asset:* [`UI/Wireframes/Final-Pngs/W1_Lender_Request_Assurance 1.png`](file:///c:/Users/areeb/Documents/FYP/Supervisor-Evaluation/UI/Wireframes/Final-Pngs/W1_Lender_Request_Assurance%201.png)

#### Engineering Annotations:
* **(1) Item & Request Context Header:** Displays borrower identity (`Ayesha K.`), requested reservation dates (`14–16 Oct`), and borrower message (`"Need it for a shelf."`).
* **(2) Assurance State Indicator:** Surfaces the engine decision state (`INSUFFICIENT_EVIDENCE`) without subjective user-rating labels.
* **(3) Direct Evidence & 90% Confidence Interval Bar [NFR-U-01]:** Visualizes the posterior Beta distribution bounds $[0.10, 0.90]$ across a normalized reliability spectrum. Avoids misleading point averages.
* **(4) Independent Manipulation Risk Band:** Explicitly decouples community behavioral anomalies (reciprocal clustering, retaliation) from historical transaction counts.
* **(5) Prescribed Safeguards Checklist:** Dynamically displays safeguards derived from the decision policy (deposit recording, handover photos, fixed return dates).
* **(6) Action Controls:** Binary decision buttons fulfilling Use Case **UC-B6** (`Accept` / `Decline`) with an iteration 2 placeholder for counter-offers.

#### Use Case & Requirements Traceability:
Fulfills **UC-B6 (Steps 1–2)**, **UC-D3/4/5 (Step 7)**, and **FR-B-06, FR-T-01, FR-T-02, FR-T-04, FR-T-05, FR-T-08, NFR-U-01**. The interface equips the lender with transparent statistical context before reserving an item, protecting newcomers from algorithmic exclusion while ensuring asset security.

---

### Figure 4.2: Screen W2 – Lender Decision & Concurrency Conflict State
![Figure 4.2: Screen W2 – Lender Decision & Concurrency Conflict State](../../UI/Wireframes/Final-Pngs/W2_Lender_Decision_Conflict%201.png)

*Source Asset:* [`UI/Wireframes/Final-Pngs/W2_Lender_Decision_Conflict 1.png`](file:///c:/Users/areeb/Documents/FYP/Supervisor-Evaluation/UI/Wireframes/Final-Pngs/W2_Lender_Decision_Conflict%201.png)

#### Engineering Annotations:
* **(1) Explicit Decision Selector:** Radio group (`Accept booking` / `Decline booking`) with optional decline justification input.
* **(2) Concurrency Pre-Warning [ADR-0001]:** Informs the lender that confirming acceptance automatically declines competing overlapping requests due to soft-hold release.
* **(3) Primary Decision Actions:** Full-width confirmation buttons (`Confirm Decision` / `Cancel`).
* **(4) Optimistic Lock Collision Alert [ADR-0002]:** A distinct warning banner demonstrating error handling when a race condition occurs and dates were claimed by a faster acceptance (`"dates taken"`).

#### Use Case & Requirements Traceability:
Fulfills **UC-B6 (Steps 3–6, Extensions 3a, 3c)** and **FR-B-05, FR-B-10, ADR-0001, ADR-0002**. Handles concurrent booking attempts predictably and informs users of schedule conflicts without data corruption.

---

### Figure 4.3: Screen W3a – Handover Inspection (Lender View)
![Figure 4.3: Screen W3a – Handover Inspection (Lender View)](../../UI/Wireframes/Final-Pngs/W3a_Handover_Inspection_Lender%201.png)

*Source Asset:* [`UI/Wireframes/Final-Pngs/W3a_Handover_Inspection_Lender 1.png`](file:///c:/Users/areeb/Documents/FYP/Supervisor-Evaluation/UI/Wireframes/Final-Pngs/W3a_Handover_Inspection_Lender%201.png)

#### Engineering Annotations:
* **(1) State & Scheduling Banner:** Shows booking state (`ACCEPTED`) and meeting timestamp (`14 Oct, 10:00 AM`).
* **(2) Physical Condition Checklist:** Functional checklist verifying item integrity (power, casing, battery, bits) with freeform condition notes.
* **(3) Safeguard Photo Upload Module:** Two upload slots with camera affordances for mandatory photographic evidence capture.
* **(4) Record-Only Deposit Confirmation:** Checkbox logging offline cash deposit receipt (record-only ledger; zero in-app financial transactions).
* **(5) State Dispatch Action:** "Send for Borrower Review" transmits the verified condition payload to the borrower.

#### Use Case & Requirements Traceability:
Fulfills **UC-B7 (Steps 1–2)** and **FR-B-11, FR-B-12**. Establishes the authoritative physical baseline for the borrowed asset before physical possession transfers.

---

### Figure 4.4: Screen W3b – Handover Confirmation (Borrower View)
![Figure 4.4: Screen W3b – Handover Confirmation (Borrower View)](../../UI/Wireframes/Final-Pngs/W3b_Handover_Confirmation_Borrower%201.png)

*Source Asset:* [`UI/Wireframes/Final-Pngs/W3b_Handover_Confirmation_Borrower 1.png`](file:///c:/Users/areeb/Documents/FYP/Supervisor-Evaluation/UI/Wireframes/Final-Pngs/W3b_Handover_Confirmation_Borrower%201.png)

#### Engineering Annotations:
* **(1) Dual-Review Summary Card:** Recapitulates the checklist items, condition notes, photos, and deposit recorded by the lender.
* **(2) Borrower Verification Remarks:** Optional textarea for borrower observations prior to receipt.
* **(3) Dual Sign-Off Action:** "Confirm Receipt & Activate" commits the dual sign-off and transitions booking state to `ACTIVE`.
* **(4) Discrepancy Escalation Action:** "I Disagree / Condition Mismatch" aborts handover and initiates dispute resolution.

#### Use Case & Requirements Traceability:
Fulfills **UC-B7 (Steps 3–4, Extensions 2a, 3a, 3b)** and **FR-B-11, FR-B-12**. Enforces the core domain invariant that no transaction becomes `ACTIVE` without bilateral physical confirmation.

---

### Figure 4.5: Screen W4 – Return Inspection Side-by-Side Comparison
![Figure 4.5: Screen W4 – Return Inspection Side-by-Side Comparison](../../UI/Wireframes/Final-Pngs/W4_Return_Inspection_Comparison%201.png)

*Source Asset:* [`UI/Wireframes/Final-Pngs/W4_Return_Inspection_Comparison 1.png`](file:///c:/Users/areeb/Documents/FYP/Supervisor-Evaluation/UI/Wireframes/Final-Pngs/W4_Return_Inspection_Comparison%201.png)

#### Engineering Annotations:
* **(1) Side-by-Side Comparative Grid:** Contrasts the original Handover Baseline (left column) against the Return Inspection (right column) to immediately reveal discrepancies.
* **(2) Differential Condition Highlighting:** Highlights new damage in high-contrast red (`[!] Crack near chuck`).
* **(3) Punctuality Marker:** Automatically evaluates return timestamp against scheduled due date (`On-time` vs `Late`).
* **(4) Bilateral Status Indicator:** Tracks dual sign-off readiness (`Lender: Pending · Borrower: Pending`).
* **(5) Conditional Branching Actions:** "Agree Condition & Close Booking" transitions to `RETURNED`, while "Report Damage" triggers the dispute workflow.

#### Use Case & Requirements Traceability:
Fulfills **UC-B8 (Steps 1–5, Extension 4a)** and **FR-B-13, FR-B-15**. Eliminates post-return ambiguity by anchoring the inspection directly to the immutable baseline photos and checklist.

---

### Figure 4.6: Screen W5 – Dispute Submission & Case Progress
![Figure 4.6: Screen W5 – Dispute Submission & Case Progress](../../UI/Wireframes/Final-Pngs/W5_Dispute_Form_Progress%201.png)

*Source Asset:* [`UI/Wireframes/Final-Pngs/W5_Dispute_Form_Progress 1.png`](file:///c:/Users/areeb/Documents/FYP/Supervisor-Evaluation/UI/Wireframes/Final-Pngs/W5_Dispute_Form_Progress%201.png)

#### Engineering Annotations:
* **(1) Categorized Dispute Taxonomy:** Bounded selection categories (Damage, Non-return, Condition mismatch, No-show).
* **(2) Multi-Format Evidence Uploader:** Dedicated attachment slots for damage photos and communication receipts.
* **(3) State Freeze Warning:** System advisory confirming that booking progression and deposit records are locked until moderator adjudication.
* **(4) Post-Submission Tracking Card:** Displays case reference (`#D-014`), assignment to the local community moderator, and counterparty notification.
* **(5) State Reversal Action [ADR-0004]:** "Withdraw Dispute" button invoking the `dispute_withdrawn` event to restore the previous valid booking state.

#### Use Case & Requirements Traceability:
Fulfills **UC-B12 (Steps 1–5, Extensions 1a, 1b, 5a, 5b)**, **FR-B-16, FR-B-17**, and **ADR-0004**. Protects community members through an orderly grievance channel within the 7-day dispute window.

---

### Figure 4.7: Screen W6 – Multi-Tenant Community Moderator Queue
![Figure 4.7: Screen W6 – Multi-Tenant Community Moderator Queue](../../UI/Wireframes/Final-Pngs/W6_Moderator_Queue_Mobile%201.png)

*Source Asset:* [`UI/Wireframes/Final-Pngs/W6_Moderator_Queue_Mobile 1.png`](file:///c:/Users/areeb/Documents/FYP/Supervisor-Evaluation/UI/Wireframes/Final-Pngs/W6_Moderator_Queue_Mobile%201.png)

#### Engineering Annotations:
* **(1) Tenant Boundary Banner [NFR-S-03]:** Community tag (`Block C Community [Isolated]`) verifying multi-tenant data boundaries.
* **(2) Unified Incident Triage Cards:** Merges bilateral interpersonal disputes (`DISPUTED`) and automated engine holds (`HELD_FOR_REVIEW`) into an auditable mobile card feed.
* **(3) Deterministic Priority Assignment:** Priority (`High`, `Med`, `Low`) is mapped deterministically from trigger reason severity (FR-T-10); trust numbers are never used to order cases.
* **(4) Escalation Governance:** Clear compliance notices stating cases unassigned within SLA automatically route to Platform Admin.

#### Use Case & Requirements Traceability:
Fulfills **UC-D6 (Step 2)**, **UC-I4 (Step 1)**, and **FR-T-10, FR-T-11, NFR-S-03**. Furnishes local leaders with an isolated, auditable mobile governance workflow.

---

### Figure 4.8: Screen W7 – Moderator Case Adjudication & Exit Decision Table
![Figure 4.8: Screen W7 – Moderator Case Adjudication & Exit Decision Table](../../UI/Wireframes/Final-Pngs/W7_Moderator_Case_Adjudication_Mobile%201.png)

*Source Asset:* [`UI/Wireframes/Final-Pngs/W7_Moderator_Case_Adjudication_Mobile 1.png`](file:///c:/Users/areeb/Documents/FYP/Supervisor-Evaluation/UI/Wireframes/Final-Pngs/W7_Moderator_Case_Adjudication_Mobile%201.png)

#### Engineering Annotations:
* **(1) Append-Only Event Trail:** Chronological timeline extracted directly from the event store (`handover_confirmed` → `return_initiated` → `dispute_opened`).
* **(2) Comparative Claims & Photo Gallery:** Opposing party statements paired with baseline vs return photo comparisons.
* **(3) Non-Composite Assurance Profile [NFR-U-01]:** Borrower transaction counts with active disputes excluded from trust weighting (ES-07).
* **(4) Binding Adjudication Form:** Resolution selector with mandatory justification field required prior to committing signed event `dispute_resolved`.
* **(5) ADR-0003 Exit State Reference Matrix:** Enforces permitted state transitions based on hold trigger type (`locality_*`, `manipulation_risk`, `engine_failure`).
* **(6) Human-Only Restriction Policy:** System constraint stipulating that restricting users is strictly a human-adjudicated decision.

#### Use Case & Requirements Traceability:
Fulfills **UC-D6 (Step 3)**, **UC-I4 (Steps 1–4, Extensions 2a, 3a–3c, 4a, 4d)**, **FR-T-10, FR-T-11, FR-M-05**, and **ADR-0003, ADR-0004**. Guarantees procedural fairness and legal defensibility through an immutable audit trail.
