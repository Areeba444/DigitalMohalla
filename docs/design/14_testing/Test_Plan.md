# Digital Mohalla: Test Plan, Iteration 1 (design step A13)

| Field | Value |
|---|---|
| Document | Design step A13: test plan for iteration 1 (FYP-1 Mid), with test cases in input / expected / actual form |
| Owner | Student 3 (A13, plan work division); suites are owned as in the plan's "Tests owned" row (§4). Drafted during integration by Student 1; **Student 3 to review** (A14). Report chapter 7 lead: Student 1 |
| Version | 1.0, 11 October 2026 |
| Status | Baseline for Part B. Design-time checks have run (§8); implementation tests run from Slice A onwards |
| Baseline | Iteration 1 plan ("Test plan for iteration 1", CI/CD), FR/NFR v1.3 (Part B verification column, Part E acceptance criteria), Use Cases v1.3, A3 transition table, ADR-0001 to ADR-0008, fixtures v1.1, `04_deployment/Deployment_Design.md` |
| Files | this plan; `transition_test_matrix.csv` (suite 1 oracle, generated); `scenario_fixtures_iteration1.json` (suites 6, 7, 9, 11, 12); `verify_fixtures.py` and `fixture_verification_results.md` (oracle and its results); `verify_design.py` (design consistency checks) |
| Author note | Drafted with Claude (GenAI); to be disclosed on Form 13 and in the AI usage log. |

## 1. Purpose and scope

The plan tests the iteration-1 core: the request-to-return loop (Module 3), the assessment engine (Module 5), dispute and hold resolution (Module 9), the scenario suite (Module 10) and minimal accounts (Module 1, login only). Locality is tested at design level (`12_locality/`, 18/18 cases). The method is tested as code only if the D-11 gate builds it.

**Out of scope for iteration 1** (scope table of the plan): scheduler jobs (expiry, no-show, reminders, overdue disputes: T15, T19, T24, I01 to I06), extensions, counter-offers, appeals and reversals, notifications beyond the stub, search, chat, reviews other than the seeded ones, and the evaluation datasets. Test cases for these are marked "It. 2" and are not run.

**Items under test:** the backend (FastAPI, `backend/`), the schema (`06_data_model/schema.sql` v2.3), the engine configuration (`11_assurance_engine/Assurance_Engine_Config_Draft.json`, 1.1.0-iteration1-draft), the resident app and moderator console (`13_wireframes/`), and the deployed instance (`04_deployment/`).

## 2. Strategy

1. **The design is the oracle.** Every expected result comes from a baselined artefact: the A3 transition table (suite 1), the A5 decision table and fixtures (suites 6, 7, 9, 11, 12), the ADRs, and the FR acceptance criteria (FR/NFR Part E). No expected value is invented in test code.
2. **Push checks down.** Rules the database can enforce (transition table, overlap constraint, append-only log, decision-table consistency) are tested at the database level and again through the API. The domain layer (transition table, replay, engine mathematics, policy) does no I/O, so it is unit-tested without a database (A8 layer rules).
3. **Failure and edge cases first-class.** Every suite has at least one negative case. The demo shows one failure per presenter (plan, demo script).
4. **Everything in CI.** Suites 1 to 7 and 9 to 14 run on every PR (`ci.yml`). A red check blocks the merge (NFR-D-04). Suite 8 and the performance part of suite 15 run on demand and at the freeze, with the config version and raw output saved.
5. **Separation of duties.** The scenario fixtures are for correctness only. The future held-out attack generator lives in a separate package, written by someone other than the detector's author (Student 3, Module 10).

## 3. Test levels, techniques and environment

