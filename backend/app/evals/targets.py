from uuid import uuid4

from app.evals.schemas import EvalExample, EvalTargetOutput
from app.evals.ticket_fixtures import get_eval_ticket_by_id
from app.evals.tracing import TraceWriter
from app.graph.builder import get_support_graph
from app.services.retrieval import retrieve_knowledge


def _ticket_query(ticket: dict[str, object]) -> str:
    return " ".join(
        [
            str(ticket.get("subject", "")),
            str(ticket.get("preview", "")),
        ]
    ).strip()


def run_plain_rag_baseline(
    example: EvalExample, trace_writer: TraceWriter | None = None
) -> EvalTargetOutput:
    ticket = get_eval_ticket_by_id(example.inputs.ticket_id)
    if trace_writer is not None:
        trace_writer.emit(
            target="plain_rag_baseline",
            example_id=example.id,
            ticket_id=example.inputs.ticket_id,
            stage="load_ticket",
            status="done",
            payload={"subject": ticket.get("subject")},
        )

    hits = retrieve_knowledge(_ticket_query(ticket))
    retrieved_doc_ids = [hit.doc_id for hit in hits]
    citations = retrieved_doc_ids[:1]
    trace_url = None
    lead_title = hits[0].title if hits else "the available support guidance"
    answer = (
        f"Hi {ticket.get('customer_name', 'there')},\n\n"
        f"We reviewed your request about \"{ticket.get('subject', 'your issue')}\". "
        f"Based on {lead_title}, support should verify the relevant details and "
        "reply with the next step.\n\n"
        "Best,\nSupportflow Agent"
    )

    if trace_writer is not None:
        trace_url = trace_writer.emit(
            target="plain_rag_baseline",
            example_id=example.id,
            ticket_id=example.inputs.ticket_id,
            stage="retrieve_and_draft",
            status="done",
            payload={
                "retrieved_doc_ids": retrieved_doc_ids,
                "citations": citations,
                "review_required": False,
            },
        )

    return EvalTargetOutput(
        target="plain_rag_baseline",
        example_id=example.id,
        ticket_id=example.inputs.ticket_id,
        status="done",
        category=None,
        category_supported=False,
        retrieved_doc_ids=retrieved_doc_ids,
        citations=citations,
        answer=answer,
        review_required=False,
        trace_url=trace_url,
        metadata={"retrieval_query": _ticket_query(ticket)},
    )


def run_graph_v1(example: EvalExample, trace_writer: TraceWriter | None = None) -> EvalTargetOutput:
    graph = get_support_graph()
    thread_id = f"eval-{example.id}-{uuid4().hex[:8]}"
    result = graph.invoke(
        {
            "ticket_id": example.inputs.ticket_id,
            "thread_id": thread_id,
            "status": "queued",
            "ticket_source": "eval",
        },
        config={"configurable": {"thread_id": thread_id}},
    )

    classification = result.get("classification")
    retrieved_chunks = result.get("retrieved_chunks", [])
    draft = result.get("draft")
    final_response = result.get("final_response")
    risk_assessment = result.get("risk_assessment")
    policy_assessment = result.get("policy_assessment")
    interrupted = "__interrupt__" in result
    status = "waiting_review" if interrupted else result.get("status", "failed")
    review_required = (
        True
        if interrupted
        else bool(getattr(risk_assessment, "review_required", result.get("review_required", False)))
    )
    citations = (
        list(final_response.citations)
        if final_response is not None
        else list(getattr(draft, "citations", []))
    )
    answer = (
        final_response.answer
        if final_response is not None
        else getattr(draft, "answer", None)
    )
    retrieved_doc_ids = [hit.doc_id for hit in retrieved_chunks]
    trace_url = None

    if trace_writer is not None:
        trace_url = trace_writer.emit(
            target="graph_v1",
            example_id=example.id,
            ticket_id=example.inputs.ticket_id,
            stage="graph_run",
            status=status,
            payload={
                "thread_id": thread_id,
                "category": getattr(classification, "category", None),
                "retrieved_doc_ids": retrieved_doc_ids,
                "citations": citations,
                "review_required": review_required,
                "interrupted": interrupted,
            },
        )

    return EvalTargetOutput(
        target="graph_v1",
        example_id=example.id,
        ticket_id=example.inputs.ticket_id,
        status=status,
        category=getattr(classification, "category", None),
        category_supported=True,
        retrieved_doc_ids=retrieved_doc_ids,
        citations=citations,
        answer=answer,
        review_required=review_required,
        trace_url=trace_url,
        metadata={
            "thread_id": thread_id,
            "risk_flags": getattr(risk_assessment, "risk_flags", []),
            "failed_policy_ids": getattr(policy_assessment, "failed_policy_ids", []),
            "final_disposition": getattr(final_response, "disposition", None),
        },
    )
