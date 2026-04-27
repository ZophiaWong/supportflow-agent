# Day 9 Durable Workflow State

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The MVP proves that a ticket can enter a LangGraph support workflow, pause for human review, and resume. The important remaining limitation is that the graph checkpointer, pending reviews, run timelines, and run state are process-local. After this change, a reviewer can run a risky ticket, restart the backend, still see the pending review, approve it, and watch the same workflow finish.

This is the highest-value post-MVP feature for an AI Agent Engineer portfolio because it demonstrates durable human-in-the-loop execution instead of a short-lived demo request.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [x] (2026-04-27 04:59Z) Inspected the current in-memory graph, pending review, run event, and run state services.
- [x] (2026-04-27 05:20Z) Added a standard-library SQLite storage layer plus a local SQLite LangGraph checkpointer.
- [x] (2026-04-27 05:21Z) Wired `PendingReviewStore`, `RunEventStore`, and `get_support_graph()` to durable SQLite storage.
- [x] (2026-04-27 05:22Z) Added an isolated runtime database test fixture and a restart-style durable workflow integration test.
- [x] (2026-04-27 05:27Z) Ran backend tests, frontend tests, frontend build, and offline eval successfully.
- [x] (2026-04-27 05:30Z) Ran backend HTTP restart smoke successfully with a persisted waiting-review run.
- [x] (2026-04-27 05:32Z) Updated README, generated DB schema notes, `.gitignore`, and this ExecPlan with observed acceptance evidence.

## Surprises & Discoveries

- Observation: The installed LangGraph package does not include a SQLite checkpointer.
  Evidence: `uv run --cache-dir /tmp/uv-cache python -c "import importlib.util; print(importlib.util.find_spec('langgraph.checkpoint.sqlite'))"` printed `None`, while `langgraph.checkpoint.memory` was installed.

- Observation: A small local SQLite checkpointer is practical for this repository.
  Evidence: Implementing the same synchronous methods used by `InMemorySaver` against three SQLite tables allowed interrupted graph runs to resume after `get_support_graph.cache_clear()` and after a backend process restart.

- Observation: Tests need isolated runtime database files now that checkpoint state is durable.
  Evidence: `backend/tests/conftest.py` sets `SUPPORTFLOW_DB_PATH` to a per-test temp file, clears runtime tables, and clears the graph cache before and after each test.

- Observation: Local curl requests to Uvicorn are blocked by the sandbox unless run with local-network approval.
  Evidence: The first `curl --noproxy '*' -s -X POST http://127.0.0.1:8000/api/v1/tickets/ticket-1001/run` exited with code `7`; rerunning with approved local HTTP access succeeded.

## Decision Log

- Decision: Use SQLite as the first durable store.
  Rationale: SQLite is local, deterministic, easy to run in a portfolio repo, and avoids external service setup while still proving durable state design.
  Date/Author: 2026-04-27 / Codex

- Decision: Keep the single LangGraph workflow and do not introduce multi-agent orchestration.
  Rationale: `AGENTS.md` says to keep LangGraph workflow-first and never introduce multi-agent patterns. Durable state improves the existing workflow without changing that architecture.
  Date/Author: 2026-04-27 / Codex

- Decision: Implement a local SQLite checkpointer instead of adding `langgraph-checkpoint-sqlite`.
  Rationale: The compatible SQLite checkpointer was not installed, network access is restricted, and the required synchronous LangGraph checkpointer surface is small enough to support with the standard library for a local portfolio project.
  Date/Author: 2026-04-27 / Codex

- Decision: Persist pending reviews and timeline events as JSON payloads in SQLite while preserving existing Pydantic API schemas.
  Rationale: This keeps route and frontend behavior stable, avoids premature relational modeling, and preserves typed validation through `model_dump(mode="json")` and `model_validate`.
  Date/Author: 2026-04-27 / Codex

- Decision: Ignore local SQLite files under `data/*.sqlite3*`.
  Rationale: The default database path is useful for local demos but is generated runtime state and should not be committed.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Day 9 is implemented. The backend now uses local SQLite for pending review records, run timeline events, and LangGraph checkpoints. The default database path is `data/supportflow.sqlite3`, and `SUPPORTFLOW_DB_PATH` can point to a different database for tests or demos. The graph topology and public API routes are unchanged.

The restart behavior is now durable for the accepted human-review flow. In the HTTP smoke test, `ticket-1001` entered `waiting_review`, the backend was stopped and restarted with the same SQLite database path, `/api/v1/reviews/pending` still returned the pending review, `/api/v1/runs/{thread_id}/state` still returned `waiting_review`, and approving the review resumed the graph to `done` with final disposition `approved`.