| Level | What | Technique | Tooling | Environment |
|---|---|---|---|---|
| Unit | Domain classes: transition table, aggregate and replay, Beta posterior, k-hop search, manipulation score, decision policy | State-transition testing, boundary values, decision tables, known-value tests | pytest (+ coverage, floor 80% on engine and lifecycle packages) | CI runner, no database |
| Integration | API + PostgreSQL: lifecycle, concurrency, authorisation, append-only log, disputes and holds, privacy | Use-case paths, concurrency harness, negative and tamper tests, decision table by actor | pytest + httpx, Postgres 16 service container with `btree_gist` | CI runner |
| Acceptance | Scenario suite ES-01 to ES-06 and ES-13 | Fixture-driven; state **and** explanation must match | pytest, `scenario_fixtures_iteration1.json` | CI runner |
| Performance | k sweep (k = 1 to 4), transition commit latency | Benchmark, load test | pytest-benchmark or a script; k6 or Locust for load | CI on demand; deployed instance at freeze |
| System | Full loop on the deployed instance, smoke test | End-to-end run, deployed smoke | `cd.yml` smoke step; scripted run | AWS host (`04_deployment/`) |
| UI | Click-through of the loop, evidence shown with every state | Smoke, review against NFR-U-01 | Playwright or manual checklist (stack decided at D-15) | CI (smoke), deployed (review) |
| Static | Lint, types, security | ruff, eslint, mypy, bandit, pip-audit | `ci.yml` | CI runner |

**Test data.** Synthetic users only, flagged `is_synthetic` and shown as synthetic. Seeded by a seed script and reset with the seed-reset script. The fixtures carry their own inputs. No real personal data, location or identity documents are used (NFR-PR-01, NFR-PR-05, NFR-S-07).

## 4. Suites (plan "Test plan for iteration 1", extended with owners and gates)

| # | Suite | Level | Technique | Pass condition | Traces to | Owner | Slice / gate |
|---|---|---|---|---|---|---|---|
| 1 | Transition matrix | Unit + integration | State-transition testing over all 294 (state, event) pairs of `transition_test_matrix.csv` | 31 valid pairs (34 triples) pass with their guard satisfied; all 263 other pairs are rejected with 409 and an audit entry | FR-B-08, NFR-R-02 | S1 | A / D-11 |
| 2 | Replay | Integration | Rebuild each test stream in `stream_seq` order | Rebuilt state equals the projection for every test transaction | FR-B-09, NFR-R-03 | S1 | A / D-11 |
| 3 | Double booking | Integration | N parallel acceptances for overlapping dates, repeated | Exactly one commits, every run; the others end DECLINED "dates taken" | FR-B-05, NFR-R-01, ADR-0002 | S1 | A / D-11 |
| 4 | Authorisation | Integration | Decision table by actor and role over every command | Only permitted actors transition; a moderator acts only in their community; every refusal is 403 and logged | NFR-S-02, NFR-S-03 | S1 | A / D-11 |
| 5 | Append-only log | Integration | Negative and tamper tests | UPDATE and DELETE fail; an edit made with triggers disabled is detected by the hash chain | FR-M-05, NFR-S-05 | S1 | A / D-11 |
| 6 | Beta posterior | Unit | Known values and boundaries | Zero history gives Beta(1,1); 18 and 2 give Beta(19,3); weights about 0.96 and 0.25 at 10 and 360 days; the interval narrows with evidence; fixture intervals match | FR-T-02, FR-T-03 | S2 | B / D-8 |
| 7 | k-hop propagation | Unit | Hand-worked graphs (A5 example, ES-13) | Expected paths, decay, one path per first hop, noisy-OR, ρ ≤ 0.6, nothing beyond k, cycles safe | FR-T-04, ADR-0006 | S1 | B / D-8 |
| 8 | k sweep | Performance | Benchmark at k = 1 to 4, seeded scale | Latency and coverage reported with the config version (not gated, NFR-P-03) | NFR-P-03 | S1 | B |
| 9 | Policy rules | Unit | Decision table (Algorithm doc §6) with the policy unit fixtures | Rule order R1 … R9 holds; an open dispute first; indirect evidence alone never gives SUFFICIENT; corroborated level 4 holds, an uncorroborated score ≥ 60 does not; no restriction without a human | FR-T-06, ADR-0007, ADR-0008 | S2 | B / D-8 |
| 10 | Engine failure | Integration | Fault injection (timeout above 2,000 ms, exception) | HELD_FOR_REVIEW with `engine_failure`, failure logged, no assessment row, no assurance state | FR-T-07, NFR-R-04 | S2 | B / D-8 |
| 11 | Scenarios ES-01 to ES-06, ES-13 | Acceptance | Synthetic fixtures | State, rule, lifecycle state and explanation all match; 7 of 7 at Mid-1 | NFR-Q-01 | S3 (S2 fixtures) | B, C / D-8, D-5 |
| 12 | Dense legitimate group | Unit | Negative test | A family-style reciprocal group (fixture PU-02) stays below the moderator-review threshold | FR-T-05 guard, ADR-0007 | S2 | C / D-5 |
| 13 | Dispute and hold resolution | Integration | Use-case paths (UC-B12, D6, I4) | A dispute closes via `dispute_resolved` and the outcome counts; a withdrawal restores the previous state; each hold ends cleared, with safeguards, or declined, as its hold reason allows | FR-B-16, FR-B-17, FR-T-10, FR-T-11, ADR-0003, ADR-0004 | S3 | C / D-5 |
| 14 | Privacy | Integration | Negative test over the API and logs | No response or log line contains an address, coordinates or a CNIC field; uploads keep no location metadata | NFR-PR-01, NFR-PR-02, NFR-S-07 | S1 | C / D-5 |
| 15 | Transition latency and deployed smoke | Performance, system | Load test and end-to-end run | P95 of transition commits recorded (target ≤ 500 ms); the full loop passes on the deployed instance | NFR-P-04, NFR-D-04 | S3 (S1 latency) | Freeze |

