# Day 11 Guardrails and Policy Engine

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The MVP has a risk gate that decides whether a ticket needs human review. After this change, safety decisions will be represented as explicit structured policy checks over ticket text, retrieved knowledge, generated drafts, and proposed tool actions. A reviewer will be able to see exactly which policy checks fired and why.

This feature demonstrates production agent engineering because it treats guardrails as testable workflow decisions rather than vague prompt instructions.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [ ] Confirm Day 10 action state and response schemas, or scope this plan to pre-action policy checks if Day 10 is not complete.
- [ ] Add policy result schemas and a policy engine service.
- [ ] Wire policy checks into the LangGraph workflow.
- [ ] Add frontend policy display in ticket and review surfaces.
- [ ] Extend offline eval with policy-trigger expectations.
- [ ] Add backend and frontend tests.
- [ ] Update docs and this ExecPlan with observed behavior.

## Surprises & Discoveries

- Observation: No implementation discoveries yet.
  Evidence: This plan has only been created.

## Decision Log

- Decision: Start with deterministic policy checks.
  Rationale: The project currently uses deterministic local workflow logic. Rule-based checks are explainable, testable, and enough to demonstrate guardrail design before adding LLM-based moderation.
  Date/Author: 2026-04-27 / Codex

- Decision: Route policy failures through the existing human-review interrupt path.
  Rationale: The app already has a review queue and resume endpoint. Reusing it keeps the workflow simple and avoids adding a parallel exception mechanism.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize implemented policies, eval changes, reviewer UI behavior, and any deferred guardrails.

## Context and Orientation

The current risk gate is implemented under `backend/app/graph/nodes/risk_gate.py`. It sets `review_required`, `risk_assessment`, and status fields in the graph state. The risk assessment schema is `backend/app/schemas/graph.py::RiskAssessment`, with `review_required`, `risk_flags`, and `reason`.

The graph state is `backend/app/graph/state.py::TicketState`. It already carries the ticket, classification, retrieved chunks, draft, risk assessment, pending review, review decision, and final response.

A policy check is a named validation step that returns a structured result. Example policy checks are:

- PII or secrets in ticket text.
- Prompt-injection language in customer input or KB content.
- Unsupported draft claims without citations.
- Refund, legal, security, or account-risk language.
- Draft tone problems such as unsupported guarantees or blame.
- High-impact tool action proposals, if Day 10 has been implemented.

## Plan of Work

First, inspect the current `risk_gate` node and tests. Identify the existing risk flags so new policy flags preserve current behavior and do not weaken MVP acceptance.

Second, add schemas. Use Pydantic models such as `PolicyCheckResult` and `PolicyAssessment`. Each result should include `policy_id`, `severity`, `passed`, `message`, and optional `evidence`. The assessment should include all results plus a computed `review_required` boolean.

Third, add a policy service such as `backend/app/services/policy_engine.py`. Implement deterministic checks for prompt injection, secrets or PII-like content, missing citations, high-risk categories, and high-impact actions when available. Keep rules small and explicit.

Fourth, update the graph. Either replace `risk_gate` internals with the policy engine or add a `run_policy_checks` node before `risk_gate`. Preserve the public `risk_assessment` field while adding a richer `policy_assessment` field if useful. The frontend and API can continue to use `risk_assessment` while also showing policy details.

Fifth, update pending reviews so reviewers see policy flags and guidance. This may require adding fields to `PendingReviewItem` and TypeScript types.

Sixth, extend the eval dataset. Add or update fixtures for prompt injection, missing citation, refund, security, and legal-risk examples. Extend the offline scorer so it can check expected policy flags or expected policy IDs.

Seventh, add tests. Backend unit tests should cover the policy engine directly. Graph/API tests should prove that policy failures route to `waiting_review`. Frontend tests should prove policy flags render on ticket detail and review queue.

## Concrete Steps

Inspect current risk and eval code:

    sed -n '1,260p' backend/app/graph/nodes/risk_gate.py
    sed -n '1,340p' backend/app/schemas/graph.py
    sed -n '1,260p' backend/app/evals/schemas.py
    sed -n '1,320p' backend/app/evals/scoring.py
    sed -n '1,220p' data/evals/supportflow_v1.jsonl

Run current backend validation:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

After implementation, run:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

    cd frontend
    npm test -- --run
    npm run build

Manual smoke target:

    POST /api/v1/tickets/ticket-1001/run

Expected result: the response has `status` equal to `waiting_review`, the risk assessment includes policy-derived flags, and the pending review payload explains why review is required.

## Validation and Acceptance

This plan is complete when all of these are true:

- Policy check results are represented by Pydantic schemas.
- The graph routes policy failures to human review with clear reasons.
- Prompt-injection, unsupported-citation, refund, legal, security, or account-risk fixtures trigger expected policies.
- Frontend review UI shows policy flags and reviewer guidance.
- Offline eval reports policy-trigger accuracy or equivalent policy coverage.
- Backend tests, frontend tests, frontend build, and offline eval pass.

## Idempotence and Recovery

Policy checks should be pure functions of ticket text, retrieved chunks, draft content, and proposed actions. Running them repeatedly should produce the same results unless inputs change. Do not persist duplicate policy records unless they are tied to a durable trace event.

## Artifacts and Notes

This plan follows the safe-tool plan in `docs/exec-plans/completed/2026-04-27-day10-safe-tool-action-layer.md`, but it can start earlier if limited to ticket, retrieval, and draft policy checks. If it starts before Day 10, record that scope decision in the Decision Log.

## Interfaces and Dependencies

At completion, there should be a policy service interface similar to:

    def evaluate_policy(
        *,
        ticket: dict[str, object],
        retrieved_chunks: list[KBHit],
        draft: DraftReply,
        proposed_actions: list[SupportAction] | None = None,
    ) -> PolicyAssessment: ...

Use existing Pydantic schemas and keep the evaluator deterministic.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.
