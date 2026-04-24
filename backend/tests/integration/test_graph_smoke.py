from app.graph.builder import get_support_graph


def test_graph_smoke() -> None:
    graph = get_support_graph()
    result = graph.invoke(
        {
            "ticket_id": "ticket-1002",
            "thread_id": "ticket-ticket-1002",
            "status": "queued",
        },
        config={"configurable": {"thread_id": "ticket-ticket-1002"}},
    )

    assert result["status"] == "done"
    assert result["classification"].category == "account"
    assert result["retrieved_chunks"][0].doc_id == "account_unlock"
    assert result["draft"].citations == ["account_unlock"]
