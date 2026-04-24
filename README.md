# supportflow-agent

supportflow-agent is a workflow-first AI support app for ticket triage and response drafting.

The current repository state is the Day 2 happy path:

- FastAPI backend with `GET /healthz`
- FastAPI ticket list endpoint at `GET /api/v1/tickets`
- FastAPI workflow run endpoint at `POST /api/v1/tickets/{ticket_id}/run`
- LangGraph workflow with four synchronous nodes:
  - `load_ticket_context`
  - `classify_ticket`
  - `retrieve_knowledge`
  - `draft_reply`
- React ticket inbox at `/tickets`
- Ticket detail panel and workflow result panel in the frontend
- Local Markdown knowledge base used by the retriever

## What the app does today

Open the frontend, select a demo ticket, and click `Run workflow`.

The frontend calls `POST /api/v1/tickets/{ticket_id}/run`, and the backend runs a fixed LangGraph path:

1. Load the selected ticket from local demo data
2. Classify the ticket with deterministic rules
3. Retrieve matching KB snippets from `data/kb`
4. Draft a reply with a lead citation

The UI then shows:

- ticket detail
- classification category and priority
- retrieved knowledge hits
- draft reply and confidence

## Repository layout

```text
backend/                  FastAPI app, LangGraph workflow, tests
frontend/                 React app, UI tests, Vite build
data/sample_tickets/      Demo tickets
data/kb/                  Local Markdown knowledge base
docs/exec-plans/active/   Active ExecPlans
```

## Backend

Key backend files:

- `backend/app/main.py`: FastAPI app and router wiring
- `backend/app/api/v1/tickets.py`: ticket list endpoint
- `backend/app/api/v1/runs.py`: workflow run endpoint
- `backend/app/services/ticket_repo.py`: demo ticket loading
- `backend/app/services/retrieval.py`: lexical KB retrieval
- `backend/app/graph/state.py`: shared graph state
- `backend/app/graph/nodes/`: graph node implementations
- `backend/app/graph/builder.py`: compiled LangGraph builder
- `backend/app/schemas/graph.py`: structured workflow response models

## Frontend

Key frontend files:

- `frontend/src/pages/TicketsPage.tsx`: main inbox page
- `frontend/src/components/TicketList.tsx`: selectable ticket list
- `frontend/src/components/TicketDetail.tsx`: selected ticket detail
- `frontend/src/components/WorkflowResultPanel.tsx`: workflow output display
- `frontend/src/lib/api.ts`: frontend API calls
- `frontend/src/lib/types.ts`: shared frontend types

## Run the backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

The backend starts on `http://127.0.0.1:8000`.

Available routes:

- `GET /healthz`
- `GET /api/v1/tickets`
- `POST /api/v1/tickets/{ticket_id}/run`

Example:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/tickets/ticket-1001/run
```

## Run the frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

The frontend starts on `http://127.0.0.1:5173/tickets`.

## Tests

Backend:

```bash
cd backend
uv run --cache-dir /tmp/uv-cache pytest
```

The `/tmp/uv-cache` override avoids cache-permission issues in restricted environments.

Frontend:

```bash
cd frontend
npm test -- --run
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Current constraints

This repository intentionally does not yet include:

- conditional routing
- risk gating
- human review interrupt/resume
- streaming
- LangSmith tracing
- database storage
- vector retrieval
- real LLM generation
- external ticket system integration

## Planning docs

Read these first when making larger changes:

- `ARCHITECTURE.md`
- `docs/product-specs/supportflow-mvp.md`
- `docs/exec-plans/active/*.md`

For multi-file features, backend/frontend refactors, graph routing changes, or observability work, use and update an ExecPlan under `docs/exec-plans/`.
