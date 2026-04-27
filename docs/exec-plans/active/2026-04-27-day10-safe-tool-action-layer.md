# Day 10 Safe Tool Action Layer

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The current workflow drafts and finalizes replies, but it does not model external side effects such as sending a reply, creating a refund case, applying a credit, escalating to another team, or adding an internal note. After this change, the workflow will propose and execute simulated support actions through a safe action layer. High-impact actions will require human approval, and every action will be auditable and idempotent.

This feature demonstrates production agent engineering because tool use is where agent systems become risky. The project should show tool execution as a controlled boundary, not as arbitrary code called by a model.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [ ] Confirm Day 9 durable workflow state is complete or explicitly decide how action state will persist.
- [ ] Add action schemas and an action ledger service.
- [ ] Add graph node or finalization integration that proposes actions from classification, draft, and risk state.
- [ ] Gate high-impact actions behind human review.
- [ ] Expose actions in backend responses and frontend ticket/review views.
- [ ] Add backend and frontend tests.
- [ ] Update docs and this ExecPlan with observed behavior.

## Surprises & Discoveries

- Observation: No implementation discoveries yet.
  Evidence: This plan has only been created.

## Decision Log

- Decision: Simulate support tools locally instead of integrating real email or ticketing systems.
  Rationale: The product roadmap and MVP explicitly keep real email and real ticketing out of scope. A local tool layer still demonstrates API boundaries, approval gates, idempotency, and auditability.
  Date/Author: 2026-04-27 / Codex

- Decision: Require human approval before executing high-impact actions.
  Rationale: Refunds, credits, and external sends are side effects. A portfolio project should show that agent autonomy is bounded by explicit policy and review.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize the action types, ledger persistence behavior, approval gates, frontend displays, and any remaining tool-use gaps.

## Context and Orientation

The backend workflow is a LangGraph graph in `backend/app/graph/builder.py`. Its state type is `backend/app/graph/state.py::TicketState`. Current nodes load a ticket, classify it, retrieve KB, draft a reply, evaluate risk, interrupt for review when needed, apply a review decision, and finalize or hand off manually.

Schemas for workflow responses live in `backend/app/schemas/graph.py`. Frontend TypeScript mirrors live in `frontend/src/lib/types.ts`. API helper functions live in `frontend/src/lib/api.ts`. Ticket UI components live in `frontend/src/components/` and pages live in `frontend/src/pages/`.

An action is a proposed or executed side effect. In this plan, actions are simulated records, not real external calls. The initial action types are:

- `send_customer_reply`, which represents sending the final support response.
- `create_refund_case`, which represents opening a refund review case.
- `apply_credit`, which represents adding account credit.
- `escalate_to_tier_2`, which represents escalation to a higher support tier.
- `add_internal_note`, which represents writing a support note.

An action ledger is an append-only or updateable store that records every proposed, approved, executed, rejected, or failed action. Idempotency means each action has a stable key so a resumed workflow cannot execute the same side effect twice.

## Plan of Work

First, confirm the Day 9 durable store exists. If Day 9 is not complete, keep the action ledger interface isolated so it can start in memory for tests but is easy to back with SQLite later. If Day 9 is complete, use the durable store directly.

Second, add Pydantic schemas in `backend/app/schemas/graph.py` or a new `backend/app/schemas/actions.py`. Define `SupportAction`, `SupportActionType`, `SupportActionStatus`, and an execution result model. Include `action_id`, `thread_id`, `ticket_id`, `action_type`, `status`, `idempotency_key`, `requires_review`, `reason`, `payload`, and timestamps.

Third, add `backend/app/services/action_ledger.py`. It should support creating proposed actions, listing by thread ID, approving or rejecting actions, marking an action executed, and refusing duplicate execution by idempotency key. Preserve deterministic behavior for tests.

Fourth, add action proposal logic. Keep it simple and inspectable: billing refund language proposes `create_refund_case`; billing credit language proposes `apply_credit`; urgent bug or security language proposes `escalate_to_tier_2`; every finalizable reply proposes `send_customer_reply`; reviewer comments can create `add_internal_note` if useful. Do not call an LLM to invent tools in this plan.

Fifth, integrate actions into the graph. Prefer adding one node before finalization, such as `propose_actions`, or enriching `risk_gate` and `finalize_reply` if that is less invasive. The graph state should include `proposed_actions` and `executed_actions`. High-impact actions should make `review_required` true, with risk flags that explain why.

Sixth, update backend responses so ticket run, run state, pending review, and final responses include relevant actions. The frontend should show proposed actions on the ticket detail and review queue. Use compact operational UI: badges for action status, labels for type, and short reason text.

Seventh, add tests. Backend tests should cover low-risk send action, refund or credit action requiring review, reject not executing an action, approve executing once, and duplicate resume not creating duplicate executed actions. Frontend tests should cover action display in ticket and review views.

## Concrete Steps

Work from the repository root unless noted.

Inspect the graph and response schemas:

    sed -n '1,260p' backend/app/graph/state.py
    sed -n '1,300p' backend/app/graph/builder.py
    sed -n '1,340p' backend/app/schemas/graph.py
    sed -n '1,320p' backend/app/api/v1/runs.py
    sed -n '1,260p' frontend/src/lib/types.ts

Run current tests before edits:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

    cd frontend
    npm test -- --run

After implementation, run:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

    cd frontend
    npm test -- --run
    npm run build

Manual smoke target:

    POST /api/v1/tickets/ticket-1003/run

Expected result: a low-risk run includes a proposed or executed `send_customer_reply` action and finishes without review if policy allows.

    POST /api/v1/tickets/ticket-1001/run

Expected result: a risky billing case includes a high-impact proposed action and pauses in `waiting_review`. Approving executes the approved action exactly once. Rejecting marks proposed actions rejected or leaves them unexecuted and ends in `manual_takeover`.

## Validation and Acceptance

This plan is complete when all of these are true:

- Action schemas are present in backend and mirrored in frontend types.
- A ledger records action lifecycle status.
- High-impact actions require human review before execution.
- Resuming the same reviewed run cannot duplicate an executed action.
- Ticket detail and review queue show proposed and executed actions.
- Backend tests, frontend tests, frontend build, and offline eval pass.

## Idempotence and Recovery

Every executable action must have an idempotency key derived from stable data such as thread ID, action type, and action payload. If the workflow is resumed twice or retried after an error, the action ledger must return the existing executed record rather than inserting a duplicate. Tests must prove this behavior.

## Artifacts and Notes

This plan depends on the durable storage direction from `docs/exec-plans/completed/2026-04-27-day09-durable-workflow-state.md`. Day 9 is complete, so new action state should use the durable SQLite storage layer unless implementation discovers a concrete reason not to.

## Interfaces and Dependencies

At completion, code should expose an interface similar to:

    class ActionLedger:
        def propose(self, action: SupportActionCreate) -> SupportAction: ...
        def list_by_thread_id(self, thread_id: str) -> list[SupportAction]: ...
        def approve_for_thread(self, thread_id: str) -> list[SupportAction]: ...
        def reject_for_thread(self, thread_id: str, reason: str | None = None) -> list[SupportAction]: ...
        def execute_once(self, action_id: str) -> SupportAction: ...

Prefer Python standard-library code and existing Pydantic schemas. Do not add external integrations.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.
