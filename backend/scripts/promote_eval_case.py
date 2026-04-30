import argparse
import json
import re
from pathlib import Path
from typing import Any

from app.evals.schemas import EvalExample, EvalTargetOutput
from app.evals.targets import run_graph_v1
from app.evals.ticket_fixtures import get_eval_ticket_by_id

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "evals" / "candidates"

SUPPORTED_CATEGORIES = {"billing", "account", "product", "bug", "other"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote a ticket or eval trace into a draft eval fixture candidate."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--ticket-id")
    source.add_argument("--trace-file", type=Path)
    parser.add_argument("--example-id", help="Trace example ID to promote.")
    parser.add_argument(
        "--target",
        choices=["plain_rag_baseline", "graph_v1"],
        default="graph_v1",
        help="Trace target to promote. Defaults to graph_v1.",
    )
    parser.add_argument("--candidate-id")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-") or "candidate"


def _action_status_references(metadata: dict[str, Any]) -> dict[str, str]:
    raw_statuses = metadata.get("action_statuses_by_type")
    if not isinstance(raw_statuses, dict):
        return {}

    references: dict[str, str] = {}
    for action_type, statuses in raw_statuses.items():
        if isinstance(action_type, str) and isinstance(statuses, list) and statuses:
            last_status = statuses[-1]
            if isinstance(last_status, str):
                references[action_type] = last_status
    return references


def _reference_outputs_from_target(output: EvalTargetOutput) -> dict[str, Any]:
    category = output.category if output.category in SUPPORTED_CATEGORIES else "other"
    metadata = dict(output.metadata)
    reference: dict[str, Any] = {
        "category": category,
        "should_retrieve_doc_ids": output.retrieved_doc_ids,
        "should_trigger_review": output.review_required,
        "must_include_citation": bool(output.citations),
        "expected_status": output.status,
    }

    for source_key, reference_key in (
        ("risk_flags", "expected_risk_flags"),
        ("failed_policy_ids", "expected_policy_ids"),
        ("proposed_action_types", "expected_action_types"),
    ):
        value = metadata.get(source_key)
        if isinstance(value, list) and value:
            reference[reference_key] = value

    action_statuses = _action_status_references(metadata)
    if action_statuses:
        reference["expected_action_statuses"] = action_statuses

    return reference


def _reference_outputs_from_trace_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        payload = {}

    category = payload.get("category")
    if category not in SUPPORTED_CATEGORIES:
        category = "other"

    reference: dict[str, Any] = {
        "category": category,
        "should_retrieve_doc_ids": payload.get("retrieved_doc_ids", []),
        "should_trigger_review": bool(payload.get("review_required", False)),
        "must_include_citation": bool(payload.get("citations", [])),
        "expected_status": event.get("status", "failed"),
    }

    for source_key, reference_key in (
        ("risk_flags", "expected_risk_flags"),
        ("failed_policy_ids", "expected_policy_ids"),
        ("proposed_action_types", "expected_action_types"),
    ):
        value = payload.get(source_key)
        if isinstance(value, list) and value:
            reference[reference_key] = value

    action_statuses = _action_status_references(payload)
    if action_statuses:
        reference["expected_action_statuses"] = action_statuses

    return reference


def candidate_from_ticket(ticket_id: str, candidate_id: str | None = None) -> dict[str, Any]:
    get_eval_ticket_by_id(ticket_id)
    example = EvalExample.model_validate(
        {
            "id": candidate_id or f"candidate-{ticket_id}",
            "inputs": {"ticket_id": ticket_id},
            "reference_outputs": {
                "category": "other",
                "should_retrieve_doc_ids": [],
                "should_trigger_review": False,
                "must_include_citation": False,
            },
            "metadata": {},
        }
    )
    output = run_graph_v1(example)
    return {
        "id": candidate_id or f"candidate-{ticket_id}",
        "inputs": {"ticket_id": ticket_id},
        "reference_outputs": _reference_outputs_from_target(output),
        "metadata": {
            "scenario": _safe_id(ticket_id),
            "source": "promote_eval_case:ticket",
            "review_required": True,
        },
    }


def _select_trace_event(
    trace_file: Path,
    *,
    target: str,
    example_id: str | None,
) -> dict[str, Any]:
    events = [
        json.loads(line)
        for line in trace_file.read_text().splitlines()
        if line.strip()
    ]
    matches = [
        event
        for event in events
        if event.get("target") == target
        and (example_id is None or event.get("example_id") == example_id)
    ]
    graph_matches = [event for event in matches if event.get("stage") == "graph_run"]
    matches = graph_matches or matches
    if not matches:
        qualifier = f" and example_id={example_id}" if example_id else ""
        raise ValueError(f"No trace event found for target={target}{qualifier}")
    return matches[-1]


def candidate_from_trace(
    trace_file: Path,
    *,
    target: str,
    example_id: str | None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    event = _select_trace_event(trace_file, target=target, example_id=example_id)
    ticket_id = event["ticket_id"]
    generated_id = candidate_id or f"candidate-{event['example_id']}-{target}"
    return {
        "id": generated_id,
        "inputs": {"ticket_id": ticket_id},
        "reference_outputs": _reference_outputs_from_trace_event(event),
        "metadata": {
            "scenario": _safe_id(generated_id),
            "source": "promote_eval_case:trace",
            "trace_file": str(trace_file),
            "review_required": True,
        },
    }


def write_candidate(
    candidate: dict[str, Any],
    *,
    output_dir: Path,
    overwrite: bool,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{_safe_id(candidate['id'])}.jsonl"
    if path.exists() and not overwrite:
        raise FileExistsError(f"Candidate already exists: {path}")
    path.write_text(json.dumps(candidate, sort_keys=True) + "\n")
    return path


def main() -> None:
    args = parse_args()
    if args.ticket_id:
        candidate = candidate_from_ticket(args.ticket_id, args.candidate_id)
    else:
        candidate = candidate_from_trace(
            args.trace_file,
            target=args.target,
            example_id=args.example_id,
            candidate_id=args.candidate_id,
        )

    path = write_candidate(
        candidate,
        output_dir=args.output_dir,
        overwrite=args.overwrite,
    )
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
