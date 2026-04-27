# supportflow-agent

supportflow-agent is a workflow-first AI support app for ticket triage, knowledge retrieval, response drafting, and human review for risky cases.

The current repository state is the post-MVP durable workflow slice:

- FastAPI backend with `GET /healthz`
- FastAPI ticket list endpoint at `GET /api/v1/tickets`
- FastAPI workflow run endpoint at `POST /api/v1/tickets/{ticket_id}/run`
- FastAPI run state endpoint at `GET /api/v1/runs/{thread_id}/state`
- FastAPI run timeline endpoint at `GET /api/v1/runs/{thread_id}/timeline`
- FastAPI pending review endpoint at `GET /api/v1/reviews/pending`
- FastAPI resume endpoint at `POST /api/v1/runs/{thread_id}/resume`
- LangGraph workflow with risk gating, human-in-the-loop resume, and inspectable run state
- React ticket inbox at `/tickets` with run timeline and state inspection
- React review queue at `/reviews`
- Local Markdown knowledge base used by the retriever
- Offline eval CLI comparing `plain_rag_baseline` with `graph_v1`

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
- current run state for the active `thread_id`
- timeline of major workflow milestones

The `/tickets` page stores the latest run `thread_id` in local storage and reloads its state and timeline from the backend. Run checkpoints, pending reviews, and timeline events are stored in local SQLite state, so a waiting review can survive a backend restart when the same database path is used.

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
data/evals/               Fixed offline eval dataset and generated local results
docs/exec-plans/active/   Active ExecPlans
```

## Backend

Key backend files:

- `backend/app/main.py`: FastAPI app and router wiring
- `backend/app/api/v1/tickets.py`: ticket list endpoint
- `backend/app/api/v1/runs.py`: workflow run and resume endpoints
- `backend/app/services/run_event_store.py`: SQLite-backed run timeline storage
- `backend/app/services/run_state_service.py`: read-only run state projection from LangGraph checkpoints
- `backend/app/api/v1/reviews.py`: pending review list endpoint
- `backend/app/services/ticket_repo.py`: demo ticket loading
- `backend/app/services/retrieval.py`: lexical KB retrieval
- `backend/app/services/pending_review_store.py`: SQLite-backed pending review storage
- `backend/app/services/sqlite_checkpointer.py`: local SQLite LangGraph checkpoint saver
- `backend/app/services/sqlite_store.py`: SQLite path and schema setup
- `backend/app/graph/state.py`: shared graph state
- `backend/app/graph/nodes/`: graph node implementations
- `backend/app/graph/builder.py`: compiled LangGraph builder
- `backend/app/schemas/graph.py`: structured workflow request and response models
- `backend/app/evals/`: offline eval schemas, target runners, scoring, tracing, and artifact writing
- `backend/scripts/run_offline_eval.py`: CLI entrypoint for local eval comparison

## Frontend

Key frontend files:

- `frontend/src/pages/TicketsPage.tsx`: main inbox page
- `frontend/src/components/RunStatePanel.tsx`: current run-state display
- `frontend/src/components/WorkflowTimeline.tsx`: major-step timeline display
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
- `GET /api/v1/runs/{thread_id}/state`
- `GET /api/v1/runs/{thread_id}/timeline`
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

Durable state note: by default, local workflow state is stored in `data/supportflow.sqlite3`. Set `SUPPORTFLOW_DB_PATH=/path/to/supportflow.sqlite3` before starting the backend to choose a different database. Reusing the same database path lets pending reviews, run timelines, and LangGraph checkpoints survive a backend restart. Local SQLite files under `data/*.sqlite3*` are ignored by git.

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

- `ticket-1003` should auto-finalize on `/tickets`, show a `Final response`, and show a completed timeline.
- `ticket-1001` should pause in `waiting_review`, show risk-gate details and an interrupt event, and appear on `/reviews`.
- Approving or editing a pending review should finish the run and show a completed result.
- Rejecting a pending review should end in `manual_takeover` with no final AI response.

Each workflow run gets a unique `thread_id`, so rerunning the same ticket starts a fresh review item instead of reusing older graph state.

## Offline evaluation

Run the offline eval from the backend directory:

```bash
cd backend
uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py
```

The command reads `data/evals/supportflow_v1.jsonl`, runs both `plain_rag_baseline` and `graph_v1` on 20 fixed examples, and writes generated artifacts under `data/evals/results/`. The first three examples use the product demo tickets; the expanded eval-only tickets live in `data/evals/supportflow_tickets.json` so the `/tickets` UI stays small.

Expected summary shape:

```text
target=plain_rag_baseline examples=20 category_accuracy=null retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=0.30 final_pass_rate=0.30 bad_cases=28
target=graph_v1 examples=20 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=1.00 final_pass_rate=1.00 bad_cases=0
wrote data/evals/results/latest_summary.json
wrote data/evals/results/bad_cases.jsonl
wrote data/evals/results/traces/<run_id>/events.jsonl
```

`data/evals/results/` is ignored by git because it is generated output. Keep `data/evals/supportflow_v1.jsonl` and `data/evals/supportflow_tickets.json` checked in as the fixed eval source data.

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
