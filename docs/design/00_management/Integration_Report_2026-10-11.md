# Integration Report: Part A design baseline (11 October 2026)

| Field | Value |
|---|---|
| Version | 1.0, 11 October 2026 |
| Author | Student 1 (integration lead), drafted with Claude (GenAI; to be disclosed on Form 13) |
| Scope | Every file in `design/`: requirements, plan, ADRs, all diagrams, schema and tests, engine design and config, fixtures, scripts |
| Result | One consistent baseline. All Part A artefacts exist; all automated checks pass (§5) |
| Backup | `../_backups/design_pre-integration_2026-10-11.zip`: the complete folder before any change (69 files, CRC-verified) |

## 1. Summary

The three students' Part A work was complete apart from the deployment diagram, the test plan and the wireframes. However, it did not yet form one design. Student 2's engine design and Student 1's requirements, schema and state machine disagreed on two rules that decide the core scenarios. Student 2's fixtures had wrong numbers. Student 2's sequence diagram and DFD sent GPS with every borrowing request, which contradicts the accepted locality design. Student 3's dispute sequence still allowed disputes from RETURNED. All of these are now resolved. The two decisions that change behaviour (D10, D11) were taken by the integration lead and recorded as ADR-0007 and ADR-0008. All other fixes follow directly from the accepted baseline. The three missing deliverables were created from the requirements and the existing design. The folder was reorganised into numbered artefact folders, and every reference was updated.

## 2. Folder structure and moves

```text
design/
├── README.md                     index: folder map, artefact register, how to regenerate and verify
├── 00_management/                plan (Plan A), team decisions D1–D9, integration decisions D10–D17, this report
├── 01_requirements/              overview, use cases v1.3, FR/NFR v1.3, traceability matrix (new)
├── 02_use_case_model/            use case diagram, SSDs (S3)
├── 03_architecture/              ADRs 0001–0008, component and layer diagrams (S1)
├── 04_deployment/                deployment diagram and design (new)
├── 05_class_model/               domain model, Student 1 class diagram
├── 06_data_model/                ER diagram, schema.sql v2.3, schema tests, A4 and assurance data dictionaries
├── 07_state_machines/            state machines, transition table (S1)
├── 08_sequence_diagrams/         sequences (a) S2, (b) S1, (c) S3
├── 09_activity_diagrams/         decision policy (S2), dispute resolution (S3)
├── 10_dfd/                       DFD level 0 and 1 (S2)
├── 11_assurance_engine/          algorithm design, config, k-hop indirect trust (S2, S1)
├── 12_locality/                  A11 locality design and tests (S1)
├── 13_wireframes/                wireframes W1–W10 (new)
├── 14_testing/                   test plan (new), fixtures, transition matrix, verification scripts
├── _tools/                       lifecycle model, draw.io writer, relabel tool
└── _references/                  FYP handbook draft, FYP-1 mid rubric (copies of files in ../helping material and ../Mid eval prep)
```

