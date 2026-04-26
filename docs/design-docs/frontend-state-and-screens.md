---
status: draft-v0.1
owner: project-maintainer
last_verified: 2026-04-25
source_of_truth_for:
  - frontend screens
  - frontend state model
  - API integration points
  - review UI behavior
  - workflow result display
---

# Frontend State and Screens

## 1. Purpose

This document defines the frontend screens and state model for `supportflow-agent`.

The frontend exists to demonstrate the workflow clearly:

```text
ticket -> graph state -> evidence -> draft -> risk/review -> final reply
```

It should not become a complex admin dashboard in v1.

## 2. Design stance

### 2.1 Product demo over visual polish

The UI should make the workflow explainable:

- what ticket entered
- what node ran
- what classification was produced
- what evidence was retrieved
- what draft was generated
- why review was required
- what final decision was made

Do not spend v1 time on animations, advanced design systems, or complex table filters.

### 2.2 Frontend mirrors backend contracts

Frontend types should mirror Pydantic API contracts.

Do not invent frontend-only status strings unless mapped explicitly.

## 3. Screens

### 3.1 Tickets page

Route:

```text
/tickets
```

Purpose:

- list demo tickets
- select one ticket
- run workflow
- show workflow result
- inspect the current run state and timeline for the latest `thread_id`

Layout:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header: SupportFlow Agent                                                   │
├───────────────┬─────────────────────────────┬───────────────────────────────┤
│ Ticket List   │ Ticket Detail + Result      │ Run State + Workflow Timeline │
│               │                             │                               │
│ ticket-1001   │ title/content/customer tier │ status                        │
│ ticket-1002   │ [Run workflow]              │ current_node                  │
│ ticket-1003   │ evidence/draft/final reply  │ run_started                   │
│               │                             │ interrupt_created/done        │
└───────────────┴─────────────────────────────┴───────────────────────────────┘
```

Minimum components:

```text
TicketList
TicketDetail
WorkflowResultPanel
RunStatePanel
WorkflowTimeline
```

### 3.2 Review queue page

Route:

```text
/reviews
```

Purpose:

- show pending review requests
- approve/edit/reject
- resume graph

Layout:

```text
┌────────────────────────────────────────────────────────────────┐
│ Review Queue                                                   │
├───────────────┬─────────────────────────────┬──────────────────┤
│ Pending Items │ Draft + Evidence            │ Decision Form    │
│               │                             │                  │
│ REV-1001      │ draft answer                │ approve          │
│ REV-1002      │ citations                   │ edit textarea    │
│               │ risk flags                  │ reject           │
└───────────────┴─────────────────────────────┴──────────────────┘
```

Minimum components:

```text
ReviewQueue
ReviewDecisionCard
DraftPanel
EvidencePanel
RiskFlagList
```

### 3.3 Knowledge page

Route:

```text
/knowledge
```

Purpose:

- show KB docs/chunks
- test retrieval query

MVP optional. Do not build before ticket workflow and review work.

### 3.4 Eval summary page

Route:

```text
/evals
```

Purpose:

- show latest offline eval summary

Week 2 only. Do not build before eval script exists.

## 4. Frontend state model

### 4.1 Local state

```ts
type TicketsPageState = {
  tickets: Ticket[];
  selectedTicketId: string | null;
  activeRun: RunTicketResponse | null;
  activeThreadId: string | null;
  runState: RunStateResponse | null;
  timeline: RunTimelineEvent[];
  isRunning: boolean;
  isInspectingRun: boolean;
  error: string | null;
};
```

### 4.2 Run status

```ts
type RunStatus =
  | "queued"
  | "running"
  | "waiting_review"
  | "done"
  | "manual_takeover"
  | "failed";
