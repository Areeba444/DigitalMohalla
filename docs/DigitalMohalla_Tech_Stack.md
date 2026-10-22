# Digital Mohalla — Technology Stack

| Field | Value |
| :--- | :--- |
| Document | Technology stack and ADR-0005 (stack choice) |
| Version | 1.0 |
| Date | 2026-10-11 |
| Authors | Team Digital Mohalla (drafted with Claude; reviewed by: Fatima Khursheed, Areeba Javed, Minahil Kashif) |
| Status | Proposed. Becomes accepted when all three students sign off (§13). Hosting is to be decided (§9). |
| Applies to | Iteration 1 build (Part B) onward; companion to `DigitalMohalla_Project_Context.md` |

---

## 1. Summary

| Layer | Choice |
| :--- | :--- |
| Backend | **Python 3.12 + FastAPI** |
| Database | **PostgreSQL 16** (with the `btree_gist` extension) |
| Database access | **SQLAlchemy 2.0** (synchronous, Core for the event store) + **Alembic** migrations, **psycopg 3** driver |
| Assurance engine maths | **NumPy + SciPy**; own k-hop graph search in plain Python |
| Frontend | **React Native via Expo** (TypeScript, Expo Router), one codebase: Android app for residents, web build for the moderator console and the demo |
| CI/CD | **GitHub Actions**, **Docker** + Docker Compose, **GHCR** image registry, **EAS Build** for Android APKs |
| Reverse proxy / HTTPS | **Caddy** |
| Hosting | **To be decided** by D-14 (§9) |

Selection rules: the team knows React and FastAPI; the proposal (§8.1) names Python, FastAPI and PostgreSQL; ADR-0002 needs a PostgreSQL exclusion constraint; everything must be free; three people, two semesters, so no extra frameworks.

---

## 2. ADR-0005: Technology stack

**Status:** Proposed, 2026-10-11

**Context.** Iteration 1 needs a live core module with CI/CD before the mid eval. The core is custom logic (event store, transition table, recency-weighted Beta posterior, bounded k-hop search, manipulation checks, decision policy), served to a mobile app for residents and a desk view for moderators. The team knows some React and FastAPI. Hosting must cost nothing. NFR-D-05 assumed React Native/Expo for Android and iOS; NFR-D-03 named AWS.

**Decision.**
1. Backend: FastAPI on Python 3.12, synchronous SQLAlchemy 2.0 with Alembic, PostgreSQL 16.
2. Frontend: React Native via Expo with TypeScript; Android plus a web build from the same codebase; iOS not targeted.
3. Engine maths with NumPy and SciPy; the k-hop search is written by the team.
4. Everything runs in Docker; CI/CD on GitHub Actions; hosting chosen separately (ADR-0006, pending).

**Alternatives rejected.**

| Alternative | Why not |
| :--- | :--- |
| Django | Team doesn't know it; its strengths (ORM CRUD, admin, auth) matter little when the core is a custom event store and engine; learning it three weeks before mid is a risk. Its one real advantage, built-in Postgres exclusion constraints, SQLAlchemy + Alembic also handle. |
| Node.js backend | Splits the engine across languages; the numeric work belongs in Python. |
| MySQL / SQLite | No exclusion constraints on date ranges, which ADR-0002 depends on. |
| EventStoreDB, Kafka | Over-engineering; a Postgres table with an append-only trigger is enough and easier to explain. |
| Celery + Redis | Not needed until scheduled jobs (iteration 2); APScheduler covers that. |
| Kubernetes, microservices | One API container and one database are enough for this scale. |
| React (web only) | Team prefers React Native for the resident app; Expo's web target covers the moderator view from the same code. |
| Async SQLAlchemy | Harder to reason about in the concurrency tests; FastAPI runs synchronous endpoints in a thread pool, which is enough here. |
| NetworkX in the engine | k-hop propagation is part of the CCP, so the team writes and explains it; NetworkX is used only in tests to cross-check paths. |
| Redux | TanStack Query holds server state; local React state covers the rest. |

**Consequences.**
- NFR-D-05 changes to "Android via Expo (React Native); web build of the same app for the moderator console; iOS not targeted".
- NFR-D-03 changes from "Target per the confirmed stack is AWS" to "Docker-based deployment to a host chosen in ADR-0006; deployment and rollback rehearsed before release".
- Both edits go into FR/NFR v1.2 with a pointer to this ADR.
- Every dependency goes into the Form 13 dependency register (§11).

---

## 3. Backend

