from app.graph.state import TicketState
from app.schemas.graph import DraftReply


def draft_reply(state: TicketState) -> TicketState:
    ticket = state["ticket"]
    classification = state["classification"]
    retrieved_chunks = state.get("retrieved_chunks", [])
    customer_name = str(ticket.get("customer_name", "there"))

    if retrieved_chunks:
        lead_hit = retrieved_chunks[0]
        answer = (
            f"Hi {customer_name},\n\n"
            f"We reviewed your {classification.category} request about "
            f"\"{ticket.get('subject', 'your issue')}\". Based on our "
            f"{lead_hit.title.lower()}, the next support step is to verify the details "
            f"listed below and continue the case with the right team.\n\n"
            f"- Confirm the account or billing details referenced in the ticket.\n"
            f"- Follow the guidance from {lead_hit.title}.\n"
            f"- Reply to the customer with the outcome once verification is complete.\n\n"
            f"Best,\nSupportflow Agent"
        )
        citations = [lead_hit.doc_id]
        confidence = 0.82
    else:
        answer = (
            f"Hi {customer_name},\n\n"
            f"We reviewed your request about \"{ticket.get('subject', 'your issue')}\" "
            "and need a support specialist to confirm the next step before we send a final answer.\n\n"
            "Best,\nSupportflow Agent"
        )
        citations = []
        confidence = 0.35

    return {
        "draft": DraftReply(
            answer=answer,
            citations=citations,
            confidence=confidence,
        ),
        "status": "done",
        "current_node": "draft_reply",
    }
