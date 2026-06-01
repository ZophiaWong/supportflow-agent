import json
import os
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.evals.dataset import load_eval_dataset
from app.evals.schemas import BadCaseRecord, EvalRunSummary
from app.evals.scoring import score_example, summarize_results
from app.evals.targets import run_graph_v1, run_plain_rag_baseline, run_rag_policy_baseline
from app.evals.tracing import TraceWriter

TARGET_RUNNERS = {
    "plain_rag_baseline": run_plain_rag_baseline,
    "rag_policy_baseline": run_rag_policy_baseline,
    "graph_v1": run_graph_v1,
}


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


@contextmanager
def _offline_llm_setting(enable_llm: bool):
    previous = os.environ.get("SUPPORTFLOW_LLM_ENABLED")
    if not enable_llm:
        os.environ["SUPPORTFLOW_LLM_ENABLED"] = "false"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("SUPPORTFLOW_LLM_ENABLED", None)
        else:
            os.environ["SUPPORTFLOW_LLM_ENABLED"] = previous


def _bad_case_breakdown(all_bad_cases: list[BadCaseRecord]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for bad_case in all_bad_cases:
        counts[bad_case.target][bad_case.failure_type] += 1
    return {
        target: dict(sorted(counter.items()))
        for target, counter in sorted(counts.items())
    }


def _bad_case_stage_breakdown(all_bad_cases: list[BadCaseRecord]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for bad_case in all_bad_cases:
        counts[bad_case.target][bad_case.failure_stage] += 1
    return {
        target: dict(sorted(counter.items()))
        for target, counter in sorted(counts.items())
    }


def _write_markdown_report(
    path: Path,
    *,
    summaries: list[EvalRunSummary],
    bad_cases: list[BadCaseRecord],
) -> None:
    cases_by_target_stage: dict[tuple[str, str], list[BadCaseRecord]] = defaultdict(list)
    for bad_case in bad_cases:
        cases_by_target_stage[(bad_case.target, bad_case.failure_stage)].append(bad_case)

    lines = [
        "# Offline Eval Report",
        "",
        "## Summary",
        "",
        "| Target | Examples | Final pass rate | Bad cases |",
        "| --- | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        lines.append(
            f"| {summary.target} | {summary.num_examples} | "
            f"{summary.final_pass_rate:.2f} | {summary.bad_case_count} |"
        )

    lines.extend(
        [
            "",
            "## Metric Rates",
            "",
            "| Target | Category | Retrieval hit | Citation coverage | Citation support | Claim support | Review routing | Unsupported claim absent | Expected status | Policy IDs | Action types | Final pass |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for summary in summaries:
        category_accuracy = (
            "n/a" if summary.category_accuracy is None else f"{summary.category_accuracy:.2f}"
        )
        claim_support = (
            "n/a" if summary.claim_support_rate is None else f"{summary.claim_support_rate:.2f}"
        )
        expected_status = (
            "n/a"
            if summary.expected_status_accuracy is None
            else f"{summary.expected_status_accuracy:.2f}"
        )
        expected_policy = (
            "n/a"
            if summary.expected_policy_accuracy is None
            else f"{summary.expected_policy_accuracy:.2f}"
        )
        expected_action_type = (
            "n/a"
            if summary.expected_action_type_accuracy is None
            else f"{summary.expected_action_type_accuracy:.2f}"
        )
        lines.append(
            f"| {summary.target} | {category_accuracy} | "
            f"{summary.retrieval_hit_rate:.2f} | {summary.citation_coverage:.2f} | "
            f"{summary.citation_support_rate:.2f} | {claim_support} | "
            f"{summary.review_trigger_accuracy:.2f} | "
            f"{summary.unsupported_claim_absence:.2f} | {expected_status} | "
            f"{expected_policy} | {expected_action_type} | "
            f"{summary.final_pass_rate:.2f} |"
        )

    lines.extend(["", "## Bad Cases by Stage", ""])
    if not bad_cases:
        lines.append("No bad cases.")
    else:
        for (target, stage), cases in sorted(cases_by_target_stage.items()):
            lines.append(f"### {target}: {stage}")
            lines.append("")
            for case in cases:
                lines.append(f"- {case.example_id}: {case.failure_type} - {case.notes}")
            lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n")


def run_offline_eval(
    dataset_path: Path,
    output_dir: Path,
    targets: list[str] | None = None,
    *,
    enable_llm: bool = False,
) -> list[EvalRunSummary]:
    examples = load_eval_dataset(dataset_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = f"eval-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
    trace_writer = TraceWriter(run_id=run_id, output_dir=output_dir)
    target_names = targets or list(TARGET_RUNNERS)

    summaries: list[EvalRunSummary] = []
    all_bad_cases: list[BadCaseRecord] = []
    with _offline_llm_setting(enable_llm):
        for target in target_names:
            if target not in TARGET_RUNNERS:
                raise ValueError(f"Unknown eval target: {target}")

            runner = TARGET_RUNNERS[target]
            target_results = [
                score_example(example, runner(example, trace_writer))
                for example in examples
            ]
            all_bad_cases.extend(
                bad_case
                for result in target_results
                for bad_case in result.bad_cases
            )
            summaries.append(
                summarize_results(
                    run_id=run_id,
                    dataset_name=dataset_path.stem,
                    target=target,
                    results=target_results,
                    trace_events_path=str(trace_writer.events_path),
                )
            )

    summary_payload = {
        "run_id": run_id,
        "dataset": dataset_path.stem,
        "num_examples": len(examples),
        "generated_at": datetime.now(UTC).isoformat(),
        "trace_events_path": str(trace_writer.events_path),
        "bad_case_breakdown": _bad_case_breakdown(all_bad_cases),
        "bad_case_breakdown_by_stage": _bad_case_stage_breakdown(all_bad_cases),
        "targets": [summary.model_dump(mode="json") for summary in summaries],
    }
    _write_json(output_dir / "latest_summary.json", summary_payload)

    bad_cases_path = output_dir / "bad_cases.jsonl"
    with bad_cases_path.open("w") as handle:
        for bad_case in all_bad_cases:
            handle.write(json.dumps(bad_case.model_dump(mode="json"), sort_keys=True) + "\n")

    _write_markdown_report(
        output_dir / "latest_report.md",
        summaries=summaries,
        bad_cases=all_bad_cases,
    )

    return summaries
