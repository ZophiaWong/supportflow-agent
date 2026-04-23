# Deliver the Day 2 LangGraph Happy Path

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository includes `docs/PLANS.md`. Maintain this document according to that file, especially the requirements that every ExecPlan be self-contained, written in plain English, and focused on observable working behavior.

## Purpose / Big Picture

After this change, supportflow-agent will stop being only a ticket list and static UI shell. A user will be able to select a demo support ticket, run one synchronous LangGraph workflow, and see the workflow output in the ticket detail area: a classification, retrieved knowledge-base evidence, and a draft reply.

This matters because the product goal is a workflow-first AI support app. The Day 2 work proves the smallest useful workflow loop: load a ticket, classify it, retrieve relevant local knowledge, draft a reply, return a structured FastAPI response, and render that response in React. Model quality is intentionally out of scope; deterministic rules and templates are acceptable because the purpose is to validate orchestration, contracts, and UI integration.

## Progress

- [x] (2026-04-23 15:20 HKT) Rewrote this ExecPlan as a pure-English, PLANS.md-shaped living document while preserving the Day 2 happy-path scope.
- [ ] Align demo knowledge-base documents so each major demo ticket category has searchable English content.
- [ ] Add backend service boundaries for ticket loading and local knowledge retrieval.
- [ ] Add graph state, structured graph schemas, four graph nodes, and the synchronous graph builder.
- [ ] Add the run-ticket API endpoint and route it through FastAPI.
- [ ] Add frontend types, API client support, ticket detail display, workflow result display, and page wiring.
- [ ] Add and run at least one backend smoke test proving the graph/API happy path.
- [ ] Run frontend checks or tests proving the selected ticket and workflow result UI still render.

## Surprises & Discoveries

- Observation: The original active plan mixed English and Chinese and did not include several mandatory sections from `docs/PLANS.md`.
  Evidence: The document had sections for scope, state design, and API sketches, but it lacked `Context and Orientation`, `Plan of Work`, `Concrete Steps`, `Validation and Acceptance`, `Idempotence and Recovery`, `Artifacts and Notes`, and `Interfaces and Dependencies`.

- Observation: The current repository already has a minimal backend, frontend, ticket data, and one knowledge-base document, so Day 2 should extend the existing shape rather than replace it.
  Evidence: Existing files include `backend/app/main.py`, `backend/app/api/v1/tickets.py`, `backend/app/schemas/ticket.py`, `backend/app/graph/state.py`, `frontend/src/pages/TicketsPage.tsx`, `frontend/src/components/TicketList.tsx`, `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts`, `data/sample_tickets/demo_tickets.json`, and `data/kb/refund_policy.md`.

## Decision Log

- Decision: Keep Day 2 to a fixed synchronous graph path with deterministic classification, lexical retrieval, and template drafting.
  Rationale: The goal is to prove workflow orchestration and API/UI contracts before introducing LLM calls, conditional routing, streaming, human review, or tracing.
  Date/Author: 2026-04-23 / Codex

- Decision: Put ticket file access behind `backend/app/services/ticket_repo.py` and knowledge-base scanning behind `backend/app/services/retrieval.py`.
  Rationale: FastAPI routes and graph nodes should depend on small service functions, not on JSON or Markdown file paths. This keeps later replacement with a database, vector store, or external ticket system local to service modules.
  Date/Author: 2026-04-23 / Codex

- Decision: Store structured intermediate values in graph state rather than collapsing the ticket, classification, evidence, and draft into one prompt string.
  Rationale: Structured state is easier to debug, easier to expose through an API, and prepares the repository for Day 3 risk gating and human review resume behavior.
  Date/Author: 2026-04-23 / Codex

- Decision: Use `thread_id = "ticket-{ticket_id}"` for the Day 2 run endpoint.
  Rationale: LangGraph checkpointers identify runs by a configurable thread identifier. A deterministic ticket-based thread id is simple, stable for smoke tests, and can be replaced later if the product needs multiple runs per ticket.
  Date/Author: 2026-04-23 / Codex

## Outcomes & Retrospective

No implementation outcome has been recorded yet. When the backend graph, API, frontend panel, and smoke tests are complete, update this section with what works, what remains intentionally deferred to Day 3, and any lessons learned while integrating LangGraph with FastAPI and React.

## Context and Orientation

