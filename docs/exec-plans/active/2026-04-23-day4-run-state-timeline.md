# Day4 Run State and Workflow Timeline

This ExecPlan is a living document.

Keep `Progress`, `Decision Log`, `Surprises & Discoveries`,
and `Outcomes & Retrospective` updated while implementing Day4.

## 1. Goal

Turn the Day3 human-in-the-loop graph into an inspectable workflow UI.

By the end of Day4, a user should be able to:

1. Start a ticket workflow run.
2. See the workflow state after each major step.
3. See when the graph is waiting for human review.
4. Resume the graph after review.
5. Refresh the page and query the current run state by `thread_id`.
6. Explain the difference between:
   - ticket status
   - run status
   - review status
   - graph checkpoint state
   - frontend timeline state

Day4 is not about adding new intelligence.
Day4 is about making the existing graph observable and understandable.

---

## 2. Context

Day2 delivered the synchronous happy path:

```text
load_ticket_context
-> classify_ticket
-> retrieve_knowledge
-> draft_reply
```

Day3 added the minimal HITL loop:

```text
draft_reply
-> risk_gate
-> human_review_interrupt
-> apply_review_decision
-> finalize_reply
```

Day4 builds on that by adding a visible run-state layer:

```text
run_ticket
-> record timeline events
-> expose run state endpoint
-> render frontend workflow timeline
-> support refresh/reload state inspection
```

The graph source of truth remains LangGraph state/checkpoint.

Any Day4 run event store is only a UI-facing index, not the canonical graph state.

---

## 3. In Scope

### Backend

- Add a run state response schema.
- Add a timeline event schema.
- Add an in-memory run event store.
- Record important lifecycle events around graph execution.
- Add endpoint to query current run state by `thread_id`.
- Add endpoint to query timeline events by `thread_id`.
- Update run and resume endpoints to write timeline events.

### Frontend

- Add a workflow state panel.
- Add a node timeline component.
- Add run status display:
  - running
  - waiting_review
  - done
  - failed
- Show classification, retrieved evidence, draft, risk assessment, and final response in a stable layout.
- After resume, reload run state and timeline.

### Docs

- Update Day4 ExecPlan.
- Update `docs/design-docs/frontend-state-and-screens.md` if screen behavior changes.
- Update `docs/design-docs/langgraph-workflow.md` if state semantics change.
- Update `ARCHITECTURE.md` only if component boundaries change.

---

## 4. Out of Scope

Do not implement these on Day4:

- LangSmith tracing.
- Offline eval.
- Database persistence.
- Postgres checkpointer.
- Production-grade event streaming.
- WebSocket.
- Full SSE implementation unless the basic polling flow is already done.
- Auth.
- Multi-user review assignment.
- Multi-run history table.
- Real email or ticketing-system write-back.
- Complex frontend animation.
- Token-level streaming.

Reason:

Day4 is about making the existing graph state visible.
Adding observability vendors, databases, or streaming too early will obscure the main learning goal.

---

## 5. Design Principle

Day4 uses a two-layer state model:

```text
LangGraph checkpoint state = source of truth
Run timeline events = UI/debug projection
```

The graph state answers:

```text
What is the current business/workflow state?
```

The timeline answers:

```text
What happened, in what order, and what should the frontend show?
```

These two should not be confused.

---

## 6. Key Concepts

### 6.1 ticket_id

Business identifier.

Example:

```text
T-1001
```

Used to identify the support ticket.

### 6.2 thread_id

LangGraph execution context identifier.

Example:

```text
ticket-T-1001
```

Used to resume graph execution and inspect checkpointed state.

### 6.3 run_id

A single execution attempt or UI run record.

Day4 may not need a real persisted `run_id`.
If needed, use a simple generated value for timeline grouping.

For now, `thread_id` is enough for the demo.

### 6.4 graph state

The structured LangGraph state containing:

- ticket
- classification
- retrieved_chunks
- draft
- risk_assessment
- review_decision
- final_response
- status
- current_node
- error

### 6.5 timeline event

A UI/debug event such as:

- run_started
- node_completed
- interrupt_created
- review_submitted
- run_resumed
- run_completed
- run_failed

Timeline events are not the graph's source of truth.

---

## 7. Target User Flow

### 7.1 Low-risk ticket

```text
User opens Tickets page
-> selects T-1002
-> clicks Run workflow
-> graph runs to completion
-> timeline shows completed nodes
-> final_response appears
```

Expected frontend status:

