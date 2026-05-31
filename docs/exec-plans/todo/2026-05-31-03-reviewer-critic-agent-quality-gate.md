# Reviewer Critic Agent Quality Gate

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

SupportFlow should demonstrate a focused multi-agent capability that improves quality rather than adding complexity for its own sake. After this change, the main support workflow still owns ticket processing, retrieval, drafting, policy checks, human review, and action execution. A new Reviewer or Critic Agent independently inspects the draft, retrieved evidence, and proposed actions before final routing, then produces a structured quality assessment that can trigger human review when the draft is unsupported or unsafe.

The user-visible result is a new quality gate in the workflow and review UI. A hiring reviewer should be able to run adversarial demo or eval tickets and see the critic catch missing citations, unsupported claims, unsafe refund or credit language, low-evidence high-confidence drafts, and prompt-injection attempts.

## Progress

- [x] (2026-05-31 HKT) Created this todo ExecPlan from the 2026-05-31 portfolio gap audit.
- [ ] Inspect current graph node ordering, policy assessment schema, LLM service, eval fixtures, and review UI.
- [ ] Define a Pydantic `ReviewAssessment` schema for critic findings.
- [ ] Add a reviewer/critic node to the LangGraph workflow after drafting and action proposal.
- [ ] Implement deterministic critic checks first, with optional LLM-backed critique only if it preserves local reproducibility.
- [ ] Feed critic findings into risk gate and human review payloads.
- [ ] Add eval fixtures for missing citation, hallucination, unsafe action, prompt injection, and low-evidence high-confidence cases.
- [ ] Update frontend review surfaces and docs to show critic findings.

## Surprises & Discoveries

- Observation: The graph already has a clean insertion point for a quality gate.
  Evidence: `backend/app/graph/builder.py` currently runs `draft_reply`, then `propose_actions`, then `risk_gate`.

- Observation: Policy checks already return structured Pydantic results.
  Evidence: `backend/app/schemas/graph.py` defines `PolicyCheckResult` and `PolicyAssessment`; `backend/app/services/policy_engine.py` returns a `PolicyAssessment`.

- Observation: Optional LLM integration exists but is intentionally advisory.
  Evidence: `docs/exec-plans/active/2026-05-28-llm-workflow-integration.md` states that policy routing and support action execution remain rule-driven.

## Decision Log

- Decision: Implement Reviewer/Critic Agent as the first multi-agent pattern.
  Rationale: It has the highest market-signal density for this repo: multi-agent quality control, groundedness checking, safety review, and eval-friendly behavior.
  Date/Author: 2026-05-31 / Codex

- Decision: Do not implement a broad supervisor/router pattern in this plan.
  Rationale: The corpus and evals should be stronger before specialist worker agents or a supervisor architecture can be meaningful.
  Date/Author: 2026-05-31 / Codex

- Decision: Keep deterministic critic checks as the required baseline.
  Rationale: The project must remain runnable without API keys. Optional LLM critique can be added only if fallback behavior and tests remain deterministic.
  Date/Author: 2026-05-31 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize the critic schema, graph insertion point, eval coverage, UI changes, and whether optional LLM critique was included or deferred.

## Context and Orientation

The LangGraph workflow is built in `backend/app/graph/builder.py`. It currently runs these main nodes: `load_ticket_context`, `classify_ticket`, `retrieve_knowledge`, `draft_reply`, `propose_actions`, `risk_gate`, `human_review_interrupt`, `apply_review_decision`, `finalize_reply`, and `manual_takeover`.

The graph state is `TicketState` in `backend/app/graph/state.py`. The public API response schemas are in `backend/app/schemas/graph.py`. Draft responses use `DraftReply`, retrieved evidence uses `KBHit`, support actions use `SupportAction`, and policy checks use `PolicyAssessment`.

In this plan, "Reviewer Agent" and "Critic Agent" mean the same focused component: a workflow node that independently evaluates the draft and action plan. It is called an agent because it performs a specialized judgment role separate from the main drafting node. It is not a free-form chat participant, and it does not own final action execution.

## Plan of Work

First, inspect the existing workflow contracts. Confirm the exact state fields available after `draft_reply` and `propose_actions`. The critic should receive ticket context, classification, retrieved chunks, draft reply, proposed actions, and any available policy context. If `policy_assessment` is only created later, the critic should not depend on it for the first version.

Second, define the structured output. Add a Pydantic model such as `ReviewAssessment` in `backend/app/schemas/graph.py`. It should include at least: `review_required`, `findings`, `unsupported_claims`, `missing_evidence`, `unsafe_action_flags`, `citation_support`, `escalation_recommendation`, `confidence`, and `rationale`. Keep fields concrete enough for frontend display and eval scoring.

Third, add a graph node such as `review_draft_quality`. Place it after `propose_actions` and before `risk_gate`. This lets the critic inspect both the draft and proposed actions before final routing. Update `TicketState` to include `review_assessment`, and update trace summaries to include critic findings.