supportflow-agent is an AI support workflow app for ticket triage and response drafting. The repository is intentionally small. The backend is a FastAPI application in `backend/app`. FastAPI is a Python web framework that maps HTTP requests to Python functions. The frontend is a React application in `frontend/src`. React renders the browser UI. LangGraph is the workflow library used by the backend to run a graph, which in this plan means a fixed sequence of named Python functions called nodes. Each node reads and returns part of a shared state dictionary.

The existing backend entrypoint is `backend/app/main.py`. Existing route modules live under `backend/app/api/v1`. Existing Pydantic API schemas live under `backend/app/schemas`. Pydantic models validate Python data and FastAPI responses. Existing graph code starts at `backend/app/graph/state.py`, but Day 2 needs a fuller state type, node modules, and a graph builder. The demo tickets are stored in `data/sample_tickets/demo_tickets.json`. Local knowledge-base Markdown files live in `data/kb`.

The existing frontend ticket page is `frontend/src/pages/TicketsPage.tsx`. Shared frontend API functions live in `frontend/src/lib/api.ts`, and shared TypeScript types live in `frontend/src/lib/types.ts`. The current list component is `frontend/src/components/TicketList.tsx`. Day 2 should add a ticket detail component and a workflow result panel, then wire them into the ticket page.

The Day 2 happy path is:

    User selects ticket
    -> frontend calls POST /api/v1/tickets/{ticket_id}/run
    -> FastAPI invokes LangGraph
    -> load_ticket_context reads the ticket
    -> classify_ticket assigns category and priority
    -> retrieve_knowledge finds local KB snippets
    -> draft_reply creates a draft answer with citations
    -> FastAPI returns a structured response
    -> frontend displays classification, retrieved chunks, and draft

The following terms are used in this plan. A ticket is a support request from `data/sample_tickets/demo_tickets.json`. A knowledge-base document is a Markdown file in `data/kb` that contains support guidance. A graph node is a Python function that receives graph state and returns a partial state update. A checkpointer is LangGraph storage for graph run state; for Day 2 use an in-memory checkpointer because the run is synchronous and local. A smoke test is a small test that proves the main path works end-to-end enough to catch wiring failures.

## Plan of Work

First, align the demo data and knowledge base. Keep `data/kb/refund_policy.md`, and add `data/kb/account_unlock.md` and `data/kb/bug_export_issue.md`. The knowledge-base text should be in English and should contain terms that overlap with the demo tickets. If a demo ticket is still Chinese, either make the KB bilingual or include enough English keywords in the retrieval query construction to make the match reliable. At the end of this step, billing/refund, account access, and bug/export cases should each have at least one relevant local document.

Second, add backend service boundaries. Create `backend/app/services/ticket_repo.py` with functions that read `data/sample_tickets/demo_tickets.json`, return all tickets, and return one ticket by id. Create `backend/app/services/retrieval.py` with a simple lexical retriever that reads Markdown files from `data/kb`, scores documents by keyword overlap, and returns the top matches as structured hits. The route layer must not open JSON files directly, and graph nodes must not walk the KB directory directly.

Third, add structured graph contracts. Create `backend/app/schemas/graph.py` with Pydantic models for `TicketClassification`, `KBHit`, `DraftReply`, and `RunTicketResponse`. Update `backend/app/graph/state.py` so `TicketState` is a `TypedDict` containing the ticket id, optional thread id, raw ticket object, classification, retrieval query, retrieved chunks, draft, status, current node, and optional error. Keep the state explicit and inspectable; do not replace it with a single prompt string.

Fourth, implement the four graph nodes. Create `backend/app/graph/nodes/load_ticket_context.py`, `classify_ticket.py`, `retrieve_knowledge.py`, and `draft_reply.py`. `load_ticket_context` reads the ticket through `ticket_repo` and marks the run as running. `classify_ticket` uses deterministic keyword rules. `retrieve_knowledge` builds a query from the ticket and classification and delegates to `retrieval.py`. `draft_reply` uses a template and the retrieved hits to create a safe draft; if no hits exist, it should lower confidence and avoid inventing citations.

Fifth, compile the graph. Create `backend/app/graph/builder.py` with a cached `get_support_graph()` function. The graph shape is fixed for Day 2: `START` to `load_ticket_context`, then `classify_ticket`, then `retrieve_knowledge`, then `draft_reply`, then `END`. Use `StateGraph(TicketState)` and compile with `InMemorySaver`. Do not add conditional routing, review interrupts, streaming, or multi-agent behavior in this plan.

