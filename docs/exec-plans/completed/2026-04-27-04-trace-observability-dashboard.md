# Day 12 Trace and Observability Dashboard

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The app already records a run timeline, but agent behavior still requires reading code or logs to understand node-level decisions. After this change, a support agent or hiring reviewer can open a run trace and see each graph step, its status, duration, inputs or summaries, retrieval choices, policy decisions, review interrupt, resume event, and action outcomes.

This feature demonstrates production agent debugging: the workflow becomes inspectable rather than opaque.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [x] (2026-04-28) Updated plan after review to require graph-node instrumentation for real span timing, align smoke tests with approval-gated customer sends, and make Day 10 action plus Day 11 policy trace attributes mandatory.
- [x] (2026-04-28) Inspected the current event timeline service and frontend timeline component.
- [x] (2026-04-28) Added trace event schemas, SQLite trace persistence, and `GET /api/v1/runs/{thread_id}/trace`.
- [x] (2026-04-28) Emitted structured trace events from wrapped graph nodes so start time, end time, duration, and failed/interrupted node status are measured at node boundaries.
- [x] (2026-04-28) Added frontend trace view from ticket detail.
- [x] (2026-04-28) Added tests for approval-gated send interrupt, high-risk review, approve resume, and reject manual-takeover traces.
- [x] (2026-04-28) Updated docs and this ExecPlan with observed behavior.

## Surprises & Discoveries

- Observation: Route-level event emission is not sufficient for the trace schema this plan requires.
  Evidence: The existing route helper in `backend/app/api/v1/runs.py` appends major timeline events only after `graph.invoke(...)` returns. That cannot know each graph node's actual start time, end time, duration, or failing node if execution aborts mid-graph.

- Observation: Low-risk customer sends are approval-gated in the current product behavior.
  Evidence: `docs/product-specs/supportflow-mvp.md` says `ticket-1003` pauses in `waiting_review` with a failed `high_impact_action_requires_review` policy before any customer reply send can execute.

- Observation: Day 10 action tools and Day 11 policy checks are already implemented, so trace attributes for action and policy data are available and should not be treated as optional future work.
  Evidence: API responses now include `proposed_actions`, `executed_actions`, and `policy_assessment`.

- Observation: LangGraph interrupts are raised as `GraphInterrupt` during the first execution of `human_review_interrupt`, then the same node completes on resume.
  Evidence: A `ticket-1003` approval smoke trace records `human_review_interrupt:interrupted`, then after resume records `human_review_interrupt:completed`, `apply_review_decision:completed`, and `finalize_reply:completed`.

- Observation: The local trace should avoid serializing full interrupt payloads into error fields.
  Evidence: The trace wrapper records failure error type/message only for failed nodes; interrupted nodes are summarized as human-input pauses and expose policy/action attributes without storing the full customer reply draft in an error string.

## Decision Log

- Decision: Build local trace data first and keep LangSmith optional.
  Rationale: The repo currently runs locally without external credentials. Local structured traces prove the product behavior and can later map to LangSmith or OpenTelemetry.
  Date/Author: 2026-04-27 / Codex

- Decision: Extend the existing timeline concept rather than creating a separate unrelated log format.
  Rationale: Users already see workflow timeline behavior. A richer trace should deepen that surface without splitting observability into two competing models.
  Date/Author: 2026-04-27 / Codex

- Decision: Instrument graph nodes or LangGraph callbacks before claiming span timing.
  Rationale: Trace events with `started_at`, `ended_at`, and `duration_ms` must be measured at node execution boundaries. Creating them after `graph.invoke(...)` returns would fabricate timing and miss mid-graph failures.
  Date/Author: 2026-04-28 / Codex

- Decision: Treat policy and action attributes as required trace data.
  Rationale: The completed action layer and policy engine are central to the demo's production-agent value. The trace dashboard must show policy decisions and action outcomes because the data already exists and reviewers need it to understand why a run paused or completed.
  Date/Author: 2026-04-28 / Codex

- Decision: Smoke tests must model approval-gated sends.
  Rationale: A plain `POST /api/v1/tickets/ticket-1003/run` now stops at `waiting_review`. Finalization and action execution can only be verified after resuming the run with an approval decision.
  Date/Author: 2026-04-28 / Codex

