from typing import Literal

from pydantic import BaseModel, model_validator


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
    pending_review: PendingReviewItem | None = None
    final_response: FinalResponse | None = None
