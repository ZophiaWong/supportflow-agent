# Day 16 Demo and Deployment Readiness

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The project is intended to help the user seek AI Agent Engineer roles. After this change, a hiring reviewer should be able to clone the repository, run the app and evals with clear commands, reset demo data deterministically, and understand the architecture quickly.

This plan turns the implemented agent workflow into a reviewer-friendly portfolio artifact.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [ ] Inspect current README, backend/frontend dev commands, env vars, and generated artifacts.
- [ ] Add deterministic demo setup and reset commands.
- [ ] Add Docker Compose or equivalent one-command local run path.
- [ ] Add portfolio README section and architecture diagram.
- [ ] Add final smoke script or documented acceptance checklist.
- [ ] Update docs and this ExecPlan with observed behavior.

## Surprises & Discoveries

- Observation: No implementation discoveries yet.
  Evidence: This plan has only been created.

## Decision Log

- Decision: Optimize for local reviewer setup before production hosting.
  Rationale: The portfolio value is highest when a reviewer can run and inspect the workflow quickly. Real deployment can come later if needed.
  Date/Author: 2026-04-27 / Codex

- Decision: Keep demo data deterministic.
  Rationale: Evals, screenshots, smoke tests, and reviewer walkthroughs are easier to trust when the same commands produce the same tickets and results.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize the demo commands, environment requirements, smoke results, and any deployment limitations.

## Context and Orientation

The backend is a FastAPI app under `backend/`. The frontend is a React app under `frontend/`. Product specs live under `docs/product-specs/`. ExecPlans live under `docs/exec-plans/`. Demo tickets and KB data live under `data/`.

The app currently exposes `/tickets` for support agents and `/reviews` for reviewers. Backend routes include health, tickets, run, state, timeline, pending reviews, and resume. Offline evals run from `backend/scripts/run_offline_eval.py`.

Demo readiness means a reviewer can run the app, exercise the main workflow, and see the agent engineering story without needing private credentials or unstated setup.

## Plan of Work

First, inspect `README.md`, package files, and existing docs. Identify all commands required to install, test, run backend, run frontend, run evals, and reset state.

Second, add deterministic setup commands. If Day 9 created SQLite state, add a safe reset command for the demo database. The reset command should be explicit and should not delete arbitrary user data.

Third, add a one-command run path. Docker Compose is preferred if it can be added without excessive complexity. It should run the backend, frontend, and persistent local state volume. If Docker Compose is too heavy for the current repo, add a `Makefile` or scripts that run backend and frontend with documented prerequisites.

Fourth, update README with a portfolio-focused section. It should describe the project as a production-shaped support workflow agent and link to MVP spec, portfolio roadmap, active/completed ExecPlans, and eval evidence.

Fifth, add an architecture diagram. A Mermaid diagram in Markdown is acceptable. It should map user actions to React pages, FastAPI routes, LangGraph nodes, durable state, KB retrieval, action ledger, guardrails, traces, and evals. Include only implemented pieces or label planned pieces clearly.

Sixth, add a final smoke checklist or script. It should verify backend health, ticket list, low-risk run, risky waiting review, approve resume, reject/manual takeover, frontend route serving, and offline eval.

Seventh, run the full acceptance commands and record evidence in this plan.

## Concrete Steps

Inspect current docs and package commands:

    sed -n '1,340p' README.md
    sed -n '1,220p' backend/pyproject.toml
    sed -n '1,220p' frontend/package.json
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

Open the frontend route documented in README, usually `http://127.0.0.1:5173/tickets` or the mapped Docker port.

## Validation and Acceptance

This plan is complete when all of these are true:

- README has a clear portfolio demo path.
- A reviewer can run backend and frontend with documented commands.
- Demo state can be reset deterministically.
- Offline eval command and expected output are documented.
- Architecture diagram reflects implemented behavior.
- Full backend tests, frontend tests, frontend build, and offline eval pass.
- Manual smoke checklist proves low-risk run, risky review, approve, and reject paths.

## Idempotence and Recovery

Demo reset commands must be safe and explicit. If Docker Compose volumes are used, document how to reset only this project's volume. If a local SQLite file is used, document the path and provide a command that targets only that path.

## Artifacts and Notes

This plan should be implemented after the highest-value agent features are stable. It should not claim features are implemented before they are. Planned features can be linked through the portfolio roadmap, but README demo claims must match actual behavior.

## Interfaces and Dependencies

Potential deliverables include:

- `docker-compose.yml`
- `Makefile`
- `backend/scripts/reset_demo_state.py`
- README portfolio section
- `docs/design-docs/architecture-diagram.md` or an updated existing design doc
- `scripts/smoke_demo.sh` if shell scripting fits the repo style

Avoid adding secrets or requiring paid external services.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.
