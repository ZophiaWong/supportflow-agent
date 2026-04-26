# Day 7 Retrieval Precision

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

Day 6 expanded the offline evaluation loop to twenty fixed examples and exposed a concrete retrieval weakness: unsupported tickets can retrieve unrelated knowledge base documents because the current lexical retriever matches generic overlapping words. After this change, `supportflow-agent` should return knowledge only when the local Markdown knowledge base contains relevant evidence. Unsupported tickets should produce no retrieved chunks, a low-confidence draft, and a `no_evidence` risk flag in the LangGraph workflow.

This is a narrow quality milestone. It keeps the current local Markdown knowledge base, deterministic rule-based graph, and offline eval command. It does not add embeddings, a vector database, a reranker, real LLM drafting, frontend retrieval controls, or a new multi-agent workflow.

## Progress

- [x] (2026-04-26 13:35Z) Created this active Day 7 ExecPlan after Day 6 was completed and moved to `docs/exec-plans/completed/`.
- [x] (2026-04-26 13:55Z) Improved lexical retrieval precision while preserving supported-ticket recall.
- [x] (2026-04-26 13:55Z) Wired graph retrieval to pass classification category as retrieval context.
- [x] (2026-04-26 13:56Z) Added backend tests for supported retrieval, unsupported no-evidence behavior, and offline eval regression coverage.
- [x] (2026-04-26 13:56Z) Ran backend tests and the offline eval command successfully.
- [x] (2026-04-26 13:58Z) Updated README, retrieval design docs, evaluation design docs, and this ExecPlan with the observed final behavior.

## Surprises & Discoveries

- Observation: There is currently no active ExecPlan after Day 6.
  Evidence: `docs/exec-plans/active/` is empty, while Day 6 lives at `docs/exec-plans/completed/2026-04-26-day6-eval-quality-loop.md`.

- Observation: Day 6 already identified the next quality gap.
  Evidence: `docs/exec-plans/completed/2026-04-26-day6-eval-quality-loop.md` records `unexpected_retrieval` bad cases for examples E-012, E-013, and E-015 because the lexical retriever has no stopword filtering and can match generic words across unrelated KB documents.

- Observation: The current retriever is intentionally simple and has no minimum evidence threshold.
  Evidence: `backend/app/services/retrieval.py` tokenizes query and document text, scores `len(overlap) / len(query_terms)`, and returns any document with at least one overlapping token.

- Observation: The graph retrieval node currently includes the category word inside the free-text query instead of passing category as structured retrieval context.
  Evidence: `backend/app/graph/nodes/retrieve_knowledge.py` builds a query by joining `classification.category`, ticket subject, and ticket preview, then calls `retrieve_knowledge_hits(query)`.

- Observation: A small deterministic lexical change is enough to resolve the Day 6 graph bad cases.
  Evidence: After token filtering, category metadata, and category-aware scoring, `python scripts/run_offline_eval.py` reports `graph_v1 ... final_pass_rate=1.00 bad_cases=0`.

- Observation: The plain baseline benefits from more precise retrieval but remains intentionally workflow-limited.
  Evidence: The same eval run reports `plain_rag_baseline ... retrieval_hit_rate=1.00 ... final_pass_rate=0.30 bad_cases=28`, with remaining failures only in review trigger and status behavior.

## Decision Log

- Decision: Make retrieval precision the Day 7 milestone.
  Rationale: The Day 6 evaluator now produces actionable bad cases, and fixing those cases improves product behavior without broadening scope into real LLMs, durable storage, or frontend changes.
  Date/Author: 2026-04-26 / Codex

- Decision: Keep lexical retrieval and improve it with token filtering, document metadata, category-aware scoring, and a minimum score threshold.
  Rationale: The project is still an MVP with a tiny local KB. A deterministic lexical fix is enough to address the observed failures and keeps the graph workflow inspectable.
  Date/Author: 2026-04-26 / Codex

- Decision: Do not weaken the Day 6 eval fixture expectations to make metrics pass.
  Rationale: The eval bad cases describe real product behavior. Unsupported questions should not receive unrelated citations, so code behavior should change instead of reference data.
  Date/Author: 2026-04-26 / Codex

- Decision: Keep `KBHit` unchanged and store document category only inside the retrieval service.
  Rationale: Category is an implementation detail for scoring. The API and frontend only need the same `doc_id`, `title`, `score`, and `snippet` fields they already consume.
  Date/Author: 2026-04-26 / Codex

- Decision: Leave `plain_rag_baseline` category-free.
  Rationale: The baseline should continue to show what a direct retrieval-and-draft path can do without classification, risk gating, or review routing.
  Date/Author: 2026-04-26 / Codex

