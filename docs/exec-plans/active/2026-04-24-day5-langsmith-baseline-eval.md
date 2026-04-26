# Day 5 Tracing and Offline Baseline Evaluation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

Day 5 adds the first evaluation and observability loop for `supportflow-agent`. After this change, a developer can run one backend command and compare the plain retrieval-and-draft baseline against the LangGraph workflow on a fixed, small dataset. The comparison should make the workflow advantage visible: `graph_v1` has classification and risk-gate behavior, while `plain_rag_baseline` does not.

The goal is not to build a perfect evaluator or production analytics system. The goal is a deterministic, local skeleton that proves the project can measure classification, retrieval, citation, and review-trigger behavior, while also writing trace records that explain what happened during each evaluated run.

## Progress

- [x] (2026-04-26 13:05Z) Replaced the Day 5 goal stub with a `docs/PLANS.md`-compliant ExecPlan.
- [ ] Add the fixed three-case eval dataset at `data/evals/supportflow_v1.jsonl`.
- [ ] Add backend eval schemas, target runners, deterministic scorers, local tracing, and result writers.
- [ ] Add the CLI script at `backend/scripts/run_offline_eval.py`.
- [ ] Add backend tests for dataset loading, scoring, target comparison, and artifact writing.
- [ ] Update README and relevant design docs with the offline eval command and expected output.
- [ ] Run backend tests and the offline eval command, then record evidence in this plan.

## Surprises & Discoveries

- Observation: The active Day 5 file only contained a short goal statement and did not yet meet the living ExecPlan requirements.
  Evidence: `docs/exec-plans/active/2026-04-24-day5-langsmith-baseline-eval.md` had only a `## Goal` section before this revision.

- Observation: The current workflow is deterministic and does not call an external LLM, which makes a local offline eval skeleton stable and cheap to run.
  Evidence: graph nodes under `backend/app/graph/nodes/` use rule-based classification, lexical retrieval, template drafting, and deterministic risk rules.

- Observation: `langsmith` is already present in `backend/uv.lock`, but it is not a direct dependency in `backend/pyproject.toml`.
  Evidence: `rg "langsmith" backend/uv.lock` finds version `0.7.34`; `backend/pyproject.toml` does not list `langsmith` in direct dependencies.

- Observation: The three current demo tickets support the planned fixed dataset expectations.
  Evidence: local graph inspection showed `ticket-1001` and `ticket-1002` interrupt with `review_required=True`, while `ticket-1003` finalizes with `review_required=False`; baseline retrieval finds the expected lead doc for each ticket.

## Decision Log

- Decision: Use three demo-aligned eval examples for Day 5.
  Rationale: The existing demo tickets and KB documents are stable, deterministic, and enough to show the baseline lacks workflow behavior. Expanding to 20 or more cases belongs after the skeleton exists.
  Date/Author: 2026-04-26 / Codex + user

- Decision: Make local JSONL tracing required and LangSmith tracing optional.
  Rationale: The eval command must work offline without credentials or network access. Optional LangSmith hooks can be added when environment variables are present, but they must not be required for success.
  Date/Author: 2026-04-26 / Codex + user

- Decision: Produce CLI summary and bad-case artifacts instead of adding an API endpoint or frontend UI.
  Rationale: Day 5 is an offline engineering loop. A CLI with persisted JSON artifacts is the smallest useful interface and avoids adding product surface area before there is a real eval history.
  Date/Author: 2026-04-26 / Codex + user

- Decision: Keep `plain_rag_baseline` intentionally simple: retrieve, draft, and cite without classification, risk gate, review interrupt, or graph state.
  Rationale: The comparison should reveal what the graph adds. Adding workflow behavior to the baseline would blur the point of the baseline.
  Date/Author: 2026-04-26 / Codex

- Decision: Use local tracing only in the first implementation, while reserving `trace_url` and `langsmith_enabled` fields for later LangSmith integration.
  Rationale: Importing LangSmith directly would require turning a transitive lockfile package into a direct dependency. Day 5 only needs a reliable offline skeleton, so dependency churn is unnecessary.
  Date/Author: 2026-04-26 / Codex + user

- Decision: Recreate trace artifacts under a unique per-run directory instead of appending to long-lived trace files.
  Rationale: A run-scoped trace directory makes repeated evals deterministic and easy to inspect. `latest_summary.json` can point to the current `run_id` without mixing old and new events.
  Date/Author: 2026-04-26 / Codex + user

## Outcomes & Retrospective

