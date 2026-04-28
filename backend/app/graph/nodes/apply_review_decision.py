from app.graph.state import TicketState
from app.schemas.actions import SupportActionCreate
from app.services.action_ledger import get_action_ledger


def apply_review_decision(state: TicketState) -> TicketState:
    ledger = get_action_ledger()
    review_decision = state["review_decision"]
    reviewer_note = review_decision.reviewer_note

    if review_decision.decision == "reject":
        actions = ledger.reject_for_thread(state["thread_id"], reviewer_note)
    else:
        actions = ledger.approve_for_thread(state["thread_id"])

    if reviewer_note:
        note_action = ledger.propose(
            SupportActionCreate(
                thread_id=state["thread_id"],
                ticket_id=state["ticket_id"],
                action_type="add_internal_note",
                idempotency_key=(
                    f"{state['thread_id']}:{state['ticket_id']}:add_internal_note:"
                    "review_decision"
                ),
                requires_review=False,
                reason="Record the reviewer note on the ticket.",
                payload={
                    "reviewer_note": reviewer_note,
                    "decision": review_decision.decision,
                },
            )
        )
        ledger.execute_once(note_action.action_id)
        actions = ledger.list_by_thread_id(state["thread_id"])

    return {
        "proposed_actions": actions,
        "executed_actions": [
            action for action in actions if action.status == "executed"
        ],
        "status": "running",
        "current_node": "apply_review_decision",
    }