| Before | After |
|---|---|
| `Digital Mohalla — Iteration 1 (FYP-1 Mid) Plan_Ver1.md` | `00_management/DigitalMohalla_Iteration1_Plan_Ver1.md` |
| `Team_Decisions_2026-10-11.md` | `00_management/` |
| `Digital_Mohalla_Project_Overview_Ver1.md`, `DigitalMohalla_Use_Cases_Ver1.md`, `DigitalMohalla_FR_NFR_Ver1.md` | `01_requirements/` |
| `Usecase Diagram.drawio`, `ssd_diagrams.drawio` | `02_use_case_model/use_case_diagram.drawio`, `ssd_diagrams.drawio` |
| `DigitalMohalla_ADRs_Ver1.md`, `architecture/*` | `03_architecture/` |
| `class_model/*` | `05_class_model/` |
| `er_schema/*` (with `archive_v1/`), `Data Dictionary/Assurance_Data_Dictionary.md` | `06_data_model/` |
| `state_machine/*` (with `archive_v1/`) | `07_state_machines/` |
| `Sequence Diagram/Sequence_Diagram_UC_B5_Request_To_Assessment.{md,drawio}` | `08_sequence_diagrams/Sequence_A_Request_To_Assessment.md`, `sequence_a_request_to_assessment.drawio` |
| `sequence/*`, `SD3.drawio` | `08_sequence_diagrams/`, `sequence_c_dispute.drawio` |
| `Acitvity Diagrams/Decision_Policy_Activity_Diagram.{md,drawio}`, `dispute_activity_diagram.drawio` | `09_activity_diagrams/Decision_Policy_Activity_Diagram.md`, `decision_policy_activity_diagram.drawio`, `dispute_resolution_activity_diagram.drawio` |
| `DFD/*` | `10_dfd/Assurance_Pipeline_DFD_Level_0_Level_1.md`, `dfd_assurance_pipeline_level0_level1.drawio` |
| `Algorithm_and_Data_Structure_Design_FINAL.md`, `Config/Assurance_Engine_Config_Draft.json`, `indirect_trust/*` | `11_assurance_engine/` (the algorithm file loses "_FINAL", matching the name the overview and plan cite) |
| `locality/*` | `12_locality/` |
| `Scenario_Fixtures/scenario_fixtures_iteration1.json` | `14_testing/` |
| `BS-FYP-Handbook-2026_DRAFT.pdf`, `FYP-1-Mid-Assessment-Guidelines-and-Rubrics.pdf` | `_references/` |

All 69 original files are kept; nothing was deleted. Path references in 17 documents and scripts were rewritten, and `verify_design.py` check C01 confirms that every cited path resolves. The archived v1 documents (`archive_v1/`) were left exactly as they were, as history. One empty folder, `state_machine/`, could not be removed because another program holds it open; delete it when convenient.

## 3. Issues found and how they were resolved

Severity: **H** changes a decision or makes a scenario fail; **M** is a wrong value or a contradiction in a deliverable; **L** is wording or housekeeping.

