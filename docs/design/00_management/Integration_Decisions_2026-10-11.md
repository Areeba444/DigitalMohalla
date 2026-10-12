# Integration decisions, 11 October 2026 (after the three Part-A deliveries)

| Field | Value |
|---|---|
| Recorded by | Student 1 (integration lead) |
| Inputs | Student 1, 2 and 3 Part-A artefacts as delivered on 2026-10-11; `Team_Decisions_2026-10-11.md` (D1–D9) |
| Purpose | Make the three students' artefacts one consistent design baseline before the A14 design gate |
| Use | Report Appendix F (meeting records), §5 "design evolution"; Form 2 "design artefacts and evolution" |
| Status | D10 and D11 were decided by Student 1 as integration lead and are recorded as ADR-0007 and ADR-0008. D12 to D17 follow directly from the accepted baseline (plan, use cases, A3, A11). Students 2 and 3 initial below; anyone may reopen a decision at the A14 review. |

Decisions D1–D9 are in `Team_Decisions_2026-10-11.md`. This note continues the numbering.

| # | Decision | Why | Applied in |
|---|---|---|---|
| D10 | **ADR-0007.** A manipulation hold needs corroboration: level 4 = risk ≥ 60 **and** ≥ 2 signals ≥ 0.5; an uncorroborated score is capped at level 3 (verification, no hold). S4 review similarity is active in iteration 1 alongside S1 and the retaliation check. | The requirements ("≥ 60 always holds") and Student 2's false-positive guard contradicted each other, and with only S1 active ES-04 could never be held | FR-T-05, FR-T-06 + AC; Use Cases §2, B5 5b, D3 4a; T06; `schema.sql` v2.3; config 1.1.0; Algorithm doc §5; fixtures v1.1 (ES-04, PU-01, PU-02); test plan suites 9, 11, 12; plan scope row |
| D11 | **ADR-0008.** New rule R6_SPARSE (n_eff < 3 and ρ < 0.3 → INSUFFICIENT_EVIDENCE) after R6_DISPUTE; with community paths (ρ ≥ 0.3) the request falls through to R9 (REVIEW_RECOMMENDED). R3 (no history) unchanged. | Under ADR-0006 ρ could never change a decision ("k-hop changes nothing"), and the ES-13 fixture was impossible | Algorithm doc §6; decision-policy activity diagram; FR-T-04, FR-T-06; UC-D3 1a; fixtures (ES-13 rebuilt, PU-05); `assessment.rule_fired`; k-hop design §4 |
| D12 | An open dispute (rule R1) gives ACTIVE_DISPUTE and the request goes to **ASSESSED**; it is not held and no new case is opened. The lifecycle holds a request exactly when the assessment has a hold reason (R2 → `manipulation_risk`, R4 → `high_value_low_confidence`). | Plan demo step 2.5 ("the borrower's next request shows ACTIVE_DISPUTE"); A3 has no hold reason for disputes and DISPUTED is reachable only from ACCEPTED, ACTIVE or RETURN_INITIATED. Student 2's activity diagram had sent R1 to "maintain DISPUTED", which is an invalid transition | Algorithm doc §6 (R1 escalate = no); decision-policy activity diagram; sequence (a); `assessment_rule_ck`; fixture PU-03 |
| D13 | Locality at request time reads the **stored** membership-time result (A11). A borrowing request carries no coordinates; GPS is read once, in memory, only when a member joins a community (UC-A3). | A11 design, UC-A3 step 3, `ILocality.outcome_for()`, `locality_outcome_for()` in the schema. Sequence (a) and the DFD had sent raw GPS with every borrowing request | Sequence (a) md and diagram; DFD md and diagram (privacy boundary moved to the membership check) |
| D14 | **One vocabulary.** The database enums in `06_data_model` are the persisted spelling; the engine contract uses snake_case, mapped in `06_data_model/Assurance_Data_Dictionary.md` §5. Value bands are Student 2's three (LOW ≤ 5,000, MEDIUM ≤ 15,000, HIGH > 15,000 PKR; VERY_HIGH removed). Verification levels are the schema's three (Student 2's `verified_identity` is not used in iteration 1; FR/NFR issue I-9 stays open). Outcome status and metric names are mapped, not renamed. | The two data dictionaries used different names for the same things | `schema.sql` v2.3; Assurance Data Dictionary §5; fixtures |
| D15 | Engine config **1.1.0-iteration1-draft** (S4 active, rule order, A11 locality parameters added; no numeric value changed). Every artefact names this version. The data dictionary reads its parameter table from the config file. | NFR-D-01: every change to parameters is versioned; one file avoids drift | Config JSON; Data Dictionary; sequence (a); DFD; fixtures |
| D16 | Folder structure `00_management` … `14_testing`, `_tools`, `_references`; file renames listed in `Integration_Report_2026-10-11.md` §2. | Plan A0 asks for a clean baseline; S2 and S3 files sat at the root or in folders with typos | Whole `design/` folder; all path references |
| D17 | Deployment (A13): one AWS EC2 host with Docker Compose (TLS reverse proxy, FastAPI API, PostgreSQL 16 with `btree_gist`), images in GHCR, CD from GitHub Actions over SSH with smoke test and rollback; instance size, region and domain to be confirmed by Student 3 by D-14. Client: resident app as a mobile app (NFR-D-05 assumption), moderator and admin console as a web app; final stack at the D-15 gate. | Plan CI/CD section, NFR-D-03 ("target per the confirmed stack is AWS"), NFR-D-05 | `04_deployment/`; `13_wireframes/` |
| D18 | A2 domain model v1.0 keeps LocalityResult, ConditionReport and Booking (the open A2 point of the 2026-10-11 meeting). | Each is realised by a table, guarded in the A3 table and drawn in sequence (b); removing them would hide database-enforced rules | `05_class_model/` domain model v1.0 |
| D19 | Diagrams follow their standard notation (UML 2.5; Gane &amp; Sarson for the DFD; crow's foot for the ERD). Four hand-drawn diagrams with notation faults were redrawn as generators with unchanged content; originals kept in `archive_v1/`. | Form 3 "design" marks; consistency checked automatically (`verify_design.py` C12) | `Design_Review_A14_2026-10-11.md` |

**Still open** (not decided here): ADR-0006 sign-off by Student 2; three-way signature of the data dictionary and tag `schema-v1`; the frontend and backend stack (D-15); timer values (iteration 2); N-2, I-3, I-5 to I-10, I-12, I-14, I-15 in the FR/NFR Part D.

| Student 1 | Student 2 | Student 3 | Date |
|---|---|---|---|
| recorded | | | 2026-10-11 |
