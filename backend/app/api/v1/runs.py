from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from langgraph.types import Command, Interrupt

from app.graph.builder import get_support_graph
from app.schemas.graph import (
    PendingReviewItem,
    RunStateResponse,
    StartRunResponse,
    RunTicketResponse,
    RunTraceResponse,
    RunTimelineResponse,
    SubmitReviewDecisionRequest,
)
from app.services.pending_review_store import get_pending_review_store
from app.services.run_event_store import get_run_event_store
from app.services.run_state_service import get_run_state
from app.services.run_trace_store import get_run_trace_store
from app.services.ticket_repo import TicketNotFoundError, get_ticket_by_id

router = APIRouter(prefix="/api/v1", tags=["runs"])


def _new_thread_id(ticket_id: str) -> str:
    return f"ticket-{ticket_id}-{uuid4().hex[:8]}"


def _append_run_started(thread_id: str, ticket_id: str) -> None:
    event_store = get_run_event_store()
    event_store.append(
        event_store.create_event(
            thread_id=thread_id,
            ticket_id=ticket_id,
            event_type="run_started",
            status="running",
            message="Workflow run started.",
        )
    )


def _build_response(result: dict[str, Any]) -> RunTicketResponse:
    return RunTicketResponse(
        thread_id=result["thread_id"],
        ticket_id=result["ticket_id"],
        status=result["status"],
        classification=result["classification"],
        retrieved_chunks=result.get("retrieved_chunks", []),
        draft=result["draft"],
        risk_assessment=result.get("risk_assessment"),
        policy_assessment=result.get("policy_assessment"),
        pending_review=result.get("pending_review"),
        final_response=result.get("final_response"),
        proposed_actions=result.get("proposed_actions", []),
        executed_actions=result.get("executed_actions", []),
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


def _append_major_run_events(
    result: dict[str, Any],
    *,
    event_store: Any,
    pending_review: PendingReviewItem | None,
) -> None:
    thread_id = result["thread_id"]
    ticket_id = result["ticket_id"]
    classification = result.get("classification")
    retrieved_chunks = result.get("retrieved_chunks", [])
    draft = result.get("draft")
    risk_assessment = result.get("risk_assessment")
    policy_assessment = result.get("policy_assessment")

    if classification is not None:
        event_store.append(
            event_store.create_event(
                thread_id=thread_id,
                ticket_id=ticket_id,
                event_type="classify_completed",
                status="running",
                node_name="classify_ticket",
                message="Ticket classification is available.",
                payload={
                    "category": classification.category,
                    "priority": classification.priority,
                    "source": result.get("classification_source"),
                    "llm_error": result.get("classification_llm_error"),
                },
            )
        )

    event_store.append(
        event_store.create_event(
            thread_id=thread_id,
            ticket_id=ticket_id,
            event_type="retrieve_completed",
            status="running",
            node_name="retrieve_knowledge",
            message="Knowledge retrieval completed.",
            payload={"retrieved_chunk_count": len(retrieved_chunks)},
        )
    )

    if draft is not None:
        event_store.append(
            event_store.create_event(
                thread_id=thread_id,
                ticket_id=ticket_id,
                event_type="draft_completed",
                status="running",
                node_name="draft_reply",
                message="Draft reply generated.",
                payload={
                    "confidence": draft.confidence,
                    "source": result.get("draft_source"),
                    "llm_error": result.get("draft_llm_error"),
                },
            )
        )

    if risk_assessment is not None:
        event_store.append(
            event_store.create_event(
                thread_id=thread_id,
                ticket_id=ticket_id,
                event_type="risk_gate_completed",
                status="running",
                node_name="risk_gate",
                message=risk_assessment.reason,
                payload={
                    "review_required": risk_assessment.review_required,
                    "risk_flags": risk_assessment.risk_flags,
                    "failed_policy_ids": (
                        policy_assessment.failed_policy_ids
                        if policy_assessment is not None
                        else []
                    ),
                },
            )
        )

    if pending_review is not None:
        event_store.append(
            event_store.create_event(
                thread_id=thread_id,
                ticket_id=ticket_id,
                event_type="interrupt_created",
                status="waiting_review",
                node_name="human_review_interrupt",
                message="Workflow is waiting for human review.",
                payload={"allowed_decisions": pending_review.allowed_decisions},
            )
        )
        return

    event_store.append(
        event_store.create_event(
            thread_id=thread_id,
            ticket_id=ticket_id,
            event_type="run_completed",
            status=result["status"],
            node_name=result.get("current_node"),
            message="Workflow completed.",
            payload={"final_disposition": getattr(result.get("final_response"), "disposition", None)},
        )
    )


def _execute_ticket_run(
    ticket_id: str,
    thread_id: str,
    *,
    raise_http_errors: bool,
) -> RunTicketResponse | None:
    graph = get_support_graph()
    store = get_pending_review_store()
    event_store = get_run_event_store()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke(
            {"ticket_id": ticket_id, "thread_id": thread_id, "status": "queued"},
            config=config,
        )
    except TicketNotFoundError as exc:
        event_store.append(
            event_store.create_event(
                thread_id=thread_id,
                ticket_id=ticket_id,
                event_type="run_failed",
                status="failed",
                message="Ticket not found.",
            )
        )
        if raise_http_errors:
            raise HTTPException(status_code=404, detail="Ticket not found") from exc
        return None
    except Exception as exc:
        event_store.append(
            event_store.create_event(
                thread_id=thread_id,
                ticket_id=ticket_id,
                event_type="run_failed",
                status="failed",
                message=f"Workflow failed: {exc}",
            )
        )
        if raise_http_errors:
            raise HTTPException(status_code=500, detail=f"Workflow failed: {exc}") from exc
        return None

    pending_review = _extract_pending_review(result)
    if pending_review is not None:
        store.upsert(pending_review)
        result["pending_review"] = pending_review
        result["status"] = "waiting_review"
    else:
        store.remove(thread_id)

    _append_major_run_events(result, event_store=event_store, pending_review=pending_review)
    return _build_response(result)


@router.post("/tickets/{ticket_id}/run", response_model=RunTicketResponse)
def run_ticket(ticket_id: str) -> RunTicketResponse:
    thread_id = _new_thread_id(ticket_id)
    _append_run_started(thread_id, ticket_id)
    response = _execute_ticket_run(ticket_id, thread_id, raise_http_errors=True)
    if response is None:
        raise HTTPException(status_code=500, detail="Workflow failed")
    return response


@router.post("/tickets/{ticket_id}/runs/start", response_model=StartRunResponse)
def start_ticket_run(ticket_id: str, background_tasks: BackgroundTasks) -> StartRunResponse:
    try:
        get_ticket_by_id(ticket_id)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Ticket not found") from exc

    thread_id = _new_thread_id(ticket_id)
    _append_run_started(thread_id, ticket_id)
    background_tasks.add_task(
        _execute_ticket_run,
        ticket_id,
        thread_id,
        raise_http_errors=False,
    )
    return StartRunResponse(thread_id=thread_id, ticket_id=ticket_id, status="running")


@router.post("/runs/{thread_id}/resume", response_model=RunTicketResponse)
def resume_run(thread_id: str, body: SubmitReviewDecisionRequest) -> RunTicketResponse:
    graph = get_support_graph()
    store = get_pending_review_store()
    event_store = get_run_event_store()
    pending_review = store.get(thread_id)
    if pending_review is None:
        raise HTTPException(status_code=404, detail="Pending review not found")

    config = {"configurable": {"thread_id": thread_id}}
    event_store.append(
        event_store.create_event(
            thread_id=thread_id,
            ticket_id=pending_review.ticket_id,
            event_type="review_submitted",
            status="running",
            node_name="apply_review_decision",
            message="Reviewer submitted a decision.",
            payload={"decision": body.decision},
        )
    )
    event_store.append(
        event_store.create_event(
            thread_id=thread_id,
            ticket_id=pending_review.ticket_id,
            event_type="run_resumed",
            status="running",
            node_name="apply_review_decision",
            message="Workflow resumed after review.",
        )
    )
    try:
        result = graph.invoke(Command(resume=body.model_dump(mode="json")), config=config)
    except Exception as exc:
        event_store.append(
            event_store.create_event(
                thread_id=thread_id,
                ticket_id=pending_review.ticket_id,
                event_type="run_failed",
                status="failed",
                message=f"Workflow failed: {exc}",
            )
        )
        raise HTTPException(status_code=500, detail=f"Workflow failed: {exc}") from exc

    store.remove(thread_id)
    result["pending_review"] = None
    event_store.append(
        event_store.create_event(
            thread_id=thread_id,
            ticket_id=result["ticket_id"],
            event_type="run_completed",
            status=result["status"],
            node_name=result.get("current_node"),
            message=(
                "Workflow completed after review."
                if result["status"] == "done"
                else "Workflow ended in manual takeover after review."
            ),
            payload={"final_disposition": getattr(result.get("final_response"), "disposition", None)},
        )
    )
    return _build_response(result)


@router.get("/runs/{thread_id}/state", response_model=RunStateResponse)
def read_run_state(thread_id: str) -> RunStateResponse:
    state = get_run_state(thread_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run state not found")
    return state


@router.get("/runs/{thread_id}/timeline", response_model=RunTimelineResponse)
def read_run_timeline(thread_id: str) -> RunTimelineResponse:
    event_store = get_run_event_store()
    events = event_store.list_by_thread_id(thread_id)
    if not events:
        raise HTTPException(status_code=404, detail="Run timeline not found")
    return RunTimelineResponse(thread_id=thread_id, events=events)


@router.get("/runs/{thread_id}/trace", response_model=RunTraceResponse)
def read_run_trace(thread_id: str) -> RunTraceResponse:
    trace_store = get_run_trace_store()
    event_store = get_run_event_store()
    events = trace_store.list_by_thread_id(thread_id)
    if not events and not event_store.has_thread(thread_id):
        raise HTTPException(status_code=404, detail="Run trace not found")
    return RunTraceResponse(thread_id=thread_id, events=events)