Not yet implemented. At completion, record whether the CLI compares both targets, whether artifacts were written, which metrics demonstrate the `graph_v1` advantage, and any gaps left for a later larger dataset or real LangSmith experiment.

## Context and Orientation

The repository currently contains a deterministic FastAPI and LangGraph MVP. The backend lives under `backend/`, the React frontend lives under `frontend/`, and development data lives under `data/`.

The existing graph is built in `backend/app/graph/builder.py`. It runs these nodes in order: load ticket context, classify ticket, retrieve knowledge, draft reply, risk gate, optionally interrupt for human review, apply review decision, finalize reply, or manual takeover. The graph state shape is defined in `backend/app/graph/state.py`.

The current API route `backend/app/api/v1/runs.py` runs the graph for a real ticket id and records major timeline events through `backend/app/services/run_event_store.py`. Day 5 should not depend on the FastAPI route layer to run evals. The eval runner should invoke service and graph code directly so it stays fast, local, and easy to test.

The existing demo tickets are in `data/sample_tickets/demo_tickets.json`. The existing Markdown knowledge base is in `data/kb/`. The lexical retriever is `backend/app/services/retrieval.py`, and the ticket loader is `backend/app/services/ticket_repo.py`.

Terms used in this plan:

- `plain_rag_baseline` means a simple pipeline that loads a ticket, retrieves matching KB snippets, and drafts a response with citations. It has no classification, no graph routing, no risk gate, and no human review.
- `graph_v1` means the existing LangGraph workflow from `backend/app/graph/builder.py`.
- An eval example is one JSONL line containing an input ticket id and reference expectations.
- A metric is a deterministic pass/fail or numeric score computed from actual target output and reference expectations.
- A bad case is a JSONL record explaining one failed metric for one target on one example.
- A trace event is a local JSON object recording a stage of execution so a developer can inspect what happened without stepping through code.

## Plan of Work

First, add a fixed dataset at `data/evals/supportflow_v1.jsonl`. Use the existing three tickets: `ticket-1001`, `ticket-1002`, and `ticket-1003`. Each example should include an `id`, `inputs.ticket_id`, `reference_outputs.category`, `reference_outputs.should_retrieve_doc_ids`, `reference_outputs.should_trigger_review`, `reference_outputs.must_include_citation`, and metadata such as scenario and risk level. The expected categories should match the existing deterministic classifier. The expected retrieved document ids should match the current KB: `refund_policy` for the refund case, `account_unlock` for the password lockout case, and `annual_plan_seats` for the plan seats case.

Second, add an eval package under `backend/app/evals/`. Keep it small and explicit. Create Pydantic schemas for `EvalExample`, `EvalReferenceOutputs`, `EvalTargetOutput`, `EvalMetricResult`, `EvalExampleResult`, `EvalRunSummary`, and `BadCaseRecord`. Keep these models focused on this milestone and do not introduce database models.

Third, implement target runners. `plain_rag_baseline` should load the ticket through `get_ticket_by_id`, build a retrieval query from the ticket subject and preview, call `retrieve_knowledge`, and produce a template draft with citations from retrieved docs. Its output should set `category` to `None`, `category_supported` to `False`, and `review_required` to `False`. `graph_v1` should call `get_support_graph().invoke(...)` with a unique eval thread id per example. If the graph returns an interrupt, convert that into `status="waiting_review"` and `review_required=True` without auto-resuming. If the graph finalizes, return the final answer and citations. Both runners must return the same `EvalTargetOutput` contract: `target`, `example_id`, `ticket_id`, `status`, `category`, `category_supported`, `retrieved_doc_ids`, `citations`, `answer`, `review_required`, `trace_url`, and `metadata`. Use unique eval thread ids so cached LangGraph checkpoint state does not leak across examples; clear Day 4 pending-review and timeline stores only in tests that call API helpers.

Fourth, implement deterministic scorers. Compute category accuracy, retrieval hit rate, citation coverage, review trigger accuracy, and a composite final pass. The composite final pass should require retrieval hit, citation coverage, and review trigger correctness for both targets. For `graph_v1`, it should also require category correctness. For `plain_rag_baseline`, record `category_supported=false` and `category_accuracy=null` rather than pretending it performed classification. Keep summary fields shape-stable across targets, using `null` for unsupported metrics.

