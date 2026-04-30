import json
from pathlib import Path

from app.evals.dataset import load_eval_dataset
from app.evals.runner import run_offline_eval
from app.evals.schemas import EvalExample, EvalTargetOutput
from app.evals.scoring import score_example
from app.evals.targets import run_graph_v1, run_plain_rag_baseline
from app.evals.ticket_fixtures import get_eval_ticket_by_id
from scripts.promote_eval_case import candidate_from_trace, write_candidate
from scripts.run_offline_eval import _threshold_misses

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
    assert examples[2].reference_outputs.expected_policy_ids == [
        "high_impact_action_requires_review"
    ]
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
    assert [case.failure_stage for case in result.bad_cases] == [
        "review_routing",
        "finalization",
    ]


def test_graph_target_can_load_eval_only_ticket() -> None:
    example = load_eval_dataset(DATASET_PATH)[3]

    output = run_graph_v1(example)

    assert output.ticket_id == "eval-ticket-2001"
    assert output.category == "bug"
    assert output.status == "waiting_review"
    assert "bug_export_issue" in output.retrieved_doc_ids
    assert "priority_requires_review" in output.metadata["risk_flags"]
    assert "priority_requires_review" in output.metadata["failed_policy_ids"]


def test_graph_target_returns_no_evidence_for_unsupported_tickets() -> None:
    examples = load_eval_dataset(DATASET_PATH)
    unsupported_examples = [examples[index] for index in (11, 12, 14)]

    for example in unsupported_examples:
        output = run_graph_v1(example)

        assert output.retrieved_doc_ids == []
        assert output.citations == []
        assert output.review_required is True
        assert "no_evidence" in output.metadata["risk_flags"]
        assert "no_evidence" in output.metadata["failed_policy_ids"]


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


def test_action_expectation_scoring_detects_missing_action_type_and_status() -> None:
    example = EvalExample.model_validate(
        {
            "id": "action-expectation",
            "inputs": {"ticket_id": "ticket-1001"},
            "reference_outputs": {
                "category": "billing",
                "should_retrieve_doc_ids": ["refund_policy"],
                "should_trigger_review": True,
                "must_include_citation": True,
                "expected_action_types": ["send_customer_reply", "create_refund_case"],
                "expected_action_statuses": {
                    "send_customer_reply": "proposed",
                    "create_refund_case": "proposed",
                },
            },
        }
    )
    output = EvalTargetOutput(
        target="graph_v1",
        example_id=example.id,
        ticket_id=example.inputs.ticket_id,
        status="waiting_review",
        category="billing",
        category_supported=True,
        retrieved_doc_ids=["refund_policy"],
        citations=["refund_policy"],
        answer="Draft with citation.",
        review_required=True,
        metadata={
            "proposed_action_types": ["send_customer_reply"],
            "action_statuses_by_type": {"send_customer_reply": ["executed"]},
        },
    )

    result = score_example(example, output)

    assert {
        (bad_case.failure_type, bad_case.failure_stage)
        for bad_case in result.bad_cases
    } >= {
        ("missing_expected_action_type", "actions"),
        ("wrong_action_status", "actions"),
    }
    assert result.final_pass is False


def test_expected_failure_stage_scoring_checks_bad_case_stage() -> None:
    example = EvalExample.model_validate(
        {
            "id": "stage-expectation",
            "inputs": {"ticket_id": "ticket-1001"},
            "reference_outputs": {
                "category": "billing",
                "should_retrieve_doc_ids": ["refund_policy"],
                "should_trigger_review": True,
                "must_include_citation": True,
                "expected_failure_stage": "review_routing",
            },
        }
    )
    output = run_plain_rag_baseline(example)
    result = score_example(example, output)
    metrics_by_name = {metric.name: metric for metric in result.metrics}

    assert metrics_by_name["expected_failure_stage"].passed is True


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
    assert graph_summary.expected_policy_accuracy is not None

    summary_path = tmp_path / "latest_summary.json"
    bad_cases_path = tmp_path / "bad_cases.jsonl"
    report_path = tmp_path / "latest_report.md"
    trace_path = Path(graph_summary.trace_events_path)

    assert summary_path.exists()
    assert bad_cases_path.exists()
    assert report_path.exists()
    assert trace_path.exists()

    summary_payload = json.loads(summary_path.read_text())
    assert summary_payload["run_id"] == graph_summary.run_id
    assert summary_payload["num_examples"] == 20
    assert summary_payload["targets"][0]["category_accuracy"] is None
    assert "bad_case_breakdown" in summary_payload
    assert summary_payload["bad_case_breakdown_by_stage"]["plain_rag_baseline"] == {
        "finalization": 20,
        "review_routing": 20,
    }
    assert "plain_rag_baseline: finalization" in report_path.read_text()

    bad_cases = [
        json.loads(line)
        for line in bad_cases_path.read_text().splitlines()
        if line.strip()
    ]
    assert "wrong_review_trigger" in {case["failure_type"] for case in bad_cases}
    assert "review_routing" in {case["failure_stage"] for case in bad_cases}
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

    assert _threshold_misses(
        summaries,
        threshold_target="graph_v1",
        min_final_pass_rate=1.0,
        min_citation_coverage=1.0,
        min_policy_trigger_accuracy=1.0,
    ) == []
    assert _threshold_misses(
        summaries,
        threshold_target="graph_v1",
        min_final_pass_rate=1.1,
        min_citation_coverage=None,
        min_policy_trigger_accuracy=None,
    ) == ["graph_v1.final_pass_rate=1.00 missed threshold 1.10"]


def test_promote_eval_case_writes_candidate_from_trace(tmp_path: Path) -> None:
    trace_file = tmp_path / "events.jsonl"
    trace_file.write_text(
        json.dumps(
            {
                "example_id": "E-001",
                "target": "graph_v1",
                "ticket_id": "ticket-1001",
                "stage": "graph_run",
                "status": "waiting_review",
                "payload": {
                    "category": "billing",
                    "retrieved_doc_ids": ["refund_policy"],
                    "citations": ["refund_policy"],
                    "review_required": True,
                    "risk_flags": ["billing_sensitive"],
                    "failed_policy_ids": ["billing_sensitive"],
                    "proposed_action_types": ["send_customer_reply"],
                    "action_statuses_by_type": {"send_customer_reply": ["proposed"]},
                },
            },
            sort_keys=True,
        )
        + "\n"
    )

    candidate = candidate_from_trace(
        trace_file,
        target="graph_v1",
        example_id="E-001",
        candidate_id="candidate-ticket-1001",
    )
    path = write_candidate(candidate, output_dir=tmp_path / "candidates", overwrite=False)

    payload = json.loads(path.read_text())
    assert payload["inputs"]["ticket_id"] == "ticket-1001"
    assert payload["reference_outputs"]["expected_action_types"] == [
        "send_customer_reply"
    ]
    assert payload["reference_outputs"]["expected_action_statuses"] == {
        "send_customer_reply": "proposed"
    }
