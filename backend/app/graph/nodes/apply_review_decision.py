from app.graph.state import TicketState


def apply_review_decision(state: TicketState) -> TicketState:
    return {
        "status": "running",
        "current_node": "apply_review_decision",
    }
