# Add Day 3 Risk Gate and Human Review

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

`docs/PLANS.md` is checked into this repository. This document must be maintained in accordance with `docs/PLANS.md`, especially the `Skeleton of a Good ExecPlan` section and the requirement that the plan stay self-contained for a novice reader.

## Purpose / Big Picture

After this change, the support workflow no longer treats every drafted reply as safe to finish automatically. A low-risk ticket should still run from ticket selection to a final response in one pass, but a risky ticket should stop in a human review state, expose the draft and evidence to a reviewer, and resume only after the reviewer approves, edits, or rejects the reply. A reviewer should be able to see this working by running a risky ticket through the backend, observing a `waiting_review` response, opening the frontend review queue, submitting a review decision, and then seeing the run finish as either a finalized response or manual takeover.

## Progress

- [x] (2026-04-25 07:10Z) Rewrote this file to match the `docs/PLANS.md` ExecPlan skeleton and to make the plan self-contained.
- [ ] Define Day 3 backend schemas for risk assessment, pending review, reviewer decision, and final response.
- [ ] Extend `backend/app/graph/state.py` so the graph can represent `waiting_review`, reviewer input, and final outcome fields.
- [ ] Add LangGraph nodes for `risk_gate`, `human_review_interrupt`, `apply_review_decision`, `finalize_reply`, and `manual_takeover`.
- [ ] Update `backend/app/graph/builder.py` to route low-risk runs directly to finalize and high-risk runs through interrupt and resume.
- [ ] Add an in-memory pending-review store and HTTP endpoints to list pending reviews and resume a run by `thread_id`.
- [ ] Update backend API tests and integration tests to cover low-risk auto-finalize and high-risk interrupt/resume behavior.
- [ ] Extend frontend shared types and API helpers for pending review and resume actions.
- [ ] Add a frontend review queue screen and controls for approve, edit, and reject.
- [ ] Update the active plan after implementation with discoveries, decision changes, completed commands, and retrospective notes.

## Surprises & Discoveries

- Observation: The repository currently implements only the Day 2 happy path. The graph ends after `draft_reply`, and the run API always returns the draft directly.
  Evidence: `backend/app/graph/builder.py` currently wires `draft_reply -> END`, and `backend/app/api/v1/runs.py` returns `status`, `classification`, `retrieved_chunks`, and `draft` without any review-specific fields.

- Observation: The review behavior already has a design source of truth in the repository, but the active ExecPlan did not restate that context.
  Evidence: `docs/design-docs/review-and-risk-gate.md` defines deterministic trigger rules, the interrupt payload shape, and the resume semantics for approve, edit, and reject.

## Decision Log

- Decision: Keep the Day 3 risk gate deterministic and rule-based instead of asking an LLM to decide whether review is required.
  Rationale: The repository already uses deterministic workflow steps for MVP behavior, and `docs/design-docs/review-and-risk-gate.md` treats human review as a safety boundary whose triggers must be inspectable.
  Date/Author: 2026-04-22 / project-maintainer

- Decision: Use a single review interrupt with three reviewer outcomes: `approve`, `edit`, and `reject`.
  Rationale: This is the smallest workflow that demonstrates human-in-the-loop control without introducing multi-step approval or branching reviewer roles.
  Date/Author: 2026-04-22 / project-maintainer

- Decision: Store pending reviews in memory for this MVP milestone.
  Rationale: The repository does not yet include a database, and the Day 3 goal is observable interrupt/resume behavior rather than durable review persistence.
  Date/Author: 2026-04-22 / project-maintainer

- Decision: Do not perform external side effects before review is complete.
  Rationale: The MVP explicitly excludes real email or ticket write-back, and stopping before side effects keeps approve, edit, and reject safe to test repeatedly.
  Date/Author: 2026-04-22 / project-maintainer

