---
status: draft-v0.1
owner: project-maintainer
last_verified: 2026-04-24
source_of_truth_for:
  - domain models
  - API request/response schemas
  - node output contracts
  - structured output validation
  - ticket_id/thread_id/run_id semantics
---

# Contracts and Schemas

## 1. Purpose

This document defines the data contracts for `supportflow-agent`.

The project should be contract-first:

```text
schema first
-> node implementation
-> API response
-> frontend rendering
-> evaluation
```

The goal is to avoid fragile string parsing and make every important boundary inspectable.

## 2. Contract layers

| Layer         | Examples                                 | Tooling                        |
| ------------- | ---------------------------------------- | ------------------------------ |
| Domain model  | Ticket, KB chunk, review decision        | Pydantic                       |
| Graph state   | TicketState                              | TypedDict                      |
| Node output   | Classification, DraftReply, RiskDecision | Pydantic                       |
| API contract  | FastAPI request/response models          | Pydantic + response_model      |
| Frontend type | TypeScript types                         | generated or manually mirrored |
| Eval example  | inputs/reference outputs                 | JSONL / LangSmith dataset      |

## 3. ID semantics

| ID          | Meaning                     | Example                |
| ----------- | --------------------------- | ---------------------- |
| `ticket_id` | Business support ticket     | `T-1001`               |
| `thread_id` | LangGraph checkpoint thread | `ticket:T-1001:active` |
| `run_id`    | One execution attempt       | `run_20260424_001`     |
| `review_id` | Human review request        | `REV-1001`             |
| `doc_id`    | Knowledge document          | `refund_policy`        |
| `chunk_id`  | Chunk inside document       | `refund_policy#0001`   |

Common mistake:

```text
Do not use ticket_id, thread_id, and run_id interchangeably.
```

## 4. Core domain schemas

```python
from typing import Literal
from pydantic import BaseModel, Field

class TicketInput(BaseModel):
    ticket_id: str
    title: str
    content: str
    channel: Literal["web", "email", "chat"]
    customer_tier: Literal["free", "pro", "enterprise"] = "free"
    created_at: str | None = None

class TicketClassification(BaseModel):
    category: Literal["billing", "account", "product", "bug", "other"]
    priority: Literal["P0", "P1", "P2", "P3"]
    summary: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)

class KBHit(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    score: float
    snippet: str
    source_path: str | None = None

class DraftReply(BaseModel):
    answer: str
    citations: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    risk_flags: list[str] = []
    suggested_action: Literal["auto_finalize", "review", "manual_takeover"]

class RiskDecision(BaseModel):
    review_required: bool
    risk_flags: list[str]
    reason: str

class ReviewDecision(BaseModel):
    decision: Literal["approve", "edit", "reject"]
    reviewer_note: str | None = None
    edited_answer: str | None = None

class FinalReply(BaseModel):
    answer: str
    citations: list[str]
    disposition: Literal["finalized", "manual_takeover"]
```

## 5. Node output contracts

### `classify_ticket`

Input state keys:

```text
ticket
```

Output:

```python
{
    "classification": TicketClassification,
    "current_node": "classify_ticket"
}
```

Validation rules:

- `summary` must be non-empty.
- `confidence` must be between 0 and 1.
- `priority` must not be inferred from customer tier alone.
- P0/P1 requires a reason.

### `retrieve_knowledge`

Input state keys:

```text
ticket
classification
```

Output:

```python
{
    "retrieval_query": str,
    "retrieved_chunks": list[KBHit],
    "current_node": "retrieve_knowledge"
}
```

Validation rules:

- `retrieved_chunks` may be empty, but must be explicit.
- Each `KBHit` must include `doc_id`, `chunk_id`, `score`, and `snippet`.
- Snippet length should be bounded for frontend rendering.

### `draft_reply`

Input state keys:

```text
ticket
classification
retrieved_chunks
```

Output:

```python
{
    "draft": DraftReply,
    "current_node": "draft_reply"
}
```

Validation rules:

- `answer` must be non-empty.
- `citations` must reference retrieved `chunk_id` values.
- If `retrieved_chunks` is empty, confidence must be lower and `suggested_action` must not be `auto_finalize`.

### `risk_gate`

Input state keys:

```text
classification
retrieved_chunks
draft
```

