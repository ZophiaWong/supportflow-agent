# LangGraph Checkpoint Retry and Replay Demo

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

SupportFlow already persists LangGraph checkpoints and can resume after a human review interrupt. That is useful, but a stronger Agentic AI portfolio should demonstrate recoverable failure and checkpoint inspection, not only approval flow. After this change, a hiring reviewer should be able to trigger a controlled workflow failure, inspect the persisted state and trace, retry or replay from a checkpoint, and see the workflow recover or branch in an explainable way.

The user-visible result should be a CLI or UI scenario that proves LangGraph is used for durable workflow engineering: failure is recorded, state survives, retry behavior is controlled, and trace or timeline data explains the recovery.

## Progress

- [x] (2026-05-31 HKT) Created this todo ExecPlan from the 2026-05-31 portfolio gap audit.
- [ ] Inspect current checkpoint storage, run state projection, trace events, timeline events, and resume behavior.
- [ ] Design controlled failure injection for retrieval, LLM, and tool/action stages.
- [ ] Add API or CLI support for reading checkpoint history for one thread.
- [ ] Add retry or replay behavior from a selected checkpoint.
- [ ] Expose the scenario through a CLI command or frontend diagnostics surface.
- [ ] Add tests that prove failure recording, retry, replay, and trace/timeline explanation.
- [ ] Update README and this plan with manual demo evidence.

## Surprises & Discoveries

- Observation: The graph already uses a local SQLite checkpointer.
  Evidence: `backend/app/graph/builder.py` compiles the graph with `SqliteSaver()`, and `backend/app/services/sqlite_store.py` defines `langgraph_checkpoints`, `langgraph_writes`, and `langgraph_blobs`.

- Observation: Existing durable-state validation covers resume after fresh graph construction, not replay or node failure recovery.
  Evidence: `backend/tests/integration/test_durable_workflow_state.py` clears the graph cache and resumes a pending review, but does not inject a failing node or replay an earlier checkpoint.

- Observation: Current run failure handling is coarse.
  Evidence: `backend/app/api/v1/runs.py` catches exceptions and appends a `run_failed` timeline event, but there is no user-facing retry or checkpoint selection behavior.

## Decision Log

- Decision: Use controlled local failure injection instead of relying on random exceptions.
  Rationale: A portfolio demo and tests must be deterministic. Failures should be triggered by scenario data, explicit request flags, or a documented environment variable rather than timing or network instability.
  Date/Author: 2026-05-31 / Codex

- Decision: Provide a CLI path first unless frontend implementation is small.
  Rationale: The core hiring signal is durable recovery and replay. A CLI can prove the backend behavior before investing in UI polish.
  Date/Author: 2026-05-31 / Codex

- Decision: Keep replay safe and side-effect-aware.
  Rationale: Replaying from checkpoints can accidentally duplicate side effects. The existing action ledger idempotency must remain the boundary for tool execution.
  Date/Author: 2026-05-31 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize which nodes support controlled failure, how checkpoint listing works, how retry or replay behaves, and which demo command proves the feature.

## Context and Orientation

The workflow is a LangGraph `StateGraph` built in `backend/app/graph/builder.py`. It loads a ticket, classifies it, retrieves knowledge, drafts a reply, proposes support actions, evaluates risk, optionally interrupts for human review, applies reviewer decisions, and then finalizes or moves to manual takeover.

The state shape is `TicketState` in `backend/app/graph/state.py`. Run state is projected by `backend/app/services/run_state_service.py`. Timeline events are stored through `backend/app/services/run_event_store.py`. Trace spans are recorded by `backend/app/graph/tracing.py` and stored through `backend/app/services/run_trace_store.py`. Checkpoints are persisted by `backend/app/services/sqlite_checkpointer.py` into SQLite tables created by `backend/app/services/sqlite_store.py`.

In this plan, "checkpoint" means a persisted snapshot of LangGraph state. "Replay" means running again from an earlier checkpoint or using that checkpoint to inspect and reproduce workflow behavior. "Retry" means attempting a failed step or run again after the failure condition has been cleared. "Fork" means creating a new run or branch from an earlier checkpoint without overwriting the original run history.

## Plan of Work

First, inspect how the current `SqliteSaver` stores and lists checkpoints. Confirm whether `graph.get_state`, `graph.get_state_history`, or the custom saver `list` method can provide enough checkpoint history for a thread. Record the exact API chosen in the Decision Log before implementation.

Second, add deterministic failure injection. The implementation should support failures in at least one retrieval path and one action/tool path. If LLM integration is active, add an LLM timeout or schema-failure scenario through the existing optional LLM wrapper. Failure injection must not require real external network failures.

Third, enrich failure recording. When a controlled failure happens, the run state, timeline, and trace should identify the failed node, error type, whether retry is possible, and any checkpoint ID that can be used for recovery. Avoid exposing raw Python stack traces as the primary user-facing message.

