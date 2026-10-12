# Data Flow Diagram (DFD) Specification: Level 0 Context & Level 1 Assurance Pipeline
## Module 5: Trust & Assurance Engine — Deliverable T7

**Project:** Digital Mohalla  
**Component:** Module 5 (Trust Estimation, Manipulation Detection, Decision Policy) & Locality Privacy Boundary  
**Deliverable:** T7 — DFD Level 0 (Context Diagram) & DFD Level 1 (Assurance Pipeline Subsystem)  
**Owner:** Student 2 (A10)  
**Version:** 1.2, 11 October 2026. v1.2 (notation review): both levels are redrawn in strict Gane & Sarson notation by `generate_dfd.py`: level 0 is a true context diagram (no data stores); level 1 balances level 0 (processes 9.0 and 10.0 carry the lender's decision and the administrator's flows; the administrator no longer writes straight into a store); store D5 makes the locality read explicit; the query flow DF-105 is merged into DF-106 (a DFD shows data, not requests). v1.0 (Student 2). v1.1 (integration): parameter values aligned with the engine config 1.1.0 (γ 0.7, ρ cap 0.6, divisors 3 and 2, 14-day retaliation window, the A5 thresholds, assurance states and rule names); the borrowing request carries no location and process 1.0 reads the stored A11 result (decision D13)  
**Status:** Design baseline; awaiting A14 second-member review  
**Traceability:** FR-T-01 through FR-T-10; FR-A-07, FR-A-08, FR-B-05, FR-B-07, FR-B-08, FR-B-09; ADR-0001, ADR-0003; NFR-PR-01, NFR-D-01, NFR-R-02, NFR-P-04; Overview §1, §5.1–§5.10

---

## 1. Architectural Scope & The Privacy Boundary Invariant

This document specifies the Data Flow Diagrams (DFD) for the **Digital Mohalla Trust & Assurance Engine (Module 5)** across two structural levels:
1. **DFD Level 0 (System Context Diagram):** Shows all external entities (Borrower, Lender, Community Moderator, System Administrator), the central Digital Mohalla System, and external persistent stores.
2. **DFD Level 1 (Module 5 Assurance Pipeline Subsystem Decomposition):** Decomposes the end-to-end evaluation pipeline into 8 formal sub-processes, 4 core data stores, and discrete, typed data flows.
3. **Scoping & Balancing Principle:** Level 0 models the overall Borrowing & Assurance Management System context. Level 1 decomposes the **Request-to-Assessment Subsystem** (UC-B5, FR-B-07, Module 5). Downstream booking state transitions (`ACCEPTED`, `ACTIVE`, `COMPLETED`, `DISPUTED`) are managed by the Booking Lifecycle Subsystem (A3/UC-B6/B7).

### The Non-Negotiable Privacy Boundary (FR-A-07 / NFR-PR-01)
> **Fundamental Architectural Constraint:**
> **Exact location data (GPS coordinates, raw location traces, and precise street addresses) NEVER crosses into the Trust Engine or any store.**
> - A device location exists only once, in memory, inside the **Locality Service** when a member joins a community (UC-A3, A11 geofence + invitation). Only the coarse outcome (`VERIFIED`, `INCONCLUSIVE` or `CONFLICTING`) and the coarse geofence signal are stored.
> - A borrowing request carries **no location at all**. **Process 1.0 (Receive Request & Check Stored Locality)** reads the member's stored coarse outcome and passes on only `communityId`, the outcome and sanitised transaction parameters (`itemId`, `category`, `itemValue`, `dates`).
> - Module 5 algorithms and the immutable Event Store receive **zero spatial coordinates**.

---

## 2. DFD Level 0: System Context Diagram

### 2.1 Level 0 elements

A context diagram has exactly one process and no data stores; the stores belong to level 1.

| Element | Gane & Sarson symbol | Flows |
|---|---|---|
| Process 0 "Digital Mohalla borrowing and assurance system" | Rounded box, number above the line | all |
| Borrower | External entity (square) | DF-01 Borrowing request (no location) in; DF-02 Request status and safeguards out |
| Lender | External entity | DF-03 Request with evidence summary out; DF-04 Booking decision in |
| Community moderator | External entity | DF-05 Escalation case with evidence trail out; DF-06 Moderator decision in |
| System administrator | External entity | DF-07 Configuration updates in; DF-08 Health and audit reports out |

v1.1 also drew the stores D1 to D4 and flows DF-09 to DF-12 on level 0; they are now on level 1 only.

---

## 3. DFD Level 1: Module 5 Assurance Pipeline Subsystem

Decomposes the assurance lifecycle from request arrival to lender notification into 8 formal sub-processes adhering strictly to Gane & Sarson rules (zero direct store-to-entity flows, fully resolved data dependencies).

