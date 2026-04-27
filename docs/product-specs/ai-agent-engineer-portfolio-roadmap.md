# AI Agent Engineer Portfolio Roadmap

## Purpose

This roadmap defines post-MVP features for `supportflow-agent` as a job-seeking portfolio project for AI Agent Engineer roles.

The goal is to make the project demonstrate production-oriented agent engineering: stateful workflow orchestration, safe tool use, human-in-the-loop control, observability, evaluation, RAG quality, and a usable full-stack product surface. The project should remain a single LangGraph workflow app. Do not add multi-agent patterns unless a later product spec explicitly changes that constraint.

## Market Signal Summary

Current AI Agent Engineer postings and framework docs repeatedly emphasize these capabilities:

- LangGraph or equivalent orchestration for stateful, multi-step workflows.
- Human-in-the-loop review for risky actions and recoverable interrupts.
- Tool calling and integration with APIs, databases, or external systems.
- RAG, prompt engineering, and grounded outputs with citations.
- Safety, guardrails, reliability, and production readiness.
- Observability, tracing, debugging, and evaluation loops.
- Python, FastAPI, React, and practical full-stack delivery.

Sources used on 2026-04-27:

- LangGraph positions list state machines, branching, and human-in-the-loop workflows as key role signals: https://agentic-engineering-jobs.com/jobs/langgraph/onsite/us
- Agentic AI Engineer postings call for LangChain/LangGraph workflows, tool orchestration, APIs, and front-end integration: https://www.sandersonplc.com/job/agentic-ai-engineer-langgraph-bhagai1_1769160952/
- Job postings mention prompt engineering, memory, tool usage, APIs, knowledge graphs, vector databases, monitoring, debugging, and deployment: https://www.linkedin.com/jobs/view/agentic-ai-engineer-langchain-langgraph-claude-100%25-remote-at-ahura-workforce-solutions-4402770167
- LangGraph documentation highlights durable execution, human-in-the-loop, memory, streaming, and debugging with LangSmith: https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph persistence docs identify checkpoints as the basis for human-in-the-loop, time travel debugging, and fault-tolerant execution: https://docs.langchain.com/oss/python/langgraph/persistence
- OpenAI Agents SDK docs emphasize traces across agent runs, model generations, tool calls, guardrails, and custom events: https://openai.github.io/openai-agents-python/tracing/
- OpenAI guardrails docs emphasize input, output, and tool-level checks for safety and cost control: https://openai.github.io/openai-agents-python/guardrails/
- OpenAI agent eval docs emphasize reproducible workflow-level evaluations and trace grading: https://platform.openai.com/docs/guides/agent-evals
- OpenTelemetry GenAI conventions show industry movement toward standard agent, tool, and LLM telemetry: https://opentelemetry.io/docs/specs/semconv/gen-ai/

## Positioning

The portfolio story should be:

> A production-shaped support workflow agent that triages tickets, retrieves grounded policy context, drafts customer replies, pauses for human review when risk is high, persists recoverable workflow state, exposes traceable decisions, and continuously improves through evals.

This is stronger than a demo chatbot because it shows:

- Workflow control instead of free-form chat.
- Reviewable state and decisions instead of opaque generation.
- Measurable eval quality instead of anecdotal prompt output.
- Safety gates around actions instead of unbounded automation.
- Full-stack delivery instead of a backend-only notebook.

## Feature Priority

### P0: Durable Workflow State

Problem: The MVP proves the workflow, but run state, pending reviews, and checkpoints are still process-local. A production agent engineer should show recoverable, long-running workflows.

Build:

- Replace in-memory run state, event timeline, pending reviews, and LangGraph checkpoint storage with a durable local store.
- Prefer SQLite for portfolio practicality.
- Persist thread IDs, graph checkpoints, current run status, timeline events, pending review payloads, reviewer decisions, and final dispositions.
- Make resume work after backend restart.
- Add a small reset or seed command for demos.

Acceptance:

- Run `ticket-1001` until `waiting_review`.
- Stop and restart the backend.
- Confirm `/api/v1/reviews/pending` still lists the pending review.
- Approve the review and confirm the graph resumes to `done`.
- Backend tests cover restart-style persistence by constructing a fresh service or app against the same database file.

Resume Talking Point:

