from app.graph.state import TicketState


def manual_takeover(state: TicketState) -> TicketState:
    return {
        "status": "manual_takeover",
        "current_node": "manual_takeover",
    }
