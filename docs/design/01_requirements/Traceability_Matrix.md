# Digital Mohalla: Traceability Matrix, Iteration 1 Core and Iteration 2 (v2.0)

| Field | Value |
|---|---|
| Document | Requirement → use case → design artefact → test, for everything iteration 1 builds (report chapter 4 "traceability matrix opened", chapter 7) |
| Owner | All three students (integration draft by Student 1) |
| Version | 2.0 draft, 9 November 2026 (DA-19, Student 3, drafted with Claude Code; review by Student 1 pending): section 4 traces all 60 committed FRs (35 CORE, 16 ENAB, 9 Module 4) from requirement to design, code, test and status; section 3 adds ES-07 to ES-12. v1.0, 11 October 2026 |
| Status | v1.0 opened at the design baseline. v2.0 opened for iteration 2; the Code and Status columns of section 4 are completed at the feature freeze from passing tests, not from this draft |
| Baseline | FR/NFR v1.3, Use Cases v1.3, ADR-0001 to ADR-0008, `14_testing/Test_Plan.md` v1.0 |

Folder abbreviations: UC = `02_use_case_model`, ARCH = `03_architecture`, DEP = `04_deployment`, CLS = `05_class_model`, DATA = `06_data_model`, SM = `07_state_machines`, SEQ = `08_sequence_diagrams`, ACT = `09_activity_diagrams`, DFD = `10_dfd`, ENG = `11_assurance_engine`, LOC = `12_locality`, WF = `13_wireframes`. T-ids are A3 transitions; TC-ids are test cases of the test plan.

## 1. Functional requirements

