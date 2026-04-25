from app.graph.state import TicketState
from app.schemas.graph import RiskAssessment


HIGH_RISK_KEYWORDS = (
    "refund",
    "payment",
    "account unlock",
    "locked out",
    "legal",
    "outage",
    "data loss",
)


def risk_gate(state: TicketState) -> TicketState:
    classification = state["classification"]
    draft = state["draft"]
    retrieved_chunks = state.get("retrieved_chunks", [])
    ticket = state["ticket"]
    text = " ".join(
        [
            str(ticket.get("subject", "")).lower(),
            str(ticket.get("preview", "")).lower(),
        ]
    )

    risk_flags: list[str] = []

    if classification.priority in {"P0", "P1"}:
        risk_flags.append("priority_requires_review")
    if draft.confidence < 0.75:
        risk_flags.append("low_confidence")
    if not retrieved_chunks:
        risk_flags.append("no_evidence")
    if classification.category == "billing" and draft.confidence < 0.85:
        risk_flags.append("billing_sensitive")
    if any(keyword in text for keyword in HIGH_RISK_KEYWORDS):
        risk_flags.append("sensitive_request")

    assessment = RiskAssessment(
        review_required=bool(risk_flags),
        risk_flags=risk_flags,
        reason=(
            "Review required because one or more Day 3 risk rules matched."
            if risk_flags
            else "No Day 3 risk rules matched, so the draft can be finalized automatically."
        ),
    )

    return {
        "risk_assessment": assessment,
        "review_required": assessment.review_required,
        "status": "running",
        "current_node": "risk_gate",
    }