| Purpose | Choice | Notes |
| :--- | :--- | :--- |
| Language | Python 3.12 | One version across dev, CI and production images |
| Package and environment manager | uv, with a committed lock file | `uv sync` reproduces the environment exactly |
| Web framework | FastAPI | Generates the OpenAPI spec used for report §5.3 and the frontend client |
| ASGI server | Uvicorn | Run inside the API container |
| Validation and schemas | Pydantic v2 | Request/response models; event payload schemas per `event_type` if N-6 uses a `payload` field |
| Settings and engine config | pydantic-settings + a YAML engine config (PyYAML) | All engine parameters in `backend/config/engine.yaml`; `config_version` = hash of the file, stored on every assessment (NFR-D-01) |
| Database toolkit | SQLAlchemy 2.0, synchronous; Core for the event store, ORM optional for read models | |
| Migrations | Alembic | Every schema change is a migration; tag `schema-v1` at the first frozen migration |
| Database driver | psycopg 3 | |
| Engine maths | NumPy, SciPy (`scipy.stats.beta` for the 90% credible interval) | |
| Graph search | Own adjacency-list bounded DFS | Owned by S1 (Module 5 indirect trust) |
| Authentication | JWT bearer tokens (PyJWT); passwords hashed with argon2 (argon2-cffi) | Meets NFR-S-01; roles carried in the token, checked on every transition (NFR-S-02) |
| File uploads | python-multipart | Handover and return photos (optional in iteration 1) |
| Logging | structlog, JSON output | A processor drops location and identifier fields (NFR-PR-01) |

### Database details
- PostgreSQL 16 with `CREATE EXTENSION btree_gist` for the overlap constraint: `EXCLUDE USING gist (item_id WITH =, daterange(start_date, end_date) WITH &&) WHERE (status IN ('ACCEPTED','ACTIVE'))` on the bookings table (ADR-0002).
- Event store: one `events` table; unique (`stream_id`, `stream_seq`); a trigger that rejects UPDATE and DELETE; each row carries a SHA-256 hash of the previous row's hash plus its own content, so tampering is detectable (NFR-S-05).
- JSONB available for event-specific data if N-6 chooses a `payload` field.
- Read models (current transaction state, trust edges, assessments, cases) are projections rebuilt from events; the replay test compares them with stored state (NFR-R-03).

---

## 4. Frontend

| Purpose | Choice | Notes |
| :--- | :--- | :--- |
| Framework | React Native via Expo (managed workflow), TypeScript | Pin the Expo SDK version at project start; upgrade only between iterations |
| Navigation | Expo Router | File-based routes; separate route groups for resident and moderator screens |
| UI components | React Native Paper | Works on Android and the web target |
| Server state and API calls | TanStack Query + a typed client generated from FastAPI's OpenAPI spec (openapi-typescript + openapi-fetch) | Regenerate the client in CI so frontend and backend can't drift |
| Forms | react-hook-form + zod | |
| Token storage | expo-secure-store on Android; in-memory or session storage on web | |
| Location | expo-location | Coarse locality only; never store raw traces (NFR-PR-02) |
| Camera and photos | expo-image-picker | Handover and return checklists |
| Builds | Web: `expo export` (static files). Android: EAS Build on iteration tags, or `eas build --local` | EAS free plan has a limited number of low-priority builds per month, so build APKs only on tags |
| Platforms | Android (residents); web build (moderator console, demo on a laptop) | iOS not targeted: distribution needs a paid Apple developer account |

Every screen that shows an assurance state also shows its evidence; no single trust number anywhere (NFR-U-01).

---

## 5. Testing

| Purpose | Tool | Covers (plan test suites) |
| :--- | :--- | :--- |
| Backend unit and integration | pytest, pytest-cov | All suites 1–15 |
| Property-based tests | Hypothesis | Beta maths (6), transition matrix (1), policy table (9) |
| API tests | FastAPI TestClient (httpx) | Authorisation (4), dispute and hold resolution (13), privacy (14) |
| Database in tests | Real PostgreSQL 16 (Docker locally, service container in CI) | Double booking (3), append-only (5), replay (2) |
| k-hop cross-check | NetworkX (tests only) | k-hop hand graph (7) |
| Load and latency | Locust | k sweep (8), transition latency (15), NFR-P-03/P-04 |
| Frontend unit | Jest (jest-expo) + React Native Testing Library | Screens and components |
| End-to-end smoke | Playwright against the web build | Deployed smoke test (15) |
| Mobile end-to-end | Deferred (Maestro is a candidate for iteration 3) | — |

Coverage floor (proposed): 80% lines on the engine and lifecycle packages. Scenario fixtures are synthetic and labelled; the held-out attack generator (iteration 3) lives in a separate package.

---

## 6. Code quality and static analysis

