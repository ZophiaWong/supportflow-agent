# Day 16 Demo and Deployment Readiness

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The project is intended to help the user seek AI Agent Engineer roles. After this change, a hiring reviewer should be able to clone the repository, run the app and evals with clear commands, reset demo data deterministically, and understand the architecture quickly.

This plan turns the implemented agent workflow into a reviewer-friendly portfolio artifact.

## Progress

- [x] (2026-04-27) Created this todo ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [x] (2026-05-25) Reviewed the plan against current README drift, frontend API environment behavior, durable SQLite state, and approval-gated customer-send behavior.
- [ ] Inspect current README, backend/frontend dev commands, env vars, and generated artifacts.
- [ ] Add deterministic demo setup and reset commands for the SQLite runtime database.
- [ ] Add Docker Compose as the one-command local run path.
- [ ] Add portfolio README section and architecture diagram.
- [ ] Add final smoke script or documented acceptance checklist.
- [ ] Update docs and this ExecPlan with observed behavior.

## Surprises & Discoveries

- Observation: Pre-revision README behavior claims were stale and needed correction before the project could be presented as a portfolio demo.
  Evidence: Before the 2026-05-25 documentation update, README said `ticket-1003` should auto-finalize and listed durable database storage as a missing constraint. Current behavior requires approval before executing a customer send, and runtime state is already stored in SQLite.

- Observation: The frontend API base URL is build-time configuration in Vite.
  Evidence: `frontend/src/lib/api.ts` reads `import.meta.env.VITE_API_BASE_URL` and otherwise falls back to `http://127.0.0.1:8000`. Local, Docker, and alternate-port demos must set or document this variable.

- Observation: The current backend already exposes run trace data that should be included in the portfolio architecture story.
  Evidence: `GET /api/v1/runs/{thread_id}/trace` is implemented and the product spec records measured graph-node spans as current acceptance evidence.

## Decision Log

- Decision: Optimize for local reviewer setup before production hosting.
  Rationale: The portfolio value is highest when a reviewer can run and inspect the workflow quickly. Real deployment can come later if needed.
  Date/Author: 2026-04-27 / Codex

- Decision: Keep demo data deterministic.
  Rationale: Evals, screenshots, smoke tests, and reviewer walkthroughs are easier to trust when the same commands produce the same tickets and results.
  Date/Author: 2026-04-27 / Codex

- Decision: Use Docker Compose as the primary one-command demo path, while keeping manual backend/frontend commands documented as a fallback.
  Rationale: Hiring reviewers should be able to run the product with minimal setup. Docker Compose can set backend and frontend environment variables consistently, while manual commands remain useful for local development and debugging.
  Date/Author: 2026-05-25 / Codex

- Decision: Make frontend API configuration explicit through `VITE_API_BASE_URL`.
  Rationale: Vite embeds environment variables into the frontend bundle. A demo running on any backend port other than `8000`, or inside Docker, will fail unless this configuration is clear and repeatable.
  Date/Author: 2026-05-25 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize the demo commands, environment requirements, smoke results, and any deployment limitations.

## Context and Orientation

The backend is a FastAPI app under `backend/`. The frontend is a React app under `frontend/`. Product specs live under `docs/product-specs/`. ExecPlans live under `docs/exec-plans/`. Demo tickets and KB data live under `data/`.

The app currently exposes `/tickets` for support agents and `/reviews` for reviewers. Backend routes include health, tickets, run, state, timeline, trace, pending reviews, and resume. Offline evals run from `backend/scripts/run_offline_eval.py`.

Demo readiness means a reviewer can run the app, exercise the main workflow, and see the agent engineering story without needing private credentials or unstated setup.

## Plan of Work

First, inspect `README.md`, package files, and existing docs. Identify all commands required to install, test, run backend, run frontend, run evals, set frontend API configuration, and reset state. Correct stale README claims as part of this work: customer sends are approval-gated, durable SQLite storage exists, and trace is an implemented endpoint.

Second, add deterministic setup commands. Add a safe reset command for the demo database at `data/supportflow.sqlite3` or a path chosen through `SUPPORTFLOW_DB_PATH`. The reset command should be explicit and should not delete arbitrary user data. It can call the existing runtime-table cleanup behavior in `backend/app/services/sqlite_store.py` rather than deleting unrelated files.