- Decision: Add a separate `run_trace_events` table instead of overloading `run_events`.
  Rationale: Existing timeline events are coarse user-facing milestones. Trace events are measured node spans with duration and richer attributes. Keeping them separate preserves the current timeline behavior while allowing a denser dashboard.
  Date/Author: 2026-04-28 / Codex

- Decision: Wrap graph nodes at graph construction time.
  Rationale: Wrapping the node functions in `backend/app/graph/builder.py` keeps each node implementation focused on workflow logic while measuring real node boundaries for tracing.
  Date/Author: 2026-04-28 / Codex

## Outcomes & Retrospective

Completed on 2026-04-28. The backend now persists measured node-span trace events in SQLite, exposes them at `GET /api/v1/runs/{thread_id}/trace`, and keeps the existing timeline endpoint intact. Each trace event includes node name, span status, start time, end time, duration, summary, and JSON attributes for classification, retrieval, draft confidence, failed policy IDs and severities, proposed/executed action IDs and types, reviewer decision, and final disposition when available.

The frontend ticket detail page now fetches the trace with run state and timeline data, then renders a "Run trace" panel showing node spans, durations, summaries, policy IDs, proposed actions, executed actions, review decisions, and final disposition. Validation passed with backend tests `36 passed`, frontend tests `13 passed`, frontend build success, and offline eval `graph_v1` final pass rate `1.00` with `0` bad cases.

Future LangSmith or OpenTelemetry work can map these local trace rows into external spans. That is deferred because local observability is enough for the current demo and keeps the project runnable without external credentials.

## Context and Orientation

The current timeline store is `backend/app/services/run_event_store.py`. It creates `RunTimelineEvent` objects with event type, node name, status, message, created time, and optional payload. The timeline route is `GET /api/v1/runs/{thread_id}/timeline` in `backend/app/api/v1/runs.py`. The frontend timeline component is `frontend/src/components/WorkflowTimeline.tsx`.

The existing timeline route is not the same thing as node-level tracing. In the current backend, `_append_major_run_events` in `backend/app/api/v1/runs.py` runs after `graph.invoke(...)` returns. That is acceptable for a coarse user timeline, but it cannot measure the real duration of `classify_ticket`, `retrieve_knowledge`, `draft_reply`, `propose_actions`, `risk_gate`, `human_review_interrupt`, `apply_review_decision`, `finalize_reply`, or `manual_takeover`.

A trace is a more detailed record of a workflow run. In this plan, a trace event should answer: what graph node ran, when it started and ended, whether it succeeded, what decision it made, and what data a reviewer needs to understand that decision. A trace should not store full secrets or unnecessarily large ticket text.

The current workflow is approval-gated. `ticket-1003` is low content risk, but the workflow still pauses in `waiting_review` because the proposed `send_customer_reply` action fails `high_impact_action_requires_review`. A trace for that first POST must show an interrupt, proposed action data, and policy failure data. Finalization appears only after the reviewer resumes the run with `approve`.

## Plan of Work

First, inspect the existing timeline store and frontend component. Decide whether to add a new `RunTraceEvent` schema or extend `RunTimelineEvent`. Prefer a new trace schema if timeline stays user-facing and trace becomes more detailed.

Second, add backend schemas such as `RunTraceEvent` and `RunTraceResponse`. Include `trace_id`, `thread_id`, `ticket_id`, `node_name`, `span_type`, `status`, `started_at`, `ended_at`, `duration_ms`, `summary`, and `attributes`. Timing fields must be measured at node boundaries or explicitly absent for events that are not spans. Do not populate duration fields from route-level approximations.

Third, add a trace store. If Day 9 durable state is complete, persist trace events in SQLite. If not, use an in-memory store and record the temporary limitation. The trace store should list events by thread ID in chronological order.

Fourth, emit trace events from graph nodes or LangGraph callbacks. This is required, not optional, because the trace schema promises real span timing and node status. A reasonable minimal implementation is a small helper that wraps each node function at graph construction time: record `started_at`, call the node, record `ended_at`, compute `duration_ms`, derive a summary and attributes from the node result, and persist a trace event. If the wrapped node raises, record a failed trace event with the exception type and message before re-raising. Route orchestration may still append coarse timeline events, but it must not be the source of trace span timing.