```text
status = done
review_status = none
final_response.disposition = draft_ready
```

### 7.2 High-risk ticket

```text
User opens Tickets page
-> selects T-1001
-> clicks Run workflow
-> graph runs until risk_gate
-> graph interrupts at human_review_interrupt
-> timeline shows waiting_review
-> user opens Review Queue
-> approves or edits
-> backend resumes graph
-> timeline shows run_resumed and run_completed
-> final_response appears
```

Expected frontend status before review:

```text
status = waiting_review
review_status = pending
risk_assessment.review_required = true
```

Expected frontend status after review:

```text
status = done
review_status = approved or edited or rejected
```

---

## 8. Backend Deliverables

### 8.1 Schemas to add or update

Add or update schema definitions for:

```text
RunStatus
RunTimelineEvent
RunStateResponse
RunTimelineResponse
```

The response shape should support the frontend without exposing internal LangGraph implementation details.

Minimum fields for `RunTimelineEvent`:

```text
event_id
thread_id
ticket_id
event_type
node_name
status
message
created_at
payload
```

Suggested event types:

```text
run_started
node_completed
interrupt_created
review_submitted
run_resumed
run_completed
run_failed
```

Minimum fields for `RunStateResponse`:

```text
thread_id
ticket_id
status
current_node
classification
retrieved_chunks
draft
risk_assessment
review_decision
final_response
error
```

Do not expose raw checkpoint internals in the API response.

---

### 8.2 In-memory run event store

Add a small service responsible for timeline events.

Suggested file:

```text
backend/app/services/run_event_store.py
```

Responsibilities:

- append event
- list events by `thread_id`
- clear events for test/demo if needed

This store is temporary.

It exists only so the frontend can render a timeline before the project has a database.

---

### 8.3 Run state service

Add a small service for reading the current run state.

Suggested file:

```text
backend/app/services/run_state_service.py
```

Responsibilities:

- call the compiled graph/checkpointer using `thread_id`
- convert graph state into `RunStateResponse`
- avoid leaking raw internal checkpoint structures
- return a clean 404 or empty state if the thread does not exist

Important design constraint:

```text
run_state_service reads graph state;
it does not mutate graph state.
```

---

### 8.4 API endpoints

Add or update these endpoints:

```text
POST /api/v1/tickets/{ticket_id}/run
GET  /api/v1/runs/{thread_id}/state
GET  /api/v1/runs/{thread_id}/timeline
POST /api/v1/runs/{thread_id}/resume
```

Day3 already has run and resume.
Day4 updates them to write timeline events and return cleaner state.

New endpoint responsibilities:

#### GET /api/v1/runs/{thread_id}/state

Returns the latest visible workflow state.

Used by:

- page refresh
- polling
- after resume
- debugging

#### GET /api/v1/runs/{thread_id}/timeline

Returns timeline events for a run/thread.

Used by:

- workflow timeline panel
- debugging
- interview demo

---

## 9. Frontend Deliverables

### 9.1 Components to add or update

Add or update:

```text
frontend/src/components/WorkflowTimeline.tsx
frontend/src/components/RunStatePanel.tsx
frontend/src/components/WorkflowResultPanel.tsx
frontend/src/components/EvidencePanel.tsx
frontend/src/components/RiskAssessmentPanel.tsx
frontend/src/pages/TicketDetailPage.tsx
frontend/src/pages/ReviewQueuePage.tsx
frontend/src/lib/api.ts
frontend/src/lib/types.ts
```

No complex UI.

Use simple cards, tags, and timeline layout.

---

### 9.2 Page behavior

The ticket detail page should show:

```text
left: ticket list
middle: ticket detail + draft/final response
right: workflow timeline + current run state
```

Minimum layout:

```text
┌──────────────────┬───────────────────────────────┬─────────────────────────┐
│ Ticket List       │ Ticket Detail / Result         │ Workflow Timeline        │
│                  │                               │                         │
│ T-1001            │ title/content                  │ run_started             │
│ T-1002            │ classification                 │ load_ticket_context     │
│ T-1003            │ retrieved evidence             │ classify_ticket         │
│                  │ draft reply                    │ retrieve_knowledge      │
│                  │ risk assessment                │ draft_reply             │
│                  │ final response                 │ risk_gate               │
│                  │                               │ waiting_review / done   │
└──────────────────┴───────────────────────────────┴─────────────────────────┘
```

---

### 9.3 Polling strategy

Day4 should use polling first.

Recommended behavior:

