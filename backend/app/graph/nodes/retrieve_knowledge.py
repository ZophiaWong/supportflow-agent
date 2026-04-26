from app.graph.state import TicketState
from app.services.retrieval import retrieve_knowledge as retrieve_knowledge_hits


def retrieve_knowledge(state: TicketState) -> TicketState:
    ticket = state["ticket"]
    classification = state["classification"]
    query = " ".join(
        [
            str(ticket.get("subject", "")),
            str(ticket.get("preview", "")),
        ]
    ).strip()

    return {
        "retrieval_query": query,
        "retrieved_chunks": retrieve_knowledge_hits(query, category=classification.category),
        "current_node": "retrieve_knowledge",
    }
