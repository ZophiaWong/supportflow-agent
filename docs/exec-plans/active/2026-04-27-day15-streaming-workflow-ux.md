# Day 15 Streaming Workflow UX

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The current ticket run endpoint behaves like a request that returns after the workflow reaches a final or waiting-review state. After this change, the frontend will show workflow progress as it happens: loading context, classification, retrieval, drafting, policy checks, review interrupt, and finalization.

This improves the product experience and demonstrates full-stack agent UX for long-running workflows.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [ ] Inspect current ticket run UI, backend run endpoint, and timeline/state polling behavior.
- [ ] Choose server-sent events or polling as the first streaming mechanism.
- [ ] Add backend progress endpoint or event stream.
- [ ] Update frontend to render live progress without manual refresh.
- [ ] Add frontend and backend tests.
- [ ] Update docs and this ExecPlan with observed behavior.

## Surprises & Discoveries

- Observation: No implementation discoveries yet.
  Evidence: This plan has only been created.

## Decision Log

- Decision: Prefer simple polling unless server-sent events are straightforward in the current stack.
  Rationale: The project already has run state and timeline endpoints. Polling can deliver visible progress with less infrastructure risk, while server-sent events can be added later if needed.
  Date/Author: 2026-04-27 / Codex

- Decision: Keep the UI operational rather than decorative.
  Rationale: `AGENTS.md` and the product direction favor a support workflow app. The UI should help agents scan progress, not present a marketing demo.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize the chosen streaming mechanism, UI behavior, tests, and any deferred real token streaming work.

## Context and Orientation

The frontend ticket page is `frontend/src/pages/TicketsPage.tsx`. Ticket details are shown by `frontend/src/components/TicketDetail.tsx`. Workflow results and timelines are shown by components under `frontend/src/components/`. API helpers are in `frontend/src/lib/api.ts`.

The backend run endpoint is `POST /api/v1/tickets/{ticket_id}/run` in `backend/app/api/v1/runs.py`. Current state and timeline endpoints are `GET /api/v1/runs/{thread_id}/state` and `GET /api/v1/runs/{thread_id}/timeline`.

Streaming workflow UX means the user sees progress while a run is ongoing. It can be implemented with server-sent events, which are one-way HTTP event streams from backend to browser, or with polling, where the frontend repeatedly asks the backend for state and timeline.

## Plan of Work

First, inspect the existing frontend run flow. Determine whether it already stores thread IDs and reloads state after a run. Preserve working behavior for completed and waiting-review runs.

Second, choose the mechanism. If backend graph execution is currently synchronous and fast, polling may be enough. Add or reuse a run-start endpoint that returns a thread ID quickly only if needed. If the synchronous endpoint cannot expose intermediate states, consider a background task or server-sent events only after recording the complexity in the Decision Log.

Third, make backend progress observable. Ensure timeline events are written as each meaningful step completes, not only after graph invocation returns. This may require moving event writes into graph nodes or adding callbacks around node execution.

Fourth, update frontend state. When a user starts a run, show a stable progress area with node status rows. Continue fetching state or consuming events until status is `done`, `waiting_review`, `manual_takeover`, or `failed`.

Fifth, handle risky runs. The UI should visibly transition into `waiting_review` and link or guide the reviewer to `/reviews` without losing the current ticket context.

Sixth, add tests. Frontend tests should simulate progress updates and assert loading, progress, completed, and waiting-review states. Backend tests should assert timeline events are available during or immediately after execution.

## Concrete Steps

Inspect current frontend run behavior:

    sed -n '1,360p' frontend/src/pages/TicketsPage.tsx
    sed -n '1,320p' frontend/src/components/TicketDetail.tsx
    sed -n '1,260p' frontend/src/components/WorkflowTimeline.tsx
    sed -n '1,240p' frontend/src/lib/api.ts
    sed -n '1,340p' backend/app/api/v1/runs.py

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

Manual smoke:

    cd backend
    uv run --cache-dir /tmp/uv-cache uvicorn app.main:app --host 127.0.0.1 --port 8000

    cd frontend
    npm run dev -- --host 127.0.0.1 --port 5173

Open `/tickets`, run `ticket-1003`, and observe progress without manual refresh. Then run `ticket-1001` and observe a transition into `waiting_review`.

## Validation and Acceptance

This plan is complete when all of these are true:

- Running a ticket shows workflow progress without manual refresh.
- A low-risk ticket visibly progresses to `done`.
- A risky ticket visibly progresses to `waiting_review`.
- Frontend tests cover progress, done, failed or manual takeover, and waiting-review states.
- Backend tests prove progress data is available through the chosen endpoint.
- Existing `/tickets` and `/reviews` behavior remains intact.

## Idempotence and Recovery

Polling should stop when a terminal status is reached and should clean up timers when components unmount. If server-sent events are used, close event streams on completion or component unmount. Re-running a ticket should create a new thread ID and not overwrite the displayed state of another run.

## Artifacts and Notes

This plan becomes easier after Day 12 trace and observability because trace or timeline events provide the progress data. If Day 12 is not complete, this plan may first improve timeline granularity.

## Interfaces and Dependencies

If polling is chosen, frontend code should rely on existing or new helpers like:

    fetchRunState(threadId: string): Promise<RunStateResponse>
    fetchRunTimeline(threadId: string): Promise<RunTimelineResponse>

If server-sent events are chosen, add a helper or hook that consumes an endpoint like:

    GET /api/v1/runs/{thread_id}/events

Document the chosen interface in this plan when implementation starts.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.