```text
After clicking Run workflow:
- immediately fetch run state
- fetch timeline
- poll every 1-2 seconds while status is running or waiting_review
- stop polling when status is done or failed
```

Reason:

Polling is simpler and sufficient for Day4.
SSE can be added later after the state model is stable.

---

## 10. Minimal Timeline Events

The backend should record at least these events:

### On run start

```text
event_type = run_started
status = running
node_name = null
```

### After happy-path completion

```text
event_type = run_completed
status = done
node_name = finalize_reply
```

### When interrupt is returned

```text
event_type = interrupt_created
status = waiting_review
node_name = human_review_interrupt
```

### When reviewer submits decision

```text
event_type = review_submitted
status = running
node_name = apply_review_decision
```

### After resume completion

```text
event_type = run_completed
status = done
node_name = finalize_reply or apply_review_decision
```

### On error

```text
event_type = run_failed
status = failed
node_name = current_node if available
```

Nice-to-have:

If simple, record a `node_completed` event after each graph node.
If not simple today, defer node-level events and only record run-level events.

---

## 11. Implementation Order

### Step 1: Create Day4 ExecPlan

Create this file:

```text
docs/exec-plans/active/2026-04-23-day4-run-state-timeline.md
```

Move completed Day3 plan to:

```text
docs/exec-plans/completed/
```

---

### Step 2: Define run state and timeline schemas

Update or create:

```text
backend/app/schemas/run.py
```

Add:

- run status type
- timeline event model
- run state response model
- timeline response model

Acceptance:

- frontend can generate matching TypeScript types
- no raw checkpoint internals leak through API

---

### Step 3: Add run event store

Create:

```text
backend/app/services/run_event_store.py
```

Acceptance:

- append event works
- list events by thread_id works
- events preserve order

---

### Step 4: Add run state service

Create:

```text
backend/app/services/run_state_service.py
```

Acceptance:

- can return latest state for an existing thread_id
- can return clean not found / empty state for unknown thread_id
- maps graph state to API response shape

---

### Step 5: Update run and resume endpoints

Update:

```text
backend/app/api/v1/runs.py
```

Acceptance:

- run endpoint records run_started
- run endpoint records waiting_review when interrupted
- run endpoint records run_completed when done
- resume endpoint records review_submitted
- resume endpoint records run_completed after resume

---

### Step 6: Add state and timeline endpoints

Update:

```text
backend/app/api/v1/runs.py
```

Add:

```text
GET /api/v1/runs/{thread_id}/state
GET /api/v1/runs/{thread_id}/timeline
```

Acceptance:

- state endpoint returns latest workflow state
- timeline endpoint returns ordered events

---

### Step 7: Update frontend types and API client

Update:

```text
frontend/src/lib/types.ts
frontend/src/lib/api.ts
```

Acceptance:

- frontend has types for run state and timeline events
- frontend can fetch state and timeline by thread_id

---

### Step 8: Add workflow timeline UI

Create:

```text
frontend/src/components/WorkflowTimeline.tsx
```

Acceptance:

- shows event type
- shows node name when present
- shows event status
- shows created_at

---

### Step 9: Add run state panel

Create:

```text
frontend/src/components/RunStatePanel.tsx
```

Acceptance:

- shows status
- shows current_node
- shows classification
- shows risk reasons
- shows final response if available
- shows error if failed

---

### Step 10: Wire ticket detail page

Update:

```text
frontend/src/pages/TicketsPage.tsx
```

or, if already split:

```text
frontend/src/pages/TicketDetailPage.tsx
```

Acceptance:

- selecting a ticket shows detail
- clicking Run workflow starts backend run
- UI stores returned thread_id
- UI fetches state and timeline
- UI updates after review resume

---

### Step 11: Add smoke test

Add:

```text
backend/tests/integration/test_run_state_timeline.py
```

Test cases:

1. low-risk ticket creates timeline and final state
2. high-risk ticket creates waiting_review state
3. resume changes state to done
4. timeline includes review_submitted and run_completed

---

## 12. Acceptance Criteria

Day4 is done when all of these are true:

- `POST /api/v1/tickets/{ticket_id}/run` still works.
- High-risk ticket still reaches `waiting_review`.
- `GET /api/v1/runs/{thread_id}/state` returns current state.
- `GET /api/v1/runs/{thread_id}/timeline` returns timeline events.
- Frontend shows workflow timeline.
- Frontend shows current run state.
- After approve/edit/reject, frontend can refresh state and show final response.
- Refreshing the browser does not lose visible run state while the backend process is still alive.
- The user can explain that the in-memory event store is a UI projection, not the source of truth.