- Decision: Rewrite the ExecPlan before implementation rather than layering incremental notes on top of the original short outline.
  Rationale: `docs/PLANS.md` requires a self-contained novice-friendly document with explicit context, concrete steps, validation, and living sections; the original file did not meet that bar.
  Date/Author: 2026-04-25 / Codex

## Outcomes & Retrospective

This plan revision has not implemented the feature yet. The concrete outcome so far is a corrected execution plan that names the actual repository files, defines the intended user-visible behavior, and gives the next contributor a precise sequence for implementing and validating the Day 3 review gate. The main gap remains the code itself. Once implementation starts, this section must be updated with the observed behavior of both the low-risk and high-risk paths, along with any compromises made to keep the MVP minimal.

## Context and Orientation

`supportflow-agent` is a workflow-first support app with a FastAPI backend in `backend/` and a React frontend in `frontend/`. The backend exposes `POST /api/v1/tickets/{ticket_id}/run` through `backend/app/api/v1/runs.py`. That endpoint compiles a LangGraph state machine from `backend/app/graph/builder.py` and runs the current Day 2 path: `load_ticket_context`, `classify_ticket`, `retrieve_knowledge`, and `draft_reply`. The shared graph state lives in `backend/app/graph/state.py`, and the structured response models live in `backend/app/schemas/graph.py`. LangGraph is the workflow library in use here; in this repository it means a state machine where each node reads and writes fields on `TicketState`, and the compiled graph can be paused and resumed using a checkpoint saver.

The frontend currently shows tickets and workflow output on the `/tickets` screen. The main page is `frontend/src/pages/TicketsPage.tsx`. API calls live in `frontend/src/lib/api.ts`, shared TypeScript models live in `frontend/src/lib/types.ts`, and the current workflow output UI lives in `frontend/src/components/WorkflowResultPanel.tsx`. There is not yet a dedicated review queue page or a way to submit a human decision from the browser.

The MVP intent for Day 3 is described by three repository documents that matter for this plan. `ARCHITECTURE.md` says the backend owns the review resume endpoint and the graph owns `risk gate`, `interrupt/resume`, and `finalize`. `docs/product-specs/supportflow-mvp.md` says risky cases must be reviewed by a human. `docs/design-docs/review-and-risk-gate.md` defines the risk trigger rules, the allowed reviewer decisions, the `POST /api/v1/runs/{thread_id}/resume` endpoint, and the meaning of `manual_takeover`.

Within this plan, “risk gate” means a deterministic backend node that inspects classification, evidence, and draft confidence to decide whether human review is required. “Interrupt” means the graph pauses and returns control to the API while preserving enough state to resume later. “Resume” means a second API call provides a reviewer decision so the graph can continue from the paused review point. “Pending review store” means an in-memory Python service that remembers review payloads for the life of the backend process only.

## Plan of Work

Start in the backend schema layer. Extend `backend/app/schemas/graph.py` with explicit Pydantic models for the new data that Day 3 needs. The minimum concrete models are `RiskAssessment`, `PendingReviewItem`, `SubmitReviewDecisionRequest`, `FinalResponse`, and an updated `RunTicketResponse` that can represent `waiting_review`, `done`, `failed`, and `manual_takeover`. Reuse existing `TicketClassification`, `KBHit`, and `DraftReply` instead of inventing duplicate structures. The response model should be able to carry either a final response or a pending review payload, because the run endpoint will now have two successful visible outcomes.

Then update `backend/app/graph/state.py` so `TicketState` can hold the new fields that nodes need to pass around. Add fields for `risk_assessment`, `review_required`, `pending_review`, `review_decision`, `final_response`, and a broader `status` union that includes `waiting_review` and `manual_takeover`. Expand `current_node` so it can name the new graph nodes. Keep the state minimal; the goal is to make node inputs and outputs explicit, not to mirror every HTTP response field redundantly.

