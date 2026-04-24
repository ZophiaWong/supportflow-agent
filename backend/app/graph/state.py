from typing import Any, Literal, TypedDict

from app.schemas.graph import DraftReply, KBHit, TicketClassification


class TicketState(TypedDict, total=False):
    thread_id: str
    ticket_id: str
    ticket: dict[str, Any]
    classification: TicketClassification
    retrieval_query: str
    retrieved_chunks: list[KBHit]
    draft: DraftReply
    status: Literal["queued", "running", "done", "failed"]
    current_node: Literal[
        "load_ticket_context",
        "classify_ticket",
        "retrieve_knowledge",
        "draft_reply",
    ]
    error: str | None
