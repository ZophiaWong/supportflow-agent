# RAG Data, Retrieval, and Eval Foundation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

SupportFlow currently has a working local knowledge base and offline eval runner, but the data and metrics are too small and too aligned with the current rules to support a strong RAG portfolio claim. After this change, a hiring reviewer should be able to run the offline eval and see a broader set of support scenarios with positive and negative retrieval cases, stronger baselines, and citation checks that make RAG quality visible.

The user-visible result is a richer demo and eval dataset: the app can show more support ticket scenarios, and the eval report can demonstrate retrieval hit quality, citation support, unsupported-claim detection, and review-routing behavior across terminal states beyond only `waiting_review`.

## Progress

- [x] (2026-05-31 HKT) Created this todo ExecPlan from the 2026-05-31 portfolio gap audit.
- [ ] Inspect the current KB, demo tickets, eval fixtures, retrieval service, draft generation, and eval scoring.
- [ ] Expand local KB sources into policy, product, troubleshooting, and historical-ticket style documents.
- [ ] Expand demo and eval tickets to include supported, unsupported, ambiguous, stale-policy, conflicting-evidence, and low-confidence scenarios.
- [ ] Add stronger eval baselines beyond the intentionally weak `plain_rag_baseline`.
- [ ] Strengthen retrieval diagnostics and scoring so the eval report can explain why evidence was or was not selected.
- [ ] Add claim-level citation verification or an explicit first version that records claim-to-evidence support.
- [ ] Update README and relevant product docs with the new RAG/eval behavior and validation evidence.

## Surprises & Discoveries

- Observation: The current product demo uses only three UI tickets.
  Evidence: `data/sample_tickets/demo_tickets.json` contains `ticket-1001`, `ticket-1002`, and `ticket-1003`.

- Observation: The current KB is too small to demonstrate real retrieval behavior.
  Evidence: `data/kb/` contains four short Markdown files: account unlock, annual plan seats, refund policy, and export failure troubleshooting.

- Observation: The current eval reports a perfect `graph_v1` score, but the dataset is narrow.
  Evidence: `README.md` documents `graph_v1 final_pass_rate=1.00`, and `data/evals/supportflow_v1.jsonl` currently has 20 examples heavily centered on `waiting_review`.

## Decision Log

- Decision: Start by improving local data and eval quality before adding a hosted vector database.
  Rationale: A local corpus, stronger fixtures, and better metrics make the RAG value clear without adding infrastructure noise.
  Date/Author: 2026-05-31 / Codex

- Decision: Keep deterministic local runs as a first-class path.
  Rationale: Hiring reviewers should be able to run tests and evals without private keys. Optional LLM behavior can be evaluated separately once the deterministic foundation is strong.
  Date/Author: 2026-05-31 / Codex

- Decision: Add stronger baselines before claiming improvement.
  Rationale: The existing `plain_rag_baseline` is intentionally weak. A more competitive portfolio should compare graph behavior against at least one baseline that also has retrieval and basic policy behavior.
  Date/Author: 2026-05-31 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize the new corpus size, scenario coverage, eval metrics, bad-case categories, and any remaining RAG limitations.

## Context and Orientation

The backend is a FastAPI and LangGraph app under `backend/`. Demo tickets live in `data/sample_tickets/demo_tickets.json`. Eval-only tickets live in `data/evals/supportflow_tickets.json`. Eval examples and expected outputs live in `data/evals/supportflow_v1.jsonl`. The local Markdown knowledge base lives in `data/kb/`.

The retrieval service is `backend/app/services/retrieval.py`. It currently tokenizes a query, compares token overlap against Markdown KB documents, adds a category boost when the ticket classification matches a document category, and returns `KBHit` objects. The graph node that calls retrieval is `backend/app/graph/nodes/retrieve_knowledge.py`. Draft generation is in `backend/app/graph/nodes/draft_reply.py` and optional LLM generation is in `backend/app/services/llm.py`.

Offline evals are implemented under `backend/app/evals/`. `backend/app/evals/targets.py` defines target runners, `backend/app/evals/scoring.py` defines metric scoring, and `backend/scripts/run_offline_eval.py` is the CLI entrypoint. The current eval compares `plain_rag_baseline` against `graph_v1`.

In this plan, "RAG" means retrieval-augmented generation: the workflow retrieves support knowledge first, then uses that evidence when drafting or reviewing a customer response. "Claim-level citation" means checking whether specific statements in the answer are supported by specific retrieved evidence spans, instead of only checking whether the answer includes a document ID.

## Plan of Work

First, inspect the current corpus and eval shape. Count KB documents, document categories, demo tickets, eval tickets, expected statuses, expected retrieved docs, and bad-case coverage. Record the findings in this plan before editing data.

Second, expand the KB into a more realistic local corpus. Add Markdown documents that cover billing, account access, product plans, export bugs, security incidents, data loss, unsupported external requests, policy exceptions, and stale or draft policies. Each document must keep the existing front matter fields used by `backend/app/services/kb_ingestion.py`: `doc_id`, `title`, `category`, `source_owner`, `effective_date`, `freshness`, and `policy_severity`.

Third, expand demo tickets. Add enough selectable tickets to make the frontend demo show more than happy path and simple approval. Include scenarios for no evidence, ambiguous category, prompt injection, unsupported claim risk, low confidence, policy conflict, stale policy, and safe finalization if the workflow supports it. Keep the UI dataset small enough to scan, but broad enough to prove behavior.

