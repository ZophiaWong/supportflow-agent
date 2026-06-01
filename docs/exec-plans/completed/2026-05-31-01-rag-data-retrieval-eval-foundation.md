# RAG Data, Retrieval, and Eval Foundation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

SupportFlow currently has a working local knowledge base and offline eval runner, but the data and metrics are too small and too aligned with the current rules to support a strong RAG portfolio claim. After this change, a hiring reviewer should be able to run the offline eval and see a broader set of support scenarios with positive and negative retrieval cases, stronger baselines, and citation checks that make RAG quality visible.

The user-visible result is a richer demo and eval dataset: the app can show more support ticket scenarios, and the eval report can demonstrate retrieval hit quality, citation support, unsupported-claim detection, and review-routing behavior across terminal states beyond only `waiting_review`.

## Progress

- [x] (2026-05-31 HKT) Created this todo ExecPlan from the 2026-05-31 portfolio gap audit.
- [x] (2026-06-01 HKT) Inspected the current KB, demo tickets, eval fixtures, retrieval service, draft generation, and eval scoring.
- [x] (2026-06-01 HKT) Expanded local KB sources into policy, product, troubleshooting, stale/draft policy, security, and incident-style documents.
- [x] (2026-06-01 HKT) Expanded demo and eval tickets to include supported, unsupported, ambiguous, stale-policy, partial-evidence, prompt-injection, action-safety, and low-risk safe-finalization-reference scenarios.
- [x] (2026-06-01 HKT) Added dataset governance metadata to every eval example and created `data/evals/DATASET_CARD.md`.
- [x] (2026-06-01 HKT) Added `backend/scripts/profile_eval_dataset.py` and generated `docs/generated/eval-dataset-profile.md`.
- [x] (2026-06-01 HKT) Added the stronger offline target `rag_policy_baseline` in addition to `plain_rag_baseline` and `graph_v1`.
- [x] (2026-06-01 HKT) Strengthened retrieval diagnostics and markdown eval reporting with metric rates by target.
- [x] (2026-06-01 HKT) Added first-version claim-level citation support checks using explicit `metadata.claims` references.
- [x] (2026-06-01 HKT) Updated README, tests, and interview-prep evidence docs with the new RAG/eval behavior and validation evidence.

## Surprises & Discoveries

- Observation: The current product demo uses only three UI tickets.
  Evidence: `data/sample_tickets/demo_tickets.json` contains `ticket-1001`, `ticket-1002`, and `ticket-1003`.

- Observation: The current KB is too small to demonstrate real retrieval behavior.
  Evidence: `data/kb/` contains four short Markdown files: account unlock, annual plan seats, refund policy, and export failure troubleshooting.

- Observation: The current eval reports a perfect `graph_v1` score, but the dataset is narrow.
  Evidence: `README.md` documents `graph_v1 final_pass_rate=1.00`, and `data/evals/supportflow_v1.jsonl` currently has 20 examples heavily centered on `waiting_review`.

- Observation: The expanded dataset is no longer centered only on `waiting_review`.
  Evidence: `docs/generated/eval-dataset-profile.md` reports 39 eval examples with 31 expected `waiting_review` and 8 expected `done`.

- Observation: The local shell environment had LLM settings enabled, so the first eval attempt made failing network calls before fallback.
  Evidence: `uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py` initially logged DNS failures for `ap2.tryallai.com`; the runner now disables LLM calls by default unless `--enable-llm` is passed.

- Observation: Once no-evidence ticket wording was cleaned up, `graph_v1` failures became concentrated in intended challenge areas.
  Evidence: The final offline eval reports `graph_v1 final_pass_rate=0.67` with 21 bad cases: 8 review-routing misses, 8 expected-status misses, and 5 claim-support misses.

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

- Decision: Add dataset governance before writing final interview-prep answers.
  Rationale: Generated data needs a data card, metadata, and a profile report so interview claims can point to evidence rather than intent.
  Date/Author: 2026-06-01 / Codex

- Decision: Keep challenge cases that lower `graph_v1` from a perfect score.
  Rationale: A non-perfect report is more credible for a portfolio because it exposes conservative routing and claim-support gaps instead of hiding them behind a narrow regression set.
  Date/Author: 2026-06-01 / Codex

- Decision: Make offline eval deterministic by default and require `--enable-llm` for LLM evaluation.
  Rationale: The offline eval should be reproducible without network access or private keys, even if a local `.env` enables LLM generation for manual demos.
  Date/Author: 2026-06-01 / Codex

- Decision: Move interview-prep material to `docs/interview-prep/` after the data and eval artifacts exist.
  Rationale: The user wanted interview material to be organized separately and grounded in generated evidence, not written as speculative answers before the data exists.
  Date/Author: 2026-06-01 / Codex

## Outcomes & Retrospective

Completed on 2026-06-01. The local KB expanded from 4 to 15 Markdown documents, the UI demo set expanded from 3 to 10 tickets, the eval-only ticket set expanded to 36 tickets, and `supportflow_v1.jsonl` expanded to 39 examples with governance metadata and 35 claim-support references.

