from fastapi import APIRouter

from app.schemas.ticket import Ticket
from app.services.ticket_repo import list_tickets as list_ticket_records

router = APIRouter(prefix="/api/v1", tags=["tickets"])

@router.get("/tickets", response_model=list[Ticket])
def list_tickets() -> list[Ticket]:
    return [Ticket.model_validate(item) for item in list_ticket_records()]