Validation passed with backend tests `29 passed`, frontend tests `9 passed`, frontend production build success, and offline eval `graph_v1` final pass rate `1.00` with `0` bad cases. The main remaining limitation is that this is a local SQLite checkpointer, not a production multi-process database setup.

## Context and Orientation

`supportflow-agent` is a FastAPI, LangGraph, and React support workflow app. The backend lives under `backend/`, the frontend under `frontend/`, and docs under `docs/`.

The current graph is created in `backend/app/graph/builder.py`. It compiles a `StateGraph` with `backend/app/services/sqlite_checkpointer.py::SqliteSaver`. A checkpoint is the saved graph state for a thread ID; LangGraph uses it to resume an interrupted workflow.

Pending review state is stored by `backend/app/services/pending_review_store.py`, which persists `PendingReviewItem` JSON payloads in SQLite. Run timeline events are stored by `backend/app/services/run_event_store.py`, which persists `RunTimelineEvent` JSON payloads in SQLite. Runtime database path and schema setup live in `backend/app/services/sqlite_store.py`. Run state is read in `backend/app/services/run_state_service.py` by asking the graph checkpointer for a snapshot. The API routes are in `backend/app/api/v1/runs.py` and `backend/app/api/v1/reviews.py`.

The user-visible routes already exist:

- `POST /api/v1/tickets/{ticket_id}/run` starts a workflow.
- `GET /api/v1/reviews/pending` lists pending human reviews.
- `POST /api/v1/runs/{thread_id}/resume` resumes a reviewed workflow.
- `GET /api/v1/runs/{thread_id}/state` reads current run state.
- `GET /api/v1/runs/{thread_id}/timeline` reads the timeline.

Durable state means these routes still work after the backend process is restarted, using persisted data instead of in-memory dictionaries.

## Plan of Work

First, inspect the current package dependencies in `backend/pyproject.toml` and the installed LangGraph version in `backend/uv.lock`. This has been completed. `langgraph.checkpoint.sqlite` is not installed, so this plan implemented a small local SQLite checkpointer in `backend/app/services/sqlite_checkpointer.py`.

Second, add a database module such as `backend/app/services/sqlite_store.py`. This has been completed. It opens a SQLite database path from `SUPPORTFLOW_DB_PATH`, defaults to `data/supportflow.sqlite3`, creates parent directories, enables WAL mode and foreign keys, and initializes tables idempotently.

Third, replace the process-local stores with durable equivalents. This has been completed. `PendingReviewStore` persists `PendingReviewItem.model_dump(mode="json")` as JSON. `RunEventStore` persists `RunTimelineEvent.model_dump(mode="json")` as JSON. Existing public method names were preserved.

Fourth, make graph construction durable. This has been completed. `backend/app/graph/builder.py` now compiles the same graph topology with `SqliteSaver()`.

Fifth, update `backend/app/services/run_state_service.py`. No code change was needed because it already reads from graph snapshots, and those snapshots are now durable.

Sixth, add tests. This has been completed in `backend/tests/conftest.py` and `backend/tests/integration/test_durable_workflow_state.py`. The new test runs `ticket-1001` until `waiting_review`, clears the graph cache to simulate fresh graph construction, confirms pending review, state, and timeline still load from SQLite, approves the review, clears the graph cache again, and confirms the final state remains `done`.

Seventh, update docs. This has been completed in `README.md` and `docs/generated/db-schema.md`. `.gitignore` now ignores local SQLite runtime files.

## Concrete Steps

Work from the repository root unless noted.

Inspect current storage code:

    sed -n '1,240p' backend/app/graph/builder.py
    sed -n '1,240p' backend/app/services/pending_review_store.py
    sed -n '1,260p' backend/app/services/run_event_store.py
    sed -n '1,240p' backend/app/services/run_state_service.py
    sed -n '1,260p' backend/app/api/v1/runs.py
    sed -n '1,200p' backend/app/api/v1/reviews.py

Run the existing backend suite before changes:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

Expected current result is close to:

    28 passed

Observed before implementation:

    28 passed in 0.43s

After implementing durable storage, run:

    cd backend
    SUPPORTFLOW_DB_PATH=/tmp/supportflow-agent-test.sqlite3 uv run --cache-dir /tmp/uv-cache pytest

Observed after implementation:

    29 passed in 3.10s

Run frontend validation because README-visible behavior still depends on the same state and timeline APIs:

    cd frontend
    npm test -- --run
    npm run build

Observed after implementation:

    Test Files  4 passed (4)
    Tests  9 passed (9)
    vite v5.4.21 building for production...
    41 modules transformed.
    built in 545ms