| # | Sev | Issue | Where | Resolution |
|---|---|---|---|---|
| IR-01 | H | "Risk ≥ 60 always holds" (FR-T-06, UC, T06, DB check) contradicted Student 2's corroboration guard. With only S1 active, ES-04 could never be held | FR/NFR, UC, SM, schema, Algorithm doc §5, config | **D10 / ADR-0007**: level 4 = score ≥ 60 and corroborated; S4 active in iteration 1; schema gains `manipulation_level`, `manipulation_corroborated` and a level check |
| IR-02 | H | Under ADR-0006, ρ could never change a decision, so the ES-13 fixture (no history, yet two paths) was impossible: "k-hop changes nothing" | Algorithm doc §6, fixtures, k-hop design §4 | **D11 / ADR-0008**: rule R6_SPARSE; ES-13 rebuilt from outcomes (R9 REVIEW_RECOMMENDED; without paths R6_SPARSE INSUFFICIENT_EVIDENCE) |
| IR-03 | M | All six 90% credible intervals in the fixtures were wrong (e.g. ES-02 [0.768, 0.988] instead of [0.752, 0.995]); the ES-04 score was 86.8 instead of 96.8. No rule outcome changed | fixtures | Recomputed by the new oracle `verify_fixtures.py` (pure-Python Beta quantiles); fixtures v1.1 |
| IR-04 | H | The decision-policy activity diagram sent R1 (open dispute) to "maintain DISPUTED": a request in LOCALITY_CHECKED cannot enter DISPUTED, and no hold reason exists for disputes | activity diagram, Algorithm doc §6 | **D12**: R1 goes to ASSESSED with ACTIVE_DISPUTE (plan demo step 2.5); the lifecycle holds exactly when a hold reason is set (R2, R4); the invalid branch was removed |
| IR-05 | H | Sequence (a) and the DFD sent raw GPS and Wi-Fi data with every borrowing request, contradicting A11 (locality checked once at joining, stored coarse result read at request time) | sequence (a), DFD | **D13**: no location in requests; `outcomeFor()` reads the stored result; the DFD privacy boundary was moved to the membership check |
| IR-06 | M | The DFD used values found nowhere else: γ 0.85, ρ_min 0.30 as a divisor, divisors 5 and 3, a 48 h retaliation window, T_high 0.80, M_warn 30, states HIGH_ASSURANCE / STANDARD_FLOW, value band STANDARD, rules R1..R8 | DFD md and drawio | Aligned with config 1.1.0 and the Algorithm doc |
| IR-07 | M | Two data dictionaries with different vocabularies: 4 value bands vs 3; verification levels; outcome status (VALID/FLAGGED vs CONFIRMED/DISPUTED/RESOLVED); metric names | A4 dictionary, assurance dictionary, fixtures | **D14**: the schema spelling is canonical; mapping table in the assurance dictionary §5; VERY_HIGH removed; fixtures use schema values |
| IR-08 | M | Config version written three ways ("1.0.0-draft", "v1.0.0", "1.0.0-iteration1-draft"); the A4 dictionary listed the engine timeout, value bands and SUFFICIENT rule as TBD although Student 2 had defined them | sequence (a), DFD, data dictionary | **D15**: config 1.1.0-iteration1-draft everywhere; the dictionary generator now reads its parameter table from the config file |
| IR-09 | M | Sequence (a) message payloads: a 4,500 PKR item labelled HIGH; event fields not in the frozen schema (`borrower_id`, `previous_state: "NONE"`, string stream ids) | sequence (a) md | Corrected to LOW and to the frozen event record (FR-B-09) |
| IR-10 | M | Sequence (c) allowed disputes from RETURNED (decision D4 forbids it), called N-6 open (closed by ADR-0005), cited Use Cases v1.1 and named ":Transaction Service" | sequence (c) | Labels corrected (D4, ADR-0005, T23/T25/T26, `BorrowingService`) |
| IR-11 | M | "Dates free of Accepted and Active bookings" survived in SSD-B5, the T01 guard and FR-B-04, against decision D6 (held until COMPLETED or NO_SHOW) | SSD, lifecycle model, FR-B-04 | Reworded to "held bookings (ADR-0002)"; state machine regenerated |
| IR-12 | M | The A3 table listed ES-06 under T05 (ASSESSED) although N-7's resolution holds it (T07); ES-05 was missing | lifecycle model | T05: ES-01, 02, 03, 05, 13; T07: ES-06; T05 to T07 guards name the A5 rules |
| IR-13 | M | The A5 decision table was not enforceable: nothing tied a stored assessment's state, decision and hold reason together | schema | `assessment.rule_fired` and `assessment_rule_ck`; new schema test (44 checks) |
| IR-14 | L | The R6 → merge edge in the activity diagram had no source (dangling) | activity diagram | Connected |
| IR-15 | L | Student 2's documents linked to files on another computer (`file:///c:/Users/areeb/...`) | sequence (a), activity md | Relative links |
| IR-16 | L | Student 2's documents claimed "Approved Baseline" before any review and had no control blocks; Student 3's diagrams cited Use Cases v1.1 | S2 and S3 documents | Control blocks with version, owner and status "awaiting A14 review"; citations updated to v1.3 |
| IR-17 | L | Companion-file names cited without `_Ver1` (files that did not exist); a broken link in the overview | use cases, FR/NFR, ADRs, schema, overview | Fixed |
| IR-18 | L | The plan's decision table still listed N-6, N-7, the SUFFICIENT rule and ADR sign-off as open; no step was ticked | plan | Status note, decision rows and checkboxes updated (A1, A3–A6, A8–A13 done) |
| IR-19 | L | Files at the root, a misspelt folder ("Acitvity Diagrams"), duplicate PDFs, mixed naming | folder | Reorganised (§2) |
| IR-20 | L | The class diagram's AssessmentResult lacked `rule_fired` and the manipulation level | class model | Regenerated |
| IR-21 | — | Deployment diagram, test plan and wireframes missing (A12, A13) | — | Created (§4) |