| FR | Use case | Design artefacts | Tests | Owner | Slice |
|---|---|---|---|---|---|
| FR-B-05 no double booking | B5, B6 | ADR-0001, ADR-0002; DATA `booking` EXCLUDE; SM T13, T17; SSD-B5; WF W4 | Suite 3; TC-08, TC-09 | S1 | A |
| FR-B-06 create request | B5 | SM T01; SEQ (a); SSD-B5; ARCH `POST /requests`; WF W1 | Suite 1; TC-01 | S1 | A |
| FR-B-07 locality, then assessment | B5 | SM T02–T08; SEQ (a); DFD L1 (process 1.0); LOC (A11, stored result); ACT decision policy | TC-03, TC-60; suite 10 | S1, S2 | A, B |
| FR-B-08 single lifecycle | B5–B8, B12 | SM (state machine, transition table); DATA `allowed_transition`; `_tools/lifecycle_model.py` | Suite 1 (`transition_test_matrix.csv`); TC-01 to TC-06 | S1 | A |
| FR-B-09 frozen event record, replay | all | ADR-0005; DATA `lifecycle_event`; SM §5 event catalogue; CLS LifecycleEvent | Suite 2; TC-07 | S1 | A |
| FR-B-10 accept, decline, expire | B6 | SM T13–T17; ARCH accept and decline endpoints; WF W3, W4 | Suite 1; TC-08 | S1 | A (expiry: it. 2) |
| FR-B-11 handover with dual confirmation | B7 | SM T18; DATA `condition_report`; SEQ (b); SSD-B7/B8; WF W5 | Suite 1; suite 13 | S1 | A |
| FR-B-12 no-show, condition dispute | B7 | SM T19 (it. 2), T23; WF W5 | It. 2 (scheduler) | S1 | it. 2 |
| FR-B-13 return and completion | B8 | SM T20–T22; SEQ (b); SSD-B7/B8; WF W6 | Suite 1; TC-07 | S1 | A |
| FR-B-15 outcome to the engine | B8 | ARCH `IOutcomeSink`; DATA `outcome`, `v_pending_outcomes`; SEQ (b) | Suite 13 (TC-53) | S1, S2 | B |
| FR-B-16 raise dispute | B12 | ADR-0004; SM T23; SEQ (c); ACT dispute resolution; SSD-B12; WF W7 | Suite 13; TC-05, TC-50 | S3 | C |
| FR-B-17 respond, withdraw | B12 | ADR-0004; SM T26; SEQ (c); ACT dispute resolution; WF W7 | TC-51, TC-52 | S3 | C |
| FR-T-01 one assurance state with evidence | D3/4/5 | ENG Algorithm doc §2, §6; DATA `assessment` (`assessment_rule_ck`); CLS AssessmentResult; WF W3 | Suites 9, 11; TC-35 | S2 | B |
| FR-T-02 Beta posterior, cold start | D3 | ENG Algorithm 1; config; fixtures ES-01 | Suite 6; TC-20 to TC-24, TC-31, TC-40 | S2 | B |
| FR-T-03 evidence weighting | D3 | ENG Algorithm 1; DATA `outcome` | Suite 6; TC-22, TC-23 | S2 | B |
| FR-T-04 bounded k-hop | D3 | ENG k-hop design, ADR-0006, ADR-0008, worked example; CLS indirect package | Suites 7, 8; TC-25 to TC-28, TC-46, TC-47 | S1 | B |
| FR-T-05 manipulation risk | D3 | ENG Algorithm 3; ADR-0007; config (S1, S4, retaliation) | Suites 9, 12; TC-30, TC-38, TC-43 | S2 | C |
| FR-T-06 decision policy, holds | D3, B5 | ENG Algorithm 4; ACT decision policy; ADR-0003, ADR-0007, ADR-0008; SM T05–T07 | Suite 9; TC-29 to TC-35 | S2 | B |
| FR-T-07 engine failure → hold | D3 | SM T08, T10; SEQ (a) timeout fragment; DFD DF-125; config timeout 2,000 ms | Suite 10; TC-36, TC-37, TC-55 | S2 | B |
| FR-T-08 factors, never one number | D2, B4 | WF W3, W9 (NFR-U-01 rule) | UI review; suite 11 explanations | S3 | B |
| FR-T-09 reviews and retaliation (seeded) | D1 | ENG retaliation check; DATA `review` | ES-05 (TC-44) | S2 | C |
| FR-T-10 escalation case | D6 | DATA `escalation_case`; SM escalation case C01–C11; ACT dispute resolution; WF W8 | Suite 13 | S3 | C |
| FR-T-11 moderator decisions | I4 | ADR-0003, ADR-0004; DATA `moderator_decision`; SM T09–T12, T25; SSD-I4; SEQ (c); WF W9 | Suite 13; TC-53 to TC-57 | S3 | C |
| FR-M-05 audit log | I6 | DATA `audit_log`, hash chains; WF W10 | Suite 5; TC-13, TC-14 | S3 (S1 storage) | C |
| FR-N-03 frozen event logging | all | DATA `lifecycle_event`; ADR-0005 | Suite 2 | S1 | A |
| FR-A-04 (part) login | A2 | ARCH IAuth; DATA `app_user` | UI smoke | S1 | A |
| FR-A-06 to A-11 locality and membership | A3, A4 | LOC (A11 design, `locality_rule.py`); DATA `locality_verification`, `invitation` | LOC 18/18 cases | S1 | design; build at D-11 gate |

## 2. Non-functional requirements measured in iteration 1

