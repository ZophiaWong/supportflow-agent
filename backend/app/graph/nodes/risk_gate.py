from app.graph.state import TicketState
from app.schemas.graph import RiskAssessment
from app.services.policy_engine import evaluate_policy


def risk_gate(state: TicketState) -> TicketState:
    classification = state["classification"]
    draft = state["draft"]
    retrieved_chunks = state.get("retrieved_chunks", [])
    ticket = state["ticket"]
    policy_assessment = evaluate_policy(
        ticket=ticket,
        classification=classification,
        retrieved_chunks=retrieved_chunks,
        draft=draft,
        proposed_actions=state.get("proposed_actions", []),
    )

    assessment = RiskAssessment(
        review_required=policy_assessment.review_required,
        risk_flags=policy_assessment.failed_policy_ids,
        reason=(
            "Review required because one or more structured policy checks failed."
            if policy_assessment.review_required
            else "All structured policy checks passed, so the draft can be finalized automatically."
        ),
    )

    return {
        "risk_assessment": assessment,
        "policy_assessment": policy_assessment,
        "review_required": assessment.review_required,
        "status": "running",
        "current_node": "risk_gate",
    }