Trace attributes must include policy and action data where the node has access to it. At minimum, traces must expose classification category and priority, retrieved document IDs, draft confidence and citations, proposed action IDs and action types, executed action IDs and action types, failed policy IDs, policy severities, review decision, and final disposition when those values exist.

Fifth, add `GET /api/v1/runs/{thread_id}/trace`. The endpoint should return 404 only when the run is unknown. Otherwise it should return a stable list of trace events.

Sixth, update frontend types and API helpers. Add a trace panel from ticket detail, either inline under the timeline or behind a tab/section. Keep it operational and scannable. Do not create a marketing-style page.

Seventh, add tests. Backend tests should assert trace event presence and important attributes for approval-gated send interruption, high-risk waiting-review interruption, approve resume, and reject manual takeover. Frontend tests should assert that trace rows render, including policy IDs and support action outcomes.

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

Expected result after the first POST: the run status is `waiting_review`. The trace includes `load_ticket_context`, `classify_ticket`, `retrieve_knowledge`, `draft_reply`, `propose_actions`, `risk_gate`, and `human_review_interrupt` spans. It does not include finalization yet. The `risk_gate` or adjacent policy trace attributes include `high_impact_action_requires_review`, and action attributes include a proposed `send_customer_reply`.

Then resume the same thread:

    POST /api/v1/runs/<thread_id>/resume
    body: {"decision":"approve","reviewer_note":"manual smoke approved"}
    GET /api/v1/runs/<thread_id>/trace

Expected result after approval: the trace includes `apply_review_decision` and `finalize_reply`, the final status is `done`, and action attributes show `send_customer_reply` as executed.

For `ticket-1001`, the trace should include billing and sensitive-request policy failures, proposed `send_customer_reply` and `create_refund_case` actions, a review interrupt, and later a resume decision after approval. A separate fresh run rejected by the reviewer should trace `manual_takeover` and rejected external actions.

Observed validation on 2026-04-28:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    # 36 passed in 14.71s

    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py
    # target=graph_v1 examples=20 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=1.00 final_pass_rate=1.00 bad_cases=0

    cd frontend
    npm test -- --run
    # 13 passed

    npm run build
    # built successfully

## Validation and Acceptance

This plan is complete because all of these are true:

- Backend exposes `GET /api/v1/runs/{thread_id}/trace`.
- Every completed or waiting-review run has trace events for major graph steps.
- Trace events include real node status, start time, end time, duration, and decision attributes measured from node instrumentation or LangGraph callbacks.
- Waiting-review traces include policy assessment attributes such as failed policy IDs and severities.
- Action traces include proposed, approved, executed, or rejected action IDs and action types when those actions exist.
- Frontend ticket detail can display the trace without reading server logs.
- Backend and frontend tests cover trace behavior.
- Existing timeline behavior still works.

## Idempotence and Recovery

Trace writes should be append-only or upserted by stable event IDs so retried route handling does not produce misleading duplicates. If duplicate traces are possible during retries, record the limitation and add a later cleanup task.

## Artifacts and Notes

This plan builds on the completed Day 10 action tools and Day 11 guardrails. Trace attributes for policy and action data are mandatory because the backend already exposes `policy_assessment`, `proposed_actions`, and `executed_actions`.

## Interfaces and Dependencies

At completion, frontend API helpers should include:

    fetchRunTrace(threadId: string): Promise<RunTraceResponse>

Backend should include a route shaped like:

    @router.get("/runs/{thread_id}/trace", response_model=RunTraceResponse)

Keep trace attributes JSON-serializable and avoid storing raw secrets.

Implemented backend interfaces:

    backend/app/schemas/graph.py::RunTraceEvent
    backend/app/schemas/graph.py::RunTraceResponse
    backend/app/services/run_trace_store.py::RunTraceStore
    backend/app/graph/tracing.py::traced_node
    backend/app/api/v1/runs.py::read_run_trace

Implemented frontend interfaces:

    frontend/src/lib/api.ts::fetchRunTrace
    frontend/src/components/WorkflowTrace.tsx::WorkflowTrace

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.

2026-04-28: Revised after review. The plan now forbids route-level fabricated span timing, requires node or callback instrumentation, aligns `ticket-1003` smoke behavior with approval-gated sends, and requires policy/action trace attributes because the action layer and policy engine are complete.

2026-04-28: Implemented the trace dashboard end to end. The implementation uses a new durable trace store and node wrapper instrumentation rather than route-level timing.