| NFR | Design artefacts | Tests |
|---|---|---|
| NFR-R-01 no double booking | ADR-0002; DATA EXCLUDE constraint | Suite 3 (TC-08) |
| NFR-R-02 invalid transitions rejected | SM transition table; DATA triggers | Suite 1 |
| NFR-R-03 replay | DATA `replay_state()` | Suite 2 (TC-07) |
| NFR-R-04 graceful degradation | SM T08; ARCH `v_pending_outcomes` catch-up | Suite 10 |
| NFR-P-03 assessment latency, k sweep | ENG complexity analysis | Suite 8 |
| NFR-P-04 transition commit P95 ≤ 500 ms | DATA (one transaction per command) | Suite 15 (TC-61) |
| NFR-S-01 hashed passwords, TLS | DATA `password_hash`; DEP proxy TLS | Config review |
| NFR-S-02, S-03 authorisation, community scope | DATA authorisation checks; WF W8 | Suite 4 (TC-10 to TC-12) |
| NFR-S-05 tamper-evident log | DATA hash chains | Suite 5 (TC-13, TC-14) |
| NFR-S-07 no identity numbers | DATA (no such column); WF rule 4 | Suite 14 (TC-58) |
| NFR-PR-01, PR-02 location privacy | LOC; DFD privacy boundary; D13; DEP §5 | Suite 14 (TC-58 to TC-60) |
| NFR-Q-01 7 of 13 scenarios | fixtures v1.1; `verify_fixtures.py` | Suite 11 (TC-40 to TC-47) |
| NFR-D-01 versioned config | config 1.1.0; `assessment.config_version` | Suite 9 (stored version); C04 of `verify_design.py` |
| NFR-D-03, D-04 rollback, automated tests | DEP §4; plan CI/CD | Suite 15 (TC-62) |
| NFR-U-01 evidence with every state | WF W0 rules, W3, W9 | UI review; suite 11 explanations |

## 3. Evaluation scenarios

| Scenario | Fixture | Expected (state / lifecycle / rule) | Tests | Demo |
|---|---|---|---|---|
| ES-01 new user | ES-01 | INSUFFICIENT_EVIDENCE / ASSESSED / R3 | TC-40 | 2.1 |
| ES-02 reliable | ES-02 | SUFFICIENT_EVIDENCE / ASSESSED / R7 | TC-41 | 2.3 |
| ES-03 recent resolved dispute | ES-03 | REVIEW_RECOMMENDED / ASSESSED / R6_DISPUTE | TC-42 | — |
| ES-04 colluding group | ES-04 | REVIEW_RECOMMENDED / HELD_FOR_REVIEW / R2 | TC-43 | 3 |
| ES-05 retaliatory review | ES-05 | SUFFICIENT_EVIDENCE / ASSESSED / R8 | TC-44 | — |
| ES-06 high value, weak evidence | ES-06 | REVIEW_RECOMMENDED / HELD_FOR_REVIEW / R4 | TC-45 | — |
| ES-13 community paths | ES-13 | REVIEW_RECOMMENDED / ASSESSED / R9 (without paths: INSUFFICIENT_EVIDENCE / R6_SPARSE) | TC-46, TC-47 | 2.2 |
| ES-07 conflicting condition reports | iteration 2 file | ACTIVE_DISPUTE / ASSESSED / R1; after resolution REVIEW_RECOMMENDED / R6_DISPUTE | TC-110, TC-111 | 2.4–2.6 |
| ES-08 failure to return | iteration 2 file | ACTIVE_DISPUTE / ASSESSED / R1; after resolution (LOST) REVIEW_RECOMMENDED / R6_DISPUTE | TC-112 | — |
| ES-09 location mismatch | iteration 2 file | none / HELD_FOR_REVIEW (`locality_conflict`); after clearing REVIEW_RECOMMENDED / R9 | TC-113 | — |
| ES-10 permission refusal | iteration 2 file | none / HELD_FOR_REVIEW (`locality_inconclusive`); after clearing INSUFFICIENT_EVIDENCE / R3 | TC-114 | — |
| ES-11 moderator reversal | iteration 2 file | REVIEW_RECOMMENDED / ASSESSED / R6_DISPUTE before and after (question Q2) | TC-115 | — |
| ES-12 old or sparse history | iteration 2 file | INSUFFICIENT_EVIDENCE / ASSESSED / R6_SPARSE | TC-116 | — |

Iteration 2 fixtures: `14_testing/scenario_fixtures_iteration2.json`, specified in `14_testing/Scenario_Specifications_ES07_ES12.md`. Final target 13 of 13 (TC-167).

## 4. Iteration 2: all committed FRs (v2.0)

