from uuid import uuid4

from app.evals.schemas import EvalExample, EvalTargetOutput
from app.evals.ticket_fixtures import get_eval_ticket_by_id
from app.evals.tracing import TraceWriter
from app.graph.builder import get_support_graph
from app.schemas.graph import DraftReply, TicketClassification
from app.services.policy_engine import (
    HIGH_RISK_KEYWORDS,
    LEGAL_SECURITY_MARKERS,
    PROMPT_INJECTION_MARKERS,
)
from app.services.retrieval import retrieve_knowledge


PRIORITY_MAP = {
    "urgent": "P0",
    "high": "P1",
    "medium": "P2",
    "low": "P3",
}


def _ticket_query(ticket: dict[str, object]) -> str:
    return " ".join(
        [
            str(ticket.get("subject", "")),
            str(ticket.get("preview", "")),
        ]
    ).strip()


def _action_statuses_by_type(actions: list[object]) -> dict[str, list[str]]:
    statuses_by_type: dict[str, list[str]] = {}
    for action in actions:
        action_type = getattr(action, "action_type", None)
        status = getattr(action, "status", None)
        if isinstance(action_type, str) and isinstance(status, str):
            statuses_by_type.setdefault(action_type, []).append(status)
    return statuses_by_type


def _match_category(text: str) -> tuple[str, str]:
    normalized = text.lower()

    if any(keyword in normalized for keyword in ["refund", "invoice", "charge", "billing", "credit"]):
        return "billing", "Ticket mentions billing, refund, invoice, charge, or credit language."
    if (
        any(keyword in normalized for keyword in ["retention window", "sso", "trial"])
        and "crash" not in normalized
        and "failed" not in normalized
    ):
        return "product", "Ticket asks about product plan, SSO, trial, or retention behavior."
    if any(keyword in normalized for keyword in ["bug", "error", "failed", "export", "crash", "outage"]):
        return "bug", "Ticket describes a product failure, outage, crash, or export error."
    if any(keyword in normalized for keyword in ["login", "password", "locked", "unlock", "admin", "mfa", "owner"]):
        return "account", "Ticket mentions account access, MFA, admin, or ownership language."
    if any(keyword in normalized for keyword in ["plan", "seat", "onboarding", "subscription", "sso", "trial"]):
        return "product", "Ticket asks about product plan, onboarding, SSO, or trial behavior."
    return "other", "Ticket does not match billing, account, bug, or product rules."


def _classify_ticket(ticket: dict[str, object]) -> TicketClassification:
    category, reason = _match_category(_ticket_query(ticket))
    source_priority = str(ticket.get("priority", "medium")).lower()
    return TicketClassification(
        category=category,  # type: ignore[arg-type]
        priority=PRIORITY_MAP.get(source_priority, "P2"),  # type: ignore[arg-type]
        reason=reason,
    )


def _retrieval_diagnostics(hits: list[object]) -> list[dict[str, object]]:
    return [
        {
            "doc_id": getattr(hit, "doc_id", None),
            "title": getattr(hit, "title", None),
            "score": getattr(hit, "score", None),
            "matched_terms": getattr(hit, "matched_terms", []),
            "category": getattr(hit, "category", None),
            "category_match": getattr(hit, "category_match", False),
            "freshness": getattr(hit, "freshness", None),
            "policy_severity": getattr(hit, "policy_severity", None),
        }
        for hit in hits
    ]


def _draft_from_hits(
    *,
    ticket: dict[str, object],
    classification: TicketClassification,
    hits: list[object],
) -> DraftReply:
    customer_name = str(ticket.get("customer_name", "there"))
    if hits:
        lead_hit = hits[0]
        answer = (
            f"Hi {customer_name},\n\n"
            f"We reviewed your {classification.category} request about "
            f"\"{ticket.get('subject', 'your issue')}\". Based on "
            f"{getattr(lead_hit, 'title', 'the retrieved support guidance')}, "
            "support should verify the relevant details and reply with the next step.\n\n"
            "Best,\nSupportflow Agent"
        )
        citations = [str(getattr(lead_hit, "doc_id"))]
        confidence = {
            "product": 0.91,
            "account": 0.78,
            "billing": 0.82,
            "bug": 0.76,
        }.get(classification.category, 0.72)
    else:
        answer = (
            f"Hi {customer_name},\n\n"
            f"We reviewed your request about \"{ticket.get('subject', 'your issue')}\" "
            "and need a support specialist to confirm the next step before we send a final answer.\n\n"
            "Best,\nSupportflow Agent"
        )
        citations = []
        confidence = 0.35

    return DraftReply(answer=answer, citations=citations, confidence=confidence)


