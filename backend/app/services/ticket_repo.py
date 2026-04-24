import json
from functools import lru_cache
from pathlib import Path

from app.schemas.ticket import Ticket

DATA_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "sample_tickets" / "demo_tickets.json"
)


class TicketNotFoundError(LookupError):
    pass


@lru_cache(maxsize=1)
def _load_ticket_source() -> tuple[dict[str, object], ...]:
    raw_data = json.loads(DATA_PATH.read_text())
    return tuple(Ticket.model_validate(item).model_dump(mode="json") for item in raw_data)


def list_tickets() -> list[dict[str, object]]:
    return list(_load_ticket_source())


def get_ticket_by_id(ticket_id: str) -> dict[str, object]:
    for ticket in _load_ticket_source():
        if ticket["id"] == ticket_id:
            return dict(ticket)

    raise TicketNotFoundError(f"Ticket not found: {ticket_id}")
