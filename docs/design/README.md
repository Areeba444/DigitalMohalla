# Digital Mohalla: Design Baseline (Iteration 1, Part A)

Digital Mohalla is a neighbourhood borrowing platform whose computing core is an evidence-based assurance engine. This folder is the integrated design baseline of all three students for iteration 1 (FYP-1 Mid). It will become `docs/design/` in the repository. Every path below is relative to this folder.

| Field | Value |
|---|---|
| Baseline | Use Cases v1.3, FR/NFR v1.3, ADR-0001 to ADR-0008, schema v2.3, engine config 1.1.0-iteration1-draft, fixtures v1.1 |
| Status (2026-10-11) | Part A steps A1–A13 complete and mutually consistent; every diagram follows its standard notation (`00_management/Design_Review_A14_2026-10-11.md`; `python 14_testing/verify_design.py`: 12/12). Open for the A14 gate: stack decision (D-15), deployment target, tag `design-v1.0` |
| What changed in integration | `00_management/Integration_Report_2026-10-11.md`; decisions D10–D17 in `00_management/Integration_Decisions_2026-10-11.md` |
| Backup of the pre-integration state | `../_backups/design_pre-integration_2026-10-11.zip` (69 files) |

## Folder map

| Folder | Contents | Plan step | Owner |
|---|---|---|---|
| `00_management/` | Iteration 1 plan (Plan A), team decisions D1–D9, integration decisions D10–D19, integration report, A14 design and notation review | — | All |
| `01_requirements/` | Project overview, use cases, FR/NFR, traceability matrix | A0 | All |
| `02_use_case_model/` | Core use case diagram, SSDs (B5, B7 with B8, B12, I4) | A9 | S3 |
| `03_architecture/` | ADRs, component and layer diagrams, REST endpoint table | A1, A8 | S1 |
| `04_deployment/` | Deployment diagram and design (provisional) | A13 | S3 |
| `05_class_model/` | Domain model (A2) and class diagrams of all three students (A7) | A2, A7 | All / each |
| `06_data_model/` | ER diagram, `schema.sql`, schema tests, A4 data dictionary, assurance data dictionary | A4, A6 | S1, S2 |
| `07_state_machines/` | Borrowing lifecycle and escalation-case state machines, transition table | A3 | S1 |
| `08_sequence_diagrams/` | Sequence (a) request to assessment, (b) handover and return, (c) dispute | A9 | S2, S1, S3 |
| `09_activity_diagrams/` | Decision-policy activity diagram, dispute-resolution activity diagram | A5, A9 | S2, S3 |
| `10_dfd/` | DFD level 0 and level 1 (assurance pipeline, privacy boundary) | A10 | S2 |
| `11_assurance_engine/` | Algorithm and data-structure design, engine config, k-hop indirect trust (ADR-0006) | A5 | S2, S1 |
| `12_locality/` | Locality method comparison, decision rule, six test cases | A11 | S1 |
| `13_wireframes/` | Wireframes W1–W10 and their design note | A12 | S3 |
| `14_testing/` | Test plan, scenario fixtures, transition test matrix, verification scripts | A13 | S3, all |
| `_tools/` | Shared generators: `lifecycle_model.py` (single source of truth of the lifecycle), `drawio.py` (diagram writer with layout checker), `relabel_drawio.py` | — | S1 |
| `_references/` | FYP handbook (draft 2026) and FYP-1 mid rubric | — | — |

## Artefact register