def _basic_policy_failures(
    *,
    ticket: dict[str, object],
    classification: TicketClassification,
    hits: list[object],
    draft: DraftReply,
) -> list[str]:
    text = _ticket_query(ticket).lower()
    kb_text = " ".join(str(getattr(hit, "snippet", "")) for hit in hits).lower()
    combined_input = f"{text} {kb_text}"
    failures: list[str] = []

    if classification.priority in {"P0", "P1"}:
        failures.append("priority_requires_review")
    if draft.confidence < 0.75:
        failures.append("low_confidence")
    if not hits:
        failures.append("no_evidence")
    if hits and not set(draft.citations) & {str(getattr(hit, "doc_id")) for hit in hits}:
        failures.append("missing_citations")
    if classification.category == "billing" and draft.confidence < 0.85:
        failures.append("billing_sensitive")
    if any(keyword in text for keyword in HIGH_RISK_KEYWORDS):
        failures.append("sensitive_request")
    if any(marker in combined_input for marker in PROMPT_INJECTION_MARKERS):
        failures.append("prompt_injection")
    if any(marker in text for marker in LEGAL_SECURITY_MARKERS):
        failures.append("legal_or_security_risk")

    return failures


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
    retrieved_evidence_by_doc_id = {
        hit.doc_id: f"{hit.title} {hit.snippet}"
        for hit in hits
    }
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
        metadata={
            "retrieval_query": _ticket_query(ticket),
            "retrieved_evidence_by_doc_id": retrieved_evidence_by_doc_id,
            "retrieval_diagnostics": _retrieval_diagnostics(hits),
            "proposed_action_types": [],
            "action_statuses_by_type": {},
        },
    )


def run_rag_policy_baseline(
    example: EvalExample, trace_writer: TraceWriter | None = None
) -> EvalTargetOutput:
    ticket = get_eval_ticket_by_id(example.inputs.ticket_id)
    classification = _classify_ticket(ticket)
    query = _ticket_query(ticket)

    if trace_writer is not None:
        trace_writer.emit(
            target="rag_policy_baseline",
            example_id=example.id,
            ticket_id=example.inputs.ticket_id,
            stage="load_ticket",
            status="done",
            payload={"subject": ticket.get("subject")},
        )

    hits = retrieve_knowledge(query, category=classification.category)
    retrieved_doc_ids = [hit.doc_id for hit in hits]
    retrieved_evidence_by_doc_id = {
        hit.doc_id: f"{hit.title} {hit.snippet}"
        for hit in hits
    }
    draft = _draft_from_hits(ticket=ticket, classification=classification, hits=list(hits))
    failed_policy_ids = _basic_policy_failures(
        ticket=ticket,
        classification=classification,
        hits=list(hits),
        draft=draft,
    )
    review_required = bool(failed_policy_ids)
    status = "waiting_review" if review_required else "done"
    trace_url = None

    if trace_writer is not None:
        trace_url = trace_writer.emit(
            target="rag_policy_baseline",
            example_id=example.id,
            ticket_id=example.inputs.ticket_id,
            stage="retrieve_policy_and_draft",
            status=status,
            payload={
                "category": classification.category,
                "retrieved_doc_ids": retrieved_doc_ids,
                "citations": draft.citations,
                "review_required": review_required,
                "failed_policy_ids": failed_policy_ids,
            },
        )

    return EvalTargetOutput(
        target="rag_policy_baseline",
        example_id=example.id,
        ticket_id=example.inputs.ticket_id,
        status=status,
        category=classification.category,
        category_supported=True,
        retrieved_doc_ids=retrieved_doc_ids,
        citations=draft.citations,
        answer=draft.answer,
        review_required=review_required,
        trace_url=trace_url,
        metadata={
            "retrieval_query": query,
            "retrieved_evidence_by_doc_id": retrieved_evidence_by_doc_id,
            "retrieval_diagnostics": _retrieval_diagnostics(hits),
            "risk_flags": failed_policy_ids,
            "failed_policy_ids": failed_policy_ids,
            "proposed_action_types": [],
            "action_statuses_by_type": {},
        },
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
    proposed_actions = result.get("proposed_actions", [])
    action_statuses_by_type = _action_statuses_by_type(proposed_actions)
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
    retrieved_evidence_by_doc_id = {
        hit.doc_id: f"{hit.title} {hit.snippet}"
        for hit in retrieved_chunks
    }
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
                "retrieved_evidence_by_doc_id": retrieved_evidence_by_doc_id,
                "retrieval_diagnostics": _retrieval_diagnostics(retrieved_chunks),
                "citations": citations,
                "review_required": review_required,
                "interrupted": interrupted,
                "risk_flags": getattr(risk_assessment, "risk_flags", []),
                "failed_policy_ids": getattr(policy_assessment, "failed_policy_ids", []),
                "proposed_action_types": list(action_statuses_by_type),
                "action_statuses_by_type": action_statuses_by_type,
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
            "retrieved_evidence_by_doc_id": retrieved_evidence_by_doc_id,
            "retrieval_diagnostics": _retrieval_diagnostics(retrieved_chunks),
            "risk_flags": getattr(risk_assessment, "risk_flags", []),
            "failed_policy_ids": getattr(policy_assessment, "failed_policy_ids", []),
            "proposed_action_types": list(action_statuses_by_type),
            "action_statuses_by_type": action_statuses_by_type,
            "final_disposition": getattr(final_response, "disposition", None),
        },
    )
