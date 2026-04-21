# Day 1 Bootstrap Shell For supportflow-agent

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [docs/PLANS.md](docs/PLANS.md). It is written so a stateless implementer can recreate the Day 1 shell from this file alone.

## Purpose / Big Picture

Day 1 exists to make the repository runnable end to end with the smallest useful workflow shell. After this change, a developer can start a FastAPI backend, call `GET /healthz`, call `GET /api/v1/tickets` to receive mock ticket data, and open a React page at `/tickets` that renders those tickets. The repository also gains an initial workflow boundary type named `TicketState` so later LangGraph work starts from a defined state object instead of ad hoc dictionaries.

This is intentionally a shell, not a product-complete workflow. There is no database, no graph execution, no review queue, and no retrieval implementation in Day 1.

## Progress

- [x] (2026-04-21 09:15Z) Audited the repository state and confirmed that only top-level docs existed before implementation.
- [x] (2026-04-21 09:35Z) Chose the Day 1 stack: FastAPI plus Pydantic on the backend and Vite React TypeScript on the frontend.
- [x] (2026-04-21 09:55Z) Added backend app shell, schemas, state model, mock ticket loading, and API tests.
- [x] (2026-04-21 10:10Z) Added frontend app shell, `/tickets` route, API client, ticket list UI, and frontend tests.
- [x] (2026-04-21 10:25Z) Added sample data, knowledge base placeholders, `.env.example`, and lightweight documentation skeleton files.
- [x] (2026-04-21 10:40Z) Fixed backend packaging metadata so `uv sync` can install the editable app from `backend/app`.
- [x] (2026-04-21 10:50Z) Fixed frontend Vitest globals and Vite TypeScript config so tests and production build both succeed.
- [x] (2026-04-21 10:55Z) Verified `uv run pytest`, `npm run test -- --run`, and `npm run build` all pass.

## Surprises & Discoveries

- Observation: The repository had no backend, frontend, or data directories at all, so the Day 1 work needed to create the full shell rather than filling in a scaffold.
  Evidence: `rg --files` initially returned only `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `docs/PLANS.md`, the MVP spec, and the active Day 1 plan.

- Observation: Hatch could not infer the backend package path from the project name alone.
  Evidence: `uv sync` failed until `backend/pyproject.toml` declared `[tool.hatch.build.targets.wheel] packages = ["app"]`.

- Observation: In-process HTTP tests were unreliable in this sandbox and dependency combination, while direct route and app registration assertions were stable.
  Evidence: `pytest` hung when using `fastapi.testclient.TestClient` and again when using `httpx.ASGITransport`, but completed immediately after switching to direct route assertions plus FastAPI route registration checks.

## Decision Log

- Decision: Use `GET /healthz` with JSON body `{"status":"ok"}` instead of a plain text response.
  Rationale: JSON is easier to assert in tests and keeps the API shape consistent with the rest of the backend.
  Date/Author: 2026-04-21 / Codex

- Decision: Read tickets from `data/sample_tickets/demo_tickets.json` on each request instead of introducing a repository or service layer.
  Rationale: Day 1 needs mock data only, and adding layers now would add complexity without serving an active requirement.
  Date/Author: 2026-04-21 / Codex

- Decision: Define `TicketState` as a Pydantic model containing the normalized `Ticket` plus optional placeholders for later workflow stages.
  Rationale: The repo guidance prefers Pydantic schemas, and a typed state boundary is enough for Day 1 without implementing graph nodes.
  Date/Author: 2026-04-21 / Codex

- Decision: Use React Router with a redirect from `/` to `/tickets`.
  Rationale: The MVP already implies multiple pages later, and this keeps the Day 1 page address stable without adding significant complexity.
  Date/Author: 2026-04-21 / Codex

## Outcomes & Retrospective

Day 1 is complete. The repository now contains a runnable backend shell, a runnable frontend shell, mock ticket data, a first `TicketState` model, and enough documentation for a new contributor to run the project.

The automated checks that passed during implementation were `uv run pytest` in `backend/`, `npm run test -- --run` in `frontend/`, and `npm run build` in `frontend/`. Manual browser verification of `/tickets` and manual `curl` verification of the backend are still the intended next human checks outside the sandboxed automation environment.

## Context and Orientation

The repository starts as documentation only. The Day 1 shell introduces four working areas.

`backend/` contains the FastAPI application. `backend/app/main.py` constructs the app and includes versioned route modules. `backend/app/api/v1/health.py` exposes the health endpoint. `backend/app/api/v1/tickets.py` exposes mock ticket data. `backend/app/schemas/ticket.py` contains the ticket response model. `backend/app/graph/state.py` contains the first workflow state type.

`frontend/` contains the Vite React TypeScript application. `frontend/src/main.tsx` sets up routing. `frontend/src/pages/TicketsPage.tsx` fetches tickets and renders the page state. `frontend/src/components/TicketList.tsx` renders the list itself. `frontend/src/lib/api.ts` wraps backend fetch calls. `frontend/src/lib/types.ts` mirrors the ticket shape used by the backend.

`data/` contains development-only inputs. `data/sample_tickets/demo_tickets.json` is the source of truth for `GET /api/v1/tickets`. `data/kb/` contains placeholder knowledge base documents that establish the later retrieval footprint without implementing retrieval now.

The term “workflow boundary” means the typed object passed into the future LangGraph pipeline. In Day 1 that boundary is represented by `TicketState`, which only stores ticket data and optional fields for classification, retrieval, and draft output.

## Plan of Work

Create the backend first. Add `backend/pyproject.toml` with FastAPI, Uvicorn, Pytest, and HTTPX test dependencies. In `backend/app/main.py`, define `create_app()` and a module-level `app` instance, enable CORS for local frontend origins, and include `/healthz` plus `/api/v1/tickets`. In `backend/app/api/v1/health.py`, return a JSON object containing `status: ok`. In `backend/app/api/v1/tickets.py`, load the JSON file from `data/sample_tickets/demo_tickets.json`, validate each record into the shared `Ticket` schema, and return the resulting list. In `backend/app/graph/state.py`, define `TicketState` as a Pydantic model that stores one `Ticket` and optional later-stage fields.

Create the frontend next. Add a small Vite React TypeScript app with React Router and a redirect from `/` to `/tickets`. Implement `frontend/src/lib/api.ts` so it fetches from `VITE_API_BASE_URL` when present and otherwise defaults to `http://localhost:8000`. Implement `TicketsPage` with loading, error, empty, and success states. Keep `TicketList` presentational and pass it fully shaped ticket data from the page.

