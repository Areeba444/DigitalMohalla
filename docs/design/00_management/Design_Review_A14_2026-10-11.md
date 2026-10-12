# Design Review and Notation Conformance (step A14), 11 October 2026

| Field | Value |
|---|---|
| Version | 1.0, 11 October 2026 |
| Reviewer | Integration review by Student 1, drafted with Claude (GenAI; to be disclosed on Form 13) |
| Scope | Every diagram (20 files, 32 pages) and the completeness of Part A |
| Method | Each page rendered with the official draw.io viewer and inspected against its notation standard; automated checks `14_testing/verify_design.py` C01–C12 (C12 encodes the notation rules below); every generated diagram also passes the layout checker in `_tools/drawio.py` (no edge through a shape, no overlapping labels or shapes) |
| Result | All diagrams conform to their standard. Seven had notation faults: three were fixed in place, and four were redrawn as generators with their content unchanged (originals in `archive_v1/`). A2 and A7 are now complete |

## 1. Standards applied

| Diagram kind | Standard | Key rules checked |
|---|---|---|
| Use case | UML 2.5 | Actors outside the system boundary only; associations plain lines; «include» / «extend» dashed open arrows, «extend» pointing to the base use case, which lists the extension point; generalisation hollow triangle |
| SSD | UML 2.5 sequence, Larman SSD convention | System as one black-box lifeline; system events solid filled arrows; replies dashed; combined fragments with operator and guards |
| Component | UML 2.5 | «component» with component icon; provided interface ball; required interface as «use» dependency; nested components; subsystem boundary |
| Layer | UML 2.5 package diagram | Packages as folders with «layer»; «use» dependencies dashed with open heads |
| Deployment | UML 2.5 | Nodes as 3-D boxes («device», «executionEnvironment»); artifacts as rectangles with «artifact» and document icon; communication paths as associations (no arrowheads); comments as folded notes |
| Domain model, class | UML 2.5 class diagrams | Compartments; multiplicities; composition ◆, aggregation ◇, dependency dashed open arrow, realisation dashed hollow triangle; packages as folders; conceptual model without operations |
| ER | Crow's-foot (Information Engineering) | PK/FK/UQ marked; cardinality at both ends; NOT NULL vs nullable shown |
| State machine | UML 2.5 state machine | Initial pseudostate, choice pseudostate, shallow history H, composite states; transitions labelled event [guard] / effect; final states |
| Sequence | UML 2.5 | Actors as stick figures; lifelines `:Class`; activation bars; sync filled / reply dashed / async open; alt/opt/ref frames with one guard per operand |
| Activity | UML 2.5 | Initial and final nodes; actions rounded; decision nodes without text and a guard on every outgoing edge; explicit merge nodes (no implicit joins); partitions; interruptible regions and accept/time events |
| DFD | Gane & Sarson (Yourdon levelling) | Context diagram: one process, no stores; processes numbered rounded boxes; stores open-ended with ID; every flow touches a process; level 1 balances level 0 |
| Wireframes | Low-fidelity convention (no formal standard) | Annotated widgets; evidence shown with every assurance state (NFR-U-01) |

## 2. Findings per diagram

| Diagram (owner) | Finding before review | Action | Status |
|---|---|---|---|
| Use case diagram (S3) | The Trust Engine, an internal component, was drawn as an actor; an «extend» label covered the B8 ellipse; associations crossed use cases; no extension points | **Redrawn** (`generate_use_case_diagram.py`, v0.3): Trust Engine removed as actor, extension points listed, clean routing; Use Cases v1.3 D3/4/5 and D6 note the change | Conforms |
| SSDs (S3) | — | None needed | Conforms |
| Component diagram (S1) | PostgreSQL drawn as a cylinder (not UML) | Drawn as an external «component» | Conforms |
| Layer diagram (S1) | Layers as plain boxes, solid arrows (not UML) | Converted to a UML package diagram («layer» folders, dashed «use» dependencies) | Conforms |
| Deployment diagram (integration) | Artifacts used the comment shape; communication paths had arrowheads; one dangling line | Artifacts as rectangles with icon, associations without heads, comments as notes | Conforms |
| Domain model (all) | Draft v0.9 | v1.0 baseline (decision D18) | Conforms |
| Class diagram S1 | — | None needed | Conforms |
| Class diagrams S2, S3 | **Missing** (A7) | **Created** from the Algorithm doc, assurance data dictionary, use cases and schema; every class names its FRs | Conforms; owners to review |
| ER diagram (S1) | — | Regenerated for schema v2.3 | Conforms |
| State machines (S1) | Guard text still "risk ≥ 60", stale baseline version | Guards name the A5 rules (ADR-0007); v2.2 | Conforms |
| Sequence (a) (S2) | Actors drawn as boxes; no activations; `alt` operator, guards and message labels overlapped; the locality `alt` had one operand, so the normal flow appeared to run after a hold | **Redrawn** (`generate_sequence_a.py`, v1.2) with the same messages; locality `alt` with `[else]`, engine `alt` nested | Conforms |
| Sequence (b) (S1) | One self-message label ran off the page; stale note | Fixed | Conforms |
| Sequence (c) (S3) | — (labels corrected in integration) | None needed | Conforms |
| Decision-policy activity (S2) | Text inside decision diamonds with "[else]" guards elsewhere; flows from two branches entering one action (implicit join); tangled routing through rule boxes | **Redrawn** (`generate_decision_policy_activity.py`, v1.2): empty decisions with guards on every edge, explicit merges, partitions = components | Conforms |
| Dispute-resolution activity (S3) | — | None needed | Conforms |
| DFD L0/L1 (S2) | Circle processes (Yourdon) mixed with open-ended stores (Gane & Sarson); level 0 showed data stores; administrator flow went straight into a store; level 1 did not balance level 0; overlapping labels | **Redrawn** (`generate_dfd.py`, v1.2) in strict Gane & Sarson with S2's processes and flow IDs; processes 9.0, 10.0 and store D5 added for balancing and the privacy boundary | Conforms |
| k-hop worked example (S1) | A worked-example graph, not a UML diagram | None needed | — |
| Wireframes (integration) | — | None needed | Conforms |

## 3. Completeness of Part A

| Step | Status after this review |
|---|---|
| A0 clean-up | Done inside the design folder; the "project instructions" wording (Beta-Binomial, M1–M9) is outside it |
| A1 ADRs | Done (ADR-0001 to ADR-0008) |
| A2 domain model | **Done** (v1.0, D18) |
| A3 state machines | Done |
| A4 data dictionary | Done |
| A5 algorithms and policy | Done |
| A6 ER and schema | Done (44/44 schema tests) |
| A7 class diagrams | **Done** (Students 1, 2 and 3) |
| A8 architecture | Done |
| A9 behaviour diagrams | Done |
| A10 DFD | Done |
| A11 locality | Done |
| A12 wireframes | Done |
| A13 test plan and deployment | Done (target to be confirmed with the stack) |
| A14 design gate | This review covers notation and consistency. Still open: the stack decision (D-15), confirmation of the deployment target, and the tag `design-v1.0` once the repository exists. Sign-offs were set aside at the user's instruction |