### 3.1 Level 1 elements

Processes (rounded boxes): 1.0 Receive request and check stored locality (privacy boundary) · 2.0 Ingest and filter
historical outcomes · 3.0 Compute direct trust posterior (Alg. 1) · 4.0 Aggregate bounded k-hop indirect trust (Alg. 2)
· 5.0 Evaluate manipulation risk (Alg. 3) · 6.0 Apply context-aware decision policy (Alg. 4) · 7.0 Synthesise
explanation and safeguards · 8.0 Dispatch escalation and record moderator decision · **9.0 Record booking decisions and
outcomes** · **10.0 Manage configuration and reports**.

Data stores (open-ended boxes): D1 Event store · D2 Trust graph · D3 Engine configuration · D4 Escalation cases and audit
log · **D5 Locality results (coarse outcome only)**.

Rules applied (Gane & Sarson): every flow starts or ends at a process (no entity-to-store or store-to-store flow);
every store is both written and read; level 1 balances level 0 (DF-01 = DF-101; DF-02 = DF-123 + DF-132; DF-03 = DF-122;
DF-04 = DF-04; DF-05 = DF-126B; DF-06 = DF-127; DF-07 = DF-128; DF-08 = DF-08).

---

## 4. Formal Data Flow Catalog (Data Dictionary of Flows)

Every data flow in the Level 0 and Level 1 DFDs is cataloged below with its source, destination, attributes, and privacy classification.