Add new node modules under `backend/app/graph/nodes/`. `risk_gate.py` should compute rule-based flags using the design doc’s triggers: severity, missing evidence, confidence threshold, billing sensitivity, and obvious risky ticket wording. `human_review_interrupt.py` should create the interrupt payload that a reviewer needs, write it into the in-memory pending-review store, and return state with `status="waiting_review"`. `apply_review_decision.py` should consume a reviewer decision after resume and normalize it into state updates. `finalize_reply.py` should produce a `FinalResponse` when the ticket is auto-finalized or approved/edited by a reviewer. `manual_takeover.py` should mark the run as `manual_takeover` when the reviewer rejects the AI draft. Keep these nodes deterministic and synchronous.

Update `backend/app/graph/builder.py` so the graph compiles with conditional routing. The intended happy path becomes `load_ticket_context -> classify_ticket -> retrieve_knowledge -> draft_reply -> risk_gate`, then either `finalize_reply -> END` for low risk or `human_review_interrupt -> END` for high risk. The resume path should continue with `apply_review_decision`, then branch to `finalize_reply` for `approve` and `edit`, or `manual_takeover` for `reject`. Preserve the existing `InMemorySaver`, because that is what lets the graph resume by `thread_id` without adding a database.

Add the backend services and API wiring next. Create a small service module such as `backend/app/services/pending_review_store.py` to keep an in-memory dictionary of pending review items keyed by `thread_id`. Update `backend/app/api/v1/runs.py` so `POST /api/v1/tickets/{ticket_id}/run` can return either a final response or a waiting-review response, and add `POST /api/v1/runs/{thread_id}/resume` that validates `SubmitReviewDecisionRequest`, resumes the graph using the stored checkpoint, removes the pending review item after a successful resume, and returns the new final state. Add a `GET /api/v1/reviews/pending` endpoint, either in `runs.py` or a new `reviews.py`, so the frontend can render the review queue. Register any new router in `backend/app/main.py`.

Finish by extending the frontend. Update `frontend/src/lib/types.ts` with TypeScript equivalents of the new backend models and broaden the workflow status unions. Update `frontend/src/lib/api.ts` with helpers to fetch pending reviews and submit a resume decision. Add a review queue screen, preferably in a new page such as `frontend/src/pages/ReviewQueuePage.tsx`, and decide whether to route to it directly or render it from the existing tickets page. The screen must show ticket identity, draft answer, evidence snippets, risk flags, and controls for approve, edit, and reject. Update `frontend/src/components/WorkflowResultPanel.tsx` so the result panel shows a clear “waiting for human review” state when `status === "waiting_review"` and a final answer when the workflow finishes.

## Concrete Steps

Run the backend tests before changing anything so you have a clean baseline.

    cd /home/poter/resume-pj/supportflow-agent/backend
    uv run --cache-dir /tmp/uv-cache pytest

Expected baseline: the current API and smoke tests pass, and there are no tests yet for risk gate or resume behavior.

Implement the backend schema, graph, service, and API changes described above. After those edits, run the focused backend tests while iterating.

    cd /home/poter/resume-pj/supportflow-agent/backend
    uv run --cache-dir /tmp/uv-cache pytest tests/test_api.py tests/integration/test_graph_smoke.py

Expected result after Day 3 backend work: the low-risk test still reaches `done`, and at least one new high-risk test shows `waiting_review` before resume and `done` or `manual_takeover` after resume.

Run the full backend suite after the focused tests pass.

    cd /home/poter/resume-pj/supportflow-agent/backend
    uv run --cache-dir /tmp/uv-cache pytest

Start the backend locally and exercise the HTTP flow manually.

    cd /home/poter/resume-pj/supportflow-agent/backend
    uv run uvicorn app.main:app --reload

