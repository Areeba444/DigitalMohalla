# Digital Mohalla

A neighbourhood resource-sharing platform (lending, borrowing, donation) built as a Final Year Project at FAST School of Computing, FAST-NUCES Islamabad.

The technical core is a **trust and risk decision engine**. It estimates whether a physical handover is safe from sparse, indirect and potentially manipulated evidence, reports its own uncertainty, and recommends safeguards or human escalation. Listings, workflow and UI exist to feed or act on that decision. The app shows decision support, never a single trust score and never a guarantee.

- **Team:** Fatima Khursheed, Areeba Javed, Minahil Kashif
- **Supervisor:** Dr. Ali Zeeshan
- **Stage:** Iteration 1 (FYP-1 Mid), Part B (implementation)

> **Synthetic data only.** Every user, item and scenario in this repository is synthetic and labelled so. No real personal data, exact location or CNIC is stored anywhere.

---

## Contents

1. [Current status](#1-current-status)
2. [Tech stack](#2-tech-stack)
3. [Repository layout](#3-repository-layout)
4. [Prerequisites](#4-prerequisites)
5. [First-time setup](#5-first-time-setup)
6. [Running the app](#6-running-the-app)
7. [Running the tests and checks](#7-running-the-tests-and-checks)
8. [Working on the code](#8-working-on-the-code)
9. [Documentation map](#9-documentation-map)
10. [Team workflow](#10-team-workflow)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Current status

| Area | State |
| :--- | :--- |
| Design baseline (Part A) | Complete: `docs/design/` |
| Database schema v2.3 | Applied by Alembic migration 0001 (tables, lifecycle triggers, hash-chained append-only log, no-double-booking constraint) |
| Borrowing lifecycle (request → locality → assessment → accept → handover → return → completed) | Done, with event store, replay and audit of rejected commands |
| Assurance engine | **Placeholder only.** A stub always answers "not enough history yet". The real engine is Slice B |
| Login and roles | Done (argon2 passwords, JWT tokens) |
| REST API (`/api/v1`) | Done for the Slice A loop |
| Web UI (Expo) | Done for Slice A: login, home, browse, new request, lender evidence screen, handover, return. Three themes to choose from |
| Disputes, moderator console, audit view | Not yet (Slice C) |
| k-hop indirect trust, manipulation checks, decision policy | Not yet (Slices B and C) |
| CI pipeline | GitHub Actions (`.github/workflows/ci.yml`): backend, frontend and API-client checks on every push and pull request; Dependabot weekly. Runs once the code is on GitHub |
| Docker, deployment (CD) | API image (`backend/Dockerfile`) and Render Blueprint (`render.yaml`): Render (API) + Neon (PostgreSQL 16), deploying `main` after CI passes. Setup steps in `infra/deploy/README.md`; ADR-0006 to be recorded |

The plan, slices and gates are in `docs/DigitalMohalla_Project_Context.md` (sections 9 to 13).

## 2. Tech stack

| Layer | Choice |
| :--- | :--- |
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Database | PostgreSQL 16 with the `btree_gist` extension |
| Data access | SQLAlchemy 2.0 (synchronous, Core), Alembic migrations, psycopg 3 |
| Auth | argon2 password hashes, JWT bearer tokens (PyJWT) |
| Engine maths (later) | NumPy, SciPy; own bounded k-hop search |
| Frontend | React Native via Expo (TypeScript, Expo Router), web build first |
| Frontend data | TanStack Query, typed client generated from the backend OpenAPI spec (openapi-typescript, openapi-fetch) |
| Backend tooling | uv, pytest, ruff, mypy, bandit, pip-audit |
| Frontend tooling | TypeScript, Jest and Playwright (installed, not yet configured) |

The full list with licences is in `docs/DigitalMohalla_Tech_Stack.md`. Hosting: Render (API, Docker) and Neon (PostgreSQL 16), see `infra/deploy/README.md`; ADR-0006 to be recorded.

## 3. Repository layout

```text
backend/
  app/
    api/                  FastAPI routes, request/response models, dependencies
    domain/
      lifecycle/          transition table, aggregate, BorrowingService, ports, actions
      assurance/          engine package (stub.py now; estimation, indirect, detection, policy later)
      accounts/           login and tokens
      moderation/         (Slice C)
    infra/
      db/                 engine factory, user lookup
      eventstore/         event store and PostgreSQL adapters
    config/               settings and the engine-config loader
  alembic/                migrations (0001 applies docs/design schema v2.3)
  config/engine.json      versioned engine parameters (config_version on every assessment)
  tests/                  unit/ integration/ scenarios/
frontend/
  src/app/                Expo Router routes: login, (resident)/..., (moderator)/ (later)
  src/api/                generated API client and TanStack Query hooks
  src/components/         UI components and request screens
  src/theme/              the three themes and the theme provider
docs/
  design/                 Part A design baseline (diagrams, schema, ADRs, test plan, UI prototypes)
  DigitalMohalla_Project_Context.md   full project handoff
  DigitalMohalla_Tech_Stack.md        stack and ADR-0005
  ai-usage-log.md                     record of AI-assisted work (keep updated)
scripts/seed_demo.py      seed synthetic users and items
data/                     dataset catalogue, cards and requirements (raw files stay local)
infra/deploy/             deployment guide (Render + Neon)
render.yaml               Render Blueprint for the API service
.github/workflows/        CI (ci.yml); Render deploys main once CI passes
CLAUDE.md                 project rules and context for Claude Code
```

Architecture rule of thumb: the **database enforces the lifecycle rules** (allowed moves, who may act, no double booking, tamper-evident log). The Python service pre-checks, audits rejections and shapes responses, but does not duplicate the rules.

## 4. Prerequisites

| Tool | Version | Notes |
| :--- | :--- | :--- |
| Git | recent | |
| uv | recent | Runs Python for the backend. `pip install uv` or see docs.astral.sh/uv. It downloads Python 3.12 for you |
| Node.js | 24 | Includes npm |
| PostgreSQL | 16 | Needs the `btree_gist` extension (included in the standard installers) |

Installing PostgreSQL on Windows with Chocolatey (run in an **administrator** shell; pick your own password):

```powershell
choco install postgresql16 -y --params "/Password:<choose-a-password> /Port:5433"
```

The examples below assume a local server on port **5433** and the superuser `postgres`. Any port works if you change the URLs.

## 5. First-time setup

### 5.1 Clone and install

```bash
git clone https://github.com/Areeba444/DigitalMohalla.git
cd DigitalMohalla

# backend dependencies (creates backend/.venv)
cd backend
uv sync

# frontend dependencies
cd ../frontend
npm install --legacy-peer-deps
```

`--legacy-peer-deps` is needed because the Expo template ships TypeScript 6 while `openapi-typescript` asks for TypeScript 5. Add frontend packages with `npx expo install <package>`.

### 5.2 Create the databases

Create one database for development and one for tests (the test suite wipes and rebuilds its schema, so never point it at data you care about):

```bash
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE digitalmohalla"
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE digitalmohalla_test"
```

### 5.3 Configure environment variables

Backend: copy `backend/.env.example` to `backend/.env` and fill it in. It is gitignored.

```text
DATABASE_URL=postgresql+psycopg://postgres:<your-password>@localhost:5433/digitalmohalla
JWT_SECRET=<a long random string>
```

Generate a secret with `python -c "import secrets; print(secrets.token_hex(32))"`.

Frontend: copy `frontend/.env.example` to `frontend/.env.local` (gitignored):

```text
EXPO_PUBLIC_API_URL=http://localhost:8000
EXPO_PUBLIC_DEMO_PASSWORD=<the demo password from scripts/seed_demo.py>
```

`EXPO_PUBLIC_DEMO_PASSWORD` only enables the quick "demo account" buttons on the login screen. It is a throwaway value for local synthetic users (see `DEMO_PASSWORD` in `scripts/seed_demo.py`). Leave it empty to hide those buttons.

### 5.4 Create the schema and seed demo data

```bash
cd backend
uv run python ../scripts/seed_demo.py --reset
```

`--reset` drops the `dm` schema, re-applies the migration and inserts 5 synthetic users (a lender, two borrowers, a moderator, an admin), 1 community and 3 items. To apply the migration without seeding use `uv run alembic upgrade head`.

## 6. Running the app

Open two terminals.

**API** (http://localhost:8000, interactive docs at `/docs`):

```bash
cd backend
uv run uvicorn app.main:app --port 8000
```

Check it: http://localhost:8000/health returns `{"status":"ok"}`.

**Web app** (http://localhost:8081):

```bash
cd frontend
npm run web -- --port 8081
```

The very first bundle can take several minutes on a slow machine; later loads are fast.

### Try the loop

Demo accounts (password: the demo password above):

| Person | Email | Role in the demo |
| :--- | :--- | :--- |
| Bilal | `borrower@example.test` | borrower |
| Chand | `borrower2@example.test` | second borrower (for date conflicts) |
| Ayesha | `lender@example.test` | lender, owns the items |

1. Sign in as Bilal, **Browse items**, pick an item, **Send request**.
2. Sign out, sign in as Ayesha. Open the request: you see the evidence summary (interval bar, separate manipulation risk, safeguards). **Accept request**.
3. Ayesha records the handover checklist. Bilal confirms receipt. Bilal starts the return, Ayesha records the return inspection, Bilal agrees. The request is **Completed**.
4. Open **History of this request** to see the event stream.

The three theme buttons (Terracotta, Nordic, Midnight) at the top of the login and home screens let the team compare looks. The choice is remembered per browser.

## 7. Running the tests and checks

### Backend

```bash
cd backend
export TEST_DATABASE_URL="postgresql+psycopg://postgres:<your-password>@localhost:5433/digitalmohalla_test"
uv run pytest                      # all tests (integration tests skip if TEST_DATABASE_URL is unset)
uv run pytest tests/unit           # no database needed
uv run pytest --cov=app            # with coverage
uv run ruff check . && uv run ruff format --check .
uv run mypy                        # strict, on app/domain
uv run bandit -q -r app            # security scan
```

PowerShell sets the variable with `$env:TEST_DATABASE_URL = "..."`.

What the suite covers today (about 340 tests): the 294-pair transition matrix from the design, event replay, rejected-command audit, the full loop, locality and engine-failure holds, the no-double-booking race (5 simultaneous acceptances, exactly one wins), authorisation, login, the REST API and a privacy check that no location or secret fields appear in responses.

### Design checks

The design folder has its own generators and checks (`docs/design/README.md` lists them), including 44 schema tests:

```bash
cd backend
DM_TEST_DSN="postgresql://postgres:<your-password>@localhost:5433/digitalmohalla_test" \
  uv run --with psycopg2-binary python ../docs/design/06_data_model/test_schema.py
```

### Frontend

```bash
cd frontend
npx tsc --noEmit                   # type check
npx expo lint                      # ESLint (config: eslint.config.js)
npx jest                           # tests in __tests__/ (files ending -test.ts or -test.tsx)
```

### Synthetic test data

```bash
python -I data/generators/build.py --tier standard          # writes data/derived/standard
python -I data/generators/validate.py data/derived/standard
cd backend && uv run python ../scripts/load_dataset.py ../data/derived/standard --reset   # into a *_test database
```

Details: `data/generators/README.md`.

### Continuous integration (GitHub Actions)

`.github/workflows/ci.yml` runs on every pull request and on pushes to `main` and `develop`, on a clean Linux machine. Three jobs run side by side:

| Job | What it checks |
| :--- | :--- |
| Backend | ruff lint and format (backend, data generator, scripts), mypy, bandit; pip-audit as a warning; every backend test against a throwaway PostgreSQL 16, including the data generator and the dataset load. Test and coverage reports are kept as a downloadable artifact |
| Frontend | `npm ci`, `tsc --noEmit`, `expo lint`, Jest; npm audit as a warning |
| API client in sync | Re-exports the OpenAPI spec (`scripts/export_openapi.py`) and regenerates `schema.d.ts`; fails if either differs from the committed files |

A green tick means every check passed. To reproduce a failure locally, run the same command from the table above. Coverage is reported, not yet enforced (the tech stack doc proposes 80% on the engine and lifecycle packages once the engine exists).

## 8. Working on the code

### Changing the backend API

After changing routes or response models, regenerate the typed frontend client:

```bash
cd backend
uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > ../frontend/src/api/openapi.json
cd ../frontend && npm run api:generate
npx tsc --noEmit
```

Commit `openapi.json` and `schema.d.ts` with the change so the frontend and backend cannot drift.

### Changing the database

The schema in `docs/design/06_data_model/schema.sql` is a frozen baseline. Every change is a **new Alembic migration** in `backend/alembic/versions/`; never edit migration 0001 or its SQL. The **event schema is frozen**: do not add or rename event fields or event types without sign-off from all three students.

### Engine parameters

All tunable engine parameters live in `backend/config/engine.json` (initial, unvalidated values, each with its source). Every stored assessment records `config_version`. Never hardcode a threshold.

### Rules of the project (summary)

- Small changes; map each piece of work to a module in `docs/DigitalMohalla_Project_Context.md` section 4.
- Tests for anything touching state transitions, trust maths, propagation or detection. Every invalid transition is tested.
- Never show a single trust number. "Insufficient evidence" is not a negative finding and is never shown in red.
- Approximate location only. No exact addresses, coordinates or CNIC in profiles, responses or logs.
- Do not write anything you could not explain at a viva. Record AI-assisted work in `docs/ai-usage-log.md` and keep the dependency register current.

The complete rules are in `CLAUDE.md` and section 2 of the project context.

## 9. Documentation map

| Document | What it is |
| :--- | :--- |
| `docs/DigitalMohalla_Project_Context.md` | Full handoff: modules, lifecycle, engine maths, scope, plan, test plan, decisions log |
| `docs/DigitalMohalla_Tech_Stack.md` | Stack decision (ADR-0005), tooling, repository layout, CI/CD design, hosting options |
| `docs/design/README.md` | Index of the Part A design baseline with regenerate and verify commands |
| `docs/design/03_architecture/` | ADRs, component and layer diagrams, REST endpoint table |
| `docs/design/06_data_model/` | ER diagram, `schema.sql`, data dictionaries |
| `docs/design/07_state_machines/` | Lifecycle state machines and transition table |
| `docs/design/11_assurance_engine/` | Engine algorithms, config draft, k-hop design |
| `docs/design/14_testing/` | Test plan, scenario fixtures, transition test matrix |
| `docs/design/Digital-MohallaUI/` | UI prototypes (static HTML), design system, HCI analysis |
| `data/README.md` | The data rules, folder map and workflow: what data the project needs, dataset cards, how derived datasets are built |
| `docs/ai-usage-log.md` | Record of AI-assisted changes (reviewer column to be filled in by a team member) |

## 10. Team workflow

Branch model (from the CI/CD plan; CI now exists, branch protection is set in the GitHub repository settings by its owner):

- `main`: what is deployed; changes only through a release pull request from `develop`.
- `develop`: where finished work is combined and tested.
- Short-lived branches from `develop`: `feature/<area>-<topic>`, `fix/<topic>`, `docs/<topic>`.
- One pull request per issue, at least one approval from someone who did not write it, and green checks before merging.
- Commit messages start with a type: `feat:`, `fix:`, `test:`, `docs:`, `chore:`.
- No secrets in the repository. `.env` files are gitignored.

Module ownership follows the project plan (S1 lifecycle, indirect trust and locality; S2 trust estimation, policy and manipulation checks; S3 moderation, evaluation and apps). Names for S1 to S3 are not yet assigned in the documents.

## 11. Troubleshooting

| Problem | Fix |
| :--- | :--- |
| Integration tests are skipped | `TEST_DATABASE_URL` is not set in the shell running pytest |
| `relation ... does not exist` in tests or the API | The schema is not applied. Run the seed script with `--reset`, or `uv run alembic upgrade head` |
| `could not open extension control file ... btree_gist` | Install PostgreSQL with the contrib extensions (the standard EnterpriseDB installer includes them) |
| Login screen says it cannot reach the server | The API is not running on `EXPO_PUBLIC_API_URL`, or an old API process is still holding port 8000 (it will lack CORS). Stop it and restart |
| Browser shows a CORS error | The web origin must be listed in `CORS_ORIGINS` (defaults to `http://localhost:8081,http://localhost:19006`) |
| Port 8000 or 8081 already in use | Stop the old process, or choose another port and update `EXPO_PUBLIC_API_URL` / `CORS_ORIGINS` |
| `npm install` ends with an ERESOLVE peer-dependency error | Use `npm install --legacy-peer-deps` |
| `npm install` or the Chocolatey download fails with a network error | Retry; a large download dropped on an unstable connection. `choco install ... --force` cleans up the partial file |
| First Expo web load shows a blank page for minutes | Metro is still bundling. Wait and reload; later loads are fast |
| Quick-login buttons missing on the login screen | `EXPO_PUBLIC_DEMO_PASSWORD` is empty in `frontend/.env.local`. Restart `npm run web` after changing it |
| `uv` or `psql` not recognised | Close and reopen the terminal so the new PATH is picked up |

---

Licence and academic notes: this is a student project. AI assistance is disclosed in `docs/ai-usage-log.md` and on Form 13.
