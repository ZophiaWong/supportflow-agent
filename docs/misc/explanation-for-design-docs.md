# Explanation For Design Docs

This document centralizes the `Interview talking points` that were previously repeated across the design docs and the generated database schema doc.

## Contracts and schemas

Source: `docs/design-docs/contracts-and-schemas.md`

Strong answer:

> I separated domain schemas, graph state, node contracts, API responses, and frontend types. The reason is that LLM systems fail at boundaries, so I want each boundary to be validated and observable.

Weak answer:

> I used Pydantic because FastAPI uses it.

## Retrieval and KB

Source: `docs/design-docs/retrieval-and-kb.md`

Strong answer:

> I started with a simple retrieval baseline because the project first needs a reliable workflow and evidence chain. The retrieval layer is behind a service interface, so I can later replace lexical search with embedding retrieval without changing the LangGraph graph.

Weak answer:

> I used RAG because every LLM app needs RAG.

## Review and risk gate

Source: `docs/design-docs/review-and-risk-gate.md`

Strong answer:

> Human review is placed after risk_gate because the reviewer needs the classification, evidence, and draft. The gate is deterministic in v1 so the safety boundary is inspectable. LangGraph interrupt is useful here because the graph can persist state, pause, and resume with the human decision.

Weak answer:

> I added human review because LangGraph supports interrupt.

## Evaluation and observability

Source: `docs/design-docs/evaluation-and-observability.md`

Strong answer:

> I evaluated the project at three levels: final response quality, node-level correctness, and trajectory correctness. This matters because a LangGraph app can fail even if the final text looks okay; for example, it may skip review or cite the wrong evidence.

Weak answer:

> I looked at a few outputs and they seemed good.

## Frontend state and screens

Source: `docs/design-docs/frontend-state-and-screens.md`

Strong answer:

> The frontend is designed to expose the workflow state, not just chat messages. This makes the project more explainable: the interviewer can see classification, retrieval evidence, draft confidence, risk flags, and human review decisions.

Weak answer:

> I made a UI because the project needs a frontend.

## Database schema

Source: `docs/generated/db-schema.md`

Strong answer:

> I did not start with a full database because the first priority was to validate the workflow. The planned schema separates business tickets, graph runs, review requests, KB chunks, and eval results, which maps directly to the system boundaries.

Weak answer:

> I added a database because every backend project should have one.
