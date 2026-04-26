# Day 4 Run State and Workflow Timeline

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

Day 4 makes the existing Day 3 workflow inspectable without changing its business behavior. A user can now start a run on `/tickets`, see a current run-state panel and a timeline of major workflow steps, refresh the page and keep inspecting the latest saved `thread_id`, and query the same run later through dedicated state and timeline endpoints while the backend process is still alive.

This milestone does not add new AI behavior. It adds observability for the current workflow so a human can understand what happened during a run and whether human review is blocking progress.

## Progress

- [x] (2026-04-25 15:20Z) Rewrote the active Day 4 ExecPlan into `PLANS.md` shape and removed stale Day 3 assumptions.
- [x] (2026-04-25 15:31Z) Added backend Day 4 schemas for `RunTimelineEvent`, `RunTimelineResponse`, and `RunStateResponse`.
- [x] (2026-04-25 15:33Z) Added `backend/app/services/run_event_store.py` for in-memory timeline events.
- [x] (2026-04-25 15:34Z) Added `backend/app/services/run_state_service.py` to map LangGraph checkpoint state into a clean API response.
- [x] (2026-04-25 15:37Z) Extended `backend/app/api/v1/runs.py` with state/timeline endpoints and major-step event recording for run and resume flows.
- [x] (2026-04-25 15:39Z) Added backend tests for run state and timeline reads, including resume behavior.
- [x] (2026-04-25 15:46Z) Added frontend Day 4 types and API methods for state and timeline.
- [x] (2026-04-25 15:53Z) Updated `/tickets` to render a run-state panel, workflow timeline, polling, and last-thread restoration from `localStorage`.
- [x] (2026-04-25 15:56Z) Added frontend tests for the new inspection behavior and restored-thread fetch.
- [x] (2026-04-25 16:00Z) Updated README and frontend design docs to reflect Day 4 behavior.
- [x] (2026-04-25 16:03Z) Ran backend tests, frontend tests, and frontend build successfully.

## Surprises & Discoveries

- Observation: LangGraph already exposes `CompiledStateGraph.get_state(config)` and returns a `StateSnapshot` with `values`, `next`, and `interrupts`, which was enough to build a read-only state service without changing graph nodes.
  Evidence: local inspection with `uv run --cache-dir /tmp/uv-cache python` against `get_support_graph()`.

- Observation: The waiting-review checkpoint snapshot still reports `status="running"` and `current_node="risk_gate"` because the interrupt happens before the `human_review_interrupt` node writes state.
  Evidence: `graph.get_state()` for an interrupted run showed `next=('human_review_interrupt',)` and interrupt payloads while `values["status"]` remained `running`.

- Observation: Re-exporting the new run-state service through `app.services.__init__` caused a circular import through `app.graph.builder`.
  Evidence: backend test collection failed until the `get_run_state` re-export was removed and direct imports were used.

- Observation: `/tickets` tests started failing because the new run-state panel duplicates classification labels already shown in the workflow result panel.
  Evidence: `getByText("account")` became ambiguous in `TicketsPage.test.tsx`; the test now asserts both copies intentionally.

## Decision Log

- Decision: Keep LangGraph checkpoint state as the source of truth and treat the timeline as a UI/debug projection only.
  Rationale: This preserves Day 3 workflow semantics and avoids creating a second business-state store.
  Date/Author: 2026-04-25 / Codex

- Decision: Add a distinct `RunStateResponse` for `GET /api/v1/runs/{thread_id}/state` instead of reusing `RunTicketResponse`.
  Rationale: The run and resume endpoints remain Day 3 action responses, while the new state endpoint is a read model optimized for inspection.
  Date/Author: 2026-04-25 / Codex + user

- Decision: Require timeline events for major workflow steps only, not every graph node.
  Rationale: Major-step events make the run understandable without over-instrumenting every node.
  Date/Author: 2026-04-25 / Codex + user

- Decision: Build refresh-safe inspection with `localStorage` of the last `thread_id` on the `/tickets` page.
  Rationale: The Day 4 goal includes refresh/reload state inspection, and local storage is the smallest viable way to preserve a thread reference across refreshes.
  Date/Author: 2026-04-25 / Codex

- Decision: Keep Day 4 transport as polling, not SSE or WebSockets.
  Rationale: Polling is enough for this local MVP and keeps the implementation simple.
  Date/Author: 2026-04-25 / Codex

