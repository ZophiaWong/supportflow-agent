from typing import Any

from app.graph.builder import get_support_graph
from app.schemas.graph import PendingReviewItem, RunStateResponse
from app.services.run_event_store import get_run_event_store


def _extract_pending_review(interrupts: tuple[Any, ...]) -> PendingReviewItem | None:
    if not interrupts:
        return None

    interrupt_value = interrupts[0]
    payload = getattr(interrupt_value, "value", interrupt_value)
    return PendingReviewItem.model_validate(payload)


def get_run_state(thread_id: str) -> RunStateResponse | None:
    graph = get_support_graph()
    snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
    values = snapshot.values

    if not values:
        ticket_id = get_run_event_store().get_thread_ticket_id(thread_id)
        if ticket_id is None:
            return None
        return RunStateResponse(
            thread_id=thread_id,
            ticket_id=ticket_id,
            status="running",
            current_node=None,
            classification=None,
            retrieved_chunks=[],
            draft=None,
            risk_assessment=None,
            policy_assessment=None,
            review_decision=None,
            final_response=None,
            pending_review=None,
            proposed_actions=[],
            executed_actions=[],
            error=None,
        )

    pending_review = _extract_pending_review(snapshot.interrupts)
    status = values["status"]
    current_node = values.get("current_node")

    if pending_review is not None:
        status = "waiting_review"
        current_node = "human_review_interrupt"

    return RunStateResponse(
        thread_id=values["thread_id"],
        ticket_id=values["ticket_id"],
        status=status,
        current_node=current_node,
        classification=values.get("classification"),
        retrieved_chunks=values.get("retrieved_chunks", []),
        draft=values.get("draft"),
        risk_assessment=values.get("risk_assessment"),
        policy_assessment=values.get("policy_assessment"),
        review_decision=values.get("review_decision"),
        final_response=values.get("final_response"),
        pending_review=pending_review,
        proposed_actions=values.get("proposed_actions", []),
        executed_actions=values.get("executed_actions", []),
        error=values.get("error"),
    )
