from app.graph.state import TicketState
from app.schemas.graph import FinalResponse


def finalize_reply(state: TicketState) -> TicketState:
    review_decision = state.get("review_decision")
    draft = state["draft"]

    answer = draft.answer
    citations = draft.citations
    disposition = "auto_finalized"

    if review_decision:
        if review_decision.decision == "approve":
            disposition = "approved"
        elif review_decision.decision == "edit":
            disposition = "edited"
            answer = review_decision.edited_answer or draft.answer

    return {
        "final_response": FinalResponse(
            answer=answer,
            citations=citations,
            disposition=disposition,
        ),
        "status": "done",
        "current_node": "finalize_reply",
    }
