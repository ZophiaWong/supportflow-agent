# Day 15 Streaming Workflow UX

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The current ticket run endpoint behaves like a request that returns after the workflow reaches a final or waiting-review state. After this change, the frontend will show workflow progress as it happens: loading context, classification, retrieval, drafting, policy checks, review interrupt, and finalization.

This improves the product experience and demonstrates full-stack agent UX for long-running workflows.

## Progress

- [x] (2026-04-27) Created this todo ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [x] (2026-05-25) Reviewed the plan against the current backend route shape, trace endpoint, and approval-gated customer-send behavior.
- [x] (2026-05-25) Moved this file to `docs/exec-plans/active/` for implementation.
- [x] (2026-05-25) Inspected current ticket detail UI, backend run endpoint, trace/state/timeline polling behavior, and existing frontend/backend tests.
- [x] (2026-05-25) Added a non-blocking run-start endpoint backed by FastAPI background execution.
- [x] (2026-05-25) Updated frontend ticket detail flow to start background runs and render live progress from trace/state polling.
- [x] (2026-05-25) Added backend and frontend test coverage for the new start-run behavior.
- [x] (2026-05-25) Updated README and this ExecPlan with observed behavior and validation evidence.

## Surprises & Discoveries

- Observation: The existing `POST /api/v1/tickets/{ticket_id}/run` cannot support frontend polling while the graph is running because it creates the thread ID and blocks until `graph.invoke(...)` returns.
  Evidence: `backend/app/api/v1/runs.py::run_ticket` generates `thread_id`, invokes the graph synchronously, and only then returns `RunTicketResponse`.

- Observation: The trace endpoint is a better source for live node progress than the current timeline endpoint.
  Evidence: `backend/app/graph/tracing.py::traced_node` writes measured graph-node trace events during node execution, while `backend/app/api/v1/runs.py::_append_major_run_events` appends major timeline events after the initial graph invocation returns.

- Observation: Demo ticket `ticket-1003` is low content risk but should not auto-finalize before approval because external customer sends are policy-gated.
  Evidence: Current policy behavior treats `send_customer_reply` as a high-impact action requiring review, so `ticket-1003` should first transition to `waiting_review` and only reach `done` after reviewer approval.

- Observation: A run can be known before LangGraph has written its first checkpoint.
  Evidence: The new start endpoint writes `run_started` before the background graph task begins. `GET /api/v1/runs/{thread_id}/state` now returns a minimal `running` state for known started threads whose graph snapshot is not available yet.

## Decision Log

- Decision: Use background-run polling rather than server-sent events for the first streaming UX.
  Rationale: The project already persists run state, timeline events, and measured node traces in SQLite. A run-start endpoint that returns `thread_id` immediately lets the frontend poll existing read endpoints with less infrastructure risk than adding a long-lived event stream.
  Date/Author: 2026-04-27 / Codex; revised 2026-05-25 / Codex

- Decision: Keep the UI operational rather than decorative.
  Rationale: `AGENTS.md` and the product direction favor a support workflow app. The UI should help agents scan progress, not present a marketing demo.
  Date/Author: 2026-04-27 / Codex

- Decision: Use `GET /api/v1/runs/{thread_id}/trace` as the primary progress source and keep `GET /api/v1/runs/{thread_id}/timeline` as coarse history.
  Rationale: Trace rows are written at graph-node boundaries and already include node status, duration, policy IDs, proposed actions, reviewer decisions, and final disposition. Timeline rows are useful for the existing product surface but are not currently emitted early enough to be the live progress source.
  Date/Author: 2026-05-25 / Codex

- Decision: Preserve the existing blocking run endpoint and add `POST /api/v1/tickets/{ticket_id}/runs/start` instead of changing existing route semantics.
  Rationale: Existing tests, evals, and manual curl examples rely on the blocking route returning a full `RunTicketResponse`. The new route gives the frontend a `thread_id` immediately without breaking those callers.
  Date/Author: 2026-05-25 / Codex

## Outcomes & Retrospective

Completed on 2026-05-25. The backend now exposes `POST /api/v1/tickets/{ticket_id}/runs/start`, which validates the ticket, writes a `run_started` timeline event, returns `thread_id` immediately, and runs the existing graph workflow in a background task. The existing blocking run endpoint remains unchanged for compatibility.

The frontend ticket detail page now calls the start endpoint, stores the returned thread ID, renders an immediate `running` state, and polls state/timeline/trace until the run leaves `running`. When state has enough workflow data, the existing workflow output panel is hydrated from `RunStateResponse`, so `waiting_review`, final responses, support actions, and policy data still appear in the familiar UI.

Validation passed: backend tests reported `43 passed`; frontend tests reported `13 passed`; frontend production build succeeded; offline eval reported `graph_v1 final_pass_rate=1.00` with `0` bad cases. Real token streaming remains deferred because this workflow uses deterministic local drafting rather than incremental LLM token output.

## Context and Orientation

The frontend ticket page is `frontend/src/pages/TicketsPage.tsx`. Ticket details are shown by `frontend/src/components/TicketDetail.tsx`. Workflow results, timelines, run state, and trace panels are shown by components under `frontend/src/components/`. API helpers are in `frontend/src/lib/api.ts`.

The backend run endpoint is `POST /api/v1/tickets/{ticket_id}/run` in `backend/app/api/v1/runs.py`. Current read endpoints are `GET /api/v1/runs/{thread_id}/state`, `GET /api/v1/runs/{thread_id}/timeline`, and `GET /api/v1/runs/{thread_id}/trace`.

Streaming workflow UX means the user sees progress while a run is ongoing. In this plan, "streaming" is implemented as short-interval polling: the browser starts a run, receives the `thread_id` immediately, and repeatedly asks the backend for trace and state until the workflow reaches a terminal status.