| Data Flow ID | Flow Name | Source | Destination | Key Attributes / Payload | Security & Privacy Classification |
|---|---|---|---|---|---|
| **DF-101** | `Borrowing Request` | Borrower | Process 1.0 | `itemId`, `startDate`, `endDate`, `borrowerMessage` (no location of any kind; locality was verified when the member joined, A11) | **Personal data** (no location) |
| **DF-102** | `Request Created Event` | Process 1.0 | D1: Event Store | frozen event fields (`stream_id`, `stream_seq=1`, `event_type="request_created"`, `actor_id`, `new_state="REQUEST_CREATED"`, …) with `payload` = item and requested period | **Internal Audit Trail** (**zero location data**) |
| **DF-103** | `Verified Request & Coarse Context` | Process 1.0 | Process 2.0 | `requestId`, `borrowerId`, `itemId`, `category`, `itemValue`, `dates`, `valueBand`, `communityId`, `localityStatus="VERIFIED"` | **Sanitized Domain Context** (**Zero GPS Coordinates Cross Boundary**) |
| **DF-104** | `Locality Hold Record` | Process 1.0 | D4: Moderation Queue | `streamId`, `holdReason` (`locality_inconclusive` \| `locality_conflict`), `coarseFlags`, `createdAt` | **Moderation Queue** (ADR-0003) |
| **DF-105** | `Historical Query` (v1.1; merged into DF-106 in v1.2: a query is not a data flow) | Process 2.0 | D1: Event Store | `subjectId`, `role`, `lookbackDays` (365), streams: confirmed outcomes, rating submissions, disputes and complaints in the 14-day retaliation window | **Internal Query** |
| **DF-106** | `Raw Event Streams` | D1: Event Store | Process 2.0 | Stream of `OutcomeEvent` (excludes active disputes), rating timestamps, counterparty reviews, dispute filings | **Internal Data** |
| **DF-107** | `Direct Evidence Set` | Process 2.0 | Process 3.0 | `List<OutcomeEvent>`, category similarity $s_i$, value similarity $v_i$, duration similarity $d_i$, elapsed days $\Delta t_i$ | **Domain Evidence Model** |
| **DF-108** | `Subject Identifiers` | Process 2.0 | Process 4.0 | `evaluatorId` (lender), `subjectId` (borrower), `maxHops` (3), `role` | **Graph Traversal Scope** |
| **DF-109** | `Interaction History` | Process 2.0 | Process 5.0 | Transaction timestamps, ratings given and received, review texts (S4), dispute records within the 14-day retaliation window | **Fraud Analysis Stream** |
| **DF-109B**| `Request Valuation` | Process 2.0 | Process 6.0 | `itemValue`, `valueBand` (`LOW` ≤ 5,000, `MEDIUM` ≤ 15,000, `HIGH` > 15,000 PKR), `durationDays` | **Policy Evaluation Input** |
| **DF-110** | `Decay & Prior Config` | D3: Config Store | Process 3.0 | `alpha_0` (1.0), `beta_0` (1.0), `half_life_days` (180), `lambda` (0.00385) | **System Configuration** |
| **DF-111** | `Direct Trust Estimate` | Process 3.0 | Process 6.0 | posterior mean $\mu \in [0, 1]$, 90% interval `lower90`, `upper90`, `alpha`, `beta`, `effectiveSampleSize`, `directEventCount` (never shown as a single score) | **Assurance Signal** (Algorithm 1) |
| **DF-112** | `Edge Weight Cache` | Process 9.0 (TrustEdgeProjector, same estimator as Alg. 1) | D2: Graph Store | `sourceId`, `targetId`, `role`, `metric`, `weight` (posterior mean of the source's confirmed outcomes about the target, ADR-0006), `evidenceCount`, `updatedAt`; recomputed when outcomes arrive (sequence (b)), not during an assessment | **Graph Optimization** |
| **DF-113** | `k-Hop Paths` | D2: Graph Store | Process 4.0 | List of valid paths $P_j = \langle v_0, \dots, v_k \rangle$, edge weights $w(e)$, hop lengths $l_j \le 3$ | **Indirect Trust Graph** |
| **DF-114** | `Indirect Parameters` | D3: Config Store | Process 4.0 | `max_hops_k` (3), `hop_decay_gamma` (0.7), `reliability_cap_rho_max` (0.6), `path_count_divisor` (3), `diversity_divisor` (2), `default_population_baseline` (0.5) | **System Configuration** |
| **DF-115** | `Indirect Trust Estimate`| Process 4.0 | Process 6.0 | `pathsUsed`, `evidenceStrength` ($I$), `reliability` ($\rho \le 0.6$), `diversity`, `estimate` ($t_{\text{indirect}}$), `priorBacked` | **Assurance Signal** (Algorithm 2) |
| **DF-116** | `Manipulation Config` | D3: Config Store | Process 5.0 | `retaliation_window_days` (14), signal weights (0.30/0.20/0.20/0.20/0.10, renormalised over active S1, S4), S1 bounds (0.3, 0.6), S4 bounds (0.70, 0.25), risk bands 20/40/60, corroboration (≥ 2 signals ≥ 0.5) | **System Configuration** |
| **DF-117** | `Manipulation Assessment`| Process 5.0 | Process 6.0 | `score` ($M \in [0, 100]$), `level` (1–4), `corroborated`, `signals` with evidence | **Risk Indicator** (Algorithm 3; never proof of fraud) |
| **DF-118** | `Manipulation Signals` | Process 5.0 | Process 7.0 | Human-readable signal summaries (e.g., `s1_reciprocal_clustering`, `s4_review_similarity`, retaliation flag) | **Audit & Explanation Input** |
| **DF-119** | `Decision Policy Config`| D3: Config Store | Process 6.0 | `tau_mu` (0.75), `tau_L` (0.60), `n_min` (3), `rho_sup` (0.30), similarity floor (0.5), value bands, 12-month dispute look-back, rule order R1–R5, R6_DISPUTE, R6_SPARSE, R7–R9 | **System Configuration** |
| **DF-120** | `Policy Decision Result`| Process 6.0 | Process 7.0 | `state` (SUFFICIENT_EVIDENCE, REVIEW_RECOMMENDED, INSUFFICIENT_EVIDENCE, ACTIVE_DISPUTE), `decision` (PROCEED, PROCEED_WITH_SAFEGUARDS, REQUEST_VERIFICATION, RESTRICT_HIGH_VALUE, ESCALATE), `ruleFired`, `holdReason` | **Decision Engine Output** (Algorithm 4) |
| **DF-121** | `Assessment Event` | Process 7.0 | D1: Event Store | `streamId`, `streamSeq=3`, `eventType="assessment_generated"`, `assuranceResult`, `config_version="1.1.0-iteration1-draft"` | **Immutable Audit Log** (NFR-D-01, FR-B-09) |
| **DF-122** | `Decorated Request` | Process 7.0 | Lender | `requestId`, `borrowerProfileSummary`, `assuranceState`, `confidence`, `factorSummary`, `safeguards` | **User Presentation** (No single score) |
| **DF-123** | `Borrower Confirmation` | Process 7.0 | Borrower | `SubmissionResult` (`requestId`, `status="REQUEST_SENT"`, `safeguardsAttached`) | **Borrower Notification** |
| **DF-124** | `Policy Escalation Hold`| Process 6.0 | D4: Moderation Queue | `streamId`, `reason` (`manipulation_risk` \| `high_value_low_confidence`), `fullEvidenceTrail` | **Escalation Case** (FR-T-10, ADR-0003) |
| **DF-125** | `Engine Timeout Hold` | Process 1.0 (the lifecycle controller supervising the `assess()` call) | D4: Moderation Queue | `streamId`, `reason="engine_failure"`, `timeoutThresholdMs=2000`, `failureLogRef` | **System Fault Alert** (FR-T-07) |
| **DF-126A**| `Read Hold Case` | D4: Moderation Queue| Process 8.0 | Active hold record, case priority, hold reason, timestamp | **Moderation Service Query** |
| **DF-126B**| `Escalation Case Alert` | Process 8.0 | Community Moderator | Case file with transaction details, item value, counterparty history, evidence trail (UC-D6) | **Moderator Interface** (No direct store flow) |
| **DF-127** | `Moderator Resolution` | Community Moderator | Process 8.0 | `caseId`, `decision` (`hold_cleared` \| `request_declined`), `mandatoryReason`, `authorisation` | **Moderator Action** (ADR-0003) |
| **DF-127B**| `Append Resolution` | Process 8.0 | D1: Event Store | `streamId`, `eventType="hold_cleared"` \| `"request_declined"`, `authorisationActor`, `stateTransition` | **Event Store Append** |
| **DF-128** | `Config Updates & Tuning`| System Administrator| Process 10.0 | Versioned parameter payloads (`config_version`, baseline thresholds, priors, weights) | **System Administration** |
| **DF-04** | `Booking Decision` | Lender | Process 9.0 | `requestId`, `accept` / `decline`, optional reason | **Lender Action** |
| **DF-08** | `Health and Audit Reports` | Process 10.0 | System Administrator | audit entries (masked), integrity check, latency metrics | **Administration** |
| **DF-128B** | `Versioned Config` | Process 10.0 | D3: Config Store | new parameter set with a new `config_version` | **System Configuration** |
| **DF-129** | `Stored Locality Outcome` | D5: Locality Results | Process 1.0 | `VERIFIED` / `INCONCLUSIVE` / `CONFLICTING`, `valid_until` | **Coarse only** (A11) |
| **DF-130** | `Audit Events` | D1: Event Store | Process 10.0 | lifecycle events and audit entries for reports | **Internal Audit Trail** |
| **DF-131** | `Booking and Closing Events` | Process 9.0 | D1: Event Store | `request_accepted`, `request_declined`, `transaction_closed` | **Immutable Audit Log** |
| **DF-132** | `Held Status` | Process 1.0 | Borrower | `HELD_FOR_REVIEW` with plain-language reason (locality, engine failure) | **Borrower Notification** |

---

## 5. Diagram source and notation

- **File:** `dfd_assurance_pipeline_level0_level1.drawio` (page 1: level 0, page 2: level 1), generated by
  `generate_dfd.py` (layout-checked; do not edit by hand). The hand-drawn v1.1 is kept in `archive_v1/`.
- **Gane & Sarson notation:** dark square = external entity; rounded box = process with its number above a line;
  box open on the right with its ID in a left cell = data store; labelled arrow = data flow. The red process 1.0 marks
  the privacy boundary.

---

## 6. Verification Against Project Constraints

1. **Zero Spatial Leakage (A11 / FR-A-07 / NFR-PR-01):** Verified. No flow in this pipeline carries a location: DF-101 has none, Process 1.0 reads the member's stored coarse outcome, and DF-103 carries only `communityId`, the outcome and sanitised transaction details (`itemId`, `category`, `itemValue`, `dates`). The only device location in the system is read in memory during the membership check (UC-A3), outside this pipeline.
2. **Elimination of Direct Store-to-Entity Links (Gane & Sarson Compliance):** Verified. Every flow starts or ends at a process; the administrator reaches D3 only through process 10.0 (DF-128, DF-128B). Data Store `D4: Moderation Queue` is read only by Process 8.0 (`Dispatch Escalation & Moderator Alerts`), which presents the alert and interface to the `Community Moderator`.
3. **Information-Flow Completeness (No "Grey Holes"):** Verified. Flow DF-103 carries `category` and `durationDays` for Algorithm 1's similarity weighting, and `itemValue` / `valueBand` via DF-109B for Algorithm 4's Rule R4/R8 thresholds.
4. **Fraud Detection Ingestion Scope:** Verified. Flows DF-105 and DF-106 query confirmed outcomes, rating submissions, review texts and disputes in the 14-day window, providing Algorithm 3 with the inputs for reciprocal clusters ($S_1$), review similarity ($S_4$) and the retaliation check.
5. **DFD Balancing:** Verified. External entities match Level 0 (Borrower, Lender, Community Moderator, System Administrator). Admin's configuration tuning is modeled via DF-128 into process 10.0, which writes D3 (DF-128B); the lender's decision (DF-04) enters process 9.0. The full balancing list is in §3.1.
6. **Immutable Audit Versioning (NFR-D-01 / FR-B-09):** Verified. Output flow DF-121 explicitly records `config_version="1.1.0-iteration1-draft"` into the immutable `assessment_generated` event stream in D1.
