# Day 9 Durable Workflow State

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The MVP proves that a ticket can enter a LangGraph support workflow, pause for human review, and resume. The important remaining limitation is that the graph checkpointer, pending reviews, run timelines, and run state are process-local. After this change, a reviewer can run a risky ticket, restart the backend, still see the pending review, approve it, and watch the same workflow finish.

This is the highest-value post-MVP feature for an AI Agent Engineer portfolio because it demonstrates durable human-in-the-loop execution instead of a short-lived demo request.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [ ] Inspect current in-memory graph, pending review, run event, and run state services.
- [ ] Add a durable SQLite-backed storage layer for run state, timeline events, pending reviews, and graph checkpoints.
- [ ] Wire backend routes and graph construction to use durable storage.
- [ ] Add restart-style backend tests.
- [ ] Update docs and this ExecPlan with observed acceptance evidence.

## Surprises & Discoveries

- Observation: No implementation discoveries yet.
  Evidence: This plan has only been created.

## Decision Log

- Decision: Use SQLite as the first durable store.
  Rationale: SQLite is local, deterministic, easy to run in a portfolio repo, and avoids external service setup while still proving durable state design.
  Date/Author: 2026-04-27 / Codex

- Decision: Keep the single LangGraph workflow and do not introduce multi-agent orchestration.
  Rationale: `AGENTS.md` says to keep LangGraph workflow-first and never introduce multi-agent patterns. Durable state improves the existing workflow without changing that architecture.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize the database schema, restart behavior, tests, and any remaining durability gaps.

## Context and Orientation

`supportflow-agent` is a FastAPI, LangGraph, and React support workflow app. The backend lives under `backend/`, the frontend under `frontend/`, and docs under `docs/`.

The current graph is created in `backend/app/graph/builder.py`. It compiles a `StateGraph` with `InMemorySaver`, which means LangGraph checkpoints disappear when the Python process stops. A checkpoint is the saved graph state for a thread ID; LangGraph uses it to resume an interrupted workflow.

Pending review state is currently in `backend/app/services/pending_review_store.py`, which stores `PendingReviewItem` objects in a Python dictionary. Run timeline events are currently in `backend/app/services/run_event_store.py`, which stores events in a Python dictionary keyed by thread ID. Run state is read in `backend/app/services/run_state_service.py` by asking the graph checkpointer for a snapshot. The API routes are in `backend/app/api/v1/runs.py` and `backend/app/api/v1/reviews.py`.

The user-visible routes already exist:

- `POST /api/v1/tickets/{ticket_id}/run` starts a workflow.
- `GET /api/v1/reviews/pending` lists pending human reviews.
- `POST /api/v1/runs/{thread_id}/resume` resumes a reviewed workflow.
- `GET /api/v1/runs/{thread_id}/state` reads current run state.
- `GET /api/v1/runs/{thread_id}/timeline` reads the timeline.

Durable state means these routes still work after the backend process is restarted, using persisted data instead of in-memory dictionaries.

## Plan of Work

First, inspect the current package dependencies in `backend/pyproject.toml` and the installed LangGraph version in `backend/uv.lock`. If LangGraph already provides a SQLite checkpointer compatible with the installed version, use it. If it is not available without adding network-dependent packages, implement a small local checkpointer only if that is practical; otherwise persist the application-level pending review and event state first and record the checkpoint limitation in `Surprises & Discoveries`.

Second, add a database module such as `backend/app/services/sqlite_store.py`. It should open a SQLite database path from an environment variable such as `SUPPORTFLOW_DB_PATH`, defaulting to a local development path like `data/supportflow.sqlite3`. It must create tables idempotently. Use Python's standard `sqlite3` module unless a dependency already exists in the repo.

Third, replace the process-local stores with durable equivalents. `PendingReviewStore` should persist `PendingReviewItem.model_dump(mode="json")` as JSON. `RunEventStore` should persist `RunTimelineEvent.model_dump(mode="json")` as JSON or normalized columns. Preserve the existing method names where possible so route changes stay small.

Fourth, make graph construction durable. Update `backend/app/graph/builder.py` so `get_support_graph()` uses a durable checkpointer if available. If a checkpointer object needs the SQLite connection, hide that detail behind a helper such as `get_checkpointer()`. Keep the graph node topology unchanged.

Fifth, update `backend/app/services/run_state_service.py`. It should continue returning `RunStateResponse`, but after this change it must work when the app is reconstructed against the same database file. If graph checkpoints are durable, read from the graph snapshot. If application-level state also needs a fallback, persist enough final and waiting-review state to return a meaningful response.

Sixth, add tests. The most important test should use a temporary SQLite database path, run `ticket-1001` until `waiting_review`, construct fresh service or app instances pointing at the same database, confirm `GET /api/v1/reviews/pending` still lists the item, then approve the review and confirm the result is `done`.

Seventh, update docs. Update `README.md` or a design doc if it currently says pending reviews and checkpoints are memory-only. Update `docs/product-specs/supportflow-mvp.md` or the portfolio roadmap only if the acceptance evidence changes.

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

After implementing durable storage, run:

    cd backend
    SUPPORTFLOW_DB_PATH=/tmp/supportflow-agent-test.sqlite3 uv run --cache-dir /tmp/uv-cache pytest

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

## Validation and Acceptance

This plan is complete when all of these are true:

- Backend tests pass.
- A new restart-style test proves pending review survives fresh app or service construction with the same SQLite database.
- A manual smoke test proves a waiting-review run can resume after backend restart.
- Existing low-risk, approve, edit, and reject behavior still works.
- Documentation no longer claims that the accepted durable behavior is memory-only.

## Idempotence and Recovery

Database initialization must use `CREATE TABLE IF NOT EXISTS` and safe schema setup so the backend can start repeatedly. Tests should use temporary database files and clean them up through pytest fixtures or temporary directories. Do not run destructive cleanup against a user-selected `SUPPORTFLOW_DB_PATH` unless the command name clearly says it resets demo data.

## Artifacts and Notes

The portfolio roadmap that produced this plan is `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`. It identifies durable workflow state as the first post-MVP implementation because it is the strongest engineering signal after MVP acceptance.

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
