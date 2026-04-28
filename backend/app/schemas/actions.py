from typing import Any, Literal

from pydantic import BaseModel, Field


SupportActionType = Literal[
    "send_customer_reply",
    "create_refund_case",
    "apply_credit",
    "escalate_to_tier_2",
    "add_internal_note",
]

SupportActionStatus = Literal["proposed", "approved", "executed", "rejected", "failed"]


class SupportActionCreate(BaseModel):
    thread_id: str
    ticket_id: str
    action_type: SupportActionType
    idempotency_key: str
    requires_review: bool
    reason: str
    payload: dict[str, Any] = Field(default_factory=dict)


class SupportAction(BaseModel):
    action_id: str
    thread_id: str
    ticket_id: str
    action_type: SupportActionType
    status: SupportActionStatus
    idempotency_key: str
    requires_review: bool
    reason: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
