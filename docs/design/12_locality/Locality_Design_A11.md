# Locality Verification Design (design step A11)

| Field | Value |
|---|---|
| Owner | Student 1 (locality) |
| Version | 1.0, 11 October 2026 |
| Status | Method chosen by Student 1 (geofence + invitation). Whether it is built in iteration 1 (Slice C) or iteration 2 is decided at the D-11 gate. Awaiting second-member review (A14). |
| Sources | Overview §1 (locality verification and privacy, six test cases), Post-Defence Direction (Problem Validation), §5.13 (location spoofing); UC-A3, UC-A4, UC-B5 step 4 and ext 4a/4b; FR-A-06 to FR-A-08, FR-A-13; NFR-PR-01, NFR-PR-02, NFR-Q-04; ES-09, ES-10 |
| Files | this document; `locality_rule.py` (reference implementation of the rule); `test_locality_cases.py` and `locality_test_results.md` (**18/18 pass**) |
| Author note | Drafted with Claude (GenAI); to be disclosed on Form 13 and in the AI usage log. |

## 1. Problem and constraints

Borrowing ends in a physical handover between neighbours, so the platform must know that a member really belongs to the community, without becoming a tracking or surveillance system (Overview scope protections). The defence panel asked the team to show that location is a real issue. The team does not run interviews or a survey, so this design, its threat analysis and its test cases are the evidence (Overview, Problem Validation; Iteration 1 plan, Form 10).

Requirements the method must meet:
- **Three-valued, never negative** (FR-A-08): verified, inconclusive or conflicting. Inconclusive and conflicting go to a moderator; nobody is rejected automatically (ES-09, ES-10).
- **Coarse only** (FR-A-07, NFR-PR-01, NFR-PR-02): store the community and the coarse result, never raw traces or exact addresses. The exact meeting point is shared only after both parties agree.
- **Measurable** (NFR-Q-04): false accepts and false rejects are measured on the six test cases.
- **Request-time check** (UC-B5 step 4): the lifecycle reads only the stored coarse outcome. This is the `locality_outcome_for()` stub already in the schema.

## 2. Candidate methods compared

The five candidates come from Overview §1. Ratings are design judgements, made before any measurement; NFR-Q-04 measures the chosen method later on the test cases.

| Method | False accepts (non-resident verified) | False rejects (resident not verified) | Privacy | Spoofing resistance | Cost to build and run |
|---|---|---|---|---|---|
| **Coarse GPS geofence** alone | Medium: a visitor standing inside passes | Medium: boundary homes, indoor fixes, permission refusal | Medium: one fix, evaluated in memory | **Low**: mock-location apps are easy to use | Low: one boundary polygon per community |
| **Community invitation** alone | Medium: a member can invite a non-resident; invitation chains of fake accounts | Medium–high: newcomers who know nobody | **High**: no location at all | Medium: social, but collusion is possible | Low: single-use codes |
| **Moderator approval** alone | Low if the moderator is diligent | Low | Medium: depends on what evidence is shown | High | **High**: moderator time for every member; slow; risk of bias |
| **Privacy-preserving address evidence** (document shown, not kept) | Low–medium: forged documents | Medium: renters, family members | **Low**: sensitive documents handled | Medium | Medium–high: secure handling, deletion, review |
| **Combination: geofence + invitation, moderator for the rest** | **Low**: needs two independent signals | Low: anything uncertain goes to a moderator, never rejected | Medium–high: one in-memory fix; only a coarse signal stored | **Medium–high**: a spoofer also needs a real member's invitation; mock-location flag detected | Medium: polygon + invitation codes; moderator only for uncertain cases |

## 3. Decision

**Chosen: coarse geofence + invitation, with a moderator deciding anything inconclusive or conflicting.**

Reasons:
- Neither signal alone is enough. GPS is easy to spoof, and invitations alone ignore the panel's location point. Together, a spoofer must also obtain a real member's single-use invitation, and a careless invitation still has to match the location.
- Uncertainty costs moderator time, never a rejection, which is the rule FR-A-08 sets.
- Privacy stays close to invitation-only: one fix is used in memory and only a four-value coarse signal is stored.
- The moderator's workload is limited to uncertain cases, unlike moderator-only approval.

### 3.1 Decision table

Implemented in `locality_rule.py` (`decide`) and enforced by the database constraint `locality_rule_ck`, so a stored outcome can never contradict its own evidence.

| Mock-location flag or duplicate-account signal | Geofence signal | Valid invitation | Outcome | What happens next |
|---|---|---|---|---|
| yes | any | any | CONFLICTING | Moderator review, flagged (possible spoofing / Sybil) |
| no | OUTSIDE | any | CONFLICTING | Moderator review; the member may re-check from home |
| no | INSIDE | yes | **VERIFIED** | Membership locality evidence complete |
| no | INSIDE | no | INCONCLUSIVE | Moderator review (visitor, or newcomer without an invitation) |
| no | NEAR_BOUNDARY | any | INCONCLUSIVE | Moderator review |
| no | UNAVAILABLE (refused, no fix, accuracy too poor) | any | INCONCLUSIVE | Moderator review; permission refusal is not negative (ES-10) |

A moderator of the community (or an admin) can then record a `MODERATOR_APPROVAL` result (VERIFIED, `approved_by` stored), or reject the membership request with a reason. Rejection is a membership decision (UC-A4), not a locality outcome.

### 3.2 How the signals are produced