---

## 13. Non-Functional Requirements

### Simplicity

Prefer simple polling over real-time streaming.

### Stability

Do not change graph business behavior unless necessary.

### Traceability

Every run should have at least a run_started event and either:

- run_completed
- interrupt_created
- run_failed

### Consistency

Frontend status labels must match backend status enums.

### No hidden side effects

Do not send real emails.
Do not write to external systems.
Do not create real support tickets.

---

## 14. Risks

### Risk 1: Confusing timeline store with graph state

Mitigation:

Document clearly:

```text
LangGraph checkpoint = source of truth
Timeline event store = UI/debug projection
```

### Risk 2: Overbuilding streaming

Mitigation:

Start with polling.
Only add SSE after the state and timeline API are stable.

### Risk 3: In-memory state disappears after restart

Mitigation:

Document this limitation.
Move database persistence to a later day.

### Risk 4: State response leaks too much internal structure

Mitigation:

Use a clean API response schema.
Do not return raw checkpoint tuples or internal config.

### Risk 5: Frontend state gets inconsistent after resume

Mitigation:

After resume, always refetch:

```text
GET /runs/{thread_id}/state
GET /runs/{thread_id}/timeline
```

---

## 15. Decision Log

### Decision: Use polling instead of SSE on Day4

Reason:

Day4's goal is state visibility, not real-time streaming infrastructure.
Polling is enough for the demo and easier to debug.

### Decision: Keep event store in memory

Reason:

Day4 should not introduce database complexity.
Database persistence belongs after the state model stabilizes.

### Decision: Treat graph checkpoint as source of truth

Reason:

The graph already owns workflow state.
Timeline events should not become a second business state store.

### Decision: Do not add LangSmith today

Reason:

LangSmith becomes valuable after local run state and timeline are stable.
Adding it now would mix product-level observability with local UI state debugging.

---

## 16. Progress

- [ ] Move Day3 ExecPlan to completed
- [ ] Create Day4 ExecPlan
- [ ] Define run state schema
- [ ] Define timeline event schema
- [ ] Add run event store
- [ ] Add run state service
- [ ] Add state endpoint
- [ ] Add timeline endpoint
- [ ] Update run endpoint to record events
- [ ] Update resume endpoint to record events
- [ ] Add frontend run state types
- [ ] Add frontend timeline types
- [ ] Add API client methods
- [ ] Add WorkflowTimeline component
- [ ] Add RunStatePanel component
- [ ] Wire ticket detail page
- [ ] Add smoke test
- [ ] Update docs if state semantics changed

---

## 17. Surprises & Discoveries

Use this section during implementation.

Template:

```text
Observation:
Evidence:
Decision:
Follow-up:
```

Example:

```text
Observation:
LangGraph checkpoint state is enough for current state but not enough for user-friendly timeline labels.

Evidence:
The frontend needs node-level display text and timestamps.

Decision:
Keep a separate in-memory event store for UI timeline.

Follow-up:
Move event store to DB later if run history becomes required.
```

---

## 18. Outcomes & Retrospective

Fill this at the end of Day4.

Questions:

1. Can the frontend display run status clearly?
2. Can the system recover visible state after browser refresh?
3. Did we avoid adding unnecessary streaming complexity?
4. Is the separation between graph state and timeline events clear?
5. What should move to Day5?

Expected Day4 outcome:

```text
The graph is no longer a black box.
A reviewer or interviewer can see what happened in the workflow,
where it paused, and what state it resumed from.
```

---

## 19. Interview Talking Points

If asked what Day4 added, answer:

```text
Day4 turned the graph from a backend-only workflow into an inspectable product flow.
I added a run state API and a timeline projection so the UI can show where the workflow is,
why it is waiting for review, and what happened after resume.
The important design decision is that LangGraph checkpoint state remains the source of truth,
while timeline events are only a UI/debug projection.
```

If asked why not use SSE immediately, answer:

```text
SSE is useful for real-time UX, but Day4's core risk is state correctness.
I chose polling first because it validates the API contract and frontend state model with less complexity.
Once the state model is stable, SSE can replace polling without changing graph semantics.
```

If asked why not use a database immediately, answer:

```text
A database is necessary for production run history,
but Day4 is still validating state semantics.
Using in-memory storage keeps the feedback loop short.
I documented the limitation and kept the event store isolated so it can be swapped later.
```
