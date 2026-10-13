# Slices B and C: branch, commit and pull-request plan

| Field | Value |
| :--- | :--- |
| Version | 1.0, 13 October 2026 |
| Source | `DigitalMohalla_Iteration1_Plan_Ver1.md` (Part B, work division) and `14_testing/Test_Plan.md` v1.3 (suites 1 to 19, TC numbers, gates in §5, regression policy in §11) |
| Team | S1 Fatima Khursheed (lifecycle, indirect trust, locality, CI) · S2 Areeba Javed (estimation, policy, detection) · S3 Minahil Kashif (moderation, evaluation, apps, deployment) |
| Applies to | All work after release PR #8 (`develop` merged into `main`, Slice A) |

## 1. How we work (same as Slice A)

1. **All three work together on one laptop** (Minahil's clone). Every commit is recorded with its owner as **both author and committer**, set at the moment of committing, for example:

   ```bash
   git -c user.name="Fatima Khursheed" -c user.email="ftmkhursheed2@gmail.com" commit -m "feat(indirect): ..."
   ```

   Areeba: `Areeba Javed <i230570@isb.nu.edu.pk>` · Minahil: `Minahil Kashif <minahilkashif1117@gmail.com>`. The owner is present and reviews their own commits before they are made. Shared commits rotate the author (next: Fatima) with the others as `Co-authored-by:` lines.
2. **One branch per piece of work**, started from the latest `develop` (`git switch develop && git pull && git switch -c feature/<area>-<topic>`).
3. **Small commits**: one commit is one step that still passes the tests, **with its test in the same commit** (test plan suites 6 to 14 are written during the slices, not after). Message types: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`, `ci:`. AI-assisted commits end with the assistant's `Co-Authored-By:` line, and the pull request adds a row to `docs/ai-usage-log.md`.
4. **Before pushing**, the checks CI runs are run locally (README section 7). Pull requests go into `develop`; Minahil opens them, so Fatima or Areeba approves (the person who opened a pull request cannot approve it); where possible the approver is not the commits' owner.
5. **Merge only when the three CI checks are green and one review approves**, with **Create a merge commit** (never squash). Delete the branch after merging.
6. **Release** at each gate: a pull request `develop` into `main` (Gate D-8 after Slice B; Gate D-5 and tag `v0.1.0-rc1` after Slice C).
7. **Testing after development** (freeze, D-5 to D-0): suite 15 (transition latency, deployed smoke) and system tests on the deployed instance, with a defect log (severity, fix, retest).

## 2. Before Slice B starts (decisions the code depends on)

| # | Decision | Who | Why it blocks |
| :--- | :--- | :--- | :--- |
| P1 | Sign ADR-0006 (trust-edge weight rule, in `03_architecture/DigitalMohalla_ADRs_Ver1.md`) | S1 and S2 | k-hop edge weights |
| P2 | Confirm the outcome mapping, assumption A1 in `data/generators/README.md` (which party gets which metric, how a dispute's fault becomes success or failure) | S2 | Outcome extraction, scenario expectations |
| P3 | SUFFICIENT_EVIDENCE thresholds (context document §15) | S2 | Decision policy, ES-02 |
| P4 | ES-05 expected state: fixture says SUFFICIENT_EVIDENCE (R8), requirements table says REVIEW_RECOMMENDED | S2 with S3 | Scenario suite |
| P5 | ES-13 expected state (still open in the context document) | S1 and S2 | Scenario suite |
| P6 | **Number clash:** the ADR document uses ADR-0006 for the trust-edge weight rule, while the tech stack document, CLAUDE.md and the README use ADR-0006 for the hosting decision. Proposal: record hosting as the next free number, ADR-0009, and update those three files | S1 (ADR lead) | Report and viva consistency; the hosting decision blocks deployment |

**Status (13 October):** P1 to P5 decided, recorded in `Team_Decisions_2026-10-13.md` (D10 to D14). P6 is deferred until the hosting decision, when CD starts.

## 3. Slice B: assurance core (D-11 to D-8)

Branches are listed in merge order; branches on the same row step can be built at the same time.

| Order | Branch | Owner | Commits (each with its tests) | Test cases (Test Plan v1.3) | Approver |
| :--- | :--- | :--- | :--- | :--- | :--- |
| B1 | `feature/outcome-extraction` | S2 Areeba | 1. outcome rows written on `transaction_closed` and `dispute_resolved` only (confirmed outcomes; disputed loans give none) · 2. category, value band and duration snapshot · 3. integration tests against the loaded `mini` dataset | suite 16: TC-23, TC-67 (engine feed), TC-69, TC-76 | S1 Fatima |
| B2 | `feature/beta-posterior` | S2 Areeba | 1. recency weight `2^(-d/180)` · 2. value-band and similarity weighting with the floor · 3. recency-weighted Beta posterior and 90% interval · 4. property tests (Hypothesis) | suite 6: TC-20 to TC-24, TC-77 | S1 Fatima |
| B2 | `feature/trust-edges` | S1 Fatima | 1. trust-edge projection from valid outcomes (ADR-0006) · 2. refresh when outcomes arrive · 3. tests against `data/derived/mini/trust_edge.csv` | suite 7: TC-27 (edge weights) | S2 Areeba |
| B3 | `feature/khop-search` | S1 Fatima | 1. bounded path search to k with cycle safety · 2. hop decay, one path per first-hop neighbour, noisy-OR, cap ρ ≤ 0.6 · 3. hand-worked graph test with a NetworkX cross-check · 4. k-sweep benchmark (k = 1 to 4) on the `scale` tier, latency and coverage saved with the config version | suites 7, 8: TC-25, TC-26, TC-28, k sweep | S2 Areeba |
| B4 | `feature/decision-policy` | S2 Areeba | 1. decision table R1 to R9 with safeguards · 2. explanation records (never a single number) · 3. real `assess()` combining direct and indirect evidence, replacing the stub · 4. `config_version` stored with every assessment; engine timeout still goes to HELD_FOR_REVIEW | suites 9, 10: TC-29 to TC-35, TC-36, TC-37, TC-39, TC-71, TC-74, TC-75 | S1 Fatima |
| B5 | `feature/scenario-suite` | S3 Minahil | 1. `backend/tests/scenarios/` running the fixtures ES-01 to ES-06 and ES-13 · 2. the same cases from `data/derived/*/labels/scenario_manifest.csv` loaded into PostgreSQL · 3. state **and** explanation compared | suite 11: TC-40, TC-41, TC-42, TC-45, TC-46, TC-47 | S1 Fatima or S2 Areeba |
| B6 | `feature/lender-evidence-screen` | S3 Minahil | 1. API fields for the evidence summary (agree the shape with S1, who owns the API) · 2. regenerate the typed client · 3. lender screen: interval, evidence count, paths, safeguards · 4. UI tests | suite 19: TC-100 | S1 Fatima or S2 Areeba |

**Gate D-8**: ES-01, ES-02, ES-03, ES-06 and ES-13 pass in CI with state and explanation. Release pull request `develop` into `main`.

## 4. Slice C: human loop (D-8 to D-5)

| Order | Branch | Owner | Commits (each with its tests) | Test cases (Test Plan v1.3) | Approver |
| :--- | :--- | :--- | :--- | :--- | :--- |
| C1 | `feature/manipulation-checks` | S2 Areeba | 1. S1 reciprocal clustering · 2. S4 review-text similarity · 3. corroboration rule (ADR-0007) and risk level · 4. retaliation check · 5. dense legitimate group stays below the threshold (case C3 in `neighborhood-sim`) | suites 9, 12, 11: TC-30, TC-38, TC-43, TC-44 | S1 Fatima |
| C1 | `feature/disputes` | S3 Minahil | 1. raise and withdraw a dispute (B12), the loan freezes · 2. escalation case with evidence trail (D6) · 3. API and tests | suite 13: TC-50 to TC-52 | S1 Fatima or S2 Areeba |
| C2 | `feature/moderator-decisions` | S3 Minahil | 1. decisions for disputes and holds (I4), mandatory reason · 2. the resolved outcome counts as evidence (uses B1) · 3. hold ends cleared, with safeguards, or declined | suite 13: TC-53 to TC-57 | S1 Fatima or S2 Areeba |
| C2 | `feature/privacy-checks` | S1 Fatima | 1. no address, coordinates or CNIC in any API response · 2. none in logs · 3. the locality method, only if the D-11 gate chose it | suites 14, 17: TC-58 to TC-60, TC-84 (fuzzing), TC-85 (uploads) | S2 Areeba |
| C3 | `feature/moderator-app` | S3 Minahil | 1. moderator queue (W6) · 2. case adjudication (W7) · 3. dispute form (W5) · 4. minimal audit-log view (I6) | suite 19: TC-105 to TC-107 (and gap UI-2, audit view) | S1 Fatima or S2 Areeba |

**Gate D-5**: feature freeze, release pull request `develop` into `main`, tag `v0.1.0-rc1`.

## 5. Still open from B0 and Slice A

### 5.1 Work items

| Branch | Owner | What | Blocked by |
| :--- | :--- | :--- | :--- |
| `infra/docker-compose` | S1 Fatima | Docker Compose with PostgreSQL and the API (plan B0) | nothing |
| `ci/cd-deploy` | S3 Minahil | First deployment, CD workflow and deployed smoke test TC-91 (plan B0 and Slice A) | hosting decision (P6) |
| `chore/dependabot-typescript` | S1 Fatima | Stop Dependabot proposing TypeScript major upgrades (TypeScript 7 does not match Expo SDK 57); close its open pull request | nothing |

### 5.2 Slice A test cases not yet written (Gate D-11 in Test Plan §5)

Slice A's tests cover most of TC-01 to TC-14 (transition matrix, replay, double booking, authorisation, append-only log and tampering), the engine-failure hold (part of TC-36), the response privacy check (part of TC-58) and login refusal (part of TC-80). These are still missing and should be added in small `test:` branches alongside Slice B:

| Branch | Owner | Test cases |
| :--- | :--- | :--- |
| `test/lifecycle-gaps` | S1 Fatima | TC-16 (Hypothesis random valid sequences replay), TC-65 (required deposit not recorded), TC-68 (late return), TC-70 (duplicate pending request), TC-72 (frozen event fields), TC-78 (API contract) |
| `test/api-security-basics` | S1 Fatima | TC-80 (expired and tampered tokens), TC-81 (client-set actor or state ignored), TC-82 (other pair's data refused), TC-83 (no plaintext password or token in logs), TC-87 (add gitleaks to CI), TC-90 (build smoke: empty database, migrate, seed, `/health`) |
| `test/ui-slice-a` | S3 Minahil | TC-101 to TC-104 (W2, W3a, W3b, W4 component tests with a mocked API) |

Tools named in the test plan that are not installed yet (add them to the dependency register when a branch first uses them): Hypothesis is installed; Schemathesis (TC-78, TC-84), gitleaks (TC-87), pytest-benchmark (suite 8), Locust is installed (TC-61), Maestro (suite 19 system flows, TC-73, TC-92), Trivy (with Docker images).

### 5.3 After all three slices (freeze, D-5 to D-0)

Test Plan §5 and §11 to §12: full regression run saved with the commit SHA and config version; suite 15 (TC-61 latency P95, TC-63 demo story, TC-73 phones); smoke TC-92 before each rehearsal; the alpha session (§12.1) with every finding in the defect log; tag `v0.1.0-mid1`.

## 6. Pull-request description template

```text
<Slice and owner>: <what this adds>

- <one line per commit>

Tests: <suites>, <how many passed locally>
Decisions used: <P1 to P5, or none>
AI assistance: <yes, logged in docs/ai-usage-log.md | no>
```
