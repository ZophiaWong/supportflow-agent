# Day 13 Evaluation Flywheel

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The MVP already has an offline eval command. After this change, evals should become a workflow for improving the agent: captured failures can become fixtures, reports identify the failing stage, and CI-friendly thresholds prevent regressions.

This feature demonstrates that the project is not just a one-time demo. It shows a measurable quality loop for classification, retrieval, drafting, policy routing, review decisions, and final disposition.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [x] (2026-04-30) Re-verified current eval dataset, runner, scorer, targets, tests, and generated reports before implementation. Current `graph_v1` final pass rate is `1.00` with `0` bad cases.
- [x] (2026-04-30) Added remaining richer eval schema fields for action expectations and expected failure stage. Existing fixtures remain valid.
- [x] (2026-04-30) Added stage-level failure reporting to bad case records, JSON summary breakdowns, and the generated Markdown report.
- [x] (2026-04-30) Added `backend/scripts/promote_eval_case.py` for drafting candidate fixtures from a ticket or trace into `data/evals/candidates/`.
- [x] (2026-04-30) Added threshold-based exit codes for CI use, defaulting threshold checks to `graph_v1`.
- [x] (2026-04-30) Updated tests, README, evaluation design docs, and this ExecPlan with observed metrics.

## Surprises & Discoveries

- Observation: The current eval schema and scoring already cover expected workflow status, expected risk flags, and expected policy IDs.
  Evidence: `backend/app/evals/schemas.py` defines `expected_status`, `expected_risk_flags`, and `expected_policy_ids`; `backend/app/evals/scoring.py` emits corresponding metrics; `backend/tests/test_offline_eval.py` asserts policy and risk metric behavior.

- Observation: The current offline eval is healthy before this plan's implementation starts.
  Evidence: On 2026-04-30, `cd backend && uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py` reported `graph_v1` with `final_pass_rate=1.00` and `bad_cases=0`.

- Observation: Action expectations need stable action types rather than action IDs.
  Evidence: `SupportAction.action_id` is derived from an eval run's generated thread id, so the eval target now exposes `proposed_action_types` and `action_statuses_by_type` in `EvalTargetOutput.metadata`.

- Observation: The plain RAG baseline now fails all 20 examples on workflow-sensitive checks.
  Evidence: The final eval run reported `wrong_review_trigger=20` and `wrong_status=20` for `plain_rag_baseline`; `graph_v1` still reported `0` bad cases.

## Decision Log

- Decision: Keep evals deterministic and local.
  Rationale: The current project uses deterministic fixtures and local knowledge. A local eval loop is easy for hiring reviewers to run and does not require API keys.
  Date/Author: 2026-04-27 / Codex

- Decision: Report failures by workflow stage.
  Rationale: A useful eval does more than produce a score. It should tell the engineer whether classification, retrieval, drafting, policy, review routing, action execution, or finalization failed.
  Date/Author: 2026-04-27 / Codex

- Decision: Treat policy and risk expectation scoring as existing baseline behavior for this plan.
  Rationale: The current dataset, schemas, scorer, and tests already validate expected risk flags, policy IDs, and workflow status. The remaining schema work should focus on action expectations and failure-stage expectations instead of duplicating existing fields.
  Date/Author: 2026-04-30 / Codex

- Decision: Threshold checks default to `graph_v1`.
  Rationale: The baseline target is intentionally weaker and would make `--min-final-pass-rate 1.0` fail even when the workflow target is healthy. The plan's acceptance text says the threshold command should succeed when `graph_v1` meets the configured threshold.
  Date/Author: 2026-04-30 / Codex

- Decision: Promotion writes reviewable candidate files, not the main dataset.
  Rationale: A promoted trace should become a draft fixture that a developer can inspect before making it part of the fixed regression suite. `data/evals/candidates/` is ignored like other local eval output.
  Date/Author: 2026-04-30 / Codex

## Outcomes & Retrospective

Implemented. The eval dataset remains backward-compatible while the schema can now express expected action types, action statuses by action type, and expected failure stage. Bad case records now include `failure_stage`, and generated artifacts include both `bad_case_breakdown_by_stage` in `latest_summary.json` and a `latest_report.md` grouped by target and stage. `backend/scripts/run_offline_eval.py` now supports `--min-final-pass-rate`, `--min-citation-coverage`, `--min-policy-trigger-accuracy`, and `--threshold-target`; the default threshold target is `graph_v1`. `backend/scripts/promote_eval_case.py` drafts candidate JSONL fixtures from a ticket or trace without modifying the main dataset.

Validation on 2026-04-30 passed: backend tests reported `39 passed`; normal offline eval reported `graph_v1 final_pass_rate=1.00` with `0` bad cases; the threshold command with all three thresholds at `1.0` exited successfully; the intentionally impossible `--min-final-pass-rate 1.1` command exited nonzero with a clear threshold-missed message. A promotion CLI smoke wrote `/tmp/supportflow-eval-candidates/candidate-E-001-graph_v1.jsonl`.

## Context and Orientation

The offline eval entrypoint is `backend/scripts/run_offline_eval.py`. Eval code lives in `backend/app/evals/`. The dataset is `data/evals/supportflow_v1.jsonl`. Generated results are written under `data/evals/results/`.

The current eval compares at least two targets: `plain_rag_baseline` and `graph_v1`. The target `graph_v1` exercises the LangGraph workflow. The current output reports category accuracy, retrieval hit rate, citation coverage, review trigger accuracy, final pass rate, and bad case count.

An evaluation flywheel means a failure discovered during development can be captured as a fixture, scored consistently, and used to prevent regressions.

## Plan of Work

First, inspect the current eval schemas, runner, scorer, targets, and tests. Record the current output in this ExecPlan before editing.