- **Geofence signal.** The app takes one fix with permission. The server compares it with the community's coarse `boundary_polygon` in memory, then discards it. If the reported accuracy is worse than `MAX_ACCURACY_M` the signal is UNAVAILABLE. If the fix is within max(`MIN_MARGIN_M`, accuracy) of the boundary it is NEAR_BOUNDARY. Otherwise it is INSIDE or OUTSIDE. A mock-location provider reported by the device sets `mock_provider_detected`.
- **Invitation.** A verified (approved) member issues a single-use code for their own community, valid for `INVITE_TTL_DAYS`, with at most `MAX_OPEN_INVITES` open codes each. Only the code's SHA-256 hash is stored. An invalid, expired, used, self-issued or other-community code is an error the member can retry (UC-A3 3d).
- **Duplicate-account signal.** This comes from the registration device / IP signal that FR-A-03 already records, where legitimately available (Overview §5.13).
- **Re-verification.** A result is valid for `VALIDITY_DAYS`, which implements "verified once or periodically". After that, the request-time check returns INCONCLUSIVE, not negative.

### 3.3 Parameters (initial, unvalidated; go into the versioned config, NFR-D-01)

| Parameter | Initial value | Basis |
|---|---|---|
| `MAX_ACCURACY_M` | 100 m | Typical outdoor phone accuracy is well below this; indoor fixes above it go to a moderator instead of being judged |
| `MIN_MARGIN_M` | 50 m | Keeps homes on the boundary line out of automatic decisions |
| `INVITE_TTL_DAYS` | 7 days | Short enough to limit code sharing |
| `MAX_OPEN_INVITES` | 3 per member | Limits invitation chains of fake accounts |
| `VALIDITY_DAYS` | 365 days | "Verified once or periodically"; the same placeholder as schema v1 |

These are starting values to be measured, like every engine parameter (Overview §5.6). NFR-Q-04 reports false accepts and false rejects on the test cases.

## 4. The six test cases (Overview §1)

Full input / expected / actual table: `locality_test_results.md` (generated by `test_locality_cases.py`; synthetic coordinates).

| Case | What is tested | Expected behaviour | IDs |
|---|---|---|---|
| GPS spoofing | Mock-location provider; undetected spoof without an invitation; spoof that lands far away | CONFLICTING when detected or contradicted; never VERIFIED without a real invitation | L1a–c |
| Boundary users | Just inside / just outside the edge; well inside | NEAR_BOUNDARY → INCONCLUSIVE (not CONFLICTING); well inside + invitation → VERIFIED | L2a–c |
| Visitors | Inside, no invitation | INCONCLUSIVE → moderator | L3 |
| Location-permission refusal | No fix, valid invitation | INCONCLUSIVE with `permission_refused`; never negative | L4 |
| Duplicate accounts | Duplicate-account signal on an otherwise valid check | CONFLICTING, flagged for the moderator | L5 |
| False rejection of genuine residents | Resident at home; resident indoors with poor accuracy; new resident without an invitation | VERIFIED automatically, or INCONCLUSIVE → moderator; no path rejects them | L6a–c |

Also covered: four invitation errors (E1–E4), the privacy check that no coordinates or accuracy are kept (P1), and that 64 combinations of inputs never produce a negative outcome (P2). The database enforces the same rules (`06_data_model/test_schema.py`, "A11 locality rule").

**Measures (NFR-Q-04).** With no negative outcome, a "false reject" means a genuine resident who is not verified automatically and needs a moderator; a "false accept" means a non-resident who reaches VERIFIED. These are counted on the test cases now and in the pilot later, together with moderator load (the share of checks that need a moderator).

## 5. Privacy design

| Data | Stored? | Where |
|---|---|---|
| Device coordinates, accuracy | **No**: used in memory during the check | — |
| Coarse geofence signal (INSIDE / NEAR_BOUNDARY / OUTSIDE / UNAVAILABLE), outcome, flags, time | Yes | `locality_verification` |
| Invitation code | Only its SHA-256 hash | `invitation` |
| Community boundary polygon | Yes (community data, not personal) | `community.boundary_polygon` |
| Exact address | **No**; profiles reject or coarsen it (FR-A-13) | — |
| Exact meeting point | Shared only after acceptance, between the two parties | chat (iteration 3) |

Request logs must not record the body of the locality request, which contains the fix (privacy test suite 14). Retention of coarse results is still open (NFR-PR-02).

## 6. Effect on other artefacts

- Schema: the method enum is now `GEOFENCE_INVITATION | MODERATOR_APPROVAL`; there is a `geofence_signal` enum, an `invitation` table and `community.boundary_polygon`; the outcome must follow the decision table (`locality_rule_ck`); an `invitation` is single-use, unexpired and from the same community (`locality_guard`). Tests: 39/39.
- Component diagram: LocalityVerifier implements this method; until the D-11 gate it stays a stub that reads stored results.
- Use case UC-A3 step 3 ("the method set is fixed in design step A11"): the method is now geofence + invitation with a moderator fallback.

## 7. Evidence for the panel's location action (Form 10)

"Location is a real issue for physical handover between neighbours. Addressed by: the locality threat analysis (spoofing, boundary users, visitors, permission refusal, duplicate accounts, false rejection), a comparison of five verification methods on false accepts, false rejects, privacy, spoofing resistance and cost, the chosen geofence + invitation design with a moderator fallback, 18 passing locality test cases and the database constraints that enforce them, and a privacy design that stores no coordinates. Evidence: `design/locality/`, `design/er_schema/test_results.txt`."
