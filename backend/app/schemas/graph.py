from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.actions import SupportAction


class TicketClassification(BaseModel):
    category: Literal["billing", "account", "product", "bug", "other"]
    priority: Literal["P0", "P1", "P2", "P3"]
    reason: str


class KBHit(BaseModel):
    doc_id: str
    title: str
    score: float
    snippet: str


class DraftReply(BaseModel):
    answer: str
    citations: list[str]
    confidence: float


class RiskAssessment(BaseModel):
    review_required: bool
    risk_flags: list[str]
    reason: str


class PolicyCheckResult(BaseModel):
    policy_id: str
    severity: Literal["info", "warning", "blocker"]
    passed: bool
    message: str
    evidence: list[str] = Field(default_factory=list)


class PolicyAssessment(BaseModel):
    review_required: bool
    failed_policy_ids: list[str] = Field(default_factory=list)
    results: list[PolicyCheckResult] = Field(default_factory=list)


class SubmitReviewDecisionRequest(BaseModel):
    decision: Literal["approve", "edit", "reject"]
    reviewer_note: str | None = None
    edited_answer: str | None = None

    @model_validator(mode="after")
    def validate_edited_answer(self) -> "SubmitReviewDecisionRequest":
        if self.decision == "edit" and not self.edited_answer:
            raise ValueError("edited_answer is required when decision is edit")
        return self


class PendingReviewItem(BaseModel):
    thread_id: str
    ticket_id: str
    classification: TicketClassification
    draft: DraftReply
    retrieved_chunks: list[KBHit]
    risk_flags: list[str]
    policy_assessment: PolicyAssessment | None = None
    proposed_actions: list[SupportAction] = Field(default_factory=list)
    allowed_decisions: list[Literal["approve", "edit", "reject"]]


class FinalResponse(BaseModel):
    answer: str
    citations: list[str]
    disposition: Literal["auto_finalized", "approved", "edited"]


class RunTicketResponse(BaseModel):
    thread_id: str
    ticket_id: str
    status: Literal["done", "failed", "running", "waiting_review", "manual_takeover"]
    classification: TicketClassification
    retrieved_chunks: list[KBHit]
    draft: DraftReply
    risk_assessment: RiskAssessment | None = None
    policy_assessment: PolicyAssessment | None = None
    pending_review: PendingReviewItem | None = None
    final_response: FinalResponse | None = None
    proposed_actions: list[SupportAction] = Field(default_factory=list)
    executed_actions: list[SupportAction] = Field(default_factory=list)


class RunTimelineEvent(BaseModel):
    event_id: str
    thread_id: str
    ticket_id: str
    event_type: Literal[
        "run_started",
        "classify_completed",
        "retrieve_completed",
        "draft_completed",
        "risk_gate_completed",
        "interrupt_created",
        "review_submitted",
        "run_resumed",
        "run_completed",
        "run_failed",
    ]
    node_name: str | None = None
    status: Literal["running", "waiting_review", "done", "failed", "manual_takeover"]
    message: str | None = None
    created_at: str
    payload: dict[str, Any] | None = None


class RunTimelineResponse(BaseModel):
    thread_id: str
    events: list[RunTimelineEvent]


class RunStateResponse(BaseModel):
    thread_id: str
    ticket_id: str
    status: Literal["running", "waiting_review", "done", "failed", "manual_takeover"]
    current_node: str | None = None
    classification: TicketClassification | None = None
    retrieved_chunks: list[KBHit]
    draft: DraftReply | None = None
    risk_assessment: RiskAssessment | None = None
    policy_assessment: PolicyAssessment | None = None
    review_decision: SubmitReviewDecisionRequest | None = None
    final_response: FinalResponse | None = None
    pending_review: PendingReviewItem | None = None
    proposed_actions: list[SupportAction] = Field(default_factory=list)
    executed_actions: list[SupportAction] = Field(default_factory=list)
    error: str | None = None
