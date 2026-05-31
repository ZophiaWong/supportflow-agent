# AI Engineer Portfolio Gap Audit

Date: 2026-05-31

## Purpose

This document captures a strict job-seeking review of `supportflow-agent` as an AI Engineer, GenAI Engineer, and Agentic AI Engineer portfolio project. It is not a project pitch and not an MVP acceptance report. Its purpose is to preserve the capability gaps that should drive future implementation plans.

The standard used here is market competitiveness for production-shaped AI workflow projects: RAG quality, workflow durability, human review, tool orchestration, guardrails, observability, evals, reproducible demos, and selective multi-agent capability where it proves a concrete engineering skill.

## Status Legend

- Implemented: behavior exists in code and has at least some validation.
- Partially implemented: the repo has a working slice, but it is too narrow, deterministic, or weakly validated for a strong portfolio claim.
- Documented only: design docs or roadmap mention the capability, but code does not implement it yet.
- Missing: no meaningful implementation found.
- Unverified: evidence was not checked deeply enough to make a firm claim.

## Market-Oriented Capability Gaps

| Market capability | Current status | Evidence | Severity | Why it matters for job seeking |
| --- | --- | --- | --- | --- |
| RAG data coverage | Partially implemented | `data/kb/` has four short Markdown documents; `data/sample_tickets/demo_tickets.json` has three UI demo tickets. | Blocker | The project cannot yet show realistic retrieval behavior, ambiguity, stale policy, conflicting sources, or domain coverage. |
| Retrieval strategy | Partially implemented | `backend/app/services/retrieval.py` uses lexical token overlap and category boost. | High | Current GenAI roles expect more than keyword lookup: hybrid retrieval, reranking, query rewriting, and diagnostics are stronger signals. |
| Citation grounding | Partially implemented | `backend/app/graph/nodes/draft_reply.py` cites the lead retrieved document in fallback mode; `backend/app/evals/scoring.py` checks citation support with token overlap. | High | Document-level citations do not prove that each draft claim is supported by retrieved evidence. |
| Eval quality | Partially implemented | `data/evals/supportflow_v1.jsonl` has 20 fixed examples, but expected statuses are heavily concentrated around `waiting_review`. | Blocker | A perfect eval score is not persuasive if the dataset is too aligned with current rules and lacks meaningful negative and terminal-state variety. |
| LangGraph checkpoint and resume | Partially implemented | `backend/app/graph/builder.py` compiles with `SqliteSaver`; integration tests cover resume after fresh graph construction. | High | The project shows human-review resume, but not targeted retry, replay, checkpoint fork, or time-travel debugging. |
| Human-in-the-loop review | Partially implemented | `backend/app/graph/nodes/human_review_interrupt.py` and `backend/app/api/v1/runs.py` support approve, edit, and reject. | Medium | The core flow exists, but review history, decision diffs, completed-review lookup, and richer audit evidence are thin. |
| Tool orchestration and action safety | Partially implemented | `backend/app/services/action_ledger.py` persists proposed, approved, executed, rejected, and failed-capable actions. | High | Actions are still local simulations with little failure behavior, adapter boundary, retry policy, or dead-letter handling. |
| Guardrails and policy checks | Partially implemented | `backend/app/services/policy_engine.py` uses deterministic keyword and citation checks. | High | This is useful but shallow; stronger projects show PII/secrets detection, prompt-injection variants, unsafe tool prevention, and draft-quality checks. |
| LLM integration | Partially implemented | `backend/app/services/llm.py` provides optional structured-output calls for classification and drafting. | Medium | It is intentionally optional and fallback-safe, but lacks cost, token, prompt, latency, retry, and provider-observability surfaces. |
| Observability | Partially implemented | `backend/app/graph/tracing.py` records local graph-node spans; README documents run trace endpoints. | Medium | Local spans help debugging, but there is no first-class LangSmith, Langfuse, OpenTelemetry, prompt, token, or retrieval-stage trace export. |
| Multi-agent capability | Missing | The current roadmap previously avoided multi-agent; no reviewer, critic, specialist, or supervisor agents are implemented. | High | Current agent engineering roles increasingly mention multi-agent systems. This repo should add a small, justified multi-agent slice rather than a broad orchestration rewrite. |
| Demo scenario breadth | Partially implemented | UI demo tickets cover only three scenarios; eval-only tickets are not available as selectable demo scenarios. | High | A hiring reviewer cannot easily see no-evidence, failure, retry, hallucination, unsafe action, or checkpoint replay behavior in the product. |
| Deployment and reproducible demo | Missing | No Docker Compose, Makefile, or one-command demo path was found; demo readiness remains a todo ExecPlan. | Medium | Reviewers need a quick, deterministic way to run the product and inspect the workflow. |
| API contract discipline | Partially implemented | Pydantic schemas and TypeScript interfaces exist separately. | Medium | Hand-maintained contracts can drift. Generated types or contract tests would strengthen full-stack engineering credibility. |

## Strict Problem List

1. The RAG corpus is too small to support a serious RAG claim. The local KB has only four short documents and the main UI has three demo tickets. This makes retrieval look like a lookup table. The minimum strengthening direction is to add policy, product, troubleshooting, account, and historical-ticket sources with both supported and unsupported requests.

2. Retrieval is lexical and category-boosted. That is acceptable for a first MVP, but it does not demonstrate retrieval engineering. The project should add a hybrid or staged retrieval path with diagnostics that explain query rewrite, source selection, scores, reranking, and why no evidence was found.

3. Citation support is document-level, not claim-level. The eval scorer currently accepts weak token overlap between the answer and retrieved evidence. A stronger project should extract draft claims and verify each claim against retrieved spans, then route unsupported claims to review.

