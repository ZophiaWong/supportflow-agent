# LangGraph Workflow Design

Status: draft  
Last updated: 2026-04-24  
Source of truth for: LangGraph state, nodes, edges, routing, interrupt, checkpoint behavior

## 1. Purpose

This document defines the main LangGraph workflow for supportflow-agent.
The project is workflow-first, not free-agent-first.

The goal is to process a support ticket through a controlled workflow:

1. Load ticket context
2. Classify ticket
3. Retrieve knowledge
4. Draft reply
5. Run risk gate
6. Interrupt for human review if needed
7. Apply review decision
8. Finalize response

## 2. Why LangGraph

This project uses LangGraph because the workflow requires:

- Shared state across multiple processing steps
- Conditional routing based on classification and risk
- Human-in-the-loop interruption
- Resume execution after review
- Inspectable intermediate states
- Future tracing and evaluation at node level

This is not a plain RAG chatbot because the system must make routing decisions, preserve workflow state, and pause for review.

## 3. Non-goals

The MVP does not include:

- Multi-agent collaboration
- Long-term user memory
- Autonomous tool planning
- External ticket system write-back
- Real email sending
- Multi-tenant workflows

## 4. State model

The graph state should store raw and structured data, not prompt strings.

```python
from typing import Any, Literal, TypedDict
from app.schemas.graph import TicketClassification, KBHit, DraftReply, ReviewDecision, FinalResponse

class TicketState(TypedDict, total=False):
    thread_id: str
    run_id: str
    ticket_id: str

    ticket: dict[str, Any]

    classification: TicketClassification
    retrieval_query: str
    retrieved_chunks: list[KBHit]

    draft: DraftReply

    risk_result: dict[str, Any]
    review_required: bool
    review: ReviewDecision

    final_response: FinalResponse

    status: Literal[
        "queued",
        "running",
        "waiting_review",
        "done",
        "manual_takeover",
        "failed"
    ]

    current_node: str
    errors: list[str]
```
