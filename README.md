# supportflow-agent

supportflow-agent is a workflow-first AI support app for ticket triage, knowledge retrieval, response drafting, and human review for risky cases.

The current repository state is the Day 3 MVP slice:

- FastAPI backend with `GET /healthz`
- FastAPI ticket list endpoint at `GET /api/v1/tickets`
- FastAPI workflow run endpoint at `POST /api/v1/tickets/{ticket_id}/run`
- FastAPI pending review endpoint at `GET /api/v1/reviews/pending`
- FastAPI resume endpoint at `POST /api/v1/runs/{thread_id}/resume`
- LangGraph workflow with risk gating and human-in-the-loop resume
- React ticket inbox at `/tickets`
- React review queue at `/reviews`
- Local Markdown knowledge base used by the retriever

## What the app does today

Open the frontend, select a demo ticket, and click `Run workflow`.

The frontend calls `POST /api/v1/tickets/{ticket_id}/run`, and the backend runs this LangGraph path:

1. Load the selected ticket from local demo data
2. Classify the ticket with deterministic rules
3. Retrieve matching KB snippets from `data/kb`
4. Draft a reply with citations and confidence
5. Run a deterministic risk gate
6. Either auto-finalize the response or interrupt for human review

The UI then shows:

- ticket detail
- classification category and priority
- retrieved knowledge hits
- draft reply and confidence
- risk flags and risk-gate reason
- final response for low-risk tickets
- waiting-review state for risky tickets

For risky tickets, open `/reviews` to:

- inspect the draft and supporting knowledge
- approve the draft
- edit the draft and resume with the edited answer
- reject the AI draft and mark the ticket for manual takeover

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
- `backend/app/api/v1/runs.py`: workflow run and resume endpoints
- `backend/app/api/v1/reviews.py`: pending review list endpoint
- `backend/app/services/ticket_repo.py`: demo ticket loading
- `backend/app/services/retrieval.py`: lexical KB retrieval
- `backend/app/services/pending_review_store.py`: in-memory pending review storage
- `backend/app/graph/state.py`: shared graph state
- `backend/app/graph/nodes/`: graph node implementations
- `backend/app/graph/builder.py`: compiled LangGraph builder
- `backend/app/schemas/graph.py`: structured workflow request and response models

## Frontend

Key frontend files:

- `frontend/src/pages/TicketsPage.tsx`: main inbox page
- `frontend/src/pages/ReviewQueuePage.tsx`: review queue page
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
- `GET /api/v1/reviews/pending`
- `POST /api/v1/runs/{thread_id}/resume`

Example low-risk run:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/tickets/ticket-1003/run
```

Example risky run and resume:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/tickets/ticket-1001/run
curl -s http://127.0.0.1:8000/api/v1/reviews/pending
curl -s -X POST http://127.0.0.1:8000/api/v1/runs/<thread_id>/resume \
  -H 'content-type: application/json' \
  -d '{"decision":"approve","reviewer_note":"evidence is sufficient"}'
```

Important note: pending reviews and LangGraph checkpoints are in memory only. Restarting the backend clears the review queue and invalidates older `thread_id` values.

## Run the frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

The frontend starts on:

- `http://127.0.0.1:5173/tickets`
- `http://127.0.0.1:5173/reviews`

## Manual behavior check

Use the shipped demo tickets to confirm the main behaviors:

- `ticket-1003` should auto-finalize on `/tickets` and show a `Final response`.
- `ticket-1001` should pause in `waiting_review`, show risk-gate details, and appear on `/reviews`.
- Approving or editing a pending review should finish the run and show a completed result.
- Rejecting a pending review should end in `manual_takeover` with no final AI response.

Each workflow run gets a unique `thread_id`, so rerunning the same ticket starts a fresh review item instead of reusing older graph state.

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

- durable database storage for reviews or runs
- streaming
- LangSmith tracing
- vector retrieval
- real LLM generation
- external ticket system integration
- external message write-back

## Planning docs

Read these first when making larger changes:

- `ARCHITECTURE.md`
- `docs/product-specs/supportflow-mvp.md`
- `docs/exec-plans/active/*.md`

For multi-file features, backend/frontend refactors, graph routing changes, or observability work, use and update an ExecPlan under `docs/exec-plans/`.
