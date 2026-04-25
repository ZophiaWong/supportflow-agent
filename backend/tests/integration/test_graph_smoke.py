from langgraph.types import Command

from app.graph.builder import get_support_graph


def test_graph_smoke_auto_finalizes_low_risk_ticket() -> None:
    graph = get_support_graph()
    result = graph.invoke(
        {
            "ticket_id": "ticket-1003",
            "thread_id": "ticket-ticket-1003",
            "status": "queued",
        },
        config={"configurable": {"thread_id": "ticket-ticket-1003"}},
    )

    assert result["status"] == "done"
    assert result["classification"].category == "product"
    assert result["retrieved_chunks"][0].doc_id == "annual_plan_seats"
    assert result["final_response"].disposition == "auto_finalized"


def test_graph_smoke_interrupts_and_resumes_high_risk_ticket() -> None:
    graph = get_support_graph()
    config = {"configurable": {"thread_id": "ticket-ticket-1001"}}

    interrupted = graph.invoke(
        {
            "ticket_id": "ticket-1001",
            "thread_id": "ticket-ticket-1001",
            "status": "queued",
        },
        config=config,
    )

    assert "__interrupt__" in interrupted
    assert interrupted["classification"].category == "billing"
    assert interrupted["risk_assessment"].review_required is True

    resumed = graph.invoke(
        Command(resume={"decision": "edit", "edited_answer": "Custom approved answer."}),
        config=config,
    )

    assert resumed["status"] == "done"
    assert resumed["final_response"].disposition == "edited"
    assert resumed["final_response"].answer == "Custom approved answer."