Questions 4 and 6 of the ADR-0006 confirmation page are now answered by Student 2's config and ADR-0008. Student 2 still has to sign the page.

## 4. New deliverables

| Deliverable | Files | Basis |
|---|---|---|
| Deployment diagram (A13) | `04_deployment/deployment_diagram.drawio`, `Deployment_Design.md`, `generate_deployment.py` | Plan CI/CD and B0, NFR-D-02 to D-05, A8; AWS EC2 + Docker Compose + GHCR + CD over SSH with rollback; target marked TBC (D17) |
| Test plan (A13) | `14_testing/Test_Plan.md`; `transition_test_matrix.csv` and its generator | The plan's 15 suites with owners, gates, entry and exit criteria; 55 test cases in input / expected / actual form; traceability; design-time evidence |
| Wireframes (A12) | `13_wireframes/wireframes.drawio` (9 pages), `Wireframes_Design.md`, `generate_wireframes.py` | The plan's screen list plus request status and audit log; every assurance screen shows evidence, never one number |
| Traceability matrix | `01_requirements/Traceability_Matrix.md` | FR / NFR → use case → artefacts → tests → owner and slice |
| Fixture oracle | `14_testing/verify_fixtures.py`, `fixture_verification_results.md` | Recomputes every fixture value; 6 new policy unit fixtures (PU-01 to PU-06) |
| Design consistency checker | `14_testing/verify_design.py` | 11 checks across all three students' artefacts |
| Decision records | ADR-0007, ADR-0008; `Integration_Decisions_2026-10-11.md` (D10–D17) | — |
| Index | `README.md` | — |

The deployment diagram, test plan and wireframes are Student 3's artefacts in the plan. They were drafted during integration and must be reviewed by Student 3 (A14).

## 5. Verification

| Check | Result |
|---|---|
| Schema tests on PostgreSQL 16.6 (`06_data_model/test_schema.py`) | **44/44 passed** (43 before integration, all still passing; 1 new decision-table check; the risk check rewritten for ADR-0007) |
| Locality cases (`12_locality/test_locality_cases.py`) | **18/18 passed** |
| Fixture oracle (`14_testing/verify_fixtures.py`) | **13/13 consistent** (7 scenarios + 6 policy unit fixtures) |
| Design consistency (`14_testing/verify_design.py`) | **11/11 checks passed** |
| Generated diagrams (state machines, ERD, architecture, class model, sequence (b), k-hop, deployment, wireframes) | Regenerated from their new locations; **0 layout problems** |
| Visual QA | Edited and new diagrams rendered with the official draw.io viewer and inspected: decision-policy activity, ERD, deployment, all wireframe pages |

## 6. Remaining work

| # | Item | Owner | When |
|---|---|---|---|
| RW-1 | Initial ADR-0007, ADR-0008 and decisions D10–D17; sign ADR-0006 (confirmation page) | S2, S3 (S2 for ADR-0006) | Before A14 |
| RW-2 | Confirm the metric list mapping (Assurance Data Dictionary §5.2); sign the data dictionary with S1 and S3, then tag `schema-v1` | S2, all | Before A14 |
| RW-3 | Review the deployment design, test plan and wireframes drafted during integration; confirm the deployment target (DP-1 to DP-6) | S3 | D-14 |
| RW-4 | ~~A2 domain-model sitting~~ **Done in the second pass:** domain model v1.0, decision D18 | — | — |
| RW-5 | ~~Class diagrams of Students 2 and 3 (A7)~~ **Done in the second pass:** `class_diagram_s2.drawio`, `class_diagram_s3.drawio`; owners to review | S2, S3 | A14 |
| RW-6 | Stack decision; tag `design-v1.0` (design and notation review done: `Design_Review_A14_2026-10-11.md`) | All | D-15 |
| RW-7 | Add `phase2_assurance.py` (named in the Algorithm doc §11) to the repository; plan S4 in Slice C | S2 | Slice B/C |
| RW-8 | Project instructions still say "Beta-Binomial" and M1–M9 (A0, N-4); "Community Connect exclusions" (cited by NFR-S-07) is missing | All | Before the report |
| RW-9 | Open FR/NFR issues N-2, N-3, I-3, I-5 to I-10, I-12, I-14, I-15 | As in FR/NFR Part D | Iteration 2 mostly |
| RW-10 | Delete the empty `state_machine/` folder; when the repository is created, copy this folder to `docs/design/` and keep `_references/` out of git if the PDFs may not be redistributed | S1 | B0 |