| # | Artefact | File(s) | Owner | Status |
|---|---|---|---|---|
| 1 | Iteration 1 plan | `00_management/DigitalMohalla_Iteration1_Plan_Ver1.md` | All | Status updated 2026-10-11 |
| 2 | Use cases (13 dressed, 55 brief) | `01_requirements/DigitalMohalla_Use_Cases_Ver1.md` | All | v1.3 baseline |
| 3 | FR / NFR with acceptance criteria | `01_requirements/DigitalMohalla_FR_NFR_Ver1.md` | All | v1.3 baseline |
| 4 | Traceability matrix | `01_requirements/Traceability_Matrix.md` | All | v1.0 opened |
| 5 | Core use case diagram | `02_use_case_model/use_case_diagram.drawio` (generated) | S3 | v0.3 (UML redraw) |
| 6 | SSDs | `02_use_case_model/ssd_diagrams.drawio` (4 pages) | S3 | v1.0, A14 review |
| 7 | ADRs 0001–0008 | `03_architecture/DigitalMohalla_ADRs_Ver1.md` | S1 (lead) | 0001–0005 accepted; 0006 proposed; 0007–0008 accepted for integration |
| 8 | Component and layer (UML package) diagrams, REST table | `03_architecture/` | S1 | v1.2 |
| 9 | Deployment diagram | `04_deployment/deployment_diagram.drawio`, `Deployment_Design.md` | S3 | v0.9 provisional (target by D-14) |
| 10 | Domain model; class diagrams S1, S2, S3 | `05_class_model/` | All / each | Domain model v1.0 (D18); class diagrams v1.0 |
| 11 | ER diagram and schema | `06_data_model/er_diagram.drawio`, `schema.sql` | S1 | v2.3, 44/44 tests |
| 12 | Data dictionary (A4) and assurance data dictionary | `06_data_model/Data_Dictionary.md`, `Assurance_Data_Dictionary.md` | S1, S2 | To be signed by all three, tag `schema-v1` |
| 13 | State machines and transition table | `07_state_machines/` | S1 | v2.2 |
| 14 | Sequence (a), (b), (c) | `08_sequence_diagrams/` | S2, S1, S3 | (a) v1.2 UML redraw, (b) v1.1, (c) v1.1 |
| 15 | Decision-policy and dispute activity diagrams | `09_activity_diagrams/` | S2, S3 | decision policy v1.2 UML redraw; dispute v1.0 |
| 16 | DFD L0 / L1 | `10_dfd/` | S2 | v1.2 Gane &amp; Sarson redraw |
| 17 | Algorithm and data-structure design, config | `11_assurance_engine/` | S2 | v1.1, config 1.1.0 |
| 18 | k-hop indirect trust | `11_assurance_engine/KHop_Indirect_Trust_Design.md` | S1 | v1.2; ADR-0006 awaits S2 |
| 19 | Locality design | `12_locality/` | S1 | v1.0, 18/18 cases |
| 20 | Wireframes | `13_wireframes/wireframes.drawio`, `Wireframes_Design.md` | S3 | v0.9, A14 review |
| 21 | Test plan, fixtures, oracles | `14_testing/` | S3, all | v1.0; fixtures 13/13 |

## Regenerate and verify

Generated files must not be edited by hand. Change the source and re-run its generator.

```text
python 14_testing/verify_design.py              # design-wide consistency and notation (12 checks)
python 14_testing/verify_fixtures.py            # fixture oracle -> fixture_verification_results.md
python 14_testing/generate_transition_matrix.py # suite-1 oracle from the lifecycle model
python 07_state_machines/generate_state_machines.py
python 02_use_case_model/generate_use_case_diagram.py
python 03_architecture/generate_architecture.py
python 04_deployment/generate_deployment.py
python 05_class_model/generate_class_model.py
python 05_class_model/generate_class_diagrams_s2_s3.py
python 08_sequence_diagrams/generate_sequence_a.py
python 08_sequence_diagrams/generate_sequence_b.py
python 09_activity_diagrams/generate_decision_policy_activity.py
python 10_dfd/generate_dfd.py
python 11_assurance_engine/generate_khop_example.py
python 13_wireframes/generate_wireframes.py
python 12_locality/test_locality_cases.py
# needs PostgreSQL 16 with btree_gist and DM_TEST_DSN=postgresql://postgres@localhost:5432/postgres
python 06_data_model/test_schema.py
python 06_data_model/generate_erd.py
python 06_data_model/generate_data_dictionary.py
```

Three diagrams remain hand-drawn in draw.io: the SSDs, sequence (c) and the dispute-resolution activity diagram. Label-only corrections can be scripted with `_tools/relabel_drawio.py`. Superseded hand-drawn versions are kept in each folder's `archive_v1/`.

**Notation:** UML 2.5 for every structural and behavioural diagram, Gane &amp; Sarson for the DFD, crow's foot for the ERD. The standards and checks are in `00_management/Design_Review_A14_2026-10-11.md`; `verify_design.py` C12 enforces the main rules.

## Conventions

- One vocabulary: the state, event, table and enum names of `07_state_machines/` and `06_data_model/schema.sql`; the engine contract maps to them in `06_data_model/Assurance_Data_Dictionary.md` §5.
- Every hand-written document starts with a control block (version, date, owner, status), as plan step A0 asks.
- Any change to the frozen event schema, an ADR or the config needs a new version and sign-off by all three students.
- GenAI assistance is noted in each document's control block and must be disclosed on Form 13 and in the AI usage log.