| Area | Backend | Frontend |
| :--- | :--- | :--- |
| Lint and format | ruff (lint + format) | ESLint (`expo lint`) + Prettier |
| Types | mypy on engine and lifecycle packages | `tsc --noEmit` |
| Security / dependencies | bandit, pip-audit | `npm audit` |
| Pre-commit | pre-commit hooks for ruff and Prettier | |
| Dependency updates | Dependabot (pip, npm, GitHub Actions) | |

---

## 7. CI/CD and infrastructure

| Purpose | Choice |
| :--- | :--- |
| Source control | GitHub; protected `main` and `develop`; `feature/*`, `fix/*`, `docs/*`; one non-author approval per merge |
| CI | GitHub Actions `ci.yml`: lint, types, security scan, unit, integration (Postgres service container), scenario suite, frontend lint/type/test, web build, OpenAPI client regeneration check; JUnit and coverage uploaded as artifacts |
| CD | GitHub Actions `cd.yml` on push to `main`: build Docker images tagged with the commit SHA → push to GHCR → deploy to the host (method depends on §9) → smoke test → redeploy previous image on failure |
| Containers | Docker; Docker Compose for local dev and single-host deployment (`api`, `db`, `caddy` services) |
| Images | Multi-architecture builds (amd64 + arm64) with Docker Buildx, so any §9 candidate works |
| Registry | GitHub Container Registry (GHCR) |
| HTTPS / reverse proxy | Caddy with automatic certificates; also serves the Expo web build as static files. HTTPS is required for browser geolocation |
| Mobile builds | EAS Build on iteration tags (`v0.1.0-mid1` etc.), APK attached to the GitHub release |
| Secrets | GitHub Environments; never committed |
| Seed and reset | `scripts/seed_demo.py` (synthetic users labelled synthetic) and a reset command for demos |

---

## 8. Repository layout

```text
backend/
  app/
    api/                 # FastAPI routers, request/response models
    domain/
      lifecycle/         # Module 3: transition table, aggregate, commands
      assurance/
        estimation/      # Module 5: recency-weighted Beta posterior
        indirect/        # Module 5: trust edges, bounded k-hop
        detection/       # Module 5: manipulation checks
        policy/          # Module 5: decision policy, explanation, safeguards
      moderation/        # Module 9: cases, decisions, audit view
      accounts/          # Module 1: users, communities, locality stub
    infra/
      db/                # SQLAlchemy engine, sessions, projections
      eventstore/        # append, read stream, replay, hash chain
    config/              # settings loader, config_version
  config/engine.yaml     # all engine parameters with their sources
  alembic/               # migrations
  tests/
    unit/  integration/  scenarios/   # scenarios = ES-01..ES-06, ES-13 fixtures (synthetic)
  pyproject.toml  uv.lock
frontend/                # Expo app
  src/app/(resident)/  src/app/(moderator)/   # Expo Router routes (Expo template keeps routes under src/app)
  src/api/               # generated OpenAPI client
infra/
  docker-compose.yml  Caddyfile  deploy/
scripts/                 # seed, reset, load tests
docs/
  adr/  design/  ai-usage-log.md  dependency-disclosure.md
.github/workflows/ci.yml  cd.yml
CLAUDE.md                # project context for Claude Code
```

---

## 9. Hosting — to be decided

