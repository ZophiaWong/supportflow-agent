from app.graph.state import TicketState
from app.services.ticket_repo import get_ticket_by_id


def load_ticket_context(state: TicketState) -> TicketState:
    ticket_id = state["ticket_id"]
    if state.get("ticket_source") == "eval":
        from app.evals.ticket_fixtures import get_eval_ticket_by_id

        ticket = get_eval_ticket_by_id(ticket_id)
    else:
        ticket = get_ticket_by_id(ticket_id)

    return {
        "ticket": ticket,
        "status": "running",
        "current_node": "load_ticket_context",
        "error": None,
    }
