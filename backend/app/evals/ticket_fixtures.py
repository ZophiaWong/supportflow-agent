import json
from functools import lru_cache
from pathlib import Path

from app.schemas.ticket import Ticket
from app.services.ticket_repo import get_ticket_by_id

EVAL_TICKETS_PATH = Path(__file__).resolve().parents[3] / "data" / "evals" / "supportflow_tickets.json"


@lru_cache(maxsize=1)
def _load_eval_tickets() -> tuple[dict[str, object], ...]:
    if not EVAL_TICKETS_PATH.exists():
        return ()

    raw_data = json.loads(EVAL_TICKETS_PATH.read_text())
    return tuple(Ticket.model_validate(item).model_dump(mode="json") for item in raw_data)


def get_eval_ticket_by_id(ticket_id: str) -> dict[str, object]:
    for ticket in _load_eval_tickets():
        if ticket["id"] == ticket_id:
            return dict(ticket)

    return get_ticket_by_id(ticket_id)