## Outcomes & Retrospective

Day 7 is implemented. The retriever now filters weak common tokens, keeps static category metadata for the current four KB documents, accepts optional category context, boosts category matches, and requires stronger evidence when category does not match. The graph retrieval node now passes classifier category separately and no longer injects the category word into the free-text query.

The fixed twenty-example eval now shows `graph_v1` passing every supported metric: retrieval hit rate `1.00`, review trigger accuracy `1.00`, expected status accuracy `1.00`, expected risk flag accuracy `1.00`, final pass rate `1.00`, and `0` bad cases. The plain baseline also reaches retrieval hit rate `1.00`, but it remains at final pass rate `0.30` because it intentionally lacks review trigger and status behavior.

Remaining gaps are intentionally deferred. The KB still uses static document metadata instead of Markdown frontmatter ingestion, retrieval is still lexical rather than embedding-based, and generated eval result files under `data/evals/results/` remain local artifacts rather than checked-in product data.

## Context and Orientation

`supportflow-agent` is a workflow-first AI support app. The backend lives under `backend/`, the React frontend lives under `frontend/`, and fixture data lives under `data/`. The current backend uses FastAPI and LangGraph. LangGraph is the library used here to model the support workflow as ordered nodes: load a ticket, classify it, retrieve knowledge, draft a reply, run a risk gate, optionally interrupt for human review, and finalize or hand off manually.

The local knowledge base is a set of Markdown files under `data/kb/`:

- `data/kb/refund_policy.md` supports billing and refund cases.
- `data/kb/account_unlock.md` supports account lockout and password-reset cases.
- `data/kb/annual_plan_seats.md` supports annual-plan seat questions.
- `data/kb/bug_export_issue.md` supports export failure and export bug cases.

The retriever is `backend/app/services/retrieval.py`. It defines `retrieve_knowledge(query: str, *, category: str | None = None, top_k: int = 3) -> list[KBHit]`. The `KBHit` schema is defined in `backend/app/schemas/graph.py` and currently includes `doc_id`, `title`, `score`, and `snippet`. The graph node `backend/app/graph/nodes/retrieve_knowledge.py` calls the retriever after classification and passes `classification.category` as structured context.

The offline evaluator is under `backend/app/evals/`, with the CLI entrypoint `backend/scripts/run_offline_eval.py`. It reads `data/evals/supportflow_v1.jsonl`, compares `plain_rag_baseline` against `graph_v1`, and writes generated results under `data/evals/results/`. Day 6 established twenty eval examples. Unsupported examples E-012, E-013, and E-015 expect `should_retrieve_doc_ids` to be empty, `expected_status` to be `waiting_review`, and `expected_risk_flags` to include `no_evidence`.

Terms used in this plan:

- Lexical retrieval means matching plain text tokens instead of using embeddings.
- Stopwords are common words such as `the`, `to`, `and`, `can`, and `should` that rarely prove document relevance.
- Support-generic words are words that occur often in support tickets but do not identify a KB article by themselves, such as `customer`, `support`, `request`, `issue`, `details`, and `confirm`.
- No-evidence behavior means the retriever returns an empty list, the draft has no citations and low confidence, and the risk gate adds `no_evidence`.
- Recall means supported tickets still retrieve the relevant document.
- Precision means unsupported tickets do not retrieve unrelated documents.

## Plan of Work

First, inspect the current Day 6 bad cases and retriever behavior before editing. Confirm that `data/evals/results/bad_cases.jsonl` contains `unexpected_retrieval` for E-012, E-013, and E-015, and confirm that `backend/app/services/retrieval.py` returns documents on any single-token overlap. This establishes the before-state.

Second, improve `backend/app/services/retrieval.py` while preserving its simple public role. Add a small, explicit stopword set and a second support-generic token set. Update `_tokenize` so it filters tokens shorter than three characters, stopwords, and support-generic tokens. Keep this list intentionally local and readable; do not add a dependency for tokenization.

Third, add lightweight document metadata inside the retriever. Define a constant mapping document id to category, for example `refund_policy -> billing`, `account_unlock -> account`, `annual_plan_seats -> product`, and `bug_export_issue -> bug`. Include this category in the internal loaded document dictionary. Do not change the public `KBHit` schema unless tests reveal that callers need the category on the API response.

Fourth, extend the retriever function signature to `retrieve_knowledge(query: str, *, category: str | None = None, top_k: int = 3) -> list[KBHit]`. Preserve compatibility by keeping `category` optional and by requiring callers that only pass `query` and `top_k` to keep working.

Fifth, replace the current single-overlap scoring rule with category-aware lexical scoring. The exact scoring can stay simple, but it must be deterministic and easy to explain:

- Compute query terms from the filtered query.
- Compute document terms from the document title, content, and document id words.
- If there is no overlap, skip the document.
- Add a category boost only when `category` is provided and equals the document category.
- Require a minimum evidence threshold before returning a document. The threshold should prevent generic unsupported examples from returning any hit while still allowing the twenty existing supported examples to retrieve their expected documents.
- Sort by descending score and then title for deterministic output.

One acceptable implementation is to score `len(overlap) / max(len(query_terms), 1)`, add `0.35` for a matching category, and require either at least two overlapping terms or a matching category plus at least one strong document term. If local test runs show this still returns unrelated docs for E-012, E-013, or E-015, tighten the rule rather than changing eval references.

Sixth, update `backend/app/graph/nodes/retrieve_knowledge.py`. Build the free-text query from ticket subject and preview only, then call `retrieve_knowledge_hits(query, category=classification.category)`. Do not prepend the category word to the query because category is now structured retrieval context.

Seventh, update `backend/app/evals/targets.py` only where needed. `graph_v1` should pick up the graph node change automatically. `plain_rag_baseline` should remain intentionally plain, with no classification or risk gate. If it currently calls `retrieve_knowledge(query)` directly, leave it as direct lexical retrieval without category context. If the implementation needs a category parameter for compatibility, pass `category=None`.

Eighth, add focused tests. Add tests in `backend/tests/` that call `retrieve_knowledge` directly with supported and unsupported queries. Supported queries should assert the expected document id is present as the top or included hit. Unsupported queries based on E-012, E-013, and E-015 should assert an empty result. Update `backend/tests/test_offline_eval.py` so it verifies `graph_v1` has no `unexpected_retrieval` bad cases and includes `no_evidence` for unsupported eval examples.

Ninth, run backend validation. From `backend/`, run `uv run --cache-dir /tmp/uv-cache pytest` and then `uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py`. Record the observed test count and eval output in this ExecPlan.

Tenth, update documentation after behavior is stable. Update `README.md` offline evaluation output to match the actual Day 7 metrics. Update `docs/design-docs/retrieval-and-kb.md` so retrieval v0 describes the actual token filtering, category boost, and minimum threshold. Update `docs/design-docs/evaluation-and-observability.md` with the new summary and bad-case breakdown. Update this ExecPlan's `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective`.

## Concrete Steps

Work from the repository root unless a command says otherwise.

Inspect the relevant current code and artifacts:

    sed -n '1,260p' backend/app/services/retrieval.py
    sed -n '1,160p' backend/app/graph/nodes/retrieve_knowledge.py
    sed -n '1,260p' backend/app/evals/targets.py
    sed -n '1,220p' data/evals/results/bad_cases.jsonl
    sed -n '1,220p' data/evals/supportflow_v1.jsonl

Before implementing the full fix, it is useful to reproduce the current unsupported retrieval behavior from the backend directory:

    cd backend
    uv run --cache-dir /tmp/uv-cache python -c "from app.services.retrieval import retrieve_knowledge; print([hit.model_dump() for hit in retrieve_knowledge('shipping address for physical welcome kit')])"

After editing the retriever, check representative direct retrieval queries:

    cd backend
    uv run --cache-dir /tmp/uv-cache python -c "from app.services.retrieval import retrieve_knowledge; print([h.doc_id for h in retrieve_knowledge('duplicate charge refund invoice', category='billing')])"
    uv run --cache-dir /tmp/uv-cache python -c "from app.services.retrieval import retrieve_knowledge; print([h.doc_id for h in retrieve_knowledge('shipping address for physical welcome kit', category='other')])"
    uv run --cache-dir /tmp/uv-cache python -c "from app.services.retrieval import retrieve_knowledge; print([h.doc_id for h in retrieve_knowledge('travel visa hotel booking question', category='other')])"

Expected shape after the fix:

    ['refund_policy']
    []
    []

Run backend tests:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

Run the offline eval:

    cd backend
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

Expected high-level result after the fix:

    target=plain_rag_baseline examples=20 category_accuracy=null retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=0.30 final_pass_rate=0.30 bad_cases=28
    target=graph_v1 examples=20 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=1.00 final_pass_rate=1.00 bad_cases=0
    wrote data/evals/results/latest_summary.json
    wrote data/evals/results/bad_cases.jsonl
    wrote data/evals/results/traces/eval-20260426T135614Z-e4ad21d5/events.jsonl

The exact baseline final pass rate and bad-case count may remain worse than `graph_v1` because `plain_rag_baseline` intentionally has no review trigger, expected status handling, or risk flags.

Inspect generated artifacts:

    python -m json.tool data/evals/results/latest_summary.json | sed -n '1,220p'
    sed -n '1,80p' data/evals/results/bad_cases.jsonl