## Plan of Work

First, inspect the existing frontend run flow. Determine how `TicketsPage` stores thread IDs, loads run state, loads timeline, and loads trace after the current blocking run request. Preserve working behavior for completed and waiting-review runs.

Second, add a new non-blocking start endpoint. Keep the existing blocking `POST /api/v1/tickets/{ticket_id}/run` route for compatibility. Add an endpoint such as `POST /api/v1/tickets/{ticket_id}/runs/start` that creates the same `thread_id`, writes the initial `run_started` event, schedules graph execution in a FastAPI background task, and returns a small response containing `thread_id`, `ticket_id`, and an initial `status` such as `running`.

Third, make the background execution reuse the same workflow logic as the existing blocking route. Avoid duplicating graph invocation, pending review extraction, pending-review persistence, and major event writing in two divergent code paths. A practical implementation is to extract the shared run body into a private helper in `backend/app/api/v1/runs.py`, then have the blocking route call it directly and the new start endpoint call it from the background task.

Fourth, update frontend state. When a user starts a run, use the new start endpoint, store the returned `thread_id`, and show a stable progress area with graph-node rows from the trace endpoint. Continue polling trace and state until status is `done`, `waiting_review`, `manual_takeover`, or `failed`. Polling should also stop when the component unmounts or when the user starts a different run.

Fifth, handle approval-gated runs. Both `ticket-1003` and `ticket-1001` should visibly transition into `waiting_review` because proposed external customer sends require approval. The UI should guide the reviewer to `/reviews` without losing the current ticket context. After approval, the UI should be able to refresh the same run and show `done`; after rejection, it should show `manual_takeover`.

Sixth, add tests. Frontend tests should simulate progress updates and assert loading, graph-node progress, waiting-review, done-after-approval, and manual-takeover states. Backend tests should assert the new start endpoint returns a `thread_id` immediately and that trace/state polling can observe a running or completed workflow through the chosen read endpoints.

## Concrete Steps

Inspect current frontend run behavior:

    sed -n '1,360p' frontend/src/pages/TicketsPage.tsx
    sed -n '1,320p' frontend/src/components/TicketDetail.tsx
    sed -n '1,260p' frontend/src/components/WorkflowTimeline.tsx
    sed -n '1,260p' frontend/src/components/WorkflowTrace.tsx
    sed -n '1,240p' frontend/src/lib/api.ts
    sed -n '1,340p' backend/app/api/v1/runs.py
    sed -n '1,280p' backend/app/graph/tracing.py

Run current tests:

    cd frontend
    npm test -- --run

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

After implementation, run:

    cd frontend
    npm test -- --run
    npm run build

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

Observed final validation on 2026-05-25:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    # 43 passed in 15.97s

    cd frontend
    npm test -- --run
    # 13 passed

    npm run build
    # built in 461ms

    cd backend
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py
    # target=graph_v1 examples=20 ... final_pass_rate=1.00 bad_cases=0

Manual smoke:

    cd backend
    uv run --cache-dir /tmp/uv-cache uvicorn app.main:app --host 127.0.0.1 --port 8000

    cd frontend
    npm run dev -- --host 127.0.0.1 --port 5173

Open `/tickets`, run `ticket-1003`, and observe trace rows appear without manual refresh until the run reaches `waiting_review`. Open `/reviews`, approve that run, and confirm the ticket detail can refresh to `done` with executed actions. Then run `ticket-1001` and observe a transition into `waiting_review`; reject a fresh risky run and confirm the UI can show `manual_takeover`.

## Validation and Acceptance

This plan is complete when all of these are true:

- Running a ticket shows workflow progress without manual refresh.
- The new non-blocking start endpoint returns a `thread_id` immediately and does not break the existing blocking run endpoint.
- `ticket-1003` visibly progresses to `waiting_review` for customer-send approval, then reaches `done` after approval.
- `ticket-1001` visibly progresses to `waiting_review`; a rejected run reaches `manual_takeover`.
- Frontend tests cover loading, trace progress, waiting-review, done-after-approval, and manual-takeover states.
- Backend tests prove trace/state progress data is available through the new start endpoint and existing read endpoints.
- Existing `/tickets` and `/reviews` behavior remains intact.

## Idempotence and Recovery

Polling should stop when a terminal status is reached and should clean up timers when components unmount. Re-running a ticket should create a new thread ID and not overwrite the displayed state of another run. If background execution fails, the backend should persist a failed timeline event and the frontend should stop polling once state or trace indicates failure.

## Artifacts and Notes

This plan builds on the completed trace and observability work. It should not introduce a second trace format or duplicate node instrumentation; it should reuse the measured trace events already emitted by graph node wrappers.

## Interfaces and Dependencies

Frontend code should rely on one new run-start helper plus existing read helpers:

    startRun(ticketId: string): Promise<StartRunResponse>
    fetchRunState(threadId: string): Promise<RunStateResponse>
    fetchRunTimeline(threadId: string): Promise<RunTimelineResponse>
    fetchRunTrace(threadId: string): Promise<RunTraceResponse>

Backend code should add one endpoint shaped like:

    POST /api/v1/tickets/{ticket_id}/runs/start

The exact response schema can be a small Pydantic model in `backend/app/schemas/graph.py` with `thread_id`, `ticket_id`, and `status`. The existing `RunTicketResponse` remains the response for the blocking route and resume route.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.

2026-05-25: Revised before activation. The plan now chooses background-run polling, uses trace as the primary progress source, preserves the existing blocking run endpoint, and aligns acceptance with the current approval-gated `send_customer_reply` behavior.

2026-05-25: Implemented the plan. Added the non-blocking start endpoint, minimal running state fallback for just-started threads, frontend start-run polling, README updates, tests, and final validation evidence.