Fifth, implement local tracing. Add a small trace writer that creates JSONL files under `data/evals/results/traces/<run_id>/events.jsonl`, where `run_id` is generated once per CLI invocation. It should record one or more events per target and example with fields including timestamp, run id, example id, target, ticket id, stage name, inputs summary, retrieved doc ids, category if present, review requirement, status, `trace_url`, and `langsmith_enabled=false`. Do not import LangSmith in this v1 skeleton. The reserved fields keep the artifact shape ready for later LangSmith integration without making external tracing part of Day 5.

Sixth, add `backend/scripts/run_offline_eval.py`. The script should resolve paths from its own location rather than from the caller's current working directory. Use `REPO_ROOT = Path(__file__).resolve().parents[2]`, because the script lives at `backend/scripts/run_offline_eval.py`. The default dataset path is `REPO_ROOT / "data/evals/supportflow_v1.jsonl"` and the default output directory is `REPO_ROOT / "data/evals/results"`. It should run both targets, write `latest_summary.json`, write `bad_cases.jsonl`, create trace events under `traces/<run_id>/events.jsonl`, and print a concise summary showing each target, number of examples, category accuracy where applicable, retrieval hit rate, citation coverage, review trigger accuracy, final pass rate, and bad-case count.

Seventh, add tests under `backend/tests/`. Include tests that dataset loading validates all three cases, scoring produces expected failures for a baseline missing review behavior, `graph_v1` scores better than `plain_rag_baseline` on review trigger accuracy for the fixed dataset, and artifact writing creates summary, bad-case, and trace files in a temporary output directory.

Finally, update README and `docs/design-docs/evaluation-and-observability.md` only as needed to reflect the actual Day 5 command and outputs. Do not add frontend eval UI in this milestone.

## Concrete Steps

Work from the repository root unless a command says otherwise.

Inspect the current graph and fixtures:

    sed -n '1,260p' backend/app/graph/builder.py
    sed -n '1,260p' backend/app/graph/state.py
    sed -n '1,260p' backend/app/services/retrieval.py
    sed -n '1,260p' data/sample_tickets/demo_tickets.json

After adding the eval package and CLI, run backend tests:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

Run the offline eval:

    cd backend
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

Expected output should resemble this shape, with exact values determined by the implemented scorers:

    target=plain_rag_baseline examples=3 final_pass_rate=... review_trigger_accuracy=... bad_cases=...
    target=graph_v1 examples=3 final_pass_rate=... review_trigger_accuracy=... bad_cases=...
    wrote data/evals/results/latest_summary.json
    wrote data/evals/results/bad_cases.jsonl
    wrote data/evals/results/traces/<run_id>/events.jsonl

After implementation, update this section with the real transcript and the exact test count.

## Validation and Acceptance

The implementation is accepted when all of these behaviors are true:

- `cd backend && uv run --cache-dir /tmp/uv-cache pytest` passes.
- `cd backend && uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py` exits with status 0.
- `data/evals/results/latest_summary.json` exists and contains summaries for `plain_rag_baseline` and `graph_v1`.
- `data/evals/results/bad_cases.jsonl` exists and contains at least one baseline bad case caused by missing workflow behavior, such as wrong review trigger behavior.
- `data/evals/results/traces/<run_id>/events.jsonl` contains local JSONL trace events for both targets, and `latest_summary.json` includes the same `run_id`.
- The summary demonstrates that `graph_v1` has workflow metrics that the baseline cannot fully satisfy, especially review-trigger accuracy and classification coverage.
- Running the eval repeatedly overwrites `latest_summary.json` and `bad_cases.jsonl` safely and creates a new run-scoped trace directory each time.

## Idempotence and Recovery

The eval command must be safe to run repeatedly. It should create `data/evals/results/` if missing and should not mutate demo tickets, KB files, graph code, or frontend files.

If a run fails halfway, delete only generated files under `data/evals/results/` and rerun the command. Do not delete `data/evals/supportflow_v1.jsonl`, because that is the fixed source dataset.

If LangSmith credentials are present, this v1 implementation should ignore them. Local tracing is the only required tracing behavior in Day 5, and every trace event should record `langsmith_enabled=false`.

If graph checkpoint state leaks between tests, make eval thread ids unique. Clearing Day 4 in-memory pending-review or timeline stores is only relevant for tests that call API helpers, because those stores do not clear cached LangGraph checkpoints.

## Artifacts and Notes

Planned dataset line shape:

    {"id":"E-001","inputs":{"ticket_id":"ticket-1001"},"reference_outputs":{"category":"billing","should_retrieve_doc_ids":["refund_policy"],"should_trigger_review":true,"must_include_citation":true},"metadata":{"scenario":"refund","risk_level":"high"}}