The generated dataset profile now shows scenario coverage by category, split, evidence condition, intended failure mode, risk level, expected review routing, expected terminal status, and expected retrieval document. The offline eval now compares three targets: `plain_rag_baseline`, `rag_policy_baseline`, and `graph_v1`.

Final validation on 2026-06-01 reported that backend tests pass:

    61 passed

The offline eval command reported:

    target=plain_rag_baseline examples=39 category_accuracy=null retrieval_hit_rate=1.00 citation_coverage=1.00 citation_support_rate=1.00 claim_support_rate=0.82 review_trigger_accuracy=0.21 final_pass_rate=0.21 bad_cases=130
    target=rag_policy_baseline examples=39 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 citation_support_rate=1.00 claim_support_rate=0.85 review_trigger_accuracy=0.87 final_pass_rate=0.21 bad_cases=108
    target=graph_v1 examples=39 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 citation_support_rate=1.00 claim_support_rate=0.85 review_trigger_accuracy=0.79 final_pass_rate=0.67 bad_cases=21

The main remaining RAG limitations are now explicit. `graph_v1` still routes low-risk safe-finalization references to `waiting_review` because customer-facing sends are approval-gated, and claim-level support fails when the draft cites one retrieved document but not every document needed by the expected claims. These are useful next-step candidates rather than hidden failures.

## Context and Orientation

The backend is a FastAPI and LangGraph app under `backend/`. Demo tickets live in `data/sample_tickets/demo_tickets.json`. Eval-only tickets live in `data/evals/supportflow_tickets.json`. Eval examples and expected outputs live in `data/evals/supportflow_v1.jsonl`. The local Markdown knowledge base lives in `data/kb/`. Dataset governance is documented in `data/evals/DATASET_CARD.md`, and the generated profile lives in `docs/generated/eval-dataset-profile.md`.

The retrieval service is `backend/app/services/retrieval.py`. It currently tokenizes a query, compares token overlap against Markdown KB documents, adds a category boost when the ticket classification matches a document category, and returns `KBHit` objects. The graph node that calls retrieval is `backend/app/graph/nodes/retrieve_knowledge.py`. Draft generation is in `backend/app/graph/nodes/draft_reply.py` and optional LLM generation is in `backend/app/services/llm.py`.

Offline evals are implemented under `backend/app/evals/`. `backend/app/evals/targets.py` defines target runners, `backend/app/evals/scoring.py` defines metric scoring, and `backend/scripts/run_offline_eval.py` is the CLI entrypoint. The current eval compares `plain_rag_baseline`, `rag_policy_baseline`, and `graph_v1`.

In this plan, "RAG" means retrieval-augmented generation: the workflow retrieves support knowledge first, then uses that evidence when drafting or reviewing a customer response. "Claim-level citation" means checking whether specific statements in the answer are supported by specific retrieved evidence spans, instead of only checking whether the answer includes a document ID.

## Plan of Work

First, inspect the current corpus and eval shape. Count KB documents, document categories, demo tickets, eval tickets, expected statuses, expected retrieved docs, and bad-case coverage. Record the findings in this plan before editing data.

Second, expand the KB into a more realistic local corpus. Add Markdown documents that cover billing, account access, product plans, export bugs, security incidents, data loss, unsupported external requests, policy exceptions, and stale or draft policies. Each document must keep the existing front matter fields used by `backend/app/services/kb_ingestion.py`: `doc_id`, `title`, `category`, `source_owner`, `effective_date`, `freshness`, and `policy_severity`.

Third, expand demo tickets. Add enough selectable tickets to make the frontend demo show more than happy path and simple approval. Include scenarios for no evidence, ambiguous category, prompt injection, unsupported claim risk, low confidence, policy conflict, stale policy, and safe finalization if the workflow supports it. Keep the UI dataset small enough to scan, but broad enough to prove behavior.

Fourth, expand eval tickets and references. Add eval examples for terminal statuses beyond `waiting_review`, including `done`, `manual_takeover`, and `failed` where the implementation supports them. Include positive and negative retrieval cases, expected no-evidence cases, expected unsupported-claim cases, expected action types, and expected policy IDs. Do not set references simply to match current output; references should describe desired behavior.

Fifth, add stronger baselines. Keep `plain_rag_baseline` for historical comparison, and add `rag_policy_baseline`. This target should perform retrieval, draft with citations, classify tickets, and apply basic review routing so that `graph_v1` is compared against a more credible alternative.

Sixth, strengthen citation and retrieval metrics. The minimum acceptable improvement is to separate citation coverage from citation support and unsupported-claim absence in the report. This implementation adds `metadata.claims` to eval examples, then checks whether each expected claim is backed by a cited retrieved document. This is not a learned natural-language judge; it is an explicit first version of claim-to-evidence support.

