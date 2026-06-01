import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_PATH = REPO_ROOT / "data" / "evals" / "supportflow_v1.jsonl"
DEFAULT_DEMO_TICKETS_PATH = REPO_ROOT / "data" / "sample_tickets" / "demo_tickets.json"
DEFAULT_EVAL_TICKETS_PATH = REPO_ROOT / "data" / "evals" / "supportflow_tickets.json"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "docs" / "generated" / "eval-dataset-profile.md"

REQUIRED_METADATA_FIELDS = [
    "scenario",
    "scenario_type",
    "dataset_split",
    "source_type",
    "generation_method",
    "review_status",
    "evidence_condition",
    "intended_failure_mode",
    "risk_level",
]


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text())


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            examples.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc
    if not examples:
        raise ValueError(f"Eval dataset is empty: {path}")
    return examples


def _load_kb_metadata(kb_path: Path) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    for path in sorted(kb_path.glob("*.md")):
        lines = path.read_text().splitlines()
        if not lines or lines[0].strip() != "---":
            raise ValueError(f"{path}: missing front matter block")
        metadata: dict[str, str] = {}
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if not line.strip():
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
        if metadata.get("doc_id") != path.stem:
            raise ValueError(f"{path}: doc_id must match filename stem")
        documents.append(metadata)
    if not documents:
        raise ValueError(f"No KB Markdown files found in {kb_path}")
    return documents


def _metadata(example: dict[str, Any]) -> dict[str, Any]:
    value = example.get("metadata", {})
    return value if isinstance(value, dict) else {}


def _reference(example: dict[str, Any]) -> dict[str, Any]:
    value = example.get("reference_outputs", {})
    return value if isinstance(value, dict) else {}


def _counter_for_metadata(examples: list[dict[str, Any]], key: str) -> Counter[str]:
    return Counter(str(_metadata(example).get(key, "<missing>")) for example in examples)


def _counter_for_reference_category(examples: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(_reference(example).get("category")) for example in examples)


def _counter_for_expected_status(examples: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(_reference(example).get("expected_status")) for example in examples)


def _counter_for_expected_review(examples: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(_reference(example).get("should_trigger_review")) for example in examples)