- Decision: Prefer direct imports for the new state service instead of expanding package re-exports.
  Rationale: This matches the repo’s existing import style and avoided a circular import.
  Date/Author: 2026-04-25 / Codex

## Outcomes & Retrospective

The Day 4 result matches the intended outcome: `/tickets` now exposes both the business result and an inspection view of the current run. Low-risk runs show a completed timeline and final response. Risky runs show `waiting_review`, an interrupt event, and continue polling until a reviewer resumes the run elsewhere. Rejected runs end in `manual_takeover` instead of a final AI response.

The main compromise is timeline granularity. The implementation records major-step events from the API layer and selected workflow boundaries instead of instrumenting every graph node. That is enough for the Day 4 demo and aligns with the chosen scope.

## Context and Orientation

The repo already shipped Day 3 before this work. Existing routes included:

- `GET /api/v1/tickets`
- `POST /api/v1/tickets/{ticket_id}/run`
- `GET /api/v1/reviews/pending`
- `POST /api/v1/runs/{thread_id}/resume`

Relevant backend files after Day 4:

- `backend/app/api/v1/runs.py`: run, resume, state, and timeline endpoints
- `backend/app/schemas/graph.py`: Day 3 and Day 4 API models
- `backend/app/services/run_event_store.py`: in-memory timeline event storage
- `backend/app/services/run_state_service.py`: read-only mapping from LangGraph checkpoint state to API state
- `backend/app/graph/state.py`: checkpoint fields written by graph nodes

Relevant frontend files after Day 4:

- `frontend/src/pages/TicketsPage.tsx`: run trigger, polling, `localStorage` restore, and three-column layout
- `frontend/src/components/RunStatePanel.tsx`: current run-state view
- `frontend/src/components/WorkflowTimeline.tsx`: major-step timeline renderer
- `frontend/src/components/WorkflowResultPanel.tsx`: Day 3 result payload panel
- `frontend/src/lib/api.ts` and `frontend/src/lib/types.ts`: Day 4 read contracts

Terms used here:

- `ticket_id`: the support ticket identifier, e.g. `ticket-1001`
- `thread_id`: the unique per-run LangGraph execution identifier, e.g. `ticket-ticket-1001-1a2b3c4d`
- graph checkpoint state: the LangGraph in-memory state for one `thread_id`
- run state: the clean API projection returned by `GET /api/v1/runs/{thread_id}/state`
- timeline event: an in-memory UI/debug event returned by `GET /api/v1/runs/{thread_id}/timeline`

## Plan of Work

Backend work extended the existing Day 3 schema module instead of creating a separate schema file. `RunTimelineEvent`, `RunTimelineResponse`, and `RunStateResponse` were added beside the existing Day 3 models so the frontend can mirror a single backend source of truth.

`backend/app/services/run_event_store.py` was added as a small in-memory store keyed by `thread_id`. It appends events, lists ordered events, and clears all state for tests. It does not drive business decisions.

`backend/app/services/run_state_service.py` was added as a read-only adapter over `get_support_graph().get_state(...)`. It converts `StateSnapshot.values` and interrupt payloads into `RunStateResponse` and normalizes the waiting-review case to `status="waiting_review"` with `current_node="human_review_interrupt"`.

`backend/app/api/v1/runs.py` was updated to append timeline events around existing run/resume behavior. `run_started` is written before graph invocation. Major-step events are appended after the initial run based on the structured result. `review_submitted`, `run_resumed`, and terminal completion events are appended around the resume path. The router now also exposes `GET /api/v1/runs/{thread_id}/state` and `GET /api/v1/runs/{thread_id}/timeline`.

Frontend work kept `frontend/src/pages/TicketsPage.tsx` as the main page rather than splitting a new `TicketDetailPage.tsx`. The page now stores the latest `thread_id`, restores it from `localStorage`, fetches state and timeline, and polls while the run is `running` or `waiting_review`. Two new presentation components render the current state and ordered timeline in a third column next to the existing ticket detail and workflow result panels.

## Concrete Steps

Commands used during implementation:

    sed -n '1,260p' docs/exec-plans/active/2026-04-23-day4-run-state-timeline.md
    sed -n '73,170p' docs/PLANS.md
    sed -n '1,260p' backend/app/api/v1/runs.py
    sed -n '1,260p' backend/app/schemas/graph.py
    sed -n '1,260p' frontend/src/lib/types.ts

