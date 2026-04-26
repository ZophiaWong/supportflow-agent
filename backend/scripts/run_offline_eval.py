import argparse
from pathlib import Path

from app.evals.runner import run_offline_eval

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
    return parser.parse_args()


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


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
    if summaries:
        print(f"wrote {_display_path(Path(summaries[0].trace_events_path))}")


if __name__ == "__main__":
    main()