Second, extend the eval schema only as needed. The current schema already includes expected workflow status, expected risk flags, and expected policy IDs, so add only the missing optional fields for expected action types, expected action statuses, and expected failure stage. Keep existing fixtures valid.

Third, update scoring so each bad case includes a `failure_stage` field. Stages should be plain names such as `classification`, `retrieval`, `drafting`, `policy`, `review_routing`, `actions`, and `finalization`. If a fixture has multiple failures, either emit multiple bad cases or record all stages in a list.

Fourth, add threshold support to `backend/scripts/run_offline_eval.py`. Accept CLI flags or a config block for thresholds such as minimum final pass rate, minimum citation coverage, and minimum policy-trigger accuracy. The command should exit nonzero when thresholds are missed.

Fifth, add a promotion command. A practical first version can be `backend/scripts/promote_eval_case.py` that accepts a ticket ID or a trace file path and writes a draft JSONL line for review. The command should not silently modify the main dataset unless explicitly asked; it can write to `data/evals/candidates/`.

Sixth, add a Markdown or JSON summary report suitable for portfolio review. It should group bad cases by target and failure stage.

Seventh, update tests for backward compatibility, threshold failures, and stage-level report content.

## Concrete Steps

Inspect current eval code:

    sed -n '1,320p' backend/app/evals/schemas.py
    sed -n '1,360p' backend/app/evals/scoring.py
    sed -n '1,360p' backend/app/evals/runner.py
    sed -n '1,300p' backend/app/evals/targets.py
    sed -n '1,220p' backend/scripts/run_offline_eval.py
    sed -n '1,260p' backend/tests/test_offline_eval.py

Run current eval:

    cd backend
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

Current re-verification output from 2026-04-30:

    target=plain_rag_baseline examples=20 category_accuracy=null retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=0.00 final_pass_rate=0.00 bad_cases=40
    target=graph_v1 examples=20 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=1.00 final_pass_rate=1.00 bad_cases=0
    wrote data/evals/results/latest_summary.json
    wrote data/evals/results/bad_cases.jsonl
    wrote data/evals/results/traces/eval-20260430T080709Z-5a1a33a3/events.jsonl

After implementation, run:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py --min-final-pass-rate 1.0

Expected result: the normal eval writes summaries and bad cases. The threshold command exits successfully only when `graph_v1` meets the configured threshold.

Final implementation output from 2026-04-30:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

    39 passed

    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

    target=plain_rag_baseline examples=20 category_accuracy=null retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=0.00 final_pass_rate=0.00 bad_cases=40
    target=graph_v1 examples=20 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=1.00 final_pass_rate=1.00 bad_cases=0
    wrote data/evals/results/latest_summary.json
    wrote data/evals/results/bad_cases.jsonl
    wrote data/evals/results/latest_report.md
    wrote data/evals/results/traces/eval-20260430T082604Z-dc96ee71/events.jsonl

    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py --min-final-pass-rate 1.0 --min-citation-coverage 1.0 --min-policy-trigger-accuracy 1.0

    target=graph_v1 ... final_pass_rate=1.00 bad_cases=0
    exit code 0

Test failure behavior with an intentionally impossible threshold:

    cd backend
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py --min-final-pass-rate 1.1

Expected result: nonzero exit code with a clear message that the threshold was missed.

Observed result:

    threshold missed: graph_v1.final_pass_rate=1.00 missed threshold 1.10
    exit code 1

## Validation and Acceptance

This plan is complete when all of these are true:

- Existing eval fixtures remain valid.
- Action expectations can be represented in eval fixtures when a case needs them.
- Bad case output identifies failing workflow stage.
- Threshold flags can fail the command in CI-friendly fashion.
- A candidate fixture promotion command exists and is documented.
- Backend tests cover scoring, thresholds, and promotion behavior.
- Docs show the current eval command and expected output shape.

## Idempotence and Recovery

Eval result generation can overwrite `data/evals/results/latest_summary.json`, `data/evals/results/bad_cases.jsonl`, and `data/evals/results/latest_report.md`, as it already does for generated eval artifacts. Promotion commands write candidate files with stable names and refuse to overwrite an existing file unless `--overwrite` is passed. Do not append to the main eval dataset without a clear command flag. The default candidate output directory is `data/evals/candidates/`, which is ignored by git.

## Artifacts and Notes

This plan becomes more valuable after Day 11 and Day 10 because policy and action expectations can be measured. It can still start earlier by adding stage-level reports and thresholds to the current eval metrics.

## Interfaces and Dependencies

At completion, the eval CLI should support threshold flags similar to:

    python scripts/run_offline_eval.py --min-final-pass-rate 1.0 --min-citation-coverage 1.0

If policy metrics exist, add:

    --min-policy-trigger-accuracy 1.0

Use Python standard library argument parsing unless the project already has a CLI framework.

The promotion command accepts these stable interfaces:

    python scripts/promote_eval_case.py --ticket-id ticket-1001
    python scripts/promote_eval_case.py --trace-file ../data/evals/results/traces/<run_id>/events.jsonl --example-id E-001

Both commands write a draft JSONL candidate under `data/evals/candidates/` by default.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.

2026-04-30: Re-verified the plan against the current eval implementation before starting work. The original plan expected policy/risk expectation fields to be added later, but the current code already supports expected status, risk flags, and policy IDs, so the plan now narrows remaining schema work to action expectations and failure-stage expectations. The current offline eval transcript was recorded as the baseline for implementation.

2026-04-30: Implemented the evaluation flywheel plan. The plan now records the final code paths, threshold behavior, candidate promotion behavior, generated report shape, and validation transcripts so a future reader can restart from this document and understand what changed.