## 5. Entry, exit and suspension criteria

| Gate | Entry | Exit (pass) |
|---|---|---|
| Every PR | Builds; lint and type checks clean | All CI suites green; review by a member who did not write the change |
| D-11 (Slice A) | Lifecycle on stubs deployed | Suites 1 to 5 green on CI; the loop runs on the deployed instance |
| D-8 (Slice B) | Engine integrated | Suites 6, 7, 9, 10 green; ES-01, ES-02, ES-03, ES-06 and ES-13 pass with state and explanation |
| D-5 (feature freeze) | Human loop integrated | Suites 12 to 14 green; ES-04 and ES-05 pass; tag `v0.1.0-rc1` |
| Freeze (D-5 to D-0) | rc1 deployed | Suite 15 run on the deployed instance; defect log has no open severity-1 or severity-2 defect; tag `v0.1.0-mid1` |

Testing of a slice is suspended when the deployed smoke test fails. It resumes after the rollback (`04_deployment/Deployment_Design.md` §4).

## 6. Test cases (input / expected / actual)

"Actual" records the latest result. "Design-verified" means the expected behaviour is already enforced and tested at the database or oracle level (§8). The implementation test still has to be written in Part B. "Not run" means the code does not exist yet.

### 6.1 Lifecycle and data integrity (suites 1 to 5)

| ID | Suite | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|---|
| TC-01 | 1 | Each of the 294 rows of `transition_test_matrix.csv`, issued as a command | VALID rows succeed when their guard holds; REJECT rows return 409, append no event and write an audit entry with the reason | Design-verified (schema: 34-row model check, CSV check, invalid-transition checks) | FR-B-08, NFR-R-02 |
| TC-02 | 1 | A booking in COMPLETED; the lender sends `request_accepted` | 409 "invalid transition"; audit entry REJECTED | Design-verified | FR-B-08 AC |
| TC-03 | 1 | A request held with `locality_inconclusive`; a moderator clears it | Next state LOCALITY_CHECKED, never ASSESSED (T09) | Design-verified | FR-B-08 AC, ADR-0003 |
| TC-04 | 1 | A request held with `manipulation_risk`; a moderator clears it to LOCALITY_CHECKED | Refused; only ASSESSED is allowed (T11) | Design-verified | ADR-0003 |
| TC-05 | 1 | A booking in RETURNED; a party opens a dispute | Refused (decision D4) | Design-verified | FR-B-16 |
| TC-06 | 1 | A command carrying a stale `stream_seq` | 409 stale; nothing appended | Design-verified | ADR-0002 |
| TC-07 | 2 | A transaction driven through the happy path (8 events) | `replay_state()` equals the projection; `request_created` carries the item and dates | Design-verified | FR-B-09 AC, NFR-R-03 |
| TC-08 | 3 | Two ASSESSED requests for overlapping dates; both lenders accept at once (3 connections × 5 rounds) | Exactly one ACCEPTED each round; the other DECLINED "dates taken" | Design-verified (race test) | FR-B-05 AC, NFR-R-01 |
| TC-09 | 3 | Two overlapping pending requests | Both are created (soft hold); accepting one declines the other | Design-verified | ADR-0001 |
| TC-10 | 4 | A lender who does not own the item tries to accept | 403, logged | Design-verified (impersonation check) | NFR-S-02 |
| TC-11 | 4 | A moderator of another community decides a case | 403, logged | Design-verified | NFR-S-03 |
| TC-12 | 4 | A party to the loan tries to decide its case as moderator | Refused | Design-verified | FR-T-11 |
| TC-13 | 5 | `UPDATE` or `DELETE` on `lifecycle_event` and on `audit_log` as the application role | Refused | Design-verified | NFR-S-05 |
| TC-14 | 5 | An event edited with the triggers disabled | `verify_event_chain()` reports the stream as tampered | Design-verified | FR-M-05 AC |

