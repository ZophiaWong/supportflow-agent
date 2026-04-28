from app.graph.state import TicketState
from app.schemas.actions import SupportAction, SupportActionCreate, SupportActionType
from app.services.action_ledger import get_action_ledger


def _ticket_text(state: TicketState) -> str:
    ticket = state["ticket"]
    return " ".join(
        [
            str(ticket.get("subject", "")),
            str(ticket.get("preview", "")),
        ]
    ).lower()


def _create_action(
    state: TicketState,
    *,
    action_type: SupportActionType,
    key_suffix: str,
    requires_review: bool,
    reason: str,
    payload: dict[str, object],
) -> SupportActionCreate:
    thread_id = state["thread_id"]
    ticket_id = state["ticket_id"]
    return SupportActionCreate(
        thread_id=thread_id,
        ticket_id=ticket_id,
        action_type=action_type,
        idempotency_key=f"{thread_id}:{ticket_id}:{key_suffix}",
        requires_review=requires_review,
        reason=reason,
        payload=payload,
    )


def _action_proposals(state: TicketState) -> list[SupportActionCreate]:
    classification = state["classification"]
    draft = state["draft"]
    text = _ticket_text(state)

    proposals = [
        _create_action(
            state,
            action_type="send_customer_reply",
            key_suffix="send_customer_reply",
            requires_review=True,
            reason="Send the final approved support reply to the customer.",
            payload={
                "answer_source": "final_response",
                "citation_ids": draft.citations,
                "draft_confidence": draft.confidence,
            },
        )
    ]

    if classification.category == "billing" and "refund" in text:
        proposals.append(
            _create_action(
                state,
                action_type="create_refund_case",
                key_suffix="create_refund_case",
                requires_review=True,
                reason="Open a refund review case for the duplicate-charge request.",
                payload={
                    "category": classification.category,
                    "priority": classification.priority,
                },
            )
        )

    if classification.category == "billing" and any(
        keyword in text for keyword in ["credit", "account credit", "compensation"]
    ):
        proposals.append(
            _create_action(
                state,
                action_type="apply_credit",
                key_suffix="apply_credit",
                requires_review=True,
                reason="Apply account credit after reviewer approval.",
                payload={
                    "category": classification.category,
                    "priority": classification.priority,
                },
            )
        )

    if classification.category == "bug" and any(
        keyword in text for keyword in ["urgent", "outage", "security", "data loss"]
    ):
        proposals.append(
            _create_action(
                state,
                action_type="escalate_to_tier_2",
                key_suffix="escalate_to_tier_2",
                requires_review=True,
                reason="Escalate the urgent product issue to tier 2 support.",
                payload={
                    "category": classification.category,
                    "priority": classification.priority,
                },
            )
        )

    return proposals


def propose_actions(state: TicketState) -> TicketState:
    ledger = get_action_ledger()
    proposed_actions = [ledger.propose(action) for action in _action_proposals(state)]
    risk_assessment = state["risk_assessment"]
    action_review_required = any(action.requires_review for action in proposed_actions)

    return {
        "proposed_actions": proposed_actions,
        "executed_actions": [
            action for action in proposed_actions if action.status == "executed"
        ],
        "review_required": risk_assessment.review_required or action_review_required,
        "status": "running",
        "current_node": "propose_actions",
    }
