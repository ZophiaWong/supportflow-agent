import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

from app.schemas.ticket import Ticket

router = APIRouter(prefix="/api/v1", tags=["tickets"])

DATA_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "sample_tickets" / "demo_tickets.json"
)


@lru_cache(maxsize=1)
def _load_ticket_source() -> tuple[Ticket, ...]:
    raw_data = json.loads(DATA_PATH.read_text())
    return tuple(Ticket.model_validate(item) for item in raw_data)


@router.get("/tickets", response_model=list[Ticket])
def list_tickets() -> list[Ticket]:
    return list(_load_ticket_source())
