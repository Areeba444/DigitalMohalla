# Digital Mohalla — CLAUDE.md

Neighbourhood resource-sharing platform (FAST-NUCES FYP). The technical core (the complex computing problem) is a **trust and risk decision engine**: it estimates whether a physical handover is safe from sparse, indirect, manipulable evidence, reports its own uncertainty, and recommends safeguards or human escalation. Listings, workflow, search and UI exist to feed or act on that decision.

**Current stage:** Iteration 1 (FYP-1 Mid), Part B. Slice A backend done (lifecycle loop, event store, API, login); frontend UI, Slices B and C pending.

## Read first
- `docs/DigitalMohalla_Project_Context.md` — full handoff: modules, lifecycle, engine maths, scope, plan, tests, decisions log. Where it and a source file disagree, the source file wins; flag the conflict.
- `docs/DigitalMohalla_Tech_Stack.md` — stack, ADR-0005, repo layout, CI/CD, hosting options.
- `starter files/more project details/` — use cases, FR/NFR, ADRs, overview, roadmap, iteration 1 plan.

Open this context file for any task touching the lifecycle, assurance engine, event schema, or iteration scope before changing code.

## Stack (see tech stack doc for detail)
- Backend: Python 3.12, FastAPI, PostgreSQL 16 (`btree_gist`), SQLAlchemy 2.0 (sync) + Alembic, psycopg 3, NumPy/SciPy. Managed with **uv**.
- Frontend: React Native via Expo (TypeScript, Expo Router, React Native Paper, TanStack Query). Android + web build. iOS not targeted.
- CI/CD: GitHub Actions, Docker/Compose, GHCR, Caddy. Hosting undecided (ADR-0006).

## Layout
```text
backend/   app/{api, domain/{lifecycle, assurance/{estimation,indirect,detection,policy}, moderation, accounts}, infra/{db,eventstore}, config}
           config/engine.yaml (to create), alembic/, tests/{unit,integration,scenarios}
frontend/  src/app/(resident), src/app/(moderator), src/api (generated client)
infra/     docker-compose.yml, Caddyfile, deploy/ (to create)
scripts/   seed, reset, load tests
docs/      adr/, design/, ai-usage-log.md, dependency-disclosure.md (to create)
```
The Expo template's demo screens are still present in `frontend/src/`.

## Commands
Backend (run from `backend/`):
```bash
uv sync                     # install from lock file
uv run pytest               # tests
uv run ruff check . && uv run ruff format --check .
uv run mypy app/domain      # engine + lifecycle packages
uv run alembic upgrade head # migrations
```
Frontend (run from `frontend/`; use `npx expo install <pkg>` to add packages, not `npm install`):
```bash
npx expo start              # dev server (add --web for web)
npx expo lint
npx tsc --noEmit
npx jest                    # once jest config is added
```
`frontend/AGENTS.md` says Expo APIs change between SDKs: check the versioned docs at https://docs.expo.dev/llms.txt before writing Expo code. Dev tools were installed with `--legacy-peer-deps` because the template ships TypeScript 6 and `openapi-typescript` wants 5.

## Run the app locally (web)
Needs PostgreSQL 16 (dev DB `digitalmohalla` on port 5433) and `backend/.env` plus `frontend/.env.local` (see the `.env.example` files).
```bash
cd backend && uv run python ../scripts/seed_demo.py --reset   # synthetic users and items
cd backend && uv run uvicorn app.main:app --port 8000          # API
cd frontend && npm run web -- --port 8081                      # Expo web app (first bundle takes minutes)
cd frontend && npm run api:generate                            # after any backend schema change (export openapi.json first)
```
The UI uses three switchable themes in `frontend/src/theme/themes.ts` (team to pick one). Slice A screens only; W5 to W7 (dispute, moderator) come with Slice C.

## Rules (summary; full text in the context doc §2)
- Small diffs; no rewrites; don't touch files outside the task; don't delete things unasked. Simplest thing that meets the spec: no extra frameworks.
- Map work to a module (context doc §4). If it maps to nothing, question it. Stay in frozen scope; out-of-scope needs a formal change request (Form 12) — push back first.
- **The event schema is frozen.** Don't add/rename fields or event types without flagging it (needs sign-off from all three students). If a task touches engine internals, the schema or the event log and is bigger than it looks, stop and flag it.
- Tunable parameters live in versioned config (`backend/config/engine.yaml`), never hardcoded; every stored assessment records `config_version`.
- Tests for anything touching state transitions, trust maths, propagation or detection. Every invalid transition is tested. Deterministic, fixed seeds.
- Assurance state is separate from lifecycle state. Never show a single trust number to users. Indirect evidence alone never yields SUFFICIENT_EVIDENCE. No restriction without human review. Zero history is INSUFFICIENT_EVIDENCE, not a negative finding.
- Call it a "recency-weighted Beta posterior" (never "Beta-Binomial"). Never say "AI-powered".
- Privacy: approximate location only; no exact addresses, no CNIC; no location or identifiers in logs or API responses. Synthetic data and attack scenarios are labelled synthetic everywhere.
- Don't fabricate references, data, results or metrics. Separate what was verified from what is inferred; give numbers, not adjectives. After a change, say what ran, what passed, what is untested.
- Anything user-facing is decision support, not a guarantee.

## Academic integrity
- After any substantial AI-assisted change, append to `docs/ai-usage-log.md`: date, what, files, who reviewed.
- Keep the dependency register (Form 13) current when adding dependencies; record pinned version and licence.
- Write nothing the team couldn't explain at a viva; add a plain-language note on complex code or maths.

## Open items
Mid-eval date, hosting (ADR-0006), S1/S2/S3 names, event-specific data field (N-6), SUFFICIENT_EVIDENCE thresholds, ES-13 expected state, locality method: see context doc §15. Don't invent values for these; ask.
