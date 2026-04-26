import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.evals.dataset import load_eval_dataset
from app.evals.schemas import BadCaseRecord, EvalRunSummary
from app.evals.scoring import score_example, summarize_results
from app.evals.targets import run_graph_v1, run_plain_rag_baseline
from app.evals.tracing import TraceWriter

TARGET_RUNNERS = {
    "plain_rag_baseline": run_plain_rag_baseline,
    "graph_v1": run_graph_v1,
}


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _bad_case_breakdown(all_bad_cases: list[BadCaseRecord]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for bad_case in all_bad_cases:
        counts[bad_case.target][bad_case.failure_type] += 1
    return {
        target: dict(sorted(counter.items()))
        for target, counter in sorted(counts.items())
    }


def run_offline_eval(
    dataset_path: Path,
    output_dir: Path,
    targets: list[str] | None = None,
) -> list[EvalRunSummary]:
    examples = load_eval_dataset(dataset_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = f"eval-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
    trace_writer = TraceWriter(run_id=run_id, output_dir=output_dir)
    target_names = targets or list(TARGET_RUNNERS)

    summaries: list[EvalRunSummary] = []
    all_bad_cases: list[BadCaseRecord] = []
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
        "targets": [summary.model_dump(mode="json") for summary in summaries],
    }
    _write_json(output_dir / "latest_summary.json", summary_payload)

    bad_cases_path = output_dir / "bad_cases.jsonl"
    with bad_cases_path.open("w") as handle:
        for bad_case in all_bad_cases:
            handle.write(json.dumps(bad_case.model_dump(mode="json"), sort_keys=True) + "\n")

    return summaries
