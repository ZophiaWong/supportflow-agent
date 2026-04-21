from pydantic import BaseModel

from app.schemas.ticket import Ticket


class TicketState(BaseModel):
    ticket: Ticket
    classification: str | None = None
    retrieval_context: list[str] = []
    draft_reply: str | None = None
    review_required: bool = False
