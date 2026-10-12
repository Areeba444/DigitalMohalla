# Digital Mohalla: Traceability Matrix, Iteration 1 Core

| Field | Value |
|---|---|
| Document | Requirement → use case → design artefact → test, for everything iteration 1 builds (report chapter 4 "traceability matrix opened", chapter 7) |
| Owner | All three students (integration draft by Student 1) |
| Version | 1.0, 11 October 2026 |
| Status | Opened at the design baseline; the "Code" column is filled during Part B |
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
| ES-07 to ES-12 | — | Iteration 2 (final target 13 of 13) | — | 2.4–2.6 use ES-07-like data |