4. The eval dataset is too friendly to the current workflow. Most examples expect `waiting_review`, and the baseline is intentionally weak. This makes the `graph_v1` perfect score less meaningful. The project needs positive and negative cases across `done`, `waiting_review`, `manual_takeover`, and `failed`, plus stronger baselines.

5. LangGraph checkpointing is present but under-shown. The repo demonstrates resume after interrupt, but not recovery from node failure, replay from checkpoint, or forked runs from an earlier checkpoint. These are high-value LangGraph capabilities for a job-seeking portfolio.

6. Failure paths are not rich enough. Current behavior can record a generic run failure, but the product does not intentionally demonstrate retrieval failure, LLM timeout, schema failure, tool execution failure, resume conflict, or retryable versus non-retryable errors.

7. Tool actions are too clean. The action ledger is durable and idempotent, but action execution is still just a local state transition. The project should simulate external adapters with failure modes, retries, and audit records.

8. Guardrails are too rule-shaped. Keyword checks are inspectable, but the project should cover prompt-injection variants, KB poisoning, PII/secrets, unsafe tool requests, and draft claims that exceed evidence.

9. LLM integration is not yet a full LLM operations story. Optional structured output and deterministic fallback are useful, but the project should trace fallback reason, provider latency, model name, token or cost estimates when available, and schema validation failures.

10. Observability is local-only. Node spans are useful, but a competitive project should be able to export or at least shape traces for LangSmith, Langfuse, or OpenTelemetry-style consumption.

11. The review surface lacks completed-review audit depth. Reviewers can approve, edit, or reject, but the app does not yet make historical review decisions, edited-answer diffs, reviewer notes, and action outcomes easy to inspect after completion.

12. The demo does not expose enough scenarios. The UI should let a reviewer select cases for happy path, no evidence, low confidence, prompt injection, unsupported claim, tool failure, LLM fallback, review rejection, and checkpoint replay.

13. Deployment readiness is deferred. Manual backend and frontend commands work for development, but a portfolio reviewer still needs a one-command or near-one-command demo path.

14. Backend and frontend contracts are duplicated manually. This is manageable now, but generated TypeScript types or contract tests would better demonstrate full-stack API discipline.

## Multi-Agent Judgment

The previous roadmap treated multi-agent work as something to avoid. For a job-seeking portfolio, that should no longer be the default conclusion. Multi-agent should be evaluated by market value and capability density, not by the original MVP boundary.

The best current multi-agent shape is a Reviewer or Critic Agent. It should not replace the main LangGraph support workflow. Instead, it should independently inspect the draft, retrieved evidence, policy assessment, and proposed actions before final routing. This demonstrates multi-agent quality control, hallucination detection, groundedness review, and safe-action review without forcing the whole system into a broad supervisor architecture.

Recommended ordering:

1. Reviewer/Critic Agent as a quality gate after drafting and action proposal.
2. Guardrail Agent if separated from reviewer behavior later.
3. Multi-source RAG agents after the corpus has enough policy, product, and historical-ticket sources.
4. Specialist agents for billing, account, product, and bug handling only after data and evals show enough domain complexity.
5. Broad supervisor/router pattern last; it has lower immediate value for this repo until the worker capabilities are substantial.

## Priority Capability Backlog

| Priority | Capability | Current gap | What it proves after implementation |
| --- | --- | --- | --- |
| 1 | RAG data, retrieval, and eval foundation | Corpus and evals are too small and too aligned with rules. | The project is not a toy demo; retrieval quality can be measured and improved. |
| 2 | LangGraph checkpoint retry and replay demo | Checkpoints support resume but not failure recovery or time-travel-style inspection. | The project uses LangGraph for durable workflow engineering, not just graph visualization. |
| 3 | Reviewer/Critic Agent quality gate | Multi-agent capability is missing. | The project can show a focused multi-agent pattern tied to groundedness and safety. |
| 4 | Tool failure and action adapter layer | Actions are local state transitions without failure behavior. | Tool calling is treated as an auditable side-effect boundary. |
| 5 | Observability export and LLM/RAG trace enrichment | Trace is local and mostly graph-node-level. | Agent decisions, LLM calls, retrieval, policies, and actions can be inspected coherently. |
| 6 | Demo scenario workbench | UI demo has only three tickets. | A reviewer can inspect failure, recovery, and safety scenarios quickly. |
| 7 | Demo packaging | No one-command demo path. | The project can be cloned and evaluated with low setup friction. |

## Not Recommended As First Priorities

- Do not start with a broad supervisor and specialist-agent rewrite. It has lower capability density until the RAG corpus and evals are stronger.
- Do not connect real email or a live ticketing system before local tool failure and audit semantics are solid.
- Do not spend another large pass on visual redesign before the core AI workflow gaps are addressed.
- Do not add a hosted vector database before proving local hybrid retrieval and eval value.
- Do not make LLM generation mandatory; preserve deterministic local runs and focus on tracing, fallback, and eval behavior.
- Do not prioritize auth, multi-tenancy, or voice. They are lower signal for this project's current AI Agent Engineer positioning.

## First ExecPlans Derived From This Audit

The first implementation plans should be created as todo ExecPlans, not active plans:

- `docs/exec-plans/todo/2026-05-31-01-rag-data-retrieval-eval-foundation.md`
- `docs/exec-plans/todo/2026-05-31-02-langgraph-checkpoint-retry-replay-demo.md`
- `docs/exec-plans/todo/2026-05-31-03-reviewer-critic-agent-quality-gate.md`

These three plans should be implemented before broader specialist-agent or supervisor-agent work.
