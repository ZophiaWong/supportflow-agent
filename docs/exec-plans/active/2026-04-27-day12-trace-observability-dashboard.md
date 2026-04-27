# Day 12 Trace and Observability Dashboard

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The app already records a run timeline, but agent behavior still requires reading code or logs to understand node-level decisions. After this change, a support agent or hiring reviewer can open a run trace and see each graph step, its status, duration, inputs or summaries, retrieval choices, policy decisions, review interrupt, resume event, and action outcomes.

This feature demonstrates production agent debugging: the workflow becomes inspectable rather than opaque.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [ ] Inspect the current event timeline service and frontend timeline component.
- [ ] Add trace event schemas and backend trace endpoint.
- [ ] Emit structured trace events from graph nodes or route orchestration.
- [ ] Add frontend trace view from ticket detail.
- [ ] Add tests for low-risk, review, approve, and reject traces.
- [ ] Update docs and this ExecPlan with observed behavior.

## Surprises & Discoveries

- Observation: No implementation discoveries yet.
  Evidence: This plan has only been created.

## Decision Log

- Decision: Build local trace data first and keep LangSmith optional.
  Rationale: The repo currently runs locally without external credentials. Local structured traces prove the product behavior and can later map to LangSmith or OpenTelemetry.
  Date/Author: 2026-04-27 / Codex

- Decision: Extend the existing timeline concept rather than creating a separate unrelated log format.
  Rationale: Users already see workflow timeline behavior. A richer trace should deepen that surface without splitting observability into two competing models.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize trace schema, endpoint behavior, frontend trace UI, and any future LangSmith/OpenTelemetry mapping.

## Context and Orientation

The current timeline store is `backend/app/services/run_event_store.py`. It creates `RunTimelineEvent` objects with event type, node name, status, message, created time, and optional payload. The timeline route is `GET /api/v1/runs/{thread_id}/timeline` in `backend/app/api/v1/runs.py`. The frontend timeline component is `frontend/src/components/WorkflowTimeline.tsx`.

A trace is a more detailed record of a workflow run. In this plan, a trace event should answer: what graph node ran, when it started and ended, whether it succeeded, what decision it made, and what data a reviewer needs to understand that decision. A trace should not store full secrets or unnecessarily large ticket text.

## Plan of Work

First, inspect the existing timeline store and frontend component. Decide whether to add a new `RunTraceEvent` schema or extend `RunTimelineEvent`. Prefer a new trace schema if timeline stays user-facing and trace becomes more detailed.

Second, add backend schemas such as `RunTraceEvent` and `RunTraceResponse`. Include `trace_id`, `thread_id`, `ticket_id`, `node_name`, `span_type`, `status`, `started_at`, `ended_at`, `duration_ms`, `summary`, and `attributes`.

Third, add a trace store. If Day 9 durable state is complete, persist trace events in SQLite. If not, use an in-memory store and record the temporary limitation. The trace store should list events by thread ID in chronological order.

Fourth, emit trace events. The safest first pass is to emit events in route orchestration where the current code already appends major run events. A richer implementation can instrument each graph node directly. Trace attributes should include classification category, retrieved document IDs, draft confidence, risk flags or policy IDs, review decision, and action IDs when available.

Fifth, add `GET /api/v1/runs/{thread_id}/trace`. The endpoint should return 404 only when the run is unknown. Otherwise it should return a stable list of trace events.

Sixth, update frontend types and API helpers. Add a trace panel from ticket detail, either inline under the timeline or behind a tab/section. Keep it operational and scannable. Do not create a marketing-style page.

Seventh, add tests. Backend tests should assert trace event presence and important attributes for low-risk completion, waiting-review interrupt, approve resume, and reject manual takeover. Frontend tests should assert that trace rows render.

## Concrete Steps

Inspect current timeline files:

    sed -n '1,280p' backend/app/services/run_event_store.py
    sed -n '1,340p' backend/app/api/v1/runs.py
    sed -n '1,340p' backend/app/schemas/graph.py
    sed -n '1,260p' frontend/src/components/WorkflowTimeline.tsx
    sed -n '1,260p' frontend/src/components/TicketDetail.tsx

Run current tests:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

    cd frontend
    npm test -- --run

After implementation, run:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

    cd frontend
    npm test -- --run
    npm run build

Manual smoke target:

    POST /api/v1/tickets/ticket-1003/run
    GET /api/v1/runs/<thread_id>/trace

Expected result: the trace includes classify, retrieve, draft, risk, and finalization events with useful attributes. For `ticket-1001`, it should include a review interrupt and later a resume decision after approval.

## Validation and Acceptance

This plan is complete when all of these are true:

- Backend exposes `GET /api/v1/runs/{thread_id}/trace`.
- Every completed or waiting-review run has trace events for major graph steps.
- Trace events include node status, duration or timestamps, and decision attributes.
- Frontend ticket detail can display the trace without reading server logs.
- Backend and frontend tests cover trace behavior.
- Existing timeline behavior still works.

## Idempotence and Recovery

Trace writes should be append-only or upserted by stable event IDs so retried route handling does not produce misleading duplicates. If duplicate traces are possible during retries, record the limitation and add a later cleanup task.

## Artifacts and Notes

This plan complements Day 11 guardrails and Day 10 action tools. If those plans are not complete, trace attributes for policy and action data can be omitted or left empty, but the schema should allow them later.

## Interfaces and Dependencies

At completion, frontend API helpers should include:

    fetchRunTrace(threadId: string): Promise<RunTraceResponse>

Backend should include a route shaped like:

    @router.get("/runs/{thread_id}/trace", response_model=RunTraceResponse)

Keep trace attributes JSON-serializable and avoid storing raw secrets.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.