Seventh, update docs. README should describe the expanded eval command and the meaning of the new metrics. The portfolio gap audit can remain unchanged unless the implementation changes the recommended priorities. Interview-prep material belongs under `docs/interview-prep/` after the data and eval artifacts exist.

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

Generate or refresh the dataset profile from the repository root:

    python3 backend/scripts/profile_eval_dataset.py

Run frontend tests if demo ticket rendering or frontend-facing types change:

    cd frontend
    npm test -- --run
    npm run build

Expected final eval behavior should not be a simple repeat of the current perfect report. The report should show multiple targets, scenario diversity, and meaningful bad-case grouping for weaker baselines. `graph_v1` should pass the agreed thresholds, but the thresholds may need to be less than 1.0 if the expanded dataset intentionally includes not-yet-supported behavior. If thresholds are changed, record the reason in the Decision Log.

## Validation and Acceptance

This plan is complete when all of these are true:

- The local KB contains enough documents to cover multiple source types, not only four policy snippets. Completed with 15 KB documents.
- Demo tickets include non-happy-path scenarios that can be opened in the UI. Completed with 10 demo tickets.
- `data/evals/supportflow_v1.jsonl` includes positive and negative cases across retrieval, citation, unsupported claim, review routing, policy, and actions. Completed with 39 examples.
- Eval references include more than only `waiting_review` terminal behavior when the implementation supports it or when a challenge case is intentionally exposing a behavior gap. Completed with 31 expected `waiting_review` and 8 expected `done`.
- At least one stronger baseline exists in addition to `plain_rag_baseline`. Completed with `rag_policy_baseline`.
- The eval report includes retrieval hit quality, citation coverage, citation support, claim support, unsupported-claim absence, review trigger accuracy, and bad-case grouping by failure stage.
- Backend tests pass.
- Offline eval runs successfully and writes `latest_summary.json`, `bad_cases.jsonl`, `latest_report.md`, and trace events.
- README and interview-prep docs explain the expanded eval and remaining limitations.

## Idempotence and Recovery

All data additions should be checked-in source files under `data/kb/`, `data/sample_tickets/`, and `data/evals/`. Generated eval output under `data/evals/results/` remains ignored and can be deleted or regenerated safely.

When adding eval fixtures, prefer additive changes and keep old examples unless a reference is demonstrably wrong. If a new fixture exposes current behavior as weak, either update code in the same implementation branch or record the expected failing stage clearly before tightening CI thresholds.

If retrieval changes cause broad score movement, inspect bad cases before changing thresholds. Thresholds should describe acceptable behavior, not mask regressions.

## Artifacts and Notes

The 2026-05-31 gap audit that motivated this plan is `docs/product-specs/ai-engineer-portfolio-gap-audit-2026-05-31.md`.

The interview-prep companion for synthetic data, eval credibility, and job-seeking defensibility is `docs/interview-prep/synthetic-rag-eval-credibility.md`. Use it with `data/evals/DATASET_CARD.md`, `docs/generated/eval-dataset-profile.md`, and `data/evals/results/latest_report.md` when preparing evidence-backed interview answers.

The old README documented this expected shape, which was too perfect to be persuasive once the dataset grew:

    target=graph_v1 examples=20 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 citation_support_rate=1.00 review_trigger_accuracy=1.00 final_pass_rate=1.00 bad_cases=0

The implementation should replace or qualify that evidence with a broader report.

The current broader report intentionally includes challenge failures:

    target=graph_v1 examples=39 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 citation_support_rate=1.00 claim_support_rate=0.85 review_trigger_accuracy=0.79 final_pass_rate=0.67 bad_cases=21

## Interfaces and Dependencies

Use the existing Pydantic models in `backend/app/schemas/graph.py` and eval models in `backend/app/evals/schemas.py` unless the new metrics require additional fields. If adding claim-level citation checks, define stable schemas before writing scorer logic. Acceptable names include:

    ClaimSupportResult
    answer_claim: str
    supporting_doc_ids: list[str]
    supported: bool
    reason: str

If adding another stronger baseline, update `TARGET_RUNNERS` in `backend/app/evals/runner.py` and CLI target choices in `backend/scripts/run_offline_eval.py`. Keep all targets runnable offline without API keys.

Do not add a hosted vector database in this plan. If vector retrieval is added, it must be local and reproducible, with dependencies documented in `backend/pyproject.toml` and tests that run without network access.

## Plan Revision Notes

2026-05-31: Initial todo ExecPlan created from the portfolio gap audit. The plan prioritizes local data, retrieval diagnostics, stronger baselines, and eval credibility before hosted retrieval infrastructure.

2026-06-01: Implemented the RAG/eval foundation and revised the plan to match actual results. The work added dataset governance, profiling, a stronger policy baseline, claim-support checks, deterministic offline eval behavior, expanded KB/tickets/eval data, README updates, and interview-prep docs grounded in generated evidence.

2026-06-01: Addressed pre-archive review notes by recording backend test pass evidence and correcting the target-comparison description before moving this plan to completed.