Run the offline eval:

    cd backend
    SUPPORTFLOW_DB_PATH=/tmp/supportflow-agent-eval.sqlite3 uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

Observed after implementation:

    target=plain_rag_baseline examples=20 category_accuracy=null retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=0.30 final_pass_rate=0.30 bad_cases=28
    target=graph_v1 examples=20 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=1.00 final_pass_rate=1.00 bad_cases=0
    wrote data/evals/results/latest_summary.json
    wrote data/evals/results/bad_cases.jsonl
    wrote data/evals/results/traces/eval-20260427T052702Z-2bbf12ca/events.jsonl

Run a manual restart smoke test:

    cd backend
    SUPPORTFLOW_DB_PATH=/tmp/supportflow-agent-demo.sqlite3 uv run --cache-dir /tmp/uv-cache uvicorn app.main:app --host 127.0.0.1 --port 8000

In another shell, start a risky run:

    curl --noproxy '*' -s -X POST http://127.0.0.1:8000/api/v1/tickets/ticket-1001/run

Stop and restart the backend with the same `SUPPORTFLOW_DB_PATH`, then run:

    curl --noproxy '*' -s http://127.0.0.1:8000/api/v1/reviews/pending

Expected result: the pending review for `ticket-1001` is still returned. Then approve it:

    curl --noproxy '*' -s -X POST http://127.0.0.1:8000/api/v1/runs/<thread_id>/resume -H 'content-type: application/json' -d '{"decision":"approve"}'

Expected result: the response has `status` equal to `done` and `final_response.disposition` equal to `approved`.

Observed HTTP restart smoke:

    POST /api/v1/tickets/ticket-1001/run
    status: waiting_review
    thread_id: ticket-ticket-1001-92682b51

    Backend stopped and restarted with SUPPORTFLOW_DB_PATH=/tmp/supportflow-agent-demo.sqlite3.

    GET /api/v1/reviews/pending
    returned the pending review for ticket-ticket-1001-92682b51

    GET /api/v1/runs/ticket-ticket-1001-92682b51/state
    status: waiting_review
    current_node: human_review_interrupt

    POST /api/v1/runs/ticket-ticket-1001-92682b51/resume
    status: done
    final_response.disposition: approved

## Validation and Acceptance

This plan is complete when all of these are true:

- Backend tests pass.
- A new restart-style test proves pending review survives fresh app or service construction with the same SQLite database.
- A manual smoke test proves a waiting-review run can resume after backend restart.
- Existing low-risk, approve, edit, and reject behavior still works.
- Documentation no longer claims that the accepted durable behavior is memory-only.

All acceptance criteria are satisfied as of 2026-04-27.

## Idempotence and Recovery

Database initialization uses `CREATE TABLE IF NOT EXISTS` and safe schema setup so the backend can start repeatedly. Tests use temporary database files through an autouse pytest fixture. Do not run destructive cleanup against a user-selected `SUPPORTFLOW_DB_PATH` unless the command name clearly says it resets demo data.

## Artifacts and Notes

The portfolio roadmap that produced this plan is `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`. It identifies durable workflow state as the first post-MVP implementation because it is the strongest engineering signal after MVP acceptance.

Runtime tables added by this plan:

    pending_reviews(thread_id, ticket_id, payload_json, updated_at)
    run_events(event_id, thread_id, ticket_id, created_at, event_type, payload_json)
    langgraph_checkpoints(thread_id, checkpoint_ns, checkpoint_id, checkpoint_blob, metadata_blob, parent_checkpoint_id)
    langgraph_writes(thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, value_blob, task_path)
    langgraph_blobs(thread_id, checkpoint_ns, channel, version, value_blob)

## Interfaces and Dependencies

Preserve these public API shapes unless a later discovery makes a change unavoidable:

- `get_pending_review_store().list_items() -> list[PendingReviewItem]`
- `get_pending_review_store().get(thread_id: str) -> PendingReviewItem | None`
- `get_pending_review_store().upsert(item: PendingReviewItem) -> PendingReviewItem`
- `get_pending_review_store().remove(thread_id: str) -> PendingReviewItem | None`
- `get_run_event_store().append(event: RunTimelineEvent) -> None`
- `get_run_event_store().list_by_thread_id(thread_id: str) -> list[RunTimelineEvent]`
- `get_run_state(thread_id: str) -> RunStateResponse | None`

Use Pydantic model serialization with `model_dump(mode="json")` when persisting schema objects. Use `model_validate` when reading persisted JSON back into schema objects.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.

2026-04-27: Implemented durable SQLite runtime state and updated this plan with observed validation and restart-smoke evidence.