Sixth, expose the run endpoint. Create `backend/app/api/v1/runs.py` with `POST /tickets/{ticket_id}/run`, returning `RunTicketResponse`. The route should construct `thread_id`, invoke the graph with `{"ticket_id": ticket_id}`, pass `{"configurable": {"thread_id": thread_id}}`, translate a missing ticket into HTTP 404, and let unexpected errors surface as HTTP 500 with a clear message. Register the router in `backend/app/main.py`.

Seventh, update the frontend. Extend `frontend/src/lib/types.ts` with types matching the backend response. Extend `frontend/src/lib/api.ts` with a `runTicket(ticketId: string)` function. Add `frontend/src/components/TicketDetail.tsx` for selected ticket fields and `frontend/src/components/WorkflowResultPanel.tsx` for classification, evidence, and draft. Update `frontend/src/pages/TicketsPage.tsx` so selecting a ticket shows details and clicking a "Run workflow" button calls the API and renders the result. Keep the UI minimal but clear.

Eighth, add tests and validation. Add `backend/tests/integration/test_graph_smoke.py` or a similarly named backend test that invokes the run endpoint for a known demo ticket and asserts `status == "done"`, a non-empty classification, at least one retrieved chunk when the ticket has matching KB content, and a draft answer. Update or add frontend tests only as needed to cover the new selected-ticket and workflow-result UI without overbuilding.

## Milestones

Milestone 1 proves data alignment. At the end of this milestone, local knowledge-base documents exist for the major demo categories and the retriever has content it can match. Validate by inspecting `data/kb` and confirming that each document has a clear title, support guidance, and words that overlap with the target tickets.

Milestone 2 proves backend boundaries. At the end of this milestone, ticket loading and knowledge retrieval are implemented as service modules. Validate by running backend tests that import the service functions or by adding a small smoke test around `get_ticket_by_id` and retrieval. A novice should be able to tell that API routes no longer need to know where the JSON and Markdown files are stored.

Milestone 3 proves the graph. At the end of this milestone, `get_support_graph().invoke({"ticket_id": "T-1001"}, config={"configurable": {"thread_id": "ticket-T-1001"}})` returns a state containing `status`, `classification`, `retrieved_chunks`, and `draft`. This milestone is complete only when the graph itself works without the frontend.

Milestone 4 proves the API. At the end of this milestone, `POST /api/v1/tickets/T-1001/run` returns HTTP 200 and a structured JSON body, while an unknown ticket id returns HTTP 404. This milestone is complete when the behavior is visible through FastAPI tests or a local HTTP request.

Milestone 5 proves the product slice. At the end of this milestone, the frontend can show ticket details, run the workflow for the selected ticket, and display the classification, KB hits, and draft reply. This milestone is complete when the browser UI or frontend tests demonstrate the full interaction.

## Concrete Steps

Work from the repository root:

    cd /home/poter/resume-pj/supportflow-agent

Inspect the current backend and frontend before editing:

    sed -n '1,220p' backend/app/main.py
    sed -n '1,220p' backend/app/api/v1/tickets.py
    sed -n '1,220p' backend/app/schemas/ticket.py
    sed -n '1,260p' frontend/src/pages/TicketsPage.tsx
    sed -n '1,220p' frontend/src/lib/api.ts
    sed -n '1,220p' frontend/src/lib/types.ts

Implement the files in this order so each layer can be validated before the next layer depends on it:

1. `data/kb/refund_policy.md`
2. `data/kb/account_unlock.md`
3. `data/kb/bug_export_issue.md`
4. `backend/app/services/__init__.py`
5. `backend/app/services/ticket_repo.py`
6. `backend/app/services/retrieval.py`
7. `backend/app/schemas/graph.py`
8. `backend/app/graph/state.py`
9. `backend/app/graph/nodes/__init__.py`
10. `backend/app/graph/nodes/load_ticket_context.py`
11. `backend/app/graph/nodes/classify_ticket.py`
12. `backend/app/graph/nodes/retrieve_knowledge.py`
13. `backend/app/graph/nodes/draft_reply.py`
14. `backend/app/graph/builder.py`
15. `backend/app/api/v1/runs.py`
16. `backend/app/main.py`
17. `frontend/src/lib/types.ts`
18. `frontend/src/lib/api.ts`
19. `frontend/src/components/TicketDetail.tsx`
20. `frontend/src/components/WorkflowResultPanel.tsx`
21. `frontend/src/pages/TicketsPage.tsx`
22. `backend/tests/integration/test_graph_smoke.py`
23. Existing or new frontend tests under `frontend/src`

