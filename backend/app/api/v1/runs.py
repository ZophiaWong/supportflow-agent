from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from langgraph.types import Command, Interrupt

from app.graph.builder import get_support_graph
from app.schemas.graph import PendingReviewItem, RunTicketResponse, SubmitReviewDecisionRequest
from app.services.pending_review_store import get_pending_review_store
from app.services.ticket_repo import TicketNotFoundError

router = APIRouter(prefix="/api/v1", tags=["runs"])


def _build_response(result: dict[str, Any]) -> RunTicketResponse:
    return RunTicketResponse(
        thread_id=result["thread_id"],
        ticket_id=result["ticket_id"],
        status=result["status"],
        classification=result["classification"],
        retrieved_chunks=result.get("retrieved_chunks", []),
        draft=result["draft"],
        risk_assessment=result.get("risk_assessment"),
        pending_review=result.get("pending_review"),
        final_response=result.get("final_response"),
    )


def _extract_pending_review(result: dict[str, Any]) -> PendingReviewItem | None:
    interrupts = result.get("__interrupt__", [])
    if not interrupts:
        return None

    interrupt_value = interrupts[0]
    if isinstance(interrupt_value, Interrupt):
        payload = interrupt_value.value
    else:
        payload = interrupt_value

    return PendingReviewItem.model_validate(payload)


@router.post("/tickets/{ticket_id}/run", response_model=RunTicketResponse)
def run_ticket(ticket_id: str) -> RunTicketResponse:
    graph = get_support_graph()
    store = get_pending_review_store()
    thread_id = f"ticket-{ticket_id}-{uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(
            {"ticket_id": ticket_id, "thread_id": thread_id, "status": "queued"},
            config=config,
        )
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {exc}") from exc

    pending_review = _extract_pending_review(result)
    if pending_review is not None:
        store.upsert(pending_review)
        result["pending_review"] = pending_review
        result["status"] = "waiting_review"
    else:
        store.remove(thread_id)

    return _build_response(result)


@router.post("/runs/{thread_id}/resume", response_model=RunTicketResponse)
def resume_run(thread_id: str, body: SubmitReviewDecisionRequest) -> RunTicketResponse:
    graph = get_support_graph()
    store = get_pending_review_store()
    pending_review = store.get(thread_id)
    if pending_review is None:
        raise HTTPException(status_code=404, detail="Pending review not found")

    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = graph.invoke(Command(resume=body.model_dump(mode="json")), config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {exc}") from exc

    store.remove(thread_id)
    result["pending_review"] = None
    return _build_response(result)