## 7. Notes

- The earlier Student 1 index and verification files (`Student1_Design_Deliverables.md`, `verify_student1_partA.py`, `Student1_PartA_Verification_Plan.md`, `Student1_PartA_Design_Review.md`) were not in the folder when integration started. `README.md` and `14_testing/verify_design.py` now cover their roles for the whole team.
- Hand-drawn diagrams by Students 2 and 3 were corrected in place: labels with `_tools/relabel_drawio.py`, and one structural edit to the decision-policy activity diagram (a new decision node, the invalid branch removed, a v1.1 note in the drawing). Their layouts were otherwise kept.
- Every change to another student's file is recorded in that file's version line and in §3, so each owner can review exactly what changed.

## 8. Addendum: completion and notation review (second pass, 11 October 2026)

At the user's request (sign-offs set aside), the remaining Part A items were completed and every diagram was checked against its standard notation. Details are in `Design_Review_A14_2026-10-11.md`.

| Change | Files |
|---|---|
| A2 domain model v1.0; LocalityResult, ConditionReport and Booking kept (D18) | `05_class_model/domain_model.drawio`, `Class_Model_Design.md` |
| A7 class diagrams for Student 2 (assurance engine) and Student 3 (moderation, scenario suite) | `05_class_model/class_diagram_s2.drawio`, `class_diagram_s3.drawio`, `generate_class_diagrams_s2_s3.py` |
| Use case diagram redrawn in UML 2.5: Trust Engine no longer an actor, extension points shown | `02_use_case_model/use_case_diagram.drawio`, `generate_use_case_diagram.py`; Use Cases v1.3 D3/4/5, D6 actor note |
| Sequence (a) redrawn in UML 2.5: stick-figure actors, `:Class` lifelines, activations, correct `alt` operands | `08_sequence_diagrams/sequence_a_request_to_assessment.drawio`, `generate_sequence_a.py`, spec v1.2 |
| Decision-policy activity diagram redrawn: guarded decisions, explicit merges, partitions | `09_activity_diagrams/decision_policy_activity_diagram.drawio`, `generate_decision_policy_activity.py`, spec v1.2 |
| DFD redrawn in strict Gane &amp; Sarson: true context diagram, balanced level 1 (processes 9.0, 10.0, store D5), no entity-to-store flow | `10_dfd/dfd_assurance_pipeline_level0_level1.drawio`, `generate_dfd.py`, spec v1.2 |
| Layer diagram as a UML package diagram; PostgreSQL as an external component | `03_architecture/` |
| Deployment: artifacts with the artifact notation, communication paths as associations, comments as notes | `04_deployment/` |
| State machine guards and sequence (b) labels updated | `07_state_machines/`, `08_sequence_diagrams/` |
| Automated notation rules (check C12) | `14_testing/verify_design.py` (12/12) |

The superseded hand-drawn diagrams are kept in `02_use_case_model/archive_v1/`, `08_sequence_diagrams/archive_v1/`, `09_activity_diagrams/archive_v1/` and `10_dfd/archive_v1/`. Their content (messages, rules, processes, flow IDs) is unchanged in the redraws.

