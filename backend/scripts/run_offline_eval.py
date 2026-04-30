import argparse
from pathlib import Path

from app.evals.runner import run_offline_eval
from app.evals.schemas import EvalRunSummary

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_PATH = REPO_ROOT / "data" / "evals" / "supportflow_v1.jsonl"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "evals" / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run supportflow-agent offline evals.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--target",
        action="append",
        choices=["plain_rag_baseline", "graph_v1"],
        help="Target to run. May be passed multiple times. Defaults to both targets.",
    )
    parser.add_argument(
        "--threshold-target",
        choices=["plain_rag_baseline", "graph_v1"],
        default="graph_v1",
        help="Target used for threshold checks. Defaults to graph_v1.",
    )
    parser.add_argument("--min-final-pass-rate", type=float)
    parser.add_argument("--min-citation-coverage", type=float)
    parser.add_argument("--min-policy-trigger-accuracy", type=float)
    return parser.parse_args()


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _threshold_misses(
    summaries: list[EvalRunSummary],
    *,
    threshold_target: str,
    min_final_pass_rate: float | None,
    min_citation_coverage: float | None,
    min_policy_trigger_accuracy: float | None,
) -> list[str]:
    thresholds = {
        "final_pass_rate": min_final_pass_rate,
        "citation_coverage": min_citation_coverage,
        "expected_policy_accuracy": min_policy_trigger_accuracy,
    }
    active_thresholds = {
        metric: threshold
        for metric, threshold in thresholds.items()
        if threshold is not None
    }
    if not active_thresholds:
        return []

    summary = next(
        (item for item in summaries if item.target == threshold_target),
        None,
    )
    if summary is None:
        return [f"threshold target {threshold_target!r} was not run"]

    misses: list[str] = []
    for metric, threshold in active_thresholds.items():
        value = getattr(summary, metric)
        if value is None:
            misses.append(
                f"{threshold_target}.{metric} is unavailable; required >= {threshold:.2f}"
            )
        elif value < threshold:
            misses.append(
                f"{threshold_target}.{metric}={value:.2f} missed threshold {threshold:.2f}"
            )
    return misses


def main() -> None:
    args = parse_args()
    summaries = run_offline_eval(args.dataset, args.output_dir, args.target)

    for summary in summaries:
        category_accuracy = (
            "null" if summary.category_accuracy is None else f"{summary.category_accuracy:.2f}"
        )
        print(
            f"target={summary.target} "
            f"examples={summary.num_examples} "
            f"category_accuracy={category_accuracy} "
            f"retrieval_hit_rate={summary.retrieval_hit_rate:.2f} "
            f"citation_coverage={summary.citation_coverage:.2f} "
            f"review_trigger_accuracy={summary.review_trigger_accuracy:.2f} "
            f"final_pass_rate={summary.final_pass_rate:.2f} "
            f"bad_cases={summary.bad_case_count}"
        )

    print(f"wrote {_display_path(args.output_dir / 'latest_summary.json')}")
    print(f"wrote {_display_path(args.output_dir / 'bad_cases.jsonl')}")
    print(f"wrote {_display_path(args.output_dir / 'latest_report.md')}")
    if summaries:
        print(f"wrote {_display_path(Path(summaries[0].trace_events_path))}")

    misses = _threshold_misses(
        summaries,
        threshold_target=args.threshold_target,
        min_final_pass_rate=args.min_final_pass_rate,
        min_citation_coverage=args.min_citation_coverage,
        min_policy_trigger_accuracy=args.min_policy_trigger_accuracy,
    )
    if misses:
        for miss in misses:
            print(f"threshold missed: {miss}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