### 6.2 Assurance engine (suites 6 to 12)

| ID | Suite | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|---|
| TC-20 | 6 | No outcomes | Beta(1,1), mean 0.5, 90% CI [0.05, 0.95] | Oracle-verified (ES-01) | FR-T-02 AC |
| TC-21 | 6 | 18 successes and 2 failures, all today | Beta(19,3), mean 0.864 | Not run | FR-T-02 |
| TC-22 | 6 | One success 10 days ago, one 360 days ago, half-life 180 days | Weights 0.962 and 0.25 | Not run | FR-T-03 AC |
| TC-23 | 6 | A disputed outcome and an unconfirmed one | Both ignored until resolved | Not run | FR-T-03 |
| TC-24 | 6 | Fixture intervals ES-02 to ES-06 | Lower and upper 90% bounds equal the Beta quantiles (e.g. ES-02 [0.752, 0.995]) | Oracle-verified (13/13) | FR-T-02 |
| TC-25 | 7 | The A5 hand-worked 8-node graph at k = 3 | 3 selected paths (q = 0.54, 0.2195, 0.21), I = 0.7164, ρ = 0.6 (capped) | Verified by `generate_khop_example.py` | FR-T-04 AC |
| TC-26 | 7 | Same graph, k = 1 to 4 | ρ = 0, 0.424, 0.600, 0.600; nothing beyond k | Verified by `generate_khop_example.py` | FR-T-04 |
| TC-27 | 7 | ES-13 edges derived from outcomes (ADR-0006) | Edge weights 0.801, 0.777, 0.658, 0.648; paths q = 0.369, 0.352; I = 0.591; ρ = 0.394 | Oracle-verified | FR-T-04, ADR-0006 |
| TC-28 | 7 | A graph with a cycle and a self-loop | Search terminates; no path repeats a node | Not run | FR-T-04 |
| TC-29 | 9 | Fixture PU-03: open dispute and a strong history | R1, ACTIVE_DISPUTE, ASSESSED (not held) | Oracle-verified; DB check | D12 |
| TC-30 | 9 | Fixture PU-01: S1 = 1.0, S4 = 0.2 (score 68) | Level 3, R5, REVIEW_RECOMMENDED, not held | Oracle-verified; DB check | ADR-0007, FR-T-06 AC |
| TC-31 | 9 | Fixture PU-04: no history, high-value item | R3, INSUFFICIENT_EVIDENCE, not held | Oracle-verified | FR-T-02 |
| TC-32 | 9 | Fixture PU-05: sparse old history, no paths | R6_SPARSE, INSUFFICIENT_EVIDENCE | Oracle-verified | ADR-0008 |
| TC-33 | 9 | Fixture PU-06: strong history, medium value, risk level 2 | R8, SUFFICIENT_EVIDENCE with safeguards | Oracle-verified | FR-T-06 |
| TC-34 | 9 | Any input where only indirect evidence is strong | Never SUFFICIENT_EVIDENCE (R7 and R8 need n_eff ≥ 3 from direct evidence) | Not run (property test) | FR-T-04, Overview §5.11 |
| TC-35 | 9 | An assessment row whose rule, state, decision or hold reason disagree | Refused by `assessment_rule_ck` | Design-verified | FR-T-06 |
| TC-36 | 10 | Engine stub sleeps 2,500 ms | HELD_FOR_REVIEW `engine_failure`; failure logged; no assessment row | Design-verified (DB path); not run (timeout) | FR-T-07 AC |
| TC-37 | 10 | Engine raises an exception | As TC-36 | Not run | FR-T-07, NFR-R-04 |
| TC-38 | 12 | Fixture PU-02: family group, S1 = 0.83, S4 = 0.10 | Score 53.8, level 3; not held | Oracle-verified | ADR-0007 |