Run backend tests from `backend`:

    cd /home/poter/resume-pj/supportflow-agent/backend
    uv run pytest

Expected success looks like this, with the exact test count allowed to differ as tests are added:

    ============================= test session starts =============================
    ...
    backend/tests/test_api.py .
    backend/tests/integration/test_graph_smoke.py .
    ============================== 2 passed in ...s ===============================

Run frontend tests from `frontend`:

    cd /home/poter/resume-pj/supportflow-agent/frontend
    npm test -- --run

Expected success looks like this, with the exact test count allowed to differ:

    RUN  v...
    PASS src/components/TicketList.test.tsx ...
    PASS src/pages/TicketsPage.test.tsx ...
    Test Files ... passed

If there is no dedicated frontend test script, inspect `frontend/package.json` and run the available check command that best proves the React code builds or tests. Record the actual command and result in `Artifacts and Notes`.

## Validation and Acceptance

The backend acceptance criteria are behavior-focused. Running the backend test suite must pass. A known ticket id, such as `T-1001` if it exists in `data/sample_tickets/demo_tickets.json`, must be accepted by `POST /api/v1/tickets/{ticket_id}/run`. The response must include `thread_id`, `ticket_id`, `status`, `classification`, `retrieved_chunks`, and `draft`. `status` must be `done`. `classification.category` must be one of `billing`, `account`, `product`, `bug`, or `other`. `classification.priority` must be one of `P0`, `P1`, `P2`, or `P3`. `retrieved_chunks` must be a list of objects containing `doc_id`, `title`, `score`, and `snippet`. `draft.answer` must be non-empty, and `draft.citations` must name only retrieved documents.

The missing-ticket behavior must also be visible. Calling the run endpoint with an id that is not in `data/sample_tickets/demo_tickets.json` must return HTTP 404 rather than a successful empty result.

The frontend acceptance criteria are also behavior-focused. On the ticket page, a user must be able to select a ticket, see its details, click "Run workflow", and then see classification, evidence, and a draft reply. Loading and error states should be visible enough that a user is not left with a dead button or blank panel.

This plan is complete only when the observable product slice works without manual data manipulation. The local system should still honor repository guardrails: no multi-agent patterns, no unnecessary abstractions, no database migration, no vector database, no streaming, and no Day 3 human review interrupt work.

## Idempotence and Recovery

The implementation is additive and safe to repeat. Re-running tests must not mutate persistent data. The in-memory LangGraph checkpointer is intentionally process-local, so restarting the backend resets graph run state. That is acceptable for Day 2.

If a knowledge-base file is edited with poor content and retrieval stops returning hits, restore the document to plain Markdown with a short title and support guidance that includes words from the matching demo ticket. If a graph node fails after partial implementation, run the graph directly before debugging the API so the failure stays close to the node. If the API works but the UI fails, inspect browser network requests and compare the actual JSON shape to `frontend/src/lib/types.ts`.

Do not use destructive cleanup commands. Do not remove existing user changes. If tests create cache files such as `__pycache__`, `.pytest_cache`, or frontend build artifacts, leave them alone unless the user explicitly asks for cleanup.

## Artifacts and Notes

The final implementation should record concise evidence here when commands have been run.

Current planning evidence:

    docs/PLANS.md requires these sections to be present and maintained:
    Progress
    Surprises & Discoveries
    Decision Log
    Outcomes & Retrospective
    Context and Orientation
    Plan of Work
    Concrete Steps
    Validation and Acceptance
    Idempotence and Recovery
    Artifacts and Notes
    Interfaces and Dependencies

Expected manual API transcript after implementation:

    cd /home/poter/resume-pj/supportflow-agent/backend
    uv run uvicorn app.main:app --reload
    curl -s -X POST http://127.0.0.1:8000/api/v1/tickets/T-1001/run
    {
      "thread_id": "ticket-T-1001",
      "ticket_id": "T-1001",
      "status": "done",
      "classification": {
        "category": "billing",
        "priority": "P2",
        "reason": "..."
      },
      "retrieved_chunks": [
        {
          "doc_id": "refund_policy",
          "title": "Refund Policy",
          "score": 0.5,
          "snippet": "..."
        }
      ],
      "draft": {
        "answer": "...",
        "citations": ["refund_policy"],
        "confidence": 0.7
      }
    }

## Interfaces and Dependencies