Third, add Docker Compose as the one-command run path. It should run the backend, frontend, and persistent local SQLite state volume. The frontend service must receive `VITE_API_BASE_URL` pointing at the backend URL used by the browser. Keep manual local commands in README for environments where Docker is unavailable.

Fourth, update README with a portfolio-focused section. It should describe the project as a production-shaped support workflow agent and link to MVP spec, portfolio roadmap, active/completed ExecPlans, and eval evidence. The README should document that `ticket-1003` pauses for approval before customer send execution and that `ticket-1001` demonstrates higher-risk review.

Fifth, add an architecture diagram. A Mermaid diagram in Markdown is acceptable. It should map user actions to React pages, FastAPI routes, LangGraph nodes, durable state, KB retrieval, action ledger, guardrails, traces, and evals. Include only implemented pieces or label planned pieces clearly.

Sixth, add a final smoke checklist or script. It should verify backend health, ticket list, customer-send approval flow for `ticket-1003`, risky waiting review for `ticket-1001`, approve resume, reject/manual takeover, trace availability, frontend route serving, and offline eval.

Seventh, run the full acceptance commands and record evidence in this plan.

## Concrete Steps

Inspect current docs and package commands:

    sed -n '1,340p' README.md
    sed -n '1,220p' backend/pyproject.toml
    sed -n '1,220p' frontend/package.json
    sed -n '1,120p' frontend/src/lib/api.ts
    find docs -maxdepth 3 -type f | sort

Run existing validation:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

    cd frontend
    npm test -- --run
    npm run build

After adding demo commands, run the documented path exactly as a reviewer would. If Docker Compose is added:

    docker compose up --build

Then verify:

    curl --noproxy '*' -s http://127.0.0.1:8000/healthz
    curl --noproxy '*' -s http://127.0.0.1:8000/api/v1/tickets

Open the frontend route documented in README, usually `http://127.0.0.1:5173/tickets` or the mapped Docker port. Confirm the frontend is configured with `VITE_API_BASE_URL` for the backend URL that the browser can reach.

## Validation and Acceptance

This plan is complete when all of these are true:

- README has a clear portfolio demo path.
- A reviewer can run backend and frontend with documented commands.
- Frontend API configuration through `VITE_API_BASE_URL` is documented for manual runs, alternate backend ports, and Docker.
- Demo state can be reset deterministically.
- Offline eval command and expected output are documented.
- Architecture diagram reflects implemented behavior.
- Full backend tests, frontend tests, frontend build, and offline eval pass.
- Manual smoke checklist proves customer-send approval, risky review, approve, reject, trace, and frontend route paths.
- README no longer claims durable runtime storage is missing or that `ticket-1003` auto-finalizes before approval.

## Idempotence and Recovery

Demo reset commands must be safe and explicit. If Docker Compose volumes are used, document how to reset only this project's volume. If a local SQLite file is used, document the path and provide a command that targets only that path. Do not delete `data/kb/`, `data/sample_tickets/`, or checked-in eval source files.

## Artifacts and Notes

This plan should be implemented after the highest-value agent features are stable. It should not claim features are implemented before they are. Planned features can be linked through the portfolio roadmap, but README demo claims must match actual behavior. If Day 15 streaming is not complete when this plan starts, document streaming as planned rather than implemented.

## Interfaces and Dependencies

Potential deliverables include:

- `docker-compose.yml`
- `Makefile`
- `backend/scripts/reset_demo_state.py`
- README portfolio section
- `docs/design-docs/architecture-diagram.md` or an updated existing design doc
- `scripts/smoke_demo.sh` if shell scripting fits the repo style

The Docker and manual frontend paths must set `VITE_API_BASE_URL` when the backend is not reachable at `http://127.0.0.1:8000`. The backend path can use `SUPPORTFLOW_DB_PATH` to keep demo state isolated from local developer state.

Avoid adding secrets or requiring paid external services.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.

2026-05-25: Revised before activation. The plan now explicitly covers README drift, Docker Compose as the primary one-command demo path, `VITE_API_BASE_URL` configuration, trace route documentation, and deterministic SQLite reset behavior.