Fourth, implement deterministic critic checks. Required checks include: draft has citations when retrieved evidence exists; citations reference retrieved document IDs; answer does not include forbidden unsupported phrases from eval references; high-confidence drafts without evidence are flagged; proposed refund, credit, customer-send, or escalation actions are flagged when evidence is missing or weak. Optional LLM-backed critique can be added behind the existing LLM configuration only after deterministic behavior is complete.

Fifth, integrate critic output into routing. The existing `risk_gate` should consider critic findings alongside policy checks. If the critic says review is required, the workflow should pause for human review with a clear reviewer-facing explanation. The pending review payload should include the critic assessment.

Sixth, update API and frontend types. Add `review_assessment` to relevant backend responses and frontend TypeScript interfaces. Show critic findings in the ticket workbench, review detail page, and run diagnostics without hiding existing policy checks.

Seventh, update evals. Add fixtures that prove the critic catches missing citation, hallucination or unsupported claim, unsafe refund or credit action, prompt injection, and low-evidence high-confidence draft. Add scoring fields for expected critic findings so the eval can fail when the critic misses important issues.

## Concrete Steps

Inspect current workflow and schemas:

    sed -n '1,140p' backend/app/graph/builder.py
    sed -n '1,220p' backend/app/graph/state.py
    sed -n '1,240p' backend/app/schemas/graph.py
    sed -n '1,220p' backend/app/services/policy_engine.py
    sed -n '1,220p' backend/app/graph/tracing.py
    sed -n '1,260p' frontend/src/lib/types.ts

Run current validation before implementation:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

After backend implementation:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py --min-final-pass-rate <chosen-threshold>

After frontend contract changes:

    cd frontend
    npm test -- --run
    npm run build

Manual demo should include at least one ticket where the normal draft looks plausible but the critic requires review because evidence is missing, a citation is unsupported, or a proposed action is unsafe. Record the ticket ID and observed critic finding in this plan.

## Validation and Acceptance

This plan is complete when all of these are true:

- A `ReviewAssessment` or equivalently named Pydantic schema exists and is included in graph state and API responses.
- The graph has a distinct reviewer/critic node after drafting and action proposal, before final review routing.
- Critic findings can independently require human review.
- Pending review payloads include critic findings so reviewers can see why the draft is risky.
- Frontend types and UI display critic findings.
- Eval fixtures cover missing citation, unsupported claim, unsafe action, prompt injection, and low-evidence high-confidence behavior.
- Offline eval fails when the critic misses expected findings and passes when the critic catches them.
- Backend tests pass, frontend tests pass, and frontend build succeeds.
- README or a design doc explains this as a focused multi-agent quality gate, not a broad supervisor architecture.

## Idempotence and Recovery

The critic node should be additive. Existing policy checks, action ledger behavior, and human review decisions should continue to work. If critic integration causes too many existing examples to route differently, update eval references only when the new behavior is intentionally better and record the decision.

If optional LLM critique is added, it must fail closed to deterministic critic behavior and record fallback reasons. Missing API keys must not break local tests or demos.

If frontend changes lag backend changes, keep API fields optional in TypeScript until the UI is fully updated. Remove optionality only when all responses reliably include the new field.

## Artifacts and Notes

The motivating gap audit is `docs/product-specs/ai-engineer-portfolio-gap-audit-2026-05-31.md`.

This plan intentionally selects the Reviewer/Critic Agent pattern as the first multi-agent feature. Specialist agents, multi-source RAG agents, and supervisor/router patterns are future candidates, not part of this plan.

## Interfaces and Dependencies

Add or update backend schemas in `backend/app/schemas/graph.py`. A concrete target shape is:

    class ReviewFinding(BaseModel):
        finding_id: str
        severity: Literal["info", "warning", "blocker"]
        category: Literal["citation", "grounding", "action_safety", "prompt_injection", "confidence", "other"]
        message: str
        evidence: list[str] = Field(default_factory=list)

    class ReviewAssessment(BaseModel):
        review_required: bool
        findings: list[ReviewFinding] = Field(default_factory=list)
        unsupported_claims: list[str] = Field(default_factory=list)
        missing_evidence: list[str] = Field(default_factory=list)
        unsafe_action_flags: list[str] = Field(default_factory=list)
        citation_support: dict[str, bool] = Field(default_factory=dict)
        escalation_recommendation: Literal["none", "human_review", "manual_takeover"]
        confidence: float
        rationale: str

The exact shape may change during implementation, but it must stay structured, Pydantic-validated, API-visible, frontend-visible, and eval-visible.

Add the node under `backend/app/graph/nodes/`, for example `review_draft_quality.py`. Wire it in `backend/app/graph/builder.py` between `propose_actions` and `risk_gate`. Update `backend/app/graph/tracing.py` so traces summarize critic findings.

Do not add AutoGen, CrewAI, or a broad multi-agent framework for this first version. Use the existing LangGraph workflow and Pydantic schemas.

## Plan Revision Notes

2026-05-31: Initial todo ExecPlan created from the portfolio gap audit. The plan chooses a Reviewer/Critic Agent as the first multi-agent capability because it directly strengthens groundedness, safety, and eval quality.
