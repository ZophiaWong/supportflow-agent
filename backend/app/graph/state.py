from typing import Any, Literal, TypedDict

from app.schemas.actions import SupportAction
from app.schemas.graph import (
    DraftReply,
    FinalResponse,
    KBHit,
    PendingReviewItem,
    RiskAssessment,
    SubmitReviewDecisionRequest,
    TicketClassification,
)


class TicketState(TypedDict, total=False):
    thread_id: str
    ticket_id: str
    ticket_source: Literal["demo", "eval"]
    ticket: dict[str, Any]
    classification: TicketClassification
    retrieval_query: str
    retrieved_chunks: list[KBHit]
    draft: DraftReply
    risk_assessment: RiskAssessment
    proposed_actions: list[SupportAction]
    executed_actions: list[SupportAction]
    review_required: bool
    pending_review: PendingReviewItem
    review_decision: SubmitReviewDecisionRequest
    final_response: FinalResponse
    status: Literal["queued", "running", "done", "failed", "waiting_review", "manual_takeover"]
    current_node: Literal[
        "load_ticket_context",
        "classify_ticket",
        "retrieve_knowledge",
        "draft_reply",
        "risk_gate",
        "propose_actions",
        "human_review_interrupt",
        "apply_review_decision",
        "finalize_reply",
        "manual_takeover",
    ]
    error: str | None
