# supportflow-agent

supportflow-agent is a workflow-first AI support app for ticket triage, knowledge retrieval, response drafting, and human review for risky cases.

The current repository state is the post-MVP workflow portfolio slice:

- FastAPI backend with `GET /healthz`
- FastAPI ticket list endpoint at `GET /api/v1/tickets`
- FastAPI workflow run endpoint at `POST /api/v1/tickets/{ticket_id}/run`
- FastAPI non-blocking workflow start endpoint at `POST /api/v1/tickets/{ticket_id}/runs/start`
- FastAPI run state endpoint at `GET /api/v1/runs/{thread_id}/state`
- FastAPI run timeline endpoint at `GET /api/v1/runs/{thread_id}/timeline`
- FastAPI run trace endpoint at `GET /api/v1/runs/{thread_id}/trace`
- FastAPI pending review endpoint at `GET /api/v1/reviews/pending`
- FastAPI resume endpoint at `POST /api/v1/runs/{thread_id}/resume`
- LangGraph workflow with policy gating, approval-gated support actions, human-in-the-loop resume, and inspectable run state
- React ticket inbox at `/tickets` and ticket workbench at `/tickets/:ticketId`
- React review queue at `/reviews`
- Local Markdown knowledge base with metadata-backed retrieval diagnostics
- Offline eval CLI comparing `plain_rag_baseline` with `graph_v1`

## What the app does today

Open the frontend, select a demo ticket, and click `Run workflow`.

The frontend calls `POST /api/v1/tickets/{ticket_id}/runs/start`, receives a `thread_id`, and polls run state plus trace data while the backend runs this LangGraph path:

1. Load the selected ticket from local demo data
2. Classify the ticket with deterministic rules
3. Retrieve matching KB snippets from `data/kb`
4. Draft a reply with citations and confidence
5. Propose simulated support actions such as sending a customer reply
6. Run deterministic policy checks over the ticket, draft, evidence, and proposed actions
7. Pause for human approval when policy requires review, then resume to finalization or manual takeover

The UI then shows:

- ticket detail
- classification category and priority
- retrieved knowledge hits
- draft reply and confidence
- policy flags and reviewer guidance
- proposed and executed support actions
- waiting-review state for approval-gated sends and risky tickets
- final response after approval or safe finalization
- a readable workflow run label such as `ticket-1001 · Run a1b2c3d4`
- current run summary for the active `thread_id`
- optional diagnostics with run state, timeline milestones, and measured graph-node trace spans

The `/tickets/:ticketId` page stores the latest run `thread_id` in local storage and reloads its state, timeline, and trace from the backend. The raw `thread_id` remains the internal workflow identifier, while the UI displays a short run label like `ticket-1001 · Run a1b2c3d4` so repeated runs of the same ticket can be distinguished. Run checkpoints, pending reviews, and timeline events are stored in local SQLite state, so a waiting review can survive a backend restart when the same database path is used.

For approval-gated or risky tickets, use the `Open review` link on the ticket workbench or open `/reviews` to:

- inspect the draft and supporting knowledge
- approve the draft and proposed support actions
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
- `backend/app/services/run_trace_store.py`: SQLite-backed graph-node trace storage
- `backend/app/services/run_state_service.py`: read-only run state projection from LangGraph checkpoints
- `backend/app/api/v1/reviews.py`: pending review list endpoint
- `backend/app/services/ticket_repo.py`: demo ticket loading
- `backend/app/services/retrieval.py`: lexical KB retrieval with diagnostics
- `backend/app/services/kb_ingestion.py`: Markdown KB metadata validation
- `backend/app/services/policy_engine.py`: deterministic policy checks
- `backend/app/services/action_ledger.py`: durable simulated support action ledger
- `backend/app/services/pending_review_store.py`: SQLite-backed pending review storage
- `backend/app/services/sqlite_checkpointer.py`: local SQLite LangGraph checkpoint saver
- `backend/app/services/sqlite_store.py`: SQLite path and schema setup
- `backend/app/graph/state.py`: shared graph state
- `backend/app/graph/nodes/`: graph node implementations
- `backend/app/graph/builder.py`: compiled LangGraph builder
- `backend/app/schemas/graph.py`: structured workflow request and response models
- `backend/app/evals/`: offline eval schemas, target runners, scoring, tracing, and artifact writing
- `backend/scripts/run_offline_eval.py`: CLI entrypoint for local eval comparison
- `backend/scripts/promote_eval_case.py`: writes candidate eval fixtures from a ticket or trace for review

## Frontend

Key frontend files:

- `frontend/src/pages/TicketsPage.tsx`: main inbox page
- `frontend/src/components/RunStatePanel.tsx`: current run-state display
- `frontend/src/components/WorkflowRunSummary.tsx`: readable current workflow run summary
- `frontend/src/components/RunDiagnostics.tsx`: collapsed run state, timeline, and trace diagnostics
- `frontend/src/components/WorkflowTimeline.tsx`: major-step timeline display
- `frontend/src/components/WorkflowTrace.tsx`: graph-node trace display
- `frontend/src/components/PolicyAssessmentList.tsx`: policy check display
- `frontend/src/components/SupportActionList.tsx`: support action display
- `frontend/src/pages/ReviewQueuePage.tsx`: review queue page
- `frontend/src/components/TicketList.tsx`: selectable ticket list
- `frontend/src/components/TicketDetail.tsx`: selected ticket detail
- `frontend/src/components/WorkflowResultPanel.tsx`: workflow output display
- `frontend/src/lib/api.ts`: frontend API calls
- `frontend/src/lib/runLabels.ts`: user-facing workflow run labels
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
- `POST /api/v1/tickets/{ticket_id}/runs/start`
- `GET /api/v1/runs/{thread_id}/state`
- `GET /api/v1/runs/{thread_id}/timeline`
- `GET /api/v1/runs/{thread_id}/trace`
- `GET /api/v1/reviews/pending`
- `POST /api/v1/runs/{thread_id}/resume`

Example approval-gated customer reply run:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/tickets/ticket-1003/run
```

This should return `waiting_review` because `send_customer_reply` is an external customer-facing action that requires approval before execution.

Example risky run and resume:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/tickets/ticket-1001/run
curl -s http://127.0.0.1:8000/api/v1/reviews/pending
curl -s -X POST http://127.0.0.1:8000/api/v1/runs/<thread_id>/resume \
  -H 'content-type: application/json' \
  -d '{"decision":"approve","reviewer_note":"evidence is sufficient"}'
```

Durable state note: by default, local workflow state is stored in `data/supportflow.sqlite3`. Set `SUPPORTFLOW_DB_PATH=/path/to/supportflow.sqlite3` before starting the backend to choose a different database. Reusing the same database path lets pending reviews, run timelines, and LangGraph checkpoints survive a backend restart. Local SQLite files under `data/*.sqlite3*` are ignored by git.

### Optional LLM generation

SupportFlow runs without an LLM by default. When LLM generation is disabled or unavailable, the graph uses deterministic classification and draft fallbacks so local tests and demos remain reproducible.

To enable the first LLM integration for `classify_ticket` and `draft_reply`, copy the example env file and edit the local `.env`:

```bash
cp .env.example .env
```

```env
SUPPORTFLOW_LLM_ENABLED=true
OPENAI_API_KEY=<your_api_key>
SUPPORTFLOW_LLM_MODEL=gpt-4o-mini
SUPPORTFLOW_LLM_BASE_URL=https://api.openai.com/v1
SUPPORTFLOW_LLM_TIMEOUT_SECONDS=20
```

The root `.env` file is ignored by git. Keep `.env.example` checked in with placeholder values only.

LLM requests are sent to `{SUPPORTFLOW_LLM_BASE_URL}/chat/completions`. LLM outputs are validated with the existing Pydantic workflow schemas. Draft citations must reference retrieved KB `doc_id` values; invalid output, provider-wrapped responses such as `{"response": "..."}`, unknown citations, request failures, missing API keys, or timeouts record a sanitized error reason and fall back to the deterministic node behavior. The policy gate, review interrupt/resume flow, and support action execution remain rule-driven.

To tell whether classification or drafting came from the LLM or the deterministic fallback, inspect the `classify_ticket` and `draft_reply` spans from `GET /api/v1/runs/{thread_id}/trace` or expand the frontend diagnostics panel. The span attributes include `classification_source` and `draft_source` with `"llm"` or `"fallback"` values, and fallback spans include `classification_llm_error` or `draft_llm_error` when an LLM call failed.

## Run the frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

The frontend starts on:

- `http://127.0.0.1:5173/tickets`
- `http://127.0.0.1:5173/reviews`

By default, the frontend calls `http://127.0.0.1:8000`. If the backend runs on another port, create `frontend/.env.local` before starting Vite:

```env
VITE_API_BASE_URL=http://127.0.0.1:8002
```

Restart the frontend dev server after changing this file. For production builds, run `npm run build` again because Vite embeds `VITE_API_BASE_URL` at build time.

## Manual behavior check

Use the shipped demo tickets to confirm the main behaviors:

- `ticket-1003` should pause in `waiting_review`, show a proposed `send_customer_reply` action, and appear on `/reviews` because customer sends require approval.
- The ticket workbench for `ticket-1003` should show a readable run label such as `ticket-1003 · Run <suffix>` and an `Open review` link that goes directly to `/reviews/<thread_id>`.
- Approving `ticket-1003` should finish the run, execute the proposed send action once, show a `Final response`, and show completed timeline and trace data.
- `ticket-1001` should pause in `waiting_review`, show billing/sensitive policy details and an interrupt event, and appear on `/reviews`.
- If the same ticket has multiple pending reviews, `/reviews` should distinguish them with labels like `ticket-1001 · Run a1b2c3d4`.
- Approving or editing a pending review should finish the run and show a completed result.
- Rejecting a pending review should end in `manual_takeover` with no final AI response.