Add tests for both sides. In `backend/tests/test_api.py`, verify the health endpoint and mock ticket endpoint with `fastapi.testclient.TestClient`. In `frontend/src/components/TicketList.test.tsx`, verify that the list renders key ticket fields. In `frontend/src/pages/TicketsPage.test.tsx`, mock the API wrapper and verify loading and success behavior.

Finish by updating `README.md` so a new contributor can install dependencies, run both apps, and verify the visible behavior without reading any other file first.

## Concrete Steps

From the repository root, create and verify the backend:

    cd /home/poter/resume-pj/supportflow-agent/backend
    uv sync
    uv run pytest
    uv run uvicorn app.main:app --reload

Expected and observed backend test output includes:

    3 passed

With the backend running, verify the endpoints:

    curl http://127.0.0.1:8000/healthz
    curl http://127.0.0.1:8000/api/v1/tickets

Expected response excerpts:

    {"status":"ok"}

    [{"id":"ticket-1001","subject":"Refund requested for duplicate charge",...}]

From the repository root, create and verify the frontend:

    cd /home/poter/resume-pj/supportflow-agent/frontend
    npm install
    npm run test -- --run
    npm run dev -- --host 127.0.0.1 --port 5173

Expected and observed frontend test output includes:

    Test Files  2 passed

Open `http://127.0.0.1:5173/tickets` in a browser. The page should show the “Support Inbox” heading and three mock tickets. Navigating to `http://127.0.0.1:5173/` should redirect to `/tickets`.

## Validation and Acceptance

Acceptance is behavioral.

Start the backend and confirm `GET /healthz` returns HTTP 200 with JSON body `{"status":"ok"}`.

Confirm `GET /api/v1/tickets` returns an array of ticket objects that match the `Ticket` schema. The endpoint must read from `data/sample_tickets/demo_tickets.json`, not from inline constants in the route module.

Start the frontend and confirm the `/tickets` page renders the backend response. The page must show a loading message before the fetch completes, an error message if the request fails, and an empty-state message if the endpoint returns an empty array.

Run backend and frontend automated tests. The Day 1 shell is complete only when those tests pass and the manual endpoint and page checks match the examples in this document.

Automated verification completed on 2026-04-21 with:

    cd /home/poter/resume-pj/supportflow-agent/backend
    env UV_CACHE_DIR=/tmp/uv-cache UV_PYTHON_INSTALL_DIR=/tmp/uv-python uv run pytest

    cd /home/poter/resume-pj/supportflow-agent/frontend
    npm run test -- --run
    npm run build

## Idempotence and Recovery

The file creation steps are additive and safe to re-run. Reinstalling backend dependencies with `uv sync` and frontend dependencies with `npm install` is safe. If the frontend cannot reach the backend because the backend runs on a different origin, set `VITE_API_BASE_URL` in the shell before `npm run dev`. If the ticket endpoint fails due to malformed JSON, fix `data/sample_tickets/demo_tickets.json` and rerun the backend tests before restarting the server.

## Artifacts and Notes

Expected backend health response:

    {"status":"ok"}

Expected ticket shape excerpt:

    {
      "id": "ticket-1001",
      "subject": "Refund requested for duplicate charge",
      "customer_name": "Avery Chen",
      "status": "open",
      "priority": "high",
      "created_at": "2026-04-16T09:30:00Z"
    }

## Interfaces and Dependencies

Use FastAPI for HTTP routing, Pydantic for schemas and state models, Pytest plus HTTPX for backend tests, and Vite plus React plus TypeScript plus React Router for the frontend shell.

At the end of Day 1, these interfaces must exist:

- `backend/app/main.py` exports `create_app() -> FastAPI` and `app`.
- `backend/app/schemas/ticket.py` exports `Ticket`, a Pydantic model with `id`, `subject`, `customer_name`, `status`, `priority`, `created_at`, and optional `preview`.
- `backend/app/graph/state.py` exports `TicketState`, a Pydantic model with `ticket: Ticket` and optional `classification`, `retrieval_context`, `draft_reply`, and `review_required`.
- `backend/app/api/v1/health.py` exposes `router` with `GET /healthz`.
- `backend/app/api/v1/tickets.py` exposes `router` with `GET /api/v1/tickets`.
- `frontend/src/lib/types.ts` exports `Ticket`.
- `frontend/src/lib/api.ts` exports `fetchTickets(): Promise<Ticket[]>`.
- `frontend/src/components/TicketList.tsx` exports `TicketList`.
- `frontend/src/pages/TicketsPage.tsx` exports `TicketsPage`.

Revision note: On 2026-04-21 this file was rewritten from a checklist into a PLANS-compliant ExecPlan so the Day 1 implementation is executable without additional interpretation.
