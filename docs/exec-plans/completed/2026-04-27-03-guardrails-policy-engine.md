# Day 11 Guardrails and Policy Engine

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The MVP has a risk gate that decides whether a ticket needs human review. After this change, safety decisions will be represented as explicit structured policy checks over ticket text, retrieved knowledge, generated drafts, and proposed tool actions. A reviewer will be able to see exactly which policy checks fired and why.

This feature demonstrates production agent engineering because it treats guardrails as testable workflow decisions rather than vague prompt instructions.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [x] (2026-04-28) Confirmed Day 10 support action state is present and in scope. Evidence: `backend/app/schemas/actions.py`, `backend/app/graph/nodes/propose_actions.py`, and the product spec describe proposed and executed support actions.
- [x] (2026-04-28) Added policy result schemas and a deterministic policy engine service. Evidence: `PolicyCheckResult` and `PolicyAssessment` in `backend/app/schemas/graph.py`, and `backend/app/services/policy_engine.py`.
- [x] (2026-04-28) Wired policy checks into the LangGraph workflow. Evidence: `propose_actions` now runs before `risk_gate`, and `risk_gate` calls `evaluate_policy`.
- [x] (2026-04-28) Added frontend policy display in ticket, run-state, review queue, and review detail surfaces. Evidence: `frontend/src/components/PolicyAssessmentList.tsx` and usage in workflow/review panels.
- [x] (2026-04-28) Extended offline eval with policy-trigger expectations. Evidence: `expected_policy_ids` in `backend/app/evals/schemas.py` and `data/evals/supportflow_v1.jsonl`.
- [x] (2026-04-28) Added backend and frontend tests. Evidence: `backend/tests/test_policy_engine.py`, updated graph/API/eval tests, and updated review queue tests.
- [x] (2026-04-28) Updated docs and this ExecPlan with observed behavior.

## Surprises & Discoveries

- Observation: Day 10 was already implemented, so high-impact support actions could be part of policy evaluation instead of being deferred.
  Evidence: `propose_actions` creates review-required `send_customer_reply` actions, and `supportflow-mvp.md` records external send approval behavior.

- Observation: To let policy checks inspect proposed actions, graph order needed to change from `draft_reply -> risk_gate -> propose_actions` to `draft_reply -> propose_actions -> risk_gate`.
  Evidence: `backend/app/graph/builder.py` now routes from `draft_reply` to `propose_actions`, then to `risk_gate`, then conditionally to review or finalization.

- Observation: Low-risk content now has `risk_assessment.review_required == true` when the only failed policy is `high_impact_action_requires_review`.
  Evidence: `tests/integration/test_graph_smoke.py::test_graph_smoke_pauses_low_risk_ticket_for_send_approval` asserts `failed_policy_ids == ["high_impact_action_requires_review"]`.

## Decision Log

- Decision: Start with deterministic policy checks.
  Rationale: The project currently uses deterministic local workflow logic. Rule-based checks are explainable, testable, and enough to demonstrate guardrail design before adding LLM-based moderation.
  Date/Author: 2026-04-27 / Codex

- Decision: Route policy failures through the existing human-review interrupt path.
  Rationale: The app already has a review queue and resume endpoint. Reusing it keeps the workflow simple and avoids adding a parallel exception mechanism.
  Date/Author: 2026-04-27 / Codex

- Decision: Treat external customer sends as a policy failure until approved, even when message content is low risk.
  Rationale: The portfolio feature is meant to demonstrate safe agent automation around side effects. A customer-facing send is an external side effect, so the explicit policy check should be visible in the same structure as content guardrails.
  Date/Author: 2026-04-28 / Codex

- Decision: Preserve `RiskAssessment` while adding `PolicyAssessment`.
  Rationale: Existing API and frontend code already consume `risk_assessment`. Adding `policy_assessment` exposes richer reviewer guidance without removing the older field. During this milestone, `risk_flags` are the failed policy IDs for compatibility with existing evals and UI chips.
  Date/Author: 2026-04-28 / Codex

## Outcomes & Retrospective

Completed on 2026-04-28. The workflow now emits structured policy checks for priority, low confidence, missing evidence, missing citations, billing sensitivity, sensitive requests, prompt injection, legal/security language, and high-impact support actions. Reviewers can see failed policy IDs, severity, messages, and evidence in the workflow output, run-state panel, review queue, and review detail page. Offline eval now checks `expected_policy_ids`, and validation passed with backend tests `32 passed`, frontend tests `13 passed`, frontend build success, and `graph_v1` offline eval final pass rate `1.00` with `0` bad cases.

Deferred guardrails remain deterministic and local. Future work can add stronger PII/secret detection, LLM moderation, or policy versioning if the app needs broader production-like coverage.

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

Expected result: the response has `status` equal to `waiting_review`, the risk assessment includes policy-derived flags, `policy_assessment.failed_policy_ids` includes policy IDs such as `billing_sensitive` and `high_impact_action_requires_review`, and the pending review payload explains why review is required.

Observed validation on 2026-04-28:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    # 32 passed in 14.40s

    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py
    # target=graph_v1 examples=20 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=1.00 final_pass_rate=1.00 bad_cases=0

    cd frontend
    npm test -- --run
    # 13 passed

    npm run build
    # built successfully

## Validation and Acceptance

This plan is complete because all of these are true:

- Policy check results are represented by Pydantic schemas.
- The graph routes policy failures to human review with clear reasons.
- Prompt-injection, unsupported-citation, refund, legal, security, or account-risk fixtures trigger expected policies.
- Frontend review UI shows policy flags and reviewer guidance.
- Offline eval reports policy-trigger accuracy or equivalent policy coverage.
- Backend tests, frontend tests, frontend build, and offline eval pass.

## Idempotence and Recovery

Policy checks should be pure functions of ticket text, retrieved chunks, draft content, and proposed actions. Running them repeatedly should produce the same results unless inputs change. Do not persist duplicate policy records unless they are tied to a durable trace event.

## Artifacts and Notes

This plan follows the completed safe-tool plan in `docs/exec-plans/completed/2026-04-27-02-safe-tool-action-layer.md`. Because that plan was implemented before this one, high-impact support action policies are included.

## Interfaces and Dependencies

At completion, there should be a policy service interface similar to:

    def evaluate_policy(
        *,
        ticket: dict[str, object],
        classification: TicketClassification,
        retrieved_chunks: list[KBHit],
        draft: DraftReply,
        proposed_actions: list[SupportAction] | None = None,
    ) -> PolicyAssessment: ...

Use existing Pydantic schemas and keep the evaluator deterministic.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.

2026-04-28: Implemented the plan end to end. The main design change was moving action proposal ahead of the risk gate so structured policy checks can evaluate high-impact proposed actions.