Fourth, expand eval tickets and references. Add eval examples for terminal statuses beyond `waiting_review`, including `done`, `manual_takeover`, and `failed` where the implementation supports them. Include positive and negative retrieval cases, expected no-evidence cases, expected unsupported-claim cases, expected action types, and expected policy IDs. Do not set references simply to match current output; references should describe desired behavior.

Fifth, add stronger baselines. Keep `plain_rag_baseline` for historical comparison, but add at least one more target such as `rag_with_basic_policy_baseline` or `llm_free_rag_policy_baseline`. This target should perform retrieval, draft with citations, and apply basic review routing so that `graph_v1` is compared against a more credible alternative.

Sixth, strengthen citation and retrieval metrics. The minimum acceptable improvement is to separate citation coverage from citation support and unsupported-claim absence in the report. A stronger implementation should add a `claims` field or derived claim extraction in eval metadata, then check which claims are supported by retrieved snippets. If true claim extraction is deferred, record that as a known limitation in this plan and in the eval report.

Seventh, update docs. README should describe the expanded eval command and the meaning of the new metrics. The portfolio gap audit can remain unchanged unless the implementation changes the recommended priorities.

## Concrete Steps

Run inspection commands from the repository root:

    wc -l data/kb/*.md data/sample_tickets/demo_tickets.json data/evals/supportflow_v1.jsonl data/evals/supportflow_tickets.json
    sed -n '1,220p' backend/app/services/retrieval.py
    sed -n '1,260p' backend/app/evals/scoring.py
    sed -n '1,220p' backend/app/evals/targets.py
    sed -n '1,120p' backend/tests/test_retrieval.py
    sed -n '1,260p' backend/tests/test_offline_eval.py

After adding or changing KB documents, validate metadata from the backend directory:

    cd backend
    uv run --cache-dir /tmp/uv-cache python -m app.services.kb_ingestion

Run backend tests and offline eval from the backend directory:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

Run frontend tests if demo ticket rendering or frontend-facing types change:

    cd frontend
    npm test -- --run
    npm run build

Expected final eval behavior should not be a simple repeat of the current perfect report. The report should show multiple targets, scenario diversity, and meaningful bad-case grouping for weaker baselines. `graph_v1` should pass the agreed thresholds, but the thresholds may need to be less than 1.0 if the expanded dataset intentionally includes not-yet-supported behavior. If thresholds are changed, record the reason in the Decision Log.

## Validation and Acceptance

This plan is complete when all of these are true:

- The local KB contains enough documents to cover multiple source types, not only four policy snippets.
- Demo tickets include non-happy-path scenarios that can be opened in the UI.
- `data/evals/supportflow_v1.jsonl` includes positive and negative cases across retrieval, citation, unsupported claim, review routing, policy, and actions.
- Eval references include more than only `waiting_review` terminal behavior when the implementation supports it.
- At least one stronger baseline exists in addition to `plain_rag_baseline`.
- The eval report includes retrieval hit quality, citation coverage, citation support, unsupported-claim absence, review trigger accuracy, and bad-case grouping by failure stage.
- Backend tests pass.
- Offline eval runs successfully and writes `latest_summary.json`, `bad_cases.jsonl`, `latest_report.md`, and trace events.
- README or relevant docs explain the expanded eval and any remaining limitations.

## Idempotence and Recovery

All data additions should be checked-in source files under `data/kb/`, `data/sample_tickets/`, and `data/evals/`. Generated eval output under `data/evals/results/` remains ignored and can be deleted or regenerated safely.

When adding eval fixtures, prefer additive changes and keep old examples unless a reference is demonstrably wrong. If a new fixture exposes current behavior as weak, either update code in the same implementation branch or record the expected failing stage clearly before tightening CI thresholds.

If retrieval changes cause broad score movement, inspect bad cases before changing thresholds. Thresholds should describe acceptable behavior, not mask regressions.

## Artifacts and Notes

The 2026-05-31 gap audit that motivated this plan is `docs/product-specs/ai-engineer-portfolio-gap-audit-2026-05-31.md`.

The current README documents this expected shape, which is too perfect to be persuasive once the dataset grows:

    target=graph_v1 examples=20 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 citation_support_rate=1.00 review_trigger_accuracy=1.00 final_pass_rate=1.00 bad_cases=0

The implementation should replace or qualify that evidence with a broader report.

## Interfaces and Dependencies

Use the existing Pydantic models in `backend/app/schemas/graph.py` and eval models in `backend/app/evals/schemas.py` unless the new metrics require additional fields. If adding claim-level citation checks, define stable schemas before writing scorer logic. Acceptable names include:

    ClaimSupportResult
    answer_claim: str
    supporting_doc_ids: list[str]
    supported: bool
    reason: str

If adding a stronger baseline, update `TARGET_RUNNERS` in `backend/app/evals/runner.py` and CLI target choices in `backend/scripts/run_offline_eval.py`. Keep all targets runnable offline without API keys.

Do not add a hosted vector database in this plan. If vector retrieval is added, it must be local and reproducible, with dependencies documented in `backend/pyproject.toml` and tests that run without network access.

## Plan Revision Notes

2026-05-31: Initial todo ExecPlan created from the portfolio gap audit. The plan prioritizes local data, retrieval diagnostics, stronger baselines, and eval credibility before hosted retrieval infrastructure.
