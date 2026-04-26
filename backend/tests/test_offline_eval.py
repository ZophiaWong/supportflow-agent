import json
from pathlib import Path

from app.evals.dataset import load_eval_dataset
from app.evals.runner import run_offline_eval
from app.evals.scoring import score_example
from app.evals.targets import run_plain_rag_baseline

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPO_ROOT / "data" / "evals" / "supportflow_v1.jsonl"


def test_load_eval_dataset_reads_three_demo_cases() -> None:
    examples = load_eval_dataset(DATASET_PATH)

    assert [example.id for example in examples] == ["E-001", "E-002", "E-003"]
    assert [example.inputs.ticket_id for example in examples] == [
        "ticket-1001",
        "ticket-1002",
        "ticket-1003",
    ]
    assert examples[0].reference_outputs.category == "billing"
    assert examples[1].reference_outputs.should_retrieve_doc_ids == ["account_unlock"]
    assert examples[2].reference_outputs.should_trigger_review is False


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
    assert [case.failure_type for case in result.bad_cases] == ["wrong_review_trigger"]


def test_offline_eval_writes_summary_bad_cases_and_traces(tmp_path: Path) -> None:
    summaries = run_offline_eval(DATASET_PATH, tmp_path)

    assert [summary.target for summary in summaries] == ["plain_rag_baseline", "graph_v1"]
    baseline_summary = summaries[0]
    graph_summary = summaries[1]
    assert baseline_summary.category_accuracy is None
    assert baseline_summary.review_trigger_accuracy < graph_summary.review_trigger_accuracy
    assert graph_summary.review_trigger_accuracy == 1.0
    assert graph_summary.final_pass_rate == 1.0

    summary_path = tmp_path / "latest_summary.json"
    bad_cases_path = tmp_path / "bad_cases.jsonl"
    trace_path = Path(graph_summary.trace_events_path)

    assert summary_path.exists()
    assert bad_cases_path.exists()
    assert trace_path.exists()

    summary_payload = json.loads(summary_path.read_text())
    assert summary_payload["run_id"] == graph_summary.run_id
    assert summary_payload["num_examples"] == 3
    assert summary_payload["targets"][0]["category_accuracy"] is None

    bad_cases = [
        json.loads(line)
        for line in bad_cases_path.read_text().splitlines()
        if line.strip()
    ]
    assert {case["failure_type"] for case in bad_cases} == {"wrong_review_trigger"}
    assert {case["target"] for case in bad_cases} == {"plain_rag_baseline"}

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