Committed scope (iteration 2 plan, decision DM05 pending with the supervisor): 35 CORE, 16 ENAB and the 9 Module 4 FRs, 60 in all. **Status today** is the plan's reading of the code on 3 November (11 met, 29 built in iteration 2, 20 left for iteration 3), not a test count; it is recounted from passing tests at each gate. **Code** names where the requirement lives today, or "—" when nothing is built. Test IDs are from `14_testing/Test_Plan.md` v2.0.

Status key: **Met**, **Partial** (what exists), **It. 2** (built in iteration 2, slice in brackets), **It. 3** (deferred, recorded in the change record).

| FR | Scope | UC | Design | Code today | Tests | Owner | Status |
|---|---|---|---|---|---|---|---|
| FR-A-01 register | ENAB | A1 | DATA `app_user`; CLS S1 | — | to add (suite 17) | S1 | It. 2 (3); OTP in it. 3 |
| FR-A-02 OTP activation | ENAB | A1 | DATA `app_user.status` | — | — | S1 | It. 3 |
| FR-A-03 registration rate limit | ENAB | A1 | NFR-S-04 | — | — | S1 | It. 3 |
| FR-A-04 login, sessions | ENAB | A2 | ARCH IAuth | `backend/app/domain/accounts/auth.py`; `POST /auth/login` | UI smoke | S1 | Partial: login and token only; It. 3 |
| FR-A-05 deny suspended | ENAB | A2 | DATA `account_status` | guard G1 refuses requests from non-ACTIVE users | — | S1 | It. 3 |
| FR-A-06 list communities | CORE | A3 | UC-A3; SSD-A3 | — | Part E criterion | S1 | It. 2 (1) |
| FR-A-07 locality method | CORE | A3 | LOC A11; DATA `locality_verification`, `invitation`; SSD-A3; DFD 11.0 | stub: stored result read by `locality_outcome_for` | TC-119, TC-124 | S1 | It. 2 (1) |
| FR-A-08 three-valued outcome | CORE | A3 | LOC decision table; ACT membership decision | stub | TC-125, TC-126 | S1 | It. 2 (1) |
| FR-A-09 membership request | CORE | A3 | SM membership M01 to M09 (M09 open-join); DATA `membership_one_live_uq`, `community.join_policy` (v2.4) | seeded only | TC-127, TC-170, TC-171 | S1 | It. 2 (1) |
| FR-A-10 moderator queue | CORE | A4 | SM membership; ACT membership decision; SSD-A4 | — | TC-128, TC-129 | S1 | It. 2 (1) |
| FR-A-11 concurrent, reversed decisions | CORE | A4 | SM membership M07, M08 | — | TC-130 | S1 | It. 2 (1) |
| FR-A-12 profile edit | ENAB | A5, A6 | — | — | — | S1 | It. 3 |
| FR-A-13 no exact address | CORE | A5 | DATA R5 (no address columns); LOC | no address column exists | Part E criterion | S1 | It. 3 (profile editing) |
| FR-A-14 block user | ENAB | A7 | DATA `user_block` | guard in request creation | — | S1 | It. 3 |
| FR-B-01 create listing | ENAB | B1 | DATA `item` (+ description, condition in DA-23) | seeded only | to add | S1 | It. 2 (1) |
| FR-B-02 restricted categories | CORE | B1, B5 | DATA `item.required_verification`, guard G1 | guard G1 in the schema | Part E criterion; test to add (F7) | S1 | It. 2 (3) |
| FR-B-03 listing moderation | ENAB | B1 | — | — | — | S1 | It. 3 |
| FR-B-04 availability calendar | ENAB | B2 | ADR-0002; DATA `booking` | bookings only | — | S1 | It. 3 |
| FR-B-05 no double booking | CORE | B5, B6 | ADR-0001, ADR-0002; DATA EXCLUDE | `service.py` `accept`; schema EXCLUDE | Suite 3; TC-08, TC-09 | S1 | Met |
| FR-B-06 create request | CORE | B5 | SM T01; SEQ (a) | `service.py` `create_request` | TC-01, TC-70 | S1, S2 | Partial: lender not notified; It. 2 (2) |
| FR-B-07 locality then assessment | CORE | B5 | SM T02 to T08; SEQ (a); DFD 1.0 | `service.py` `_locality_and_assessment` (stub locality) | TC-03, TC-60, TC-113, TC-114 | S1 | It. 2 (1) |
| FR-B-08 single lifecycle | CORE | B5 to B8, B12 | SM; `07_state_machines/transition_table.md` | `backend/app/domain/lifecycle/transition_table.py`, `aggregate.py` | Suite 1; TC-01 to TC-06, TC-117 | S1 | Met (regenerated for ADR-0009) |
| FR-B-09 frozen event record | CORE | all | ADR-0005; DATA `lifecycle_event` | `backend/app/infra/eventstore/postgres.py` | Suite 2; TC-07 | S1 | Met |
| FR-B-10 accept, decline, counter, expire | CORE | B6 | SM T13 to T17 | `service.py` `accept`, `decline` | TC-08, TC-120 | S1 | Partial: no counter-offer or expiry; It. 2 (2) |
| FR-B-11 handover, photos | CORE | B7 | SM T18; ADR-0014; CLS S3 uploads | checklist only (D20) | TC-150 to TC-153 | S3 | It. 2 (2) |
| FR-B-12 no-show | CORE | B7 | SM T19; ADR-0012 | — | TC-122 | S1 | It. 2 (2) |
| FR-B-13 return and completion | CORE | B8 | SM T20 to T22; SEQ (b) | `service.py` `initiate_return`, `confirm_return` | Suite 16 | S1 | Met |
| FR-B-14 extension, overdue dispute | CORE | B8, B13 | SM T24, I01 to I06; ADR-0012 | — | TC-123 | S1 | It. 2 (2) |
| FR-B-15 outcome, reviews unlock | CORE | B8 | DATA `outcome`; D11 | `backend/app/infra/db/outcomes.py` | TC-53, TC-69, TC-133 | S2 | Partial: reviews do not unlock; It. 2 (2) |
| FR-B-16 raise dispute | CORE | B12 | ADR-0004; SM T23; SEQ (c) | `service.py` `raise_dispute` | TC-05, TC-50 | S3 | Met |
| FR-B-17 respond, no response, withdraw | CORE | B12 | ADR-0004; SM C02 to C04; SEQ (g) | `service.py` `withdraw_dispute` | TC-51, TC-52 | S3 | Partial: withdraw only; It. 2 (1) |
| FR-B-18 scheduled jobs | CORE | B13 | ADR-0012; DEP v1.1 cron | — | TC-120, TC-121 | S1 | It. 2 (2) |
| FR-T-01 one state with evidence | CORE | D3/4/5 | ENG §2, §6 | `backend/app/domain/assurance/engine.py` | Suites 9, 11 | S2 | Met |
| FR-T-02 Beta posterior | CORE | D3 | ENG Algorithm 1 | `estimation/posterior.py` | Suite 6 | S2 | Met |
| FR-T-03 evidence weighting | CORE | D3 | ENG Algorithm 1; D17 | `estimation/posterior.py`, `similarity.py` | Suite 6 | S2 | Met |
| FR-T-04 bounded k-hop | CORE | D3 | ENG k-hop; ADR-0006, ADR-0008 | `indirect/khop.py`, `edges.py` | Suite 7; TC-46, TC-47 | S1, S2 | Met |
| FR-T-05 manipulation risk | CORE | D3 | ENG Algorithm 3; ADR-0007 | `detection/manipulation.py` (S1, S4, retaliation) | Suites 12, 25 | S2 | Partial; It. 2 (2) |
| FR-T-06 decision policy | CORE | D3, B5 | ENG Algorithm 4; ACT decision policy (and proposed ADR-0010 variant) | `policy/decision.py` | Suite 9 | S2 | Partial: borrower role only, DM09 open; It. 2 (3) |
| FR-T-07 engine failure hold | CORE | D3 | SM T08, T10 | `service.py` `_assess` | Suite 10 | S2 | Met |
| FR-T-08 factors, never one number | CORE | D2, B4 | UC-D2; WF W3, W9 | `backend/app/api/evidence.py` (lender view) | TC-100; suite 11 | S2 | Partial: lender view only; It. 2 (3) |
| FR-T-09 reviews | CORE | D1 | UC-D1; SSD-D1; DATA `review` | seeded reviews; retaliation check in `manipulation.py` | TC-133 to TC-136 | S2 | It. 2 (2) |
| FR-T-10 escalation case | CORE | D6 | SM escalation case v3.0; DATA `escalation_case` | cases opened with holds and disputes; moderator queue `GET /moderation/cases` | Suite 13 | S3 | Partial: needs notifications; It. 3 |
| FR-T-11 decisions, appeal, reversal | CORE | I4 | SM C02 to C11; SEQ (g), (h); ADR-0009; CLS S3 v2.0; ACT dispute resolution v1.1 | `backend/app/domain/moderation/decisions.py` (decisions only) | TC-53 to TC-57, TC-140 to TC-149 | S3 | Partial: decisions only; It. 2 (2) |
| FR-T-12 report | ENAB | D7 | — | — | — | S3 | It. 3 |
| FR-M-01 admin users | ENAB | I1 | — | — | — | S3 | It. 3 |
| FR-M-02 admin categories | ENAB | I2 | — | — | — | S3 | It. 3 |
| FR-M-03 report queue | ENAB | I3 | — | — | — | S3 | It. 3 |
| FR-M-05 audit log | CORE | I6 | UC-I6 v1.4; DATA `audit_log`; CLS S3 v2.0 | table and hash chain in the schema; no API or screen | Suites 5, 29; TC-154 to TC-158 | S3 | Partial; It. 2 (3) |
| FR-C-01 chat | ENAB | G1 | — | — | — | S2 | It. 3 |
| FR-C-02 notifications | ENAB | G3 | ADR-0013 | — | Suite 23 | S2 | It. 3 (in-app part built in it. 2 for other FRs) |
| FR-N-03 evaluation events | CORE | all | ADR-0005 | event store | TC-72 | S1 | Met |
| FR-S-01 hybrid retrieval and ranking | M4 | B3 | UC-B3; SEQ (i); ADR-0016; DA-22 | — (app-side substring filter) | TC-159, TC-161, TC-162 | S2 | It. 2 (3) |
| FR-S-02 fallbacks | M4 | B3 | SEQ (i) `alt` fragments | — | TC-160 | S1, S2 | It. 2 (2) |
| FR-S-03 filters and sorts | M4 | B3 | UC-B3 step 5; FR/NFR v1.4 changes S1 to S3 | value-band chips in the app | TC-163 | S1 | It. 2 (2) |
| FR-S-04 lender evidence on item | M4 | B4 | UC-B4 | `GET /items/{item_id}` without lender evidence | TC-161, TC-162 | S2 | It. 2 (3) |
| FR-S-05 search log | M4 | B3 | SEQ (i) step 3; CLS S3 SearchLogger; DA-23 | — | TC-165 | S3 | It. 2 (2) |
| FR-S-06 item request | M4 | B9 | — | — | — | S2 | It. 3 |
| FR-S-07 fair matching | M4 | B10 | — | — | — | S2 | It. 3 (issue I-7) |
| FR-S-08 fairness report | M4 | B10 | — | — | — | S2 | It. 3 |
| FR-S-09 saved searches | M4 | B11 | — | — | — | S2 | It. 3 |

**Counts.** Met 11; It. 2 29 (Partial today: 9 of them); It. 3 20. Reaching all 29 gives 40 of 60 (67%) against the 60% floor (36), the plan's target.

**Owners in section 4** follow the iteration 2 plan (decision D21 proposed: Module 7 to Student 2; Module 4 split S1 retrieval and filters, S2 meaning-based search and ranking, S3 logging and evaluation).
