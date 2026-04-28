from app.graph.state import TicketState
from app.schemas.graph import FinalResponse
from app.services.action_ledger import get_action_ledger


def finalize_reply(state: TicketState) -> TicketState:
    ledger = get_action_ledger()
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

    final_response = FinalResponse(
        answer=answer,
        citations=citations,
        disposition=disposition,
    )

    actions = ledger.list_by_thread_id(state["thread_id"])
    for action in actions:
        if action.status == "approved" or (
            action.status == "proposed" and not action.requires_review
        ):
            ledger.execute_once(action.action_id)
    actions = ledger.list_by_thread_id(state["thread_id"])

    return {
        "final_response": final_response,
        "proposed_actions": actions,
        "executed_actions": [
            action for action in actions if action.status == "executed"
        ],
        "status": "done",
        "current_node": "finalize_reply",
    }
