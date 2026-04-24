from app.graph.state import TicketState
from app.services.ticket_repo import get_ticket_by_id


def load_ticket_context(state: TicketState) -> TicketState:
    ticket_id = state["ticket_id"]
    return {
        "ticket": get_ticket_by_id(ticket_id),
        "status": "running",
        "current_node": "load_ticket_context",
        "error": None,
    }
