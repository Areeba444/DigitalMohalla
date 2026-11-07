# Membership decision activity diagram (DA-13)

| Field | Value |
|---|---|
| Owner / reviewer | Student 3 (Minahil Kashif) / Student 1 (Fatima Khursheed) |
| Version | 1.0, 7 November 2026 (draft for review) |
| Scope | UC-A3 and UC-A4: from the locality check at join to the moderator's decision |
| Files | `membership_decision_activity_diagram.drawio`, `generate_membership_decision_activity.py` |
| Author note | Drafted with Claude Code (GenAI); disclosed in the AI usage log. |

**What it shows.** Three partitions: the applicant, the system (membership and locality, Module 1) and the community's moderator (Module 9). The applicant gives one optional coarse fix and an optional invitation code. The system evaluates both in memory with the A11 rule and discards the coordinates. An unusable code is the only path that stops the flow, and the applicant can retry. Otherwise the outcome is CONFLICTING, INCONCLUSIVE or VERIFIED, and every one of them creates a PENDING request. The moderator may ask for more information (with a deadline) or decide with a reason. The system applies the decision only while the request is still undecided.

**Rationale.** The diagram makes the panel's location action visible as behaviour: locality produces evidence for a person to weigh, never a rejection (FR-A-08). Duplicate requests stop before anything is stored (UC-A3 4b, `membership_one_live_uq`). The check "still undecided" before applying a decision is what makes two moderators, or a withdrawal racing a decision, safe (UC-A4 4a, 4c; FR-A-11). Notation follows the decision-policy activity diagram: decision nodes carry no text, every outgoing edge has a guard, and alternative flows meet in explicit merge nodes.

**Realises:** FR-A-07, FR-A-08, FR-A-09, FR-A-10, FR-A-11, NFR-PR-01, NFR-S-03.
**Maps to code (F2, F3 in the plan):** a membership service and a `LocalityVerifier` that ports `12_locality/locality_rule.py`; tables `membership`, `locality_verification`, `invitation`; the moderator membership queue (wireframe W11). States M01 to M05: `07_state_machines/membership_state_machine.drawio`.

**Outcome rule (from `Locality_Design_A11.md`).** CONFLICTING: a mock-location provider, a duplicate-account signal, or a fix outside the community. VERIFIED: a fix inside the community with a valid invitation. INCONCLUSIVE: everything else (weak fix, near the boundary, permission refused, or no invitation). The A11 test cases (18 checks) are the acceptance tests for this branch (suite 20).
