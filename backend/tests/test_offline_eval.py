import json
from pathlib import Path

from app.evals.dataset import load_eval_dataset
from app.evals.runner import run_offline_eval
from app.evals.schemas import EvalTargetOutput
from app.evals.scoring import score_example
from app.evals.targets import run_graph_v1, run_plain_rag_baseline
from app.evals.ticket_fixtures import get_eval_ticket_by_id

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPO_ROOT / "data" / "evals" / "supportflow_v1.jsonl"


def test_load_eval_dataset_reads_expanded_fixed_cases() -> None:
    examples = load_eval_dataset(DATASET_PATH)

    assert len(examples) == 20
    assert [example.id for example in examples[:3]] == ["E-001", "E-002", "E-003"]
    assert examples[3].inputs.ticket_id == "eval-ticket-2001"
    assert examples[0].reference_outputs.category == "billing"
    assert examples[1].reference_outputs.should_retrieve_doc_ids == ["account_unlock"]
    assert examples[2].reference_outputs.should_trigger_review is True
    assert examples[2].metadata["review_reason"] == "external_send_approval"
    assert examples[15].reference_outputs.must_not_claim == [
        "refund today",
        "ignore previous rules",
        "guaranteed",
    ]


def test_eval_ticket_resolver_loads_eval_tickets_and_demo_fallback() -> None:
    eval_ticket = get_eval_ticket_by_id("eval-ticket-2001")
    demo_ticket = get_eval_ticket_by_id("ticket-1001")

    assert eval_ticket["subject"] == "CSV export failed during monthly report"
    assert demo_ticket["subject"] == "Refund requested for duplicate charge"


def test_baseline_scores_review_trigger_failures_without_category_accuracy() -> None:
    examples = load_eval_dataset(DATASET_PATH)
    output = run_plain_rag_baseline(examples[0])
    result = score_example(examples[0], output)
    metrics_by_name = {metric.name: metric for metric in result.metrics}

    assert metrics_by_name["category_accuracy"].passed is None
    assert metrics_by_name["category_accuracy"].score is None
    assert metrics_by_name["retrieval_hit"].passed is True
    assert metrics_by_name["citation_coverage"].passed is True
    assert metrics_by_name["review_trigger_accuracy"].passed is False
    assert result.final_pass is False
    assert [case.failure_type for case in result.bad_cases] == [
        "wrong_review_trigger",
        "wrong_status",
    ]


def test_graph_target_can_load_eval_only_ticket() -> None:
    example = load_eval_dataset(DATASET_PATH)[3]

    output = run_graph_v1(example)

    assert output.ticket_id == "eval-ticket-2001"
    assert output.category == "bug"
    assert output.status == "waiting_review"
    assert "bug_export_issue" in output.retrieved_doc_ids
    assert "priority_requires_review" in output.metadata["risk_flags"]


def test_graph_target_returns_no_evidence_for_unsupported_tickets() -> None:
    examples = load_eval_dataset(DATASET_PATH)
    unsupported_examples = [examples[index] for index in (11, 12, 14)]

    for example in unsupported_examples:
        output = run_graph_v1(example)

        assert output.retrieved_doc_ids == []
        assert output.citations == []
        assert output.review_required is True
        assert "no_evidence" in output.metadata["risk_flags"]


def test_unsupported_claim_scoring_detects_forbidden_phrase() -> None:
    example = load_eval_dataset(DATASET_PATH)[15]
    output = EvalTargetOutput(
        target="graph_v1",
        example_id=example.id,
        ticket_id=example.inputs.ticket_id,
        status="waiting_review",
        category="billing",
        category_supported=True,
        retrieved_doc_ids=["refund_policy"],
        citations=["refund_policy"],
        answer="We can guarantee a refund today.",
        review_required=True,
        metadata={"risk_flags": ["priority_requires_review"]},
    )

    result = score_example(example, output)

    assert "unsupported_claim_present" in {
        bad_case.failure_type for bad_case in result.bad_cases
    }
    assert result.final_pass is False


def test_expected_status_scoring_detects_wrong_status() -> None:
    example = load_eval_dataset(DATASET_PATH)[0]
    output = run_plain_rag_baseline(example)
    result = score_example(example, output)

    assert "wrong_status" in {bad_case.failure_type for bad_case in result.bad_cases}


def test_offline_eval_writes_summary_bad_cases_and_traces(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    summaries = run_offline_eval(DATASET_PATH, tmp_path)

    assert [summary.target for summary in summaries] == ["plain_rag_baseline", "graph_v1"]
    baseline_summary = summaries[0]
    graph_summary = summaries[1]
    assert baseline_summary.category_accuracy is None
    assert baseline_summary.review_trigger_accuracy < graph_summary.review_trigger_accuracy
    assert graph_summary.review_trigger_accuracy >= 0.9
    assert graph_summary.final_pass_rate > baseline_summary.final_pass_rate
    assert graph_summary.expected_risk_flag_accuracy is not None

    summary_path = tmp_path / "latest_summary.json"
    bad_cases_path = tmp_path / "bad_cases.jsonl"
    trace_path = Path(graph_summary.trace_events_path)

    assert summary_path.exists()
    assert bad_cases_path.exists()
    assert trace_path.exists()

    summary_payload = json.loads(summary_path.read_text())
    assert summary_payload["run_id"] == graph_summary.run_id
    assert summary_payload["num_examples"] == 20
    assert summary_payload["targets"][0]["category_accuracy"] is None
    assert "bad_case_breakdown" in summary_payload

    bad_cases = [
        json.loads(line)
        for line in bad_cases_path.read_text().splitlines()
        if line.strip()
    ]
    assert "wrong_review_trigger" in {case["failure_type"] for case in bad_cases}
    assert "plain_rag_baseline" in {case["target"] for case in bad_cases}
    assert not [
        case
        for case in bad_cases
        if case["target"] == "graph_v1" and case["failure_type"] == "unexpected_retrieval"
    ]
    assert graph_summary.final_pass_rate == 1.0
    assert graph_summary.bad_case_count == 0

    trace_events = [
        json.loads(line)
        for line in trace_path.read_text().splitlines()
        if line.strip()
    ]
    assert {event["target"] for event in trace_events} == {
        "plain_rag_baseline",
        "graph_v1",
    }
    assert all(event["langsmith_enabled"] is False for event in trace_events)
