from fastapi import APIRouter, HTTPException

from app.graph.builder import get_support_graph
from app.schemas.graph import RunTicketResponse
from app.services.ticket_repo import TicketNotFoundError

router = APIRouter(prefix="/api/v1", tags=["runs"])


@router.post("/tickets/{ticket_id}/run", response_model=RunTicketResponse)
def run_ticket(ticket_id: str) -> RunTicketResponse:
    graph = get_support_graph()
    thread_id = f"ticket-{ticket_id}"
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

    return RunTicketResponse(
        thread_id=thread_id,
        ticket_id=ticket_id,
        status=result["status"],
        classification=result["classification"],
        retrieved_chunks=result["retrieved_chunks"],
        draft=result["draft"],
    )