- "I made the agent workflow durable, so human review can happen minutes or days later without losing graph state."

### P1: Safe Tool Action Layer

Problem: Job postings value tool calling and API integration, but real email or ticketing write-back is outside the MVP. A simulated but well-designed action layer can demonstrate the same engineering skill without risky external dependencies.

Build:

- Add a tool/action abstraction for support actions:
  - `send_customer_reply`
  - `create_refund_case`
  - `apply_credit`
  - `escalate_to_tier_2`
  - `add_internal_note`
- Keep tools local and simulated by default.
- Store every proposed action in an action ledger with status `proposed`, `approved`, `executed`, `rejected`, or `failed`.
- Require human approval for high-impact actions such as refunds, credits, and external sends.
- Add idempotency keys so resumed workflows do not execute the same action twice.
- Expose proposed and executed actions in the ticket detail and review UI.

Acceptance:

- Low-risk reply can create a proposed `send_customer_reply` action and auto-finalize only if policy allows it.
- Refund or credit cases must pause for review before execution.
- Rejecting an action records reviewer feedback and does not execute the action.
- Retrying a resumed run does not duplicate executed actions.

Resume Talking Point:

- "I built tool execution like a production side-effect boundary: policy gated, auditable, idempotent, and human-reviewable."

### P1: Guardrails and Policy Engine

Problem: AI Agent Engineer roles increasingly focus on safe, reliable automation. The current risk gate is useful, but it should evolve into explicit policy checks around inputs, retrieved context, generated drafts, and tool actions.

Build:

- Add structured policy checks for:
  - PII or secrets in ticket text.
  - Prompt-injection attempts in customer input or KB content.
  - Unsupported claims without citations.
  - Refund, legal, security, or account-risk language.
  - Draft tone problems such as blame, unsupported guarantees, or missing escalation language.
- Return policy results as Pydantic schemas.
- Route policy failures to human review with clear reasons.
- Add frontend display for policy flags and reviewer guidance.

Acceptance:

- Prompt-injection fixture is detected and routed to review.
- Draft with missing citations fails the citation policy.
- Refund/security/legal fixtures pause with explicit policy reasons.
- Offline eval includes policy-trigger accuracy.

Resume Talking Point:

- "I treated guardrails as structured workflow decisions, not prompt-only suggestions."

### P1: Trace and Observability Dashboard

Problem: Agent debugging is a core hiring signal. The backend already has event traces, but the product should expose a trace view that explains what happened and why.

Build:

- Add structured spans/events for graph nodes, retrieval, drafting, risk policy, review interrupt, resume, and tool actions.
- Include duration, status, selected category, retrieved document IDs, citations, risk score, policy flags, and action IDs.
- Add a `/runs/{thread_id}/trace` backend endpoint.
- Add a frontend run trace view from ticket detail.
- Keep LangSmith optional, but structure local traces so they can map to LangSmith or OpenTelemetry later.

Acceptance:

- Every completed run shows a chronological trace with node-level status.
- Failed policy checks and review interrupts are visible without reading server logs.
- Tests assert important trace fields exist for low-risk, review, approve, and reject paths.

Resume Talking Point:

- "I made agent behavior inspectable at the graph-node level, including retrieval inputs, policy decisions, and human review transitions."

### P2: Evaluation Flywheel

Problem: The MVP has offline evals. The next step is a realistic improvement loop: collect failures, turn them into fixtures, and prevent regressions.

Build:

- Add an eval dataset format that can include expected category, expected citations, expected policy flags, expected review decision, and expected final disposition.
- Add failure reports that group bad cases by failure type.
- Add a command to promote a captured trace or ticket into an eval fixture.
- Add CI-friendly thresholds for final pass rate, citation coverage, and policy-trigger accuracy.
- Add a small frontend or Markdown eval report for portfolio review.

Acceptance:

- A new bad-case ticket can be added to the eval dataset in one documented command.
- Eval output names the failing stage: classification, retrieval, drafting, policy, review routing, or finalization.
- CI fails when `graph_v1` drops below configured thresholds.

Resume Talking Point:

- "I built a closed-loop eval workflow where production-style traces become regression tests."

### P2: Knowledge Base Operations and Retrieval Quality

Problem: RAG is already present, but a portfolio project should show retrieval quality controls beyond keyword matching.