Fourth, implement checkpoint inspection. Add either a backend endpoint such as `GET /api/v1/runs/{thread_id}/checkpoints` or a backend CLI command under `backend/scripts/`. The output should show checkpoint ID, node or step context when available, status, created time or checkpoint time, and a short summary. If both endpoint and CLI are feasible, implement the endpoint first and add a simple script that calls service code directly.

Fifth, implement retry or replay. The minimum acceptable behavior is a CLI command that takes a `thread_id` and a checkpoint ID, replays from that checkpoint into a new thread ID, and records the relationship between original and replayed runs. A stronger implementation can add a retry endpoint that clears a controlled failure flag and resumes from the last safe checkpoint.

Sixth, make side effects safe. Replayed runs must not duplicate already executed actions. If a replay reaches action execution, it should either use a new thread-specific idempotency key or clearly mark that the replay is dry-run/diagnostic. Record the chosen policy in the Decision Log.

Seventh, add tests and docs. Tests should cover controlled failure, checkpoint listing, retry or replay success, trace/timeline attributes, and idempotent action behavior. README should include a short manual scenario showing how to trigger failure, inspect checkpoints, and recover.

## Concrete Steps

Inspect current checkpoint and run-state behavior:

    sed -n '1,220p' backend/app/graph/builder.py
    sed -n '1,420p' backend/app/services/sqlite_checkpointer.py
    sed -n '1,220p' backend/app/services/run_state_service.py
    sed -n '1,340p' backend/app/api/v1/runs.py
    sed -n '1,260p' backend/app/graph/tracing.py
    sed -n '1,180p' backend/tests/integration/test_durable_workflow_state.py

Run current backend tests before implementation:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

After implementation, run:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

If frontend diagnostics are changed, also run:

    cd frontend
    npm test -- --run
    npm run build

A final manual demo should look like this in spirit, though exact command names can change during implementation:

    cd backend
    uv run --cache-dir /tmp/uv-cache python scripts/demo_checkpoint_replay.py --ticket-id ticket-1003 --fail-node retrieve_knowledge
    uv run --cache-dir /tmp/uv-cache python scripts/list_run_checkpoints.py --thread-id <thread_id>
    uv run --cache-dir /tmp/uv-cache python scripts/replay_run_from_checkpoint.py --thread-id <thread_id> --checkpoint-id <checkpoint_id>

The transcript should show a failed run, at least one checkpoint, a replayed or retried run, and trace or timeline evidence for both.

## Validation and Acceptance

This plan is complete when all of these are true:

- A controlled failure can be triggered deterministically in at least retrieval and one LLM or tool/action-related stage.
- Failed runs persist state, timeline events, and trace spans that identify the failed node and error type.
- A user can list checkpoint history for a thread through a documented CLI command or API endpoint.
- A user can retry or replay from a selected checkpoint without corrupting the original run.
- Replaying does not duplicate already executed support actions.
- Tests cover failure recording, checkpoint listing, retry or replay behavior, and action idempotency.
- README or a design doc documents the demo scenario and any limitations.
- Backend tests and offline eval pass after implementation.

## Idempotence and Recovery

Failure injection must be opt-in and deterministic. It must not affect normal runs unless explicitly requested. If environment variables are used for failure injection, tests must clear them after use.

Replay should create new run identity or clearly operate in dry-run mode. Never overwrite the original thread history. Any replay parent-child relationship should be recorded in trace, timeline, or response metadata.

If a replay command fails halfway, the original run must remain readable. New partial replay runs may be left in SQLite as failed diagnostic runs, but they must be clearly labeled.

## Artifacts and Notes

The motivating gap audit is `docs/product-specs/ai-engineer-portfolio-gap-audit-2026-05-31.md`.

The existing durable behavior proves this narrower case:

    Run ticket until waiting_review.
    Clear the graph construction cache.
    Read pending review and state from SQLite.
    Resume approval to done.

This plan must go beyond that by proving failure recovery and checkpoint replay.

## Interfaces and Dependencies

Prefer existing LangGraph checkpoint APIs where possible. If adding backend models, place them in `backend/app/schemas/graph.py` or a new focused schema module if the response grows. Candidate shapes:

    RunCheckpointSummary
    thread_id: str
    checkpoint_id: str
    parent_checkpoint_id: str | None
    current_node: str | None
    status: str | None
    summary: str

    ReplayRunRequest
    checkpoint_id: str
    dry_run: bool = True

If adding routes, place them in `backend/app/api/v1/runs.py` unless the module becomes too large, in which case create `backend/app/api/v1/checkpoints.py` and wire it from `backend/app/main.py`.

Do not add external infrastructure for this plan. The feature should work with local SQLite and the existing backend test stack.

## Plan Revision Notes

2026-05-31: Initial todo ExecPlan created from the portfolio gap audit. The plan focuses on deterministic failure injection, checkpoint inspection, and safe replay before UI polish.
