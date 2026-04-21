from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Ticket(BaseModel):
    id: str
    subject: str
    customer_name: str
    status: Literal["open", "pending", "resolved"]
    priority: Literal["low", "medium", "high", "urgent"]
    created_at: datetime
    preview: str | None = None
