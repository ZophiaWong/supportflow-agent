from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph.nodes.apply_review_decision import apply_review_decision
from app.graph.nodes.classify_ticket import classify_ticket
from app.graph.nodes.draft_reply import draft_reply
from app.graph.nodes.finalize_reply import finalize_reply
from app.graph.nodes.human_review_interrupt import human_review_interrupt
from app.graph.nodes.load_ticket_context import load_ticket_context
from app.graph.nodes.manual_takeover import manual_takeover
from app.graph.nodes.risk_gate import risk_gate
from app.graph.nodes.retrieve_knowledge import retrieve_knowledge
from app.graph.state import TicketState
from app.services.sqlite_checkpointer import SqliteSaver


def _route_after_risk_gate(state: TicketState) -> str:
    return "human_review_interrupt" if state.get("review_required") else "finalize_reply"


def _route_after_review_decision(state: TicketState) -> str:
    review_decision = state.get("review_decision")
    if review_decision and review_decision.decision == "reject":
        return "manual_takeover"
    return "finalize_reply"


@lru_cache(maxsize=1)
def get_support_graph():
    builder = StateGraph(TicketState)

    builder.add_node("load_ticket_context", load_ticket_context)
    builder.add_node("classify_ticket", classify_ticket)
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("draft_reply", draft_reply)
    builder.add_node("risk_gate", risk_gate)
    builder.add_node("human_review_interrupt", human_review_interrupt)
    builder.add_node("apply_review_decision", apply_review_decision)
    builder.add_node("finalize_reply", finalize_reply)
    builder.add_node("manual_takeover", manual_takeover)

    builder.add_edge(START, "load_ticket_context")
    builder.add_edge("load_ticket_context", "classify_ticket")
    builder.add_edge("classify_ticket", "retrieve_knowledge")
    builder.add_edge("retrieve_knowledge", "draft_reply")
    builder.add_edge("draft_reply", "risk_gate")
    builder.add_conditional_edges("risk_gate", _route_after_risk_gate)
    builder.add_edge("human_review_interrupt", "apply_review_decision")
    builder.add_conditional_edges("apply_review_decision", _route_after_review_decision)
    builder.add_edge("finalize_reply", END)
    builder.add_edge("manual_takeover", END)

    return builder.compile(checkpointer=SqliteSaver())