In a second shell, run a low-risk ticket and a high-risk ticket.

    curl -s -X POST http://127.0.0.1:8000/api/v1/tickets/ticket-1002/run
    curl -s -X POST http://127.0.0.1:8000/api/v1/tickets/ticket-1001/run
    curl -s http://127.0.0.1:8000/api/v1/reviews/pending
    curl -s -X POST http://127.0.0.1:8000/api/v1/runs/ticket-ticket-1001/resume \
      -H 'content-type: application/json' \
      -d '{"decision":"approve","reviewer_note":"evidence is sufficient"}'

Expected manual transcript shape:

    First run returns JSON with "status": "done" and a populated "final_response".
    Second run returns JSON with "status": "waiting_review" and a populated "pending_review".
    The pending reviews endpoint includes the risky ticket thread.
    The resume call returns JSON with "status": "done" and the final approved answer.

Run the frontend tests after the UI work is complete.

    cd /home/poter/resume-pj/supportflow-agent/frontend
    npm test -- --run

Build the frontend to catch typing and bundling regressions.

    cd /home/poter/resume-pj/supportflow-agent/frontend
    npm run build

Start the frontend and verify the browser flow.

    cd /home/poter/resume-pj/supportflow-agent/frontend
    npm run dev -- --host 127.0.0.1 --port 5173

Expected manual UI behavior: `/tickets` still runs a safe ticket to completion, and the review queue screen shows at least one pending review with visible draft, citations, and reviewer controls. Submitting approve, edit, or reject updates the UI to show the final result or manual takeover.

This section must be updated during implementation with the commands actually run and any deviations from the expected transcripts.

## Validation and Acceptance

Acceptance is behavioral, not structural.

A low-risk ticket is accepted only if `POST /api/v1/tickets/{ticket_id}/run` completes in one request with `status: "done"` and a non-empty `final_response.answer`, while still preserving the classification and knowledge evidence that led to the answer.

A high-risk ticket is accepted only if the initial run returns `status: "waiting_review"`, exposes a review payload that includes `thread_id`, `ticket_id`, `draft`, `retrieved_chunks`, and `risk_flags`, and also causes the pending-review list endpoint to return an item for that same thread. In reviewer-facing prose, `retrieved_chunks` is the evidence shown to the reviewer, but the field name should stay `retrieved_chunks` throughout the backend and frontend interfaces.

The resume flow is accepted only if `POST /api/v1/runs/{thread_id}/resume` supports all three reviewer decisions. `approve` must finalize the original draft, `edit` must finalize the edited answer, and `reject` must return `status: "manual_takeover"` without producing an AI final response. Each of these behaviors must be covered by backend tests. At least one frontend test should cover rendering of a waiting-review state or review queue action.

The implementation is complete only if running the backend test command, the frontend test command, and the frontend build command all succeed from a clean checkout with the documented commands in this plan.

## Idempotence and Recovery

The code-editing steps in this plan are additive and safe to repeat. Re-running tests or rebuilding the frontend should not mutate repository state beyond normal caches. Re-running `POST /api/v1/tickets/{ticket_id}/run` for the same ticket should either overwrite the prior in-memory pending-review record for that `thread_id` or return the current waiting state deterministically; choose one behavior and document it in the implementation notes.

Because the pending-review store and LangGraph checkpoint saver are both in memory, restarting the backend will discard waiting reviews. That is acceptable for this MVP milestone, but it must be stated clearly in code comments or API behavior so a novice does not mistake the system for durable storage. If a resume attempt fails because the process restarted or the `thread_id` is unknown, the API should return a clear `404` or `409` style error that tells the user the review item no longer exists and the ticket must be re-run.

If a frontend review action fails, the UI should keep the pending review visible and show the error instead of clearing local state optimistically. That makes retry safe and avoids losing the reviewer’s edits.

## Artifacts and Notes