Each workflow run gets a unique `thread_id`, so rerunning the same ticket starts a fresh review item instead of reusing older graph state. The default ticket view keeps diagnostics collapsed; expand `Run state, timeline, and trace` when debugging graph state or node spans.

## Offline evaluation

Generate the dataset profile from the repository root:

```bash
python3 backend/scripts/profile_eval_dataset.py
```

This writes `docs/generated/eval-dataset-profile.md`, including KB counts, scenario distribution, expected status distribution, evidence conditions, and governance checks for missing metadata or broken KB references.

Run the offline eval from the backend directory:

```bash
cd backend
uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py
```

The command reads `data/evals/supportflow_v1.jsonl`, runs `plain_rag_baseline`, `rag_policy_baseline`, and `graph_v1` on 39 fixed examples, and writes generated artifacts under `data/evals/results/`. Offline eval defaults to deterministic mode and disables LLM calls even if a local `.env` enables LLM generation. Pass `--enable-llm` only when intentionally evaluating the configured LLM path.

The first three examples use the product demo tickets. The expanded eval-only tickets live in `data/evals/supportflow_tickets.json` so the `/tickets` UI stays scannable.

Expected summary shape:

```text
target=plain_rag_baseline examples=39 category_accuracy=null retrieval_hit_rate=1.00 citation_coverage=1.00 citation_support_rate=1.00 claim_support_rate=0.82 review_trigger_accuracy=0.21 final_pass_rate=0.21 bad_cases=130
target=rag_policy_baseline examples=39 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 citation_support_rate=1.00 claim_support_rate=0.85 review_trigger_accuracy=0.87 final_pass_rate=0.21 bad_cases=108
target=graph_v1 examples=39 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 citation_support_rate=1.00 claim_support_rate=0.85 review_trigger_accuracy=0.79 final_pass_rate=0.67 bad_cases=21
wrote data/evals/results/latest_summary.json
wrote data/evals/results/bad_cases.jsonl
wrote data/evals/results/latest_report.md
wrote data/evals/results/traces/<run_id>/events.jsonl
```

This broader dataset intentionally does not produce a perfect `graph_v1` score. The remaining graph bad cases are useful evidence: low-risk reference cases expose the current conservative approval-gated send behavior, and claim-level citation cases expose where a cited answer does not cover every expected claim. Bad case records include `failure_stage`, using plain workflow stages such as `classification`, `retrieval`, `drafting`, `policy`, `review_routing`, `actions`, and `finalization`. `latest_summary.json` and `latest_report.md` group failures by target and stage.

KB retrieval is backed by Markdown front matter under `data/kb/`. Validate the KB metadata from the backend directory:

```bash
cd backend
uv run --cache-dir /tmp/uv-cache python -m app.services.kb_ingestion
```

Workflow responses include retrieval diagnostics on each KB hit, including matched terms, category match, category boost, document metadata, and citation id.

Use thresholds for CI-friendly regression checks. Thresholds default to the `graph_v1` target:

```bash
cd backend
uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py --min-final-pass-rate 1.0 --min-citation-coverage 1.0 --min-policy-trigger-accuracy 1.0
```

To draft a new eval fixture candidate without modifying the checked-in dataset:

```bash
cd backend
uv run --cache-dir /tmp/uv-cache python scripts/promote_eval_case.py --ticket-id ticket-1001
uv run --cache-dir /tmp/uv-cache python scripts/promote_eval_case.py --trace-file ../data/evals/results/traces/<run_id>/events.jsonl --example-id E-001
```

The promotion command writes one JSONL candidate under `data/evals/candidates/`. Review that candidate before adding it to `data/evals/supportflow_v1.jsonl`.

`data/evals/results/` is ignored by git because it is generated output. Keep `data/evals/supportflow_v1.jsonl` and `data/evals/supportflow_tickets.json` checked in as the fixed eval source data.

## Draw the LangGraph

Generate a local Mermaid diagram from the currently compiled LangGraph:

```bash
cd backend
uv run --cache-dir /tmp/uv-cache python scripts/draw_langgraph.py
```

The default output is `docs/generated/current-langgraph.md`. Pass `--output ../docs/generated/current-langgraph.mmd` to write raw Mermaid instead of Markdown.

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

- streaming
- hosted LangSmith tracing
- vector retrieval
- mandatory LLM generation
- external ticket system integration
- real external message write-back

## Planning docs

Read these first when making larger changes:

- `ARCHITECTURE.md`
- `docs/product-specs/supportflow-mvp.md`
- `docs/exec-plans/active/*.md`

For multi-file features, backend/frontend refactors, graph routing changes, or observability work, use and update an ExecPlan under `docs/exec-plans/`.
