# supportflow-agent MVP

## Problem

Support teams need a structured workflow to triage tickets, retrieve knowledge,
draft replies, and send risky cases to human review.

## Users

- Support agent
- Reviewer

## In scope

- ticket list
- ticket processing workflow
- knowledge retrieval
- draft generation
- human review interruption
- final response display
- simulated support actions with human approval before external sends
- structured policy checks for review routing and reviewer guidance

## Out of scope

- real email integration
- real ticketing systems
- multi-tenant auth
- production-grade analytics

## MVP acceptance

- one ticket can enter the workflow
- system can show a draft reply
- risky cases can be reviewed by a human

## Current acceptance evidence

Verified on 2026-04-28.

- One ticket can enter the workflow: `POST /api/v1/tickets/ticket-1003/run` now pauses in `waiting_review` with a proposed `send_customer_reply` action and a failed `high_impact_action_requires_review` policy because external customer sends require approval before execution.
- System can show a draft reply, action plan, and policy assessment: backend and frontend tests passed, and workflow responses include draft content, KB evidence, citations, proposed actions, action status, failed policy IDs, severity, reviewer-facing messages, and evidence.
- Risky cases can be reviewed by a human: `ticket-1001` enters `waiting_review` with policy-derived flags such as `billing_sensitive`, `sensitive_request`, and `high_impact_action_requires_review`; approve executes the proposed actions once, while reject leaves external actions unexecuted and moves the run to `manual_takeover`.
- Automated acceptance passed: backend tests `32 passed`, frontend tests `13 passed`, frontend production build succeeded, and offline eval reported `graph_v1` final pass rate `1.00` with `0` bad cases.

Verified on 2026-04-26.

- One ticket can enter the workflow: `POST /api/v1/tickets/ticket-1003/run` completed through the backend HTTP server with status `done` and final disposition `auto_finalized`.
- System can show a draft reply: backend and frontend tests passed, and the low-risk workflow response included a non-empty `draft`, retrieved KB evidence, citations, and a final response.
- Risky cases can be reviewed by a human: `ticket-1001` entered `waiting_review`, appeared in the pending review flow, and resumed through approve to status `done`; `ticket-1002` resumed through reject to status `manual_takeover`.
- Automated acceptance passed: backend tests `28 passed`, frontend tests `9 passed`, frontend production build succeeded, and offline eval reported `graph_v1` final pass rate `1.00` with `0` bad cases.
- Runtime route smoke passed: the backend served `/healthz`, tickets, run, pending review, resume, state, and timeline endpoints; the Vite frontend served `/tickets` and `/reviews`.
