from langgraph.types import interrupt

from app.graph.state import TicketState
from app.schemas.graph import PendingReviewItem, SubmitReviewDecisionRequest


def human_review_interrupt(state: TicketState) -> TicketState:
    pending_review = PendingReviewItem(
        thread_id=state["thread_id"],
        ticket_id=state["ticket_id"],
        classification=state["classification"],
        draft=state["draft"],
        retrieved_chunks=state.get("retrieved_chunks", []),
        risk_flags=state["risk_assessment"].risk_flags,
        allowed_decisions=["approve", "edit", "reject"],
    )

    review_decision = SubmitReviewDecisionRequest.model_validate(
        interrupt(pending_review.model_dump(mode="json"))
    )

    return {
        "pending_review": pending_review,
        "review_decision": review_decision,
        "status": "running",
        "current_node": "human_review_interrupt",
    }