```

### 4.3 Derived UI state

```ts
const canRun = selectedTicket != null && !isRunning;
const showReviewHint = activeRun?.status === "waiting_review";
const showFinalReply = activeRun?.final_response != null;
const showDraft = activeRun?.draft != null;
const shouldPoll = runState?.status === "running" || runState?.status === "waiting_review";
```

## 5. API integration

### Fetch tickets

```ts
GET / api / v1 / tickets;
```

### Run ticket

```ts
POST / api / v1 / tickets / { ticket_id } / run;
```

### Get pending reviews

```ts
GET / api / v1 / reviews / pending;
```

### Resume run

```ts
POST / api / v1 / runs / { thread_id } / resume;
```

### Get run state

```ts
GET / api / v1 / runs / { thread_id } / state;
```

### Get run timeline

```ts
GET / api / v1 / runs / { thread_id } / timeline;
```

## 6. Initial implementation order

### Day2

Build:

- `TicketsPage`
- `TicketList`
- `TicketDetail`
- `WorkflowResultPanel`
- `EvidencePanel`

Do not build review UI yet.

### Day3

Build:

- `ReviewQueuePage`
- `ReviewDecisionCard`
- resume API integration

### Day4

Build:

- `RunStatePanel`
- `WorkflowTimeline`
- `fetchRunState`
- `fetchRunTimeline`
- polling on `/tickets`
- last-thread restore after refresh

### Week 2

Build:

- eval summary panel
- link to LangSmith trace if available

## 7. Workflow result panel

Must display:

- category
- priority
- classification reason
- retrieved evidence
- draft answer
- citations
- confidence
- risk flags
- final status
- current `thread_id`

Day 4 adds a separate run inspection column that shows:

- run status
- current node
- timeline of major-step events
- refresh-safe inspection of the latest saved `thread_id`

Recommended order:

```text
1. Status badge
2. Classification
3. Evidence
4. Draft
5. Risk/review
6. Final reply
```

## 8. Evidence panel

Display each KB hit:

```text
[refund_policy#0001] Refund Policy
score: 0.82
snippet: 退款通常会在 1-3 个工作日内处理...
```

Rules:

- snippet should be collapsed after 3 lines
- chunk_id should be visible
- citations in draft should visually match evidence chips

## 9. Review UI behavior

Reviewer actions:

| Action  | UI behavior               |
| ------- | ------------------------- |
| approve | no edited answer required |
| edit    | textarea required         |
| reject  | reviewer note recommended |

Validation:

- disable submit while request is pending
- show error if edit selected but edited answer empty
- after resume success, remove item from pending queue
- show final status

## 10. Error states

Frontend must handle:

- API unavailable
- ticket not found
- run failed
- waiting review
- resume conflict
- unknown enum/status

Do not crash on partial run response.

## 11. Streaming plan

MVP:

```text
run endpoint returns Day 3 action response synchronously
```

Next:

```text
poll /runs/{thread_id}/state
poll /runs/{thread_id}/timeline
```

Stretch:

```text
SSE /runs/{thread_id}/events
```

Do not start with WebSocket.

## 12. Folder structure

```text
frontend/src/
  app/
    router.tsx
    providers.tsx
  pages/
    TicketsPage.tsx
    ReviewQueuePage.tsx
    KnowledgePage.tsx
    EvalSummaryPage.tsx
  components/
    TicketList.tsx
    TicketDetail.tsx
    WorkflowResultPanel.tsx
    RunStatePanel.tsx
    WorkflowTimeline.tsx
    DraftPanel.tsx
    ReviewDecisionCard.tsx
    RiskFlagList.tsx
    StateTimeline.tsx
  lib/
    api.ts
    types.ts
    runStatus.ts
```

## 13. Testing

Minimum frontend checks:

- tickets render
- selecting ticket updates detail panel
- run button calls API
- result panel renders classification/evidence/draft
- edit review requires edited answer
- unknown status renders fallback

## 14. What not to build in v1

Do not build:

- login
- RBAC
- complex dashboard
- advanced filtering
- drag-and-drop review queue
- theme system
- WebSocket
- chart-heavy observability page

## 15. Update triggers

Update this document when:

- adding/removing a screen
- changing API response consumed by frontend
- changing run status enum
- changing review behavior
- adding streaming
- adding eval or trace UI
