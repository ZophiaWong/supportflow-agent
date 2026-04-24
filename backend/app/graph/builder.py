from functools import lru_cache

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.nodes.classify_ticket import classify_ticket
from app.graph.nodes.draft_reply import draft_reply
from app.graph.nodes.load_ticket_context import load_ticket_context
from app.graph.nodes.retrieve_knowledge import retrieve_knowledge
from app.graph.state import TicketState


@lru_cache(maxsize=1)
def get_support_graph():
    builder = StateGraph(TicketState)

    builder.add_node("load_ticket_context", load_ticket_context)
    builder.add_node("classify_ticket", classify_ticket)
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("draft_reply", draft_reply)

    builder.add_edge(START, "load_ticket_context")
    builder.add_edge("load_ticket_context", "classify_ticket")
    builder.add_edge("classify_ticket", "retrieve_knowledge")
    builder.add_edge("retrieve_knowledge", "draft_reply")
    builder.add_edge("draft_reply", END)

    return builder.compile(checkpointer=InMemorySaver())
