# System sequence diagrams for iteration 2: SSD-A3, SSD-A4, SSD-D1 (DA-12)

| Field | Value |
|---|---|
| Owner / reviewer | Student 3 (Minahil Kashif) / Student 1 (Fatima Khursheed) |
| Version | 1.0, 7 November 2026 (draft for review) |
| Scope | UC-A3 (request membership), UC-A4 (approve or reject membership), UC-D1 (submit review) |
| Files | `ssd_diagrams.drawio` pages 5 to 7 (one SSD file for the system since 13 November 2026; pages 1 to 4 are the iteration 1 SSDs), `generate_ssd_iteration2.py` |
| Author note | Drafted with Claude Code (GenAI); disclosed in the AI usage log. |

Same convention as `ssd_diagrams.drawio` (iteration 1): the system is one black box, numbered system operations are solid arrows, results are dashed, and the use-case extensions appear as `alt` / `opt` fragments. Each page carries its FRs and rationale in its header box.

| SSD | System operations | FRs | Rationale in one line |
|---|---|---|---|
| A3 | `openJoinCommunity`, `selectCommunity`, `checkLocality`, `submitJoinRequest` | FR-A-06 to A-09, NFR-PR-01 | The member only ever sees coarse outcomes; every uncertain outcome still creates a request for a moderator |
| A4 | `openMembershipQueue`, `openRequest`, `requestInformation` (opt), `decide` | FR-A-08, A-10, A-11, NFR-S-03 | A reason is always required and a decision applies only while the request is undecided |
| D1 | `openReview`, `submitReview`, `editReview` (opt) | FR-T-09, FR-B-15, NFR-U-01 | Only the two parties to a completed loan review, once each; flags are internal (D19) and reviews never enter the trust estimate |

**Maps to:** the membership state machine (M01 to M08) and the membership-decision activity diagram for A3 and A4; wireframes W9 to W11 (A3, A4) and W15 (D1); build items F2 and F3 (Fatima) and A3 (Areeba). UC-D1 is listed in brief form in Use Cases v1.3; its dressed version is part of DA-02 (Use Cases v1.4), and this SSD should be checked against it once that is written.