Planned summary shape:

    {
      "dataset": "supportflow_v1",
      "num_examples": 3,
      "targets": [
        {
          "target": "plain_rag_baseline",
          "num_examples": 3,
          "category_supported": false,
          "category_accuracy": null,
          "retrieval_hit_rate": 1.0,
          "citation_coverage": 1.0,
          "review_trigger_accuracy": 0.33,
          "final_pass_rate": 0.33,
          "bad_case_count": 2
        },
        {
          "target": "graph_v1",
          "num_examples": 3,
          "category_supported": true,
          "category_accuracy": 1.0,
          "retrieval_hit_rate": 1.0,
          "citation_coverage": 1.0,
          "review_trigger_accuracy": 1.0,
          "final_pass_rate": 1.0,
          "bad_case_count": 0
        }
      ]
    }

The numbers above are target expectations, not guaranteed until implementation runs against the actual graph and KB. If actual deterministic behavior differs, update the dataset expectations or document the discovered gap rather than hiding the mismatch.

Planned bad-case shape:

    {
      "example_id": "E-001",
      "target": "plain_rag_baseline",
      "failure_type": "wrong_review_trigger",
      "expected": {"should_trigger_review": true},
      "actual": {"review_required": false},
      "trace_url": null,
      "notes": "Baseline has no risk gate, so it cannot trigger review for sensitive refund cases."
    }

## Interfaces and Dependencies

Add `backend/app/evals/schemas.py` with Pydantic models:

- `EvalInputs`
- `EvalReferenceOutputs`
- `EvalExample`
- `EvalTargetOutput`
- `EvalMetricResult`
- `EvalExampleResult`
- `EvalRunSummary`
- `BadCaseRecord`

`EvalTargetOutput` must include these fields:

- `target: Literal["plain_rag_baseline", "graph_v1"]`
- `example_id: str`
- `ticket_id: str`
- `status: Literal["done", "waiting_review", "manual_takeover", "failed"]`
- `category: str | None`
- `category_supported: bool`
- `retrieved_doc_ids: list[str]`
- `citations: list[str]`
- `answer: str | None`
- `review_required: bool`
- `trace_url: str | None`
- `metadata: dict[str, object]`

Add `backend/app/evals/dataset.py` with:

- `load_eval_dataset(path: Path) -> list[EvalExample]`

Add `backend/app/evals/targets.py` with:

- `run_plain_rag_baseline(example: EvalExample, trace_writer: TraceWriter | None = None) -> EvalTargetOutput`
- `run_graph_v1(example: EvalExample, trace_writer: TraceWriter | None = None) -> EvalTargetOutput`

Add `backend/app/evals/scoring.py` with:

- `score_example(example: EvalExample, output: EvalTargetOutput) -> EvalExampleResult`
- `summarize_results(dataset_name: str, target: str, results: list[EvalExampleResult]) -> EvalRunSummary`

Add `backend/app/evals/tracing.py` with:

- `TraceWriter`
- `is_langsmith_enabled() -> bool`

Add `backend/app/evals/runner.py` with:

- `run_offline_eval(dataset_path: Path, output_dir: Path, targets: list[str] | None = None) -> list[EvalRunSummary]`

Add `backend/scripts/run_offline_eval.py` as the CLI entrypoint. It may use the standard library `argparse`; do not add a CLI framework.

Do not import LangSmith or change `backend/pyproject.toml` in this Day 5 skeleton. The local trace schema should include `trace_url` and `langsmith_enabled` so a later change can add LangSmith without changing downstream result readers.

## Assumptions and Defaults

Day 5 stays backend-only except for documentation. There is no frontend `/evals` page in this milestone.

The dataset uses the three existing demo tickets. New synthetic tickets are out of scope for this implementation.

Evaluation is deterministic and code-based. No LLM judge is used.

Generated eval result artifacts under `data/evals/results/` are development artifacts. Keep the source dataset checked in; generated results may be overwritten by future runs.

Revision note: 2026-04-26. Replaced the Day 5 goal stub with a full living ExecPlan based on the agreed scope: three demo-aligned eval cases, CLI summary and bad cases, required local JSONL tracing, and optional LangSmith integration only when configured.

Revision note: 2026-04-26. Tightened the implementation contract after review: `EvalTargetOutput` fields are now explicit, unsupported baseline category accuracy is `null`, trace files are run-scoped under `traces/<run_id>/events.jsonl`, CLI paths are resolved from the script location, LangSmith imports are deferred to a later change, and graph checkpoint isolation relies on unique eval thread ids.