Checkpoint inspection command used to confirm LangGraph read behavior:

    cd backend
    uv run --cache-dir /tmp/uv-cache python - <<'PY'
    from app.graph.builder import get_support_graph
    graph = get_support_graph()
    print(graph.get_state({"configurable": {"thread_id": "does-not-exist"}}))
    PY

Verification commands:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

    cd frontend
    npm test -- --run
    npm run build

Expected transcripts after completion:

    backend: 18 passed
    frontend tests: 7 passed
    frontend build: vite build succeeds and writes dist assets

## Validation and Acceptance

Behavior now visible in the implemented app:

- `POST /api/v1/tickets/{ticket_id}/run` still returns the Day 3 run response shape.
- `GET /api/v1/runs/{thread_id}/state` returns the current clean run state and `404` for unknown thread IDs.
- `GET /api/v1/runs/{thread_id}/timeline` returns ordered timeline events and `404` for unknown thread IDs.
- `ticket-1003` produces a `done` state, completed major-step timeline, and final response.
- `ticket-1001` produces a `waiting_review` state, an `interrupt_created` timeline event, and a pending review item.
- approving or editing a risky run adds `review_submitted`, `run_resumed`, and `run_completed` events and yields `status="done"`.
- rejecting a risky run yields `status="manual_takeover"` and no final AI response.
- refreshing `/tickets` keeps the last `thread_id` inspection available through `localStorage` as long as the backend process is still alive.

## Idempotence and Recovery

Re-running the same ticket is safe because each run gets a unique `thread_id`. Timeline state is isolated per run and never merged across different attempts.

Polling is read-only. If polling fails, the current UI leaves the last known state visible and shows an error in the run-state panel. Refreshing the page retries state and timeline reads using the stored `thread_id`.

All Day 4 storage remains in memory. Restarting the backend clears checkpoints, pending reviews, and timelines. This is an intentional MVP limitation and is documented in README.

## Artifacts and Notes

Expected low-risk timeline shape:

    run_started
    classify_completed
    retrieve_completed
    draft_completed
    risk_gate_completed
    run_completed

Expected risky timeline shape before review:

    run_started
    classify_completed
    retrieve_completed
    draft_completed
    risk_gate_completed
    interrupt_created

Expected risky timeline tail after approval or edit:

    review_submitted
    run_resumed
    run_completed

Implemented route additions:

    GET /api/v1/runs/{thread_id}/state
    GET /api/v1/runs/{thread_id}/timeline

## Interfaces and Dependencies

`backend/app/schemas/graph.py` now defines:

- `RunTimelineEvent`
- `RunTimelineResponse`
- `RunStateResponse`

These reuse existing Day 3 schema types:

- `TicketClassification`
- `KBHit`
- `DraftReply`
- `RiskAssessment`
- `PendingReviewItem`
- `SubmitReviewDecisionRequest`
- `FinalResponse`

`backend/app/services/run_event_store.py` provides:

- `append(event: RunTimelineEvent) -> None`
- `create_event(...) -> RunTimelineEvent`
- `list_by_thread_id(thread_id: str) -> list[RunTimelineEvent]`
- `clear() -> None`

`backend/app/services/run_state_service.py` provides:

- `get_run_state(thread_id: str) -> RunStateResponse | None`

`backend/app/api/v1/runs.py` exposes:

- `POST /api/v1/tickets/{ticket_id}/run`
- `POST /api/v1/runs/{thread_id}/resume`
- `GET /api/v1/runs/{thread_id}/state`
- `GET /api/v1/runs/{thread_id}/timeline`

`frontend/src/lib/types.ts` mirrors the backend models with:

- `RunStateResponse`
- `RunTimelineEvent`
- `RunTimelineResponse`

`frontend/src/lib/api.ts` exposes:

- `fetchRunState(threadId: string)`
- `fetchRunTimeline(threadId: string)`

## Assumptions and Defaults

- Day 4 keeps the Day 3 graph routing and risk rules unchanged.
- Timeline granularity is major-step only.
- Polling is the only required refresh mechanism.
- Storage remains in memory only.
- `/tickets` is the main Day 4 inspection surface; `/reviews` remains the separate human review queue.

Revision note: 2026-04-25. Replaced the stale Day 4 draft with the implemented Day 4 behavior, added the required living-document sections, recorded real decisions and surprises, and aligned all examples and contracts with the actual repo state.