**Decide by D-14** (before Slice A's first deployment). Record the choice as ADR-0006 and update NFR-D-03.

### Requirements any host must meet
1. Free for the whole FYP (through FYP-2 Final), not a short trial.
2. Runs the API container from GHCR; reachable by CD (SSH, deploy hook or git push).
3. PostgreSQL 16 with the `btree_gist` extension, persisting beyond 30 days.
4. HTTPS on a stable address.
5. Persistent storage for handover and return photos (or an external free object store).
6. Awake for the demo without a long cold start, or a reliable warm-up step.
7. No exact location or identifiers in host logs (NFR-PR-01).

### Candidates (as checked on 2026-10-11; recheck before deciding)

| Option | Fit | Main catch |
| :--- | :--- | :--- |
| Oracle Cloud Always Free VM | Runs the full Docker Compose stack (API, Postgres, Caddy) on one ARM VM; no expiry | Card needed for sign-up verification; ARM capacity can be hard to get; idle VMs can be reclaimed |
| Render (API) + Neon (Postgres) | No card; Neon free Postgres is permanent and supports `btree_gist` | Render free services sleep after 15 minutes idle (about a minute to wake); temporary filesystem, so photos need external storage; Render's own free Postgres expires after 30 days, so don't use it |
| Azure for Students | No card; credit for students | Credit-based, so a VM running all year must stay small; renewal depends on student status |
| AWS (currently named in NFR-D-03) | Familiar | New-account free plan is credit-based and ends after 6 months, so it does not last the whole FYP |

Whichever is chosen, the stack stays in Docker, so switching provider changes only the CD deploy step and connection settings.

---

## 10. Deferred to later iterations

| Technology | Purpose | When |
| :--- | :--- | :--- |
| APScheduler | B13 scheduled jobs: expiry, no-show, reminders, overdue escalation | Iteration 2 |
| Expo push notifications | G3 push channel | Iteration 3 |
| SMTP email (free provider) | G3 email channel | Iteration 3 |
| S3-compatible object storage | Photos at pilot scale | Iteration 3 (if the host lacks persistent disk) |
| sentence-transformers + FAISS | Module 4 semantic search (B3) | Iteration 3 |
| LightGBM | Learning-to-rank, only if search ever needs it | Not planned |
| Maestro | Mobile end-to-end tests | Iteration 3, if time |

---

## 11. Dependency register (Form 13 starting point)

Licences are the commonly published ones; confirm each at install time and record the pinned version.

| Dependency | Role | Licence (verify) |
| :--- | :--- | :--- |
| Python | Language | PSF |
| FastAPI | Web framework | MIT |
| Uvicorn | ASGI server | BSD-3-Clause |
| Pydantic, pydantic-settings | Validation, settings | MIT |
| SQLAlchemy | Database toolkit | MIT |
| Alembic | Migrations | MIT |
| psycopg 3 | PostgreSQL driver | LGPL-3.0 |
| NumPy | Numerics | BSD-3-Clause |
| SciPy | Beta distribution | BSD-3-Clause |
| PyYAML | Engine config | MIT |
| PyJWT | Tokens | MIT |
| argon2-cffi | Password hashing | MIT |
| python-multipart | Uploads | Apache-2.0 |
| structlog | Logging | MIT / Apache-2.0 |
| PostgreSQL | Database | PostgreSQL Licence |
| React Native, Expo, Expo Router | Frontend | MIT |
| React Native Paper | UI components | MIT |
| TanStack Query | Server state | MIT |
| openapi-typescript, openapi-fetch | Typed API client | MIT |
| react-hook-form, zod | Forms, validation | MIT |
| pytest, pytest-cov | Tests | MIT |
| Hypothesis | Property tests | MPL-2.0 |
| NetworkX (tests only) | k-hop cross-check | BSD-3-Clause |
| Locust | Load tests | MIT |
| Playwright | End-to-end tests | Apache-2.0 |
| Jest, React Native Testing Library | Frontend tests | MIT |
| ruff, mypy | Lint, types | MIT |
| bandit | Security scan | Apache-2.0 |
| pip-audit | Dependency audit | Apache-2.0 |
| ESLint, Prettier, TypeScript | Frontend quality | MIT / MIT / Apache-2.0 |
| eslint-config-expo (dev; 57.0.2 installed 2026-10-13, with eslint 9.39.5) | Expo's ESLint rules | MIT |
| @react-native/jest-preset (dev; ^0.86.3, matches React Native 0.86) | Peer of jest-expo 57 | MIT |
| @expo-google-fonts/fraunces (^0.4.1), @expo-google-fonts/plus-jakarta-sans (^0.4.2); installed 2026-10-13 | App typefaces from the team's design system (Fraunces headlines, Plus Jakarta Sans text); only 7 weights are loaded | Packages MIT; fonts SIL Open Font License 1.1 |
| uv | Python packaging | MIT / Apache-2.0 |
| Docker Engine, Compose | Containers | Apache-2.0 |
| Caddy | Reverse proxy, HTTPS | Apache-2.0 |
| GitHub Actions, GHCR, EAS Build | CI/CD services | Hosted services (terms of service) |
| actions/checkout, actions/setup-node, actions/upload-artifact (v4); astral-sh/setup-uv (v6) | CI steps in `.github/workflows/ci.yml` | MIT |

---

## 12. Who sets up what (B0)

| Student | Responsibility |
| :--- | :--- |
| S1 | Repo, branch protection, `ci.yml`, backend skeleton (uv, FastAPI, SQLAlchemy, Alembic, Postgres with `btree_gist`), event store, pre-commit |
| S2 | Engine package skeleton, `engine.yaml` with every parameter and its source, `config_version`, scenario fixture format |
| S3 | Expo app skeleton (Expo Router, Paper, generated API client), Docker Compose, Caddy, `cd.yml`, EAS setup, hosting evaluation for ADR-0006 |

---

## 13. Sign-off

| | Student 1 | Student 2 | Student 3 | Date |
| :--- | :--- | :--- | :--- | :--- |
| ADR-0005 accepted | | | | |
| ADR-0006 (hosting) accepted | | | | |
