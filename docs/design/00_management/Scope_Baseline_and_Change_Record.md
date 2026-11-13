# Scope Baseline and Change Record, Iteration 2 (DA-01)

| Field | Value |
|---|---|
| Owner | Fatima Khursheed (Student 1); reviewed by Minahil Kashif |
| Version | 1.0 draft, 3 November 2026 |
| Status | Draft for the supervisor, Dr. Ali Zeeshan. Each change below takes effect only when the approver column is signed (handbook C.5.3) |
| Answers | Review items DM04 (calendar) and DM05 (no approval trail for scope changes); handbook Step 5 and Form 4 (at least 60% of committed scope at FYP-1 Final) |
| Plan | Iteration 2 plan (Claude Doc): https://claude.ai/artifact/47uvQtEp8ypwKEjfh1yFpL |
| GenAI | Drafted with Claude (Claude Code); reviewed by the owner |

## 1. Committed scope and the 60% measure

The handbook requires at least 60% of committed scope at FYP-1 Final but does not say how to count it. This project counts functional requirements whose acceptance criteria pass in tests, the method of the module roadmap.

| Group | FRs | In the committed denominator |
|---|---|---|
| CORE (committed core: Modules 1, 3, 5, 9, 10) | 35 | Yes |
| ENAB (needed for the core to run) | 16 | Yes |
| Module 4 Search & Discovery, FR-S-01 to S-09 (added by the supervisor) | 9 | Yes |
| Other SUPP (FR-M-04, FR-C-03, FR-N-01, FR-N-02) | 4 | No, supporting |
| STRC (Modules 2, 6, 8 and stretch parts of others) | 16 | No, stretch |
| **Committed total** | **60** | 60% = 36 FRs |

| Status at FYP-1 Final (planned) | Count | FRs |
|---|---|---|
| Met in iteration 1 | 11 | B-05, B-08, B-09, B-13, B-16, T-01, T-02, T-03, T-04, T-07, N-03 |
| Met in iteration 2 | 29 | A-01, A-06 to A-11, B-01, B-02, B-06, B-07, B-10, B-11, B-12, B-14, B-15, B-17, B-18, T-05, T-06, T-08, T-09, T-11, M-05, S-01 to S-05 |
| **Total met** | **40 of 60 (67%)** | floor 36; cut order in the plan |
| Iteration 3 | 20 | A-02 to A-05, A-12 to A-14, B-03, B-04, T-10, T-12, M-01 to M-03, C-01, C-02, S-06 to S-09 |

The count is recomputed from passing tests at the Slice 2 gate and at the freeze, and the report states the method.

## 2. Change record

Each row is one recorded change: what, why, the evidence that prompted it, what it affects, and who approves it.

| ID | Change | Why | Evidence | Affects | Approver |
|---|---|---|---|---|---|
| CR-01 | Module 4 Search & Discovery moves from iteration 3 to iteration 2: FR-S-01 to S-05 now; S-06 to S-09 in iteration 3 | Supervisor's request; the review found that proposal §8.1 still lists search and matching (DM05) | Supervisor meeting, early November 2026 | Plan, scope count, design DA-20 to DA-25 | Supervisor |
| CR-02 | Search technology: PostgreSQL full-text plus pgvector exact search and a small embedding model, instead of the overview's BERT-768 and FAISS | Free-tier memory, one store to keep consistent, filters inside retrieval (I-5) | ADR-0016 | Overview §4, FR-S-01, Form 13 | Supervisor |
| CR-03 | Hosting: Render and Neon instead of one AWS host; NFR-D-03 reworded | As built in iteration 1; no server administration needed | ADR-0011; mid report §3.6 | NFR-D-03, deployment diagram | Supervisor |
| CR-04 | Client platforms: Android and web; iOS not targeted; NFR-D-05 reworded | No iOS device or developer account; team decision of 13 October | Team decisions 2026-10-13 | NFR-D-05 | Supervisor |
| CR-05 | FR-S-01 and S-03: "distance" and "radius" become same community; "price" becomes deposit; the transaction-type filter waits for donation listings | The system stores no coordinates (NFR-PR-01); lending has no price; only lending exists | Architecture_Design_v2.md §4; schema v2.4 | FR-S-01, FR-S-03 (FR/NFR v1.4) | Supervisor |
| CR-06 | FR-B-10's clause "opens a chat thread" moves to FR-C-01 (G1, iteration 3) | Chat is a separate module; keeping the clause would block FR-B-10 for a feature of another iteration | FR/NFR v1.3 FR-B-10 | FR-B-10, FR-C-01 | Supervisor |
| CR-07 | Registration (A1) built in iteration 2 without the OTP step of A9 (FR-A-02 stays in iteration 3) | A new user is needed to demonstrate joining a community; OTP needs an e-mail or SMS provider | UC-A1 v1.4 *a | FR-A-01, FR-A-02 | Supervisor |
| CR-08 | Ownership (team decision D21): Module 7 and the apps lead to Areeba; Module 4 split (keyword: Fatima; meaning-based and ranking: Areeba; logging and evaluation: Minahil); uploads and the operations rehearsal to Minahil; design artefacts DA-08, DA-13, DA-14 to Minahil | Share Fatima's load (DM10); keep the evaluator of search apart from its authors | Review DM10; plan | Individual assessment (Form 11) | All three, supervisor |
| CR-09 | Learning-to-rank (overview §4 Tiers 2 and 3) and fair matching (B10) stay in FYP-2 | Both need data or algorithms beyond iteration 2's time: pilot click logs for LTR; Hungarian matching with fairness (issue I-7 open) | Overview §4 | FR-S-07, S-08; overview Tier 2, 3 | Supervisor |
| CR-10 | Lifecycle v3: three event types added and dispute closure by item possession | FR-B-10 counter-offer; DM14 defect | ADR-0009, ADR-0015 | Frozen event schema (FR-B-09) | All three |

## 3. Revised timeline (DM04)

Iteration 2 dates assume semester week 1 was 24 August 2026; the coordinators confirm the real dates.

| Period | Iteration | Gate |
|---|---|---|
| 2 to 10 November 2026 | 2: design artefacts and UI track | Design gate 10 November |
| 11 to 27 November 2026 | 2: three build slices | Slice gates 16 and 22 November; poster 20 November; freeze 27 November |
| Week of 30 November 2026 | FYP-1 Final (assumed) | Panel demo and report |
| January to early March 2027 | 3: full integration, accounts, chat, admin tools, attack generator, preliminary comparison | FYP-2 Mid, week 8 |
| March to mid-April 2027 | 4: evaluation, pilot, no new scope | Report draft by mid-April |
| By May 2027 | FYP-2 Final | Inside the supervisory window the review cites (FYP-2 January to mid-April, complete by May) |

The mid report's Table 9.2, which runs iteration 2 to January and iteration 4 to June, is superseded by this table.
