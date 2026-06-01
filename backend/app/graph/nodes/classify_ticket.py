from app.graph.state import TicketState
from app.schemas.graph import TicketClassification
from app.services import llm


PRIORITY_MAP = {
    "urgent": "P0",
    "high": "P1",
    "medium": "P2",
    "low": "P3",
}


def _match_category(text: str) -> tuple[str, str]:
    normalized = text.lower()

    if any(keyword in normalized for keyword in ["refund", "invoice", "charge", "billing", "credit"]):
        return "billing", "Ticket mentions billing or duplicate-charge language."
    if (
        any(keyword in normalized for keyword in ["retention window", "sso", "trial"])
        and "crash" not in normalized
        and "failed" not in normalized
    ):
        return "product", "Ticket asks about product plan, SSO, trial, or retention behavior."
    if any(keyword in normalized for keyword in ["bug", "error", "failed", "export", "crash", "outage"]):
        return "bug", "Ticket describes a product failure or export error."
    if any(keyword in normalized for keyword in ["login", "password", "locked", "unlock", "admin", "mfa", "owner"]):
        return "account", "Ticket mentions account access or password recovery."
    if any(keyword in normalized for keyword in ["plan", "seat", "onboarding", "subscription", "sso", "trial"]):
        return "product", "Ticket asks about product plan or seat behavior."
    return "other", "Ticket does not match the Day 2 rules for billing, account, bug, or product."


def classify_ticket(state: TicketState) -> TicketState:
    ticket = state["ticket"]
    llm_result = llm.generate_ticket_classification(ticket)
    if llm_result.value is not None:
        return {
            "classification": llm_result.value,
            "classification_source": "llm",
            "current_node": "classify_ticket",
        }

    text = " ".join(
        [
            str(ticket.get("subject", "")),
            str(ticket.get("preview", "")),
        ]
    )
    category, reason = _match_category(text)
    source_priority = str(ticket.get("priority", "medium")).lower()

    result: TicketState = {
        "classification": TicketClassification(
            category=category,
            priority=PRIORITY_MAP.get(source_priority, "P2"),
            reason=reason,
        ),
        "classification_source": "fallback",
        "current_node": "classify_ticket",
    }
    if llm_result.error_reason:
        result["classification_llm_error"] = llm_result.error_reason
    return result