### 6.3 Scenario suite (suite 11, NFR-Q-01)

Each scenario passes only if the assurance state, the rule, the lifecycle state **and** the explanation match. The explanation check asserts the listed facts, not the exact wording.

| ID | Scenario | Expected state / lifecycle | Rule | Explanation must contain | Actual |
|---|---|---|---|---|---|
| TC-40 | ES-01 new user | INSUFFICIENT_EVIDENCE / ASSESSED | R3 | "Insufficient verified history; lender review required"; wide interval; no negative wording | Oracle-verified |
| TC-41 | ES-02 reliable | SUFFICIENT_EVIDENCE / ASSESSED | R7 | 90% CI [0.752, 0.995]; effective evidence 9.5 | Oracle-verified |
| TC-42 | ES-03 recent resolved dispute | REVIEW_RECOMMENDED / ASSESSED | R6_DISPUTE | the resolved dispute; safeguards | Oracle-verified |
| TC-43 | ES-04 colluding group | REVIEW_RECOMMENDED / HELD_FOR_REVIEW (`manipulation_risk`) | R2 | both signals with evidence (S1 = 1.0, S4 = 0.92), score 96.8, "not proof"; case opened | Oracle-verified |
| TC-44 | ES-05 retaliatory review | SUFFICIENT_EVIDENCE / ASSESSED | R8 | the review flagged as suspected retaliation and down-weighted | Oracle-verified |
| TC-45 | ES-06 high value, weak evidence | REVIEW_RECOMMENDED / HELD_FOR_REVIEW (`high_value_low_confidence`) | R4 | similarity 0.25; lower bound 0.30 | Oracle-verified |
| TC-46 | ES-13 community paths | REVIEW_RECOMMENDED / ASSESSED | R9 | both paths with weights; ρ 0.39; "without these paths: INSUFFICIENT_EVIDENCE" | Oracle-verified |
| TC-47 | ES-13 counterfactual (no paths) | INSUFFICIENT_EVIDENCE / ASSESSED | R6_SPARSE | sparse history, no community support | Oracle-verified |

### 6.4 Human loop, privacy and system (suites 13 to 15)

| ID | Suite | Input / precondition | Expected | Actual | Traces |
|---|---|---|---|---|---|
| TC-50 | 13 | An ACTIVE loan; the lender raises a dispute with photos | DISPUTED; `previous_state` stored; case opened; deposit record frozen | Design-verified | FR-B-16 AC |
| TC-51 | 13 | An open dispute; the raising party withdraws | Previous state restored (`dispute_withdrawn`); case WITHDRAWN | Design-verified | FR-B-17 AC |
| TC-52 | 13 | An open dispute; the other party tries to withdraw | Refused | Design-verified | FR-B-17 |
| TC-53 | 13 | A moderator resolves a dispute with a reason | COMPLETED via `dispute_resolved`; decision logged; resolved outcome recorded as evidence | Design-verified | FR-T-11 AC |
| TC-54 | 13 | A decision without a reason | Refused | Design-verified | FR-T-11 |
| TC-55 | 13 | An engine-failure hold; a moderator imposes safeguards | Refused (UC-I4 3c); "clear" re-runs the assessment from LOCALITY_CHECKED | Design-verified | ADR-0003 |
| TC-56 | 13 | A request cancelled while held | CANCELLED; case WITHDRAWN without a decision | Design-verified | UC-B6 *a, D8 |
| TC-57 | 13 | Two moderators decide the same case at once | One decision applied; the other sees the current state, nothing applied | Not run | UC-I4 4a |
| TC-58 | 14 | Every API response of the seeded loop | No address, coordinate or CNIC field | Design-verified (catalogue scan: no such columns); API not run | NFR-PR-01, NFR-S-07 |
| TC-59 | 14 | An uploaded photo with EXIF GPS data | Refused unless metadata is stripped (`metadata_stripped`) | Design-verified | NFR-PR-01 |
| TC-60 | 14 | A borrowing request payload | Contains no location fields; locality read from the stored A11 result | Design-verified (A11, D13) | FR-B-07 |
| TC-61 | 15 | 200 transition commits under load | P95 ≤ 500 ms recorded with the config version | Not run | NFR-P-04 |
| TC-62 | 15 | CD to the AWS host | `/health` and the scripted request reach ASSESSED; on failure the previous tag is redeployed | Not run | NFR-D-03, NFR-D-04 |
| TC-63 | 15 | The demo story on the deployed instance (plan demo 2.1 to 2.6) | Every step behaves as scripted | Not run | Demo script |