Observed backend validation transcript:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    ...
    collected 28 items
    28 passed in 0.40s

## Validation and Acceptance

The implementation is accepted when all of these behaviors are true:

- `cd backend && uv run --cache-dir /tmp/uv-cache pytest` passes.
- `cd backend && uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py` exits with status 0.
- Supported direct retrieval queries still retrieve the expected KB documents for billing, account, product, and bug/export examples.
- Unsupported direct retrieval queries modeled on E-012, E-013, and E-015 return an empty list.
- `graph_v1` returns no retrieved docs for E-012, E-013, and E-015.
- `graph_v1` risk flags include `no_evidence` for E-012, E-013, and E-015.
- `graph_v1` has no `unexpected_retrieval` bad cases in `data/evals/results/bad_cases.jsonl`.
- `graph_v1` reaches a final pass rate of `1.00` on the current twenty-example dataset unless a newly discovered, documented behavior gap remains.
- `plain_rag_baseline` remains intentionally plain and does not gain classification, risk gate, graph state, or review handling.
- README and design docs describe the actual retrieval behavior and actual eval output after implementation.

Add or update tests so these cases are covered:

- `retrieve_knowledge("duplicate charge refund invoice", category="billing")` includes `refund_policy`.
- `retrieve_knowledge("administrator locked out password reset", category="account")` includes `account_unlock`.
- `retrieve_knowledge("temporary seat increase annual onboarding", category="product")` includes `annual_plan_seats`.
- `retrieve_knowledge("export failed csv report error", category="bug")` includes `bug_export_issue`.
- Unsupported examples modeled on shipping, travel, and unrelated data-loss requests return `[]` when category is `other`.
- `run_graph_v1` on E-012, E-013, and E-015 produces empty `retrieved_doc_ids`, `review_required=True`, and a `no_evidence` risk flag.
- The offline eval runner writes summary, bad cases, and trace events after the retrieval change.

## Idempotence and Recovery

The retrieval change is deterministic and should be safe to run repeatedly. Tests and offline eval may overwrite generated files under `data/evals/results/`, which is expected. Do not check generated eval result files into git.

If the first threshold is too strict and supported examples stop retrieving expected docs, lower the threshold or add category-aware strong-token handling while keeping unsupported examples empty. If the threshold is too loose and unsupported examples still retrieve docs, tighten token filtering or the minimum overlap rule. Do not change `data/evals/supportflow_v1.jsonl` to make the current code pass.

If a document category mapping becomes stale after adding KB files, update the mapping and add tests for the new document. Avoid introducing dynamic frontmatter parsing in this milestone unless it is necessary to keep the implementation simpler than the static mapping.

If `uv run` fails due to cache permissions, keep using `--cache-dir /tmp/uv-cache`. If dependency installation requires network access in a restricted environment, use the existing backend virtualenv if present:

    cd backend
    source /home/poter/resume-pj/supportflow-agent/backend/.venv/bin/activate
    pytest
    python scripts/run_offline_eval.py

## Artifacts and Notes

Current Day 6 bad cases that motivate this plan:

    E-012 graph_v1 unexpected_retrieval retrieved ["annual_plan_seats", "refund_policy", "account_unlock"]
    E-013 graph_v1 unexpected_retrieval retrieved ["annual_plan_seats", "refund_policy", "bug_export_issue"]
    E-015 graph_v1 unexpected_retrieval retrieved ["bug_export_issue", "account_unlock", "refund_policy"]

Current retriever behavior to replace:

    query_terms = _tokenize(query)
    overlap = query_terms & document_terms
    if not overlap:
        continue
    score = round(len(overlap) / len(query_terms), 4)

Target retriever behavior in plain English:

    Ignore weak common terms.
    Prefer documents whose category matches the classifier category.
    Require enough meaningful evidence before returning a hit.
    Return an empty list when the KB does not cover the ticket.

## Interfaces and Dependencies

Keep the existing `KBHit` Pydantic model in `backend/app/schemas/graph.py` unless there is a concrete need to expose category metadata to the API. The preferred public function signature at the end of this milestone is:

    def retrieve_knowledge(
        query: str,
        *,
        category: str | None = None,
        top_k: int = 3,
    ) -> list[KBHit]:
        ...

The graph node in `backend/app/graph/nodes/retrieve_knowledge.py` should call:

    retrieve_knowledge_hits(query, category=classification.category)

The baseline target in `backend/app/evals/targets.py` should remain classification-free. It may continue to call:

    retrieve_knowledge(query)

or explicitly:

    retrieve_knowledge(query, category=None)

Do not add new runtime dependencies for this milestone.
