from typing import Literal

from pydantic import BaseModel


class TicketClassification(BaseModel):
    category: Literal["billing", "account", "product", "bug", "other"]
    priority: Literal["P0", "P1", "P2", "P3"]
    reason: str


class KBHit(BaseModel):
    doc_id: str
    title: str
    score: float
    snippet: str


class DraftReply(BaseModel):
    answer: str
    citations: list[str]
    confidence: float


class RunTicketResponse(BaseModel):
    thread_id: str
    ticket_id: str
    status: Literal["done", "failed", "running"]
    classification: TicketClassification
    retrieved_chunks: list[KBHit]
    draft: DraftReply