Build:

- Add KB metadata: category, effective date, source owner, freshness, and policy severity.
- Add an ingestion command that validates Markdown front matter and builds a local retrieval index.
- Consider local vector or hybrid retrieval if it can be added without bloating the repo.
- Add citation verification that checks draft claims against retrieved KB snippets.
- Add a retrieval diagnostics panel showing why documents were selected.

Acceptance:

- KB ingestion fails on missing required metadata.
- Retrieval diagnostics show score, matched terms, category boost, and citation IDs.
- Eval reports retrieval hit rate and citation support rate.

Resume Talking Point:

- "I improved RAG from a demo lookup into a managed knowledge pipeline with metadata, diagnostics, and evals."

### P2: Streaming Workflow UX

Problem: Agent workflows are easier to understand when progress is visible as nodes complete. This is a high-impact UI feature that demonstrates full-stack agent product sense.

Build:

- Add server-sent events or polling for workflow progress.
- Stream graph node status, partial draft tokens if available, retrieval completion, policy checks, and interrupt state.
- Keep the UI dense and operational: timeline, draft, policy flags, citations, and action proposals should remain scannable.

Acceptance:

- Running a ticket shows progress without requiring manual refresh.
- A risky run visibly transitions into `waiting_review`.
- Frontend tests cover the loading, progress, completed, and waiting-review states.

Resume Talking Point:

- "I exposed a long-running graph workflow as an understandable product experience, not a blocking request."

### P3: Demo and Deployment Readiness

Problem: Hiring reviewers need to run the project quickly. A strong demo path increases the value of every feature above.

Build:

- Add Docker Compose for backend, frontend, and SQLite volume.
- Add `make demo` or documented scripts for seed, test, eval, and dev servers.
- Add a portfolio README section with screenshots or short GIFs.
- Add an architecture diagram that maps user actions to graph nodes, stores, evals, and UI views.

Acceptance:

- A reviewer can clone the repo and run the demo with minimal setup.
- README links to the portfolio roadmap, MVP spec, active/completed ExecPlans, and eval evidence.
- Demo data can be reset deterministically.

Resume Talking Point:

- "I packaged the project so reviewers can run and inspect the workflow quickly."

## Recommended Build Sequence

1. Durable Workflow State
2. Safe Tool Action Layer
3. Guardrails and Policy Engine
4. Trace and Observability Dashboard
5. Evaluation Flywheel
6. Knowledge Base Operations and Retrieval Quality
7. Streaming Workflow UX
8. Demo and Deployment Readiness

This sequence prioritizes the strongest engineering signal first. Durable state unlocks credible human-in-the-loop behavior. Tool actions and guardrails make the agent feel production-relevant. Observability and evals make the behavior inspectable and measurable. Retrieval, streaming, and deployment polish the portfolio.

## Features To Avoid For Now

- Multi-agent routing or agent-to-agent communication.
  Rationale: Job postings mention it, but this repo explicitly says not to introduce multi-agent patterns. A reliable single workflow is a clearer signal.

- Real email or ticketing write-back.
  Rationale: A simulated tool layer demonstrates the same side-effect design without account setup, secrets, or external failure modes.

- Full multi-tenant auth.
  Rationale: Useful later, but lower signal than durable workflows, guarded actions, evals, and traces for AI Agent Engineer roles.

- Voice support.
  Rationale: Some roles mention conversational systems, but voice would distract from this project's strongest support-workflow narrative.

## Product Success Criteria

The roadmap is successful when a hiring reviewer can see:

- A ticket enter a durable LangGraph workflow.
- KB evidence retrieved and cited.
- A draft generated with structured policy checks.
- A risky action paused for human review.
- A reviewer approve, edit, or reject the proposed response or tool action.
- The workflow resume after backend restart.
- A trace explain each node, retrieval result, policy decision, and side effect.
- Offline evals measure quality and fail on regressions.
- The project run locally with clear commands and deterministic demo data.

## Next ExecPlan Recommendation

Create one active ExecPlan for `Durable Workflow State`. It should cover backend storage, graph checkpointing, API behavior, frontend reload behavior, tests, and documentation. This is a multi-file feature touching backend, frontend, graph state, and acceptance evidence, so it requires an ExecPlan under `docs/exec-plans/active/`.