## 7. Traceability summary

| Requirement | Test cases |
|---|---|
| FR-B-05, NFR-R-01 | TC-08, TC-09 |
| FR-B-07 | TC-03, TC-60 |
| FR-B-08, NFR-R-02 | TC-01 to TC-06 |
| FR-B-09, NFR-R-03 | TC-07 |
| FR-B-16, FR-B-17 | TC-05, TC-50 to TC-52 |
| FR-T-02, FR-T-03 | TC-20 to TC-24, TC-31, TC-40 |
| FR-T-04 | TC-25 to TC-28, TC-34, TC-46, TC-47 |
| FR-T-05, FR-T-06 | TC-29 to TC-35, TC-38, TC-43, TC-45 |
| FR-T-07, NFR-R-04 | TC-36, TC-37 |
| FR-T-10, FR-T-11 | TC-53 to TC-57 |
| FR-M-05, NFR-S-05 | TC-13, TC-14 |
| NFR-S-02, NFR-S-03 | TC-10 to TC-12 |
| NFR-PR-01, NFR-S-07 | TC-58 to TC-60 |
| NFR-Q-01 | TC-40 to TC-47 |
| NFR-P-03, NFR-P-04, NFR-D-03, NFR-D-04 | suite 8, TC-61 to TC-63 |

The full requirement-to-artefact-to-test matrix is `01_requirements/Traceability_Matrix.md`.

## 8. Design-time verification already run (evidence for chapter 7)

| Check | Command | Result (11 October 2026) |
|---|---|---|
| Schema rules on PostgreSQL 16.6 (transition table, guards, overlap race, append-only, tamper, privacy scan, decision-table check) | `python 06_data_model/test_schema.py` (needs `DM_TEST_DSN`) | **44/44 passed** (`06_data_model/test_results.txt`) |
| Locality decision table and the six Overview §1 cases | `python 12_locality/test_locality_cases.py` | **18/18 passed** |
| Fixture oracle (posterior, intervals, k-hop, manipulation score, decision table) | `python 14_testing/verify_fixtures.py` | **13/13 fixtures consistent** (`fixture_verification_results.md`) |
| Design consistency (paths, vocabulary, config values, generated files) | `python 14_testing/verify_design.py` | See its output (all checks pass at integration) |
| Diagram layout checks | each `generate_*.py` | 0 layout problems |

Defects found by these checks during integration (report chapter 7.7, "defects and corrective actions"): all six fixture intervals were miscomputed; the ES-04 score was miscalculated (86.8 instead of 96.8); ES-13 was impossible under ADR-0006; the ES-04 hold could not happen with one active signal; R1 sent a new request to DISPUTED. All are fixed, and each fix is recorded in `00_management/Integration_Report_2026-10-11.md`.

## 9. Defect management

Defects are GitHub issues labelled `defect` and `sev-1` to `sev-4`:

- **Severity 1:** wrong state, data loss or a privacy leak.
- **Severity 2:** a failed acceptance criterion.
- **Severity 3:** a degraded feature with a workaround.
- **Severity 4:** cosmetic.

Each defect links its failing test case. The fix PR adds or updates the test that would have caught it. The defect log (report chapter 7 and Appendix C) lists the ID, severity, test case, cause, fix and commit.

## 10. Risks to testing

| Risk | Effect | Mitigation |
|---|---|---|
| `btree_gist` missing in a test database | Suite 3 cannot run | Use the official `postgres:16` image in CI and Compose (the embedded `pgserver` lacks it) |
| Flaky concurrency tests | False reds block merges | Repeat rounds deterministically; use a fresh item per round; fail on any double commit |
| Fixtures tuned to the detector | Overstated detection quality | The held-out attack generator stays separate (Module 10, Student 3) |
| Timer-dependent cases (expiry, no-show) | Not testable without the scheduler | Marked iteration 2; the DB guards are tested now with explicit events |
| Engine timeout depends on machine speed | Flaky suite 10 | Inject the delay in the stub instead of relying on load |