Use only the existing backend and frontend stacks unless the repository already declares a needed dependency. Do not add a database, vector store, external LLM provider, streaming transport, or multi-agent framework for Day 2.

In `backend/app/services/ticket_repo.py`, define these functions:

    def list_tickets() -> list[dict[str, object]]:
        ...

    def get_ticket_by_id(ticket_id: str) -> dict[str, object]:
        ...

`get_ticket_by_id` should raise a clear not-found exception when the ticket does not exist. If a custom exception is added, keep it in the same module and translate it to HTTP 404 in `backend/app/api/v1/runs.py`.

In `backend/app/services/retrieval.py`, define a local retrieval function with this shape:

    def retrieve_knowledge(query: str, *, top_k: int = 3) -> list[KBHit]:
        ...

The function should read Markdown files from `data/kb`, compute a simple keyword-overlap score, sort descending by score, and return at most `top_k` hits. A hit should include a stable `doc_id` derived from the file stem, a human-readable title, a numeric score, and a snippet.

In `backend/app/schemas/graph.py`, define these Pydantic models:

    class TicketClassification(BaseModel):
        category: Literal["billing", "account", "product", "bug", "other"]
        priority: Literal["P0", "P1", "P2", "P3"]
        reason: str

    class KBHit(BaseModel):
        doc_id: str
        title: str
        score: float
        snippet: str

    class DraftReply(BaseModel):
        answer: str
        citations: list[str]
        confidence: float

    class RunTicketResponse(BaseModel):
        thread_id: str
        ticket_id: str
        status: Literal["done", "failed", "running"]
        classification: TicketClassification
        retrieved_chunks: list[KBHit]
        draft: DraftReply

In `backend/app/graph/state.py`, define `TicketState` as a `TypedDict` with these fields:

    class TicketState(TypedDict, total=False):
        thread_id: str
        ticket_id: str
        ticket: dict[str, Any]
        classification: TicketClassification
        retrieval_query: str
        retrieved_chunks: list[KBHit]
        draft: DraftReply
        status: Literal["queued", "running", "done", "failed"]
        current_node: Literal[
            "load_ticket_context",
            "classify_ticket",
            "retrieve_knowledge",
            "draft_reply",
        ]
        error: str | None

Each graph node should be a plain synchronous Python function that accepts `TicketState` and returns a partial `TicketState`. The intended signatures are:

    def load_ticket_context(state: TicketState) -> TicketState: ...
    def classify_ticket(state: TicketState) -> TicketState: ...
    def retrieve_knowledge(state: TicketState) -> TicketState: ...
    def draft_reply(state: TicketState) -> TicketState: ...

In `backend/app/graph/builder.py`, define:

    @lru_cache(maxsize=1)
    def get_support_graph():
        builder = StateGraph(TicketState)
        builder.add_node("load_ticket_context", load_ticket_context)
        builder.add_node("classify_ticket", classify_ticket)
        builder.add_node("retrieve_knowledge", retrieve_knowledge)
        builder.add_node("draft_reply", draft_reply)
        builder.add_edge(START, "load_ticket_context")
        builder.add_edge("load_ticket_context", "classify_ticket")
        builder.add_edge("classify_ticket", "retrieve_knowledge")
        builder.add_edge("retrieve_knowledge", "draft_reply")
        builder.add_edge("draft_reply", END)
        return builder.compile(checkpointer=InMemorySaver())

In `backend/app/api/v1/runs.py`, expose:

    @router.post("/tickets/{ticket_id}/run", response_model=RunTicketResponse)
    def run_ticket(ticket_id: str) -> RunTicketResponse:
        ...

In `frontend/src/lib/types.ts`, add TypeScript types that mirror the backend response names and nesting. In `frontend/src/lib/api.ts`, add:

    export async function runTicket(ticketId: string): Promise<RunTicketResponse> {
      ...
    }

The frontend should call the endpoint path `/api/v1/tickets/${ticketId}/run`, matching the existing API base URL conventions in `frontend/src/lib/api.ts`.

## Revision Notes

2026-04-23 / Codex: Rewrote the active Day 2 graph happy-path ExecPlan into pure English and reshaped it to follow the `Skeleton of a Good ExecPlan` in `docs/PLANS.md`. The update preserves the original intent, scope, fixed graph path, service boundaries, API contract, and frontend acceptance while adding self-contained context, concrete commands, validation criteria, recovery guidance, interface definitions, and living-document records.
