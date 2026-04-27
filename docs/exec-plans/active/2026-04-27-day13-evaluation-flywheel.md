# Day 13 Evaluation Flywheel

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The MVP already has an offline eval command. After this change, evals should become a workflow for improving the agent: captured failures can become fixtures, reports identify the failing stage, and CI-friendly thresholds prevent regressions.

This feature demonstrates that the project is not just a one-time demo. It shows a measurable quality loop for classification, retrieval, drafting, policy routing, review decisions, and final disposition.

## Progress

- [x] (2026-04-27) Created this active ExecPlan from `docs/product-specs/ai-agent-engineer-portfolio-roadmap.md`.
- [ ] Inspect current eval dataset, runner, scorer, targets, and generated reports.
- [ ] Add richer eval schema fields for policy flags and action expectations when available.
- [ ] Add stage-level failure reporting.
- [ ] Add a command for promoting a ticket or trace into an eval fixture.
- [ ] Add threshold-based exit codes for CI use.
- [ ] Update docs and this ExecPlan with observed metrics.

## Surprises & Discoveries

- Observation: No implementation discoveries yet.
  Evidence: This plan has only been created.

## Decision Log

- Decision: Keep evals deterministic and local.
  Rationale: The current project uses deterministic fixtures and local knowledge. A local eval loop is easy for hiring reviewers to run and does not require API keys.
  Date/Author: 2026-04-27 / Codex

- Decision: Report failures by workflow stage.
  Rationale: A useful eval does more than produce a score. It should tell the engineer whether classification, retrieval, drafting, policy, review routing, action execution, or finalization failed.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize dataset changes, report format, threshold behavior, and latest metrics.

## Context and Orientation

The offline eval entrypoint is `backend/scripts/run_offline_eval.py`. Eval code lives in `backend/app/evals/`. The dataset is `data/evals/supportflow_v1.jsonl`. Generated results are written under `data/evals/results/`.

The current eval compares at least two targets: `plain_rag_baseline` and `graph_v1`. The target `graph_v1` exercises the LangGraph workflow. The current output reports category accuracy, retrieval hit rate, citation coverage, review trigger accuracy, final pass rate, and bad case count.

An evaluation flywheel means a failure discovered during development can be captured as a fixture, scored consistently, and used to prevent regressions.

## Plan of Work

First, inspect the current eval schemas, runner, scorer, targets, and tests. Record the current output in this ExecPlan before editing.

Second, extend the eval schema only as needed. Add optional fields for expected policy IDs, expected action types, expected action statuses, and expected failure stage. Keep existing fixtures valid.

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

After implementation, run:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py --min-final-pass-rate 1.0

Expected result: the normal eval writes summaries and bad cases. The threshold command exits successfully only when `graph_v1` meets the configured threshold.

Test failure behavior with an intentionally impossible threshold:

    cd backend
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py --min-final-pass-rate 1.1

Expected result: nonzero exit code with a clear message that the threshold was missed.

## Validation and Acceptance

This plan is complete when all of these are true:

- Existing eval fixtures remain valid.
- Bad case output identifies failing workflow stage.
- Threshold flags can fail the command in CI-friendly fashion.
- A candidate fixture promotion command exists and is documented.
- Backend tests cover scoring, thresholds, and promotion behavior.
- Docs show the current eval command and expected output shape.

## Idempotence and Recovery

Eval result generation can overwrite `data/evals/results/latest_summary.json` and `data/evals/results/bad_cases.jsonl`, as it already does. Promotion commands should write candidate files with stable names or explicit overwrite behavior. Do not append to the main eval dataset without a clear command flag.

## Artifacts and Notes

This plan becomes more valuable after Day 11 and Day 10 because policy and action expectations can be measured. It can still start earlier by adding stage-level reports and thresholds to the current eval metrics.

## Interfaces and Dependencies

At completion, the eval CLI should support threshold flags similar to:

    python scripts/run_offline_eval.py --min-final-pass-rate 1.0 --min-citation-coverage 1.0

If policy metrics exist, add:

    --min-policy-trigger-accuracy 1.0

Use Python standard library argument parsing unless the project already has a CLI framework.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created by splitting the AI Agent Engineer portfolio roadmap into implementation milestones.