def _counter_for_expected_docs(examples: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for example in examples:
        doc_ids = _reference(example).get("should_retrieve_doc_ids", [])
        if not doc_ids:
            counter["<no expected retrieval>"] += 1
        else:
            counter.update(doc_ids)
    return counter


def _count_claims(examples: list[dict[str, Any]]) -> int:
    count = 0
    for example in examples:
        claims = _metadata(example).get("claims", [])
        if isinstance(claims, list):
            count += len(claims)
    return count


def _markdown_counter_table(counter: Counter[str]) -> list[str]:
    lines = ["| Value | Count |", "| --- | ---: |"]
    for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {value} | {count} |")
    return lines


def _metadata_issues(
    *,
    examples: list[dict[str, Any]],
    ticket_ids: set[str],
    kb_doc_ids: set[str],
) -> list[str]:
    issues: list[str] = []
    seen_example_ids: set[str] = set()
    for example in examples:
        example_id = str(example.get("id"))
        metadata = _metadata(example)
        reference = _reference(example)
        inputs = example.get("inputs", {})
        ticket_id = inputs.get("ticket_id") if isinstance(inputs, dict) else None

        if example_id in seen_example_ids:
            issues.append(f"{example_id}: duplicate example id")
        seen_example_ids.add(example_id)

        missing_fields = [
            key for key in REQUIRED_METADATA_FIELDS if key not in metadata
        ]
        if missing_fields:
            issues.append(f"{example_id}: missing metadata fields {missing_fields}")

        if ticket_id not in ticket_ids:
            issues.append(
                f"{example_id}: ticket {ticket_id!r} is not in demo or eval tickets"
            )

        for doc_id in reference.get("should_retrieve_doc_ids", []):
            if doc_id not in kb_doc_ids:
                issues.append(f"{example_id}: expected doc {doc_id!r} is not in data/kb")

        claims = metadata.get("claims", [])
        if not isinstance(claims, list):
            issues.append(f"{example_id}: metadata.claims must be a list when present")
            continue
        for index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                issues.append(f"{example_id}: claim #{index + 1} is not an object")
                continue
            supporting_doc_ids = claim.get("supporting_doc_ids", [])
            if not isinstance(supporting_doc_ids, list):
                issues.append(
                    f"{example_id}: claim #{index + 1} supporting_doc_ids must be a list"
                )
                continue
            for doc_id in supporting_doc_ids:
                if doc_id not in kb_doc_ids:
                    issues.append(
                        f"{example_id}: claim #{index + 1} support doc {doc_id!r} is not in data/kb"
                    )
    return issues


def build_profile_markdown(
    *,
    dataset_path: Path,
    demo_tickets_path: Path,
    eval_tickets_path: Path,
) -> tuple[str, list[str]]:
    examples = _load_jsonl(dataset_path)
    demo_tickets = _load_json_list(demo_tickets_path)
    eval_tickets = _load_json_list(eval_tickets_path)
    kb_documents = _load_kb_metadata(REPO_ROOT / "data" / "kb")

    ticket_ids = {ticket["id"] for ticket in demo_tickets + eval_tickets}
    kb_doc_ids = {document["doc_id"] for document in kb_documents}
    issues = _metadata_issues(examples=examples, ticket_ids=ticket_ids, kb_doc_ids=kb_doc_ids)

    kb_category_counter = Counter(document["category"] for document in kb_documents)
    kb_freshness_counter = Counter(document["freshness"] for document in kb_documents)
    kb_severity_counter = Counter(document["policy_severity"] for document in kb_documents)

    lines = [
        "# Eval Dataset Profile",
        "",
        "This generated profile summarizes the local synthetic RAG/eval dataset. It is a coverage and regression profile, not a claim about real production traffic distribution.",
        "",
        "## Scope",
        "",
        f"- Dataset file: `{dataset_path.relative_to(REPO_ROOT)}`",
        f"- KB documents: {len(kb_documents)}",
        f"- Demo tickets: {len(demo_tickets)}",
        f"- Eval-only tickets: {len(eval_tickets)}",
        f"- Eval examples: {len(examples)}",
        f"- Claim-support references: {_count_claims(examples)}",
        "",
        "## KB Documents by Category",
        "",
        *_markdown_counter_table(kb_category_counter),
        "",
        "## KB Documents by Freshness",
        "",
        *_markdown_counter_table(kb_freshness_counter),
        "",
        "## KB Documents by Policy Severity",
        "",
        *_markdown_counter_table(kb_severity_counter),
        "",
        "## Eval Examples by Reference Category",
        "",
        *_markdown_counter_table(_counter_for_reference_category(examples)),
        "",
        "## Eval Examples by Scenario Type",
        "",
        *_markdown_counter_table(_counter_for_metadata(examples, "scenario_type")),
        "",
        "## Eval Examples by Dataset Split",
        "",
        *_markdown_counter_table(_counter_for_metadata(examples, "dataset_split")),
        "",
        "## Eval Examples by Evidence Condition",
        "",
        *_markdown_counter_table(_counter_for_metadata(examples, "evidence_condition")),
        "",
        "## Eval Examples by Intended Failure Mode",
        "",
        *_markdown_counter_table(_counter_for_metadata(examples, "intended_failure_mode")),
        "",
        "## Eval Examples by Risk Level",
        "",
        *_markdown_counter_table(_counter_for_metadata(examples, "risk_level")),
        "",
        "## Expected Review Routing",
        "",
        *_markdown_counter_table(_counter_for_expected_review(examples)),
        "",
        "## Expected Terminal Status",
        "",
        *_markdown_counter_table(_counter_for_expected_status(examples)),
        "",
        "## Expected Retrieval Documents",
        "",
        *_markdown_counter_table(_counter_for_expected_docs(examples)),
        "",
        "## Governance Checks",
        "",
    ]

    if issues:
        lines.append("The following issues need correction before using this dataset as interview evidence:")
        lines.append("")
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("No metadata, ticket-reference, KB-reference, or claim-support reference issues detected.")

    lines.extend(
        [
            "",
            "## Interpretation Notes",
            "",
            "- `source_type=synthetic` means these examples are hand-authored portfolio fixtures, not real customer traffic.",
            "- `challenge` examples intentionally include cases that may expose conservative routing, partial evidence, prompt injection, stale policy, or unsupported requests.",
            "- `safe_auto_finalize_reference` is a reference expectation for low-risk support answers; current graph behavior may still route those cases to review because customer-facing sends are approval-gated.",
            "- Claim-support references map expected answer claims to KB document IDs so citation quality can be checked beyond citation presence.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n", issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile the local SupportFlow eval dataset.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--demo-tickets", type=Path, default=DEFAULT_DEMO_TICKETS_PATH)
    parser.add_argument("--eval-tickets", type=Path, default=DEFAULT_EVAL_TICKETS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate and print the profile without writing the markdown artifact.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown, issues = build_profile_markdown(
        dataset_path=args.dataset,
        demo_tickets_path=args.demo_tickets,
        eval_tickets_path=args.eval_tickets,
    )

    print(markdown)
    if not args.check_only:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown)
        print(f"wrote {args.output.relative_to(REPO_ROOT)}")

    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
