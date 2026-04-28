from typing import Any, Literal

from pydantic import BaseModel, Field


EvalTargetName = Literal["plain_rag_baseline", "graph_v1"]


class EvalInputs(BaseModel):
    ticket_id: str


class EvalReferenceOutputs(BaseModel):
    category: Literal["billing", "account", "product", "bug", "other"]
    should_retrieve_doc_ids: list[str]
    should_trigger_review: bool
    must_include_citation: bool
    must_not_claim: list[str] = Field(default_factory=list)
    expected_risk_flags: list[str] = Field(default_factory=list)
    expected_policy_ids: list[str] = Field(default_factory=list)
    expected_status: Literal["done", "waiting_review", "manual_takeover", "failed"] | None = None


class EvalExample(BaseModel):
    id: str
    inputs: EvalInputs
    reference_outputs: EvalReferenceOutputs
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalTargetOutput(BaseModel):
    target: EvalTargetName
    example_id: str
    ticket_id: str
    status: Literal["done", "waiting_review", "manual_takeover", "failed"]
    category: str | None
    category_supported: bool
    retrieved_doc_ids: list[str]
    citations: list[str]
    answer: str | None
    review_required: bool
    trace_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalMetricResult(BaseModel):
    name: Literal[
        "category_accuracy",
        "retrieval_hit",
        "citation_coverage",
        "review_trigger_accuracy",
        "unsupported_claim_absent",
        "expected_status",
        "expected_risk_flags",
        "expected_policy_ids",
        "final_pass",
    ]
    passed: bool | None
    score: float | None
    expected: Any = None
    actual: Any = None
    notes: str | None = None


class BadCaseRecord(BaseModel):
    example_id: str
    target: EvalTargetName
    failure_type: str
    expected: dict[str, Any]
    actual: dict[str, Any]
    trace_url: str | None = None
    notes: str


class EvalExampleResult(BaseModel):
    example_id: str
    target: EvalTargetName
    output: EvalTargetOutput
    metrics: list[EvalMetricResult]
    final_pass: bool
    bad_cases: list[BadCaseRecord]


class EvalRunSummary(BaseModel):
    run_id: str
    dataset: str
    target: EvalTargetName
    num_examples: int
    category_supported: bool
    category_accuracy: float | None
    retrieval_hit_rate: float
    citation_coverage: float
    review_trigger_accuracy: float
    unsupported_claim_absence: float
    expected_status_accuracy: float | None
    expected_risk_flag_accuracy: float | None
    expected_policy_accuracy: float | None
    final_pass_rate: float
    bad_case_count: int
    trace_events_path: str