Output:

```python
{
    "risk_flags": list[str],
    "review_required": bool,
    "current_node": "risk_gate"
}
```

Validation rules:

- Risk gate must be deterministic in v1.
- Billing + low confidence should trigger review.
- No evidence should trigger review.

## 6. FastAPI routes and contracts

### Health

```http
GET /healthz
```

Response:

```json
{ "status": "ok" }
```

### Tickets

```http
GET /api/v1/tickets
```

Response:

```python
class TicketListResponse(BaseModel):
    items: list[TicketInput]
```

```http
GET /api/v1/tickets/{ticket_id}
```

Response:

```python
class TicketDetailResponse(BaseModel):
    ticket: TicketInput
```

### Run workflow

```http
POST /api/v1/tickets/{ticket_id}/run
```

Response:

```python
class RunTicketResponse(BaseModel):
    ticket_id: str
    thread_id: str
    run_id: str
    status: Literal["running", "waiting_review", "done", "manual_takeover", "failed"]
    classification: TicketClassification | None = None
    retrieved_chunks: list[KBHit] = []
    draft: DraftReply | None = None
    risk_flags: list[str] = []
    interrupt: dict | None = None
    final_reply: FinalReply | None = None
```

### Resume review

```http
POST /api/v1/runs/{thread_id}/resume
```

Request:

```python
class ResumeRunRequest(BaseModel):
    decision: Literal["approve", "edit", "reject"]
    reviewer_note: str | None = None
    edited_answer: str | None = None
```

Response:

```python
class ResumeRunResponse(BaseModel):
    ticket_id: str
    thread_id: str
    status: Literal["done", "manual_takeover", "failed"]
    final_reply: FinalReply | None = None
```

### Run state

```http
GET /api/v1/runs/{thread_id}/state
```

Response:

```python
class RunStateResponse(BaseModel):
    ticket_id: str
    thread_id: str
    status: str
    current_node: str | None
    events: list[dict]
    state: dict
```

MVP note: expose summarized state first. Do not expose secrets, raw prompts, or full KB document bodies.

## 7. Frontend TypeScript mirror

```ts
export type TicketCategory =
  | "billing"
  | "account"
  | "product"
  | "bug"
  | "other";
export type TicketPriority = "P0" | "P1" | "P2" | "P3";

export type TicketClassification = {
  category: TicketCategory;
  priority: TicketPriority;
  summary: string;
  reason: string;
  confidence: number;
};

export type KBHit = {
  doc_id: string;
  chunk_id: string;
  title: string;
  score: number;
  snippet: string;
  source_path?: string | null;
};

export type DraftReply = {
  answer: string;
  citations: string[];
  confidence: number;
  risk_flags: string[];
  suggested_action: "auto_finalize" | "review" | "manual_takeover";
};
```

## 8. Contract failure policy

| Failure                 | Example                         | Handling                   |
| ----------------------- | ------------------------------- | -------------------------- |
| Invalid LLM output      | missing `category`              | retry once, then fail node |
| Missing citation        | draft cites unknown chunk       | force review               |
| No KB hits              | empty `retrieved_chunks`        | low confidence + review    |
| API response mismatch   | response_model validation error | fail request loudly        |
| Frontend unknown status | new enum not handled            | show fallback badge + log  |

Do not silently coerce unsupported values into valid-looking outputs.

## 9. Structured output policy

When using LLM for structured output:

- prefer Pydantic schema binding
- validate the returned object
- never parse important fields by regex
- store validation errors in state/events
- retry only when likely recoverable
- after retry failure, route to human review or manual takeover

## 10. Testing

Minimum tests:

```text
test_classification_contract_valid
test_draft_contract_requires_citations
test_run_response_model_validates
test_resume_request_reject_without_edited_answer
test_frontend_types_match_api_schema
```

## 11. Interview talking points

Strong answer:

> I separated domain schemas, graph state, node contracts, API responses, and frontend types. The reason is that LLM systems fail at boundaries, so I want each boundary to be validated and observable.

Weak answer:

> I used Pydantic because FastAPI uses it.

## 12. Update triggers

Update this document when:

- adding an API route
- changing a Pydantic model
- changing `TicketState`
- changing a node output
- adding frontend-visible status values
- changing ID policy