Important example payloads to preserve during implementation:

    POST /api/v1/tickets/ticket-1001/run
    {
      "thread_id": "ticket-ticket-1001",
      "ticket_id": "ticket-1001",
      "status": "waiting_review",
      "classification": { "...": "..." },
      "retrieved_chunks": [{ "...": "..." }],
      "draft": { "...": "..." },
      "risk_assessment": {
        "review_required": true,
        "risk_flags": ["billing_sensitive", "low_confidence"],
        "reason": "billing ticket with insufficient confidence"
      },
      "pending_review": {
        "thread_id": "ticket-ticket-1001",
        "retrieved_chunks": [{ "...": "..." }],
        "allowed_decisions": ["approve", "edit", "reject"]
      }
    }

    POST /api/v1/runs/ticket-ticket-1001/resume
    {
      "decision": "edit",
      "reviewer_note": "remove refund timing promise",
      "edited_answer": "..."
    }

    Resume success should return either:
    - "status": "done" with "final_response"
    - or "status": "manual_takeover" with no final AI answer

When implementation starts, replace these placeholders with real observed snippets from test output or `curl` responses. Keep them short and focused on proof.

## Interfaces and Dependencies

Use only the existing stack already present in this repository: FastAPI, Pydantic, LangGraph, React, TypeScript, and the existing in-memory checkpoint behavior from `langgraph.checkpoint.memory.InMemorySaver`. Do not add a database, background worker, multi-agent orchestration, or external review service for this milestone.

In `backend/app/schemas/graph.py`, define or extend the following interfaces with stable names:

    class RiskAssessment(BaseModel):
        review_required: bool
        risk_flags: list[str]
        reason: str

    class SubmitReviewDecisionRequest(BaseModel):
        decision: Literal["approve", "edit", "reject"]
        reviewer_note: str | None = None
        edited_answer: str | None = None

    class PendingReviewItem(BaseModel):
        thread_id: str
        ticket_id: str
        classification: TicketClassification
        draft: DraftReply
        retrieved_chunks: list[KBHit]
        risk_flags: list[str]
        allowed_decisions: list[Literal["approve", "edit", "reject"]]

    class FinalResponse(BaseModel):
        answer: str
        citations: list[str]
        disposition: Literal["auto_finalized", "approved", "edited", "manual_takeover"]

`backend/app/graph/state.py` must end with a `TicketState` definition that can carry at least `risk_assessment`, `pending_review`, `review_decision`, `final_response`, and the expanded statuses `queued`, `running`, `waiting_review`, `done`, `failed`, and `manual_takeover`.

`backend/app/graph/builder.py` must expose `get_support_graph()` and continue compiling a single LangGraph with an in-memory checkpointer. The graph must have node names `risk_gate`, `human_review_interrupt`, `apply_review_decision`, `finalize_reply`, and `manual_takeover` in addition to the existing Day 2 nodes.

For imports, use minimal direct imports by default. New backend code should continue importing concrete modules such as `app.schemas.graph`, `app.graph.nodes.risk_gate`, and `app.api.v1.reviews` rather than introducing broader package-level barrel exports. Only update existing narrow re-export files such as `backend/app/graph/nodes/__init__.py` and `backend/app/services/__init__.py` when a new symbol genuinely needs package-level exposure.

`backend/app/api/v1/runs.py` must expose:

    POST /api/v1/tickets/{ticket_id}/run
    POST /api/v1/runs/{thread_id}/resume

If the pending-review list lives in a dedicated router, add:

    GET /api/v1/reviews/pending

`frontend/src/lib/types.ts` must define TypeScript equivalents for the new backend models so the frontend can render pending reviews and final responses without `any`. `frontend/src/lib/api.ts` must expose functions analogous to:

    runTicket(ticketId: string): Promise<RunTicketResponse>
    fetchPendingReviews(): Promise<PendingReviewItem[]>
    resumeRun(threadId: string, body: SubmitReviewDecisionRequest): Promise<RunTicketResponse>

Revision note: on 2026-04-25 this plan was rewritten to match the `Skeleton of a Good ExecPlan` in `docs/PLANS.md` because the prior file was only a short outline and did not satisfy the repository requirement for a self-contained living ExecPlan.
