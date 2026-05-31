# LLM Workflow Integration

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

SupportFlow should demonstrate real LLM-assisted support workflow behavior while preserving the current deterministic safety boundaries. This change adds optional LLM calls to the graph nodes where generation is useful: ticket classification and customer reply drafting.

The policy gate, review routing, interrupt/resume behavior, and support action execution remain rule-driven.

## Progress

- [x] (2026-05-28) Added optional LLM service configuration and structured-output request handling.
- [x] (2026-05-28) Wired `classify_ticket` and `draft_reply` to try LLM output first and fall back to existing deterministic behavior.
- [x] (2026-05-28) Added backend tests for structured draft success, invalid citation fallback, LLM error fallback, no-evidence low confidence, and classification fallback.
- [x] (2026-05-28) Documented LLM environment variables and safety boundaries in README.
- [x] (2026-05-28) Added root `.env.example`, local `.env` loading, and `.gitignore` protection for local env files.
- [x] (2026-05-28) Added `draft_source` trace visibility so users can distinguish LLM drafts from deterministic fallback drafts.
- [x] (2026-05-29) Switched the LLM HTTP client from `urllib` to `requests`, changed configuration to `base_url + /chat/completions`, and preserved sanitized fallback reasons in logs and trace attributes.
- [x] (2026-05-30) Added strict structured-output request assertions and provider non-compliance fallback coverage for wrapped draft responses such as `{"response": "..."}`.
- [x] (2026-05-31) Updated README and contracts documentation to match the current validation-failure fallback behavior.

## Surprises & Discoveries

- Observation: The backend has no OpenAI SDK dependency and uses a small HTTP client wrapper for chat completions.
  Evidence: `backend/pyproject.toml` includes FastAPI, LangGraph, Pydantic, Requests, and Uvicorn for runtime dependencies.

- Observation: LLM integration can be kept inside generation nodes without changing API schemas.
  Evidence: `TicketClassification` and `DraftReply` already exist in `backend/app/schemas/graph.py` and are persisted through the current graph state.

- Observation: Some OpenAI-compatible providers may ignore `response_format=json_schema` and return provider- or model-wrapped fields such as `response`.
  Evidence: Local tests now cover wrapped draft payloads and keep them on the existing `schema_validation_failed` fallback path instead of normalizing them into `DraftReply`.

## Decision Log

- Decision: Use `requests` for the OpenAI-compatible chat-completions endpoint.
  Rationale: The project can accept the dependency, and `requests` makes HTTP status, response body, timeout, and fallback diagnostics easier to preserve than the earlier `urllib` call.
  Date/Author: 2026-05-29 / Codex

- Decision: Treat LLM output as advisory and schema-bound.
  Rationale: Invalid JSON, schema failures, out-of-range confidence, unknown citations, network errors, and missing keys should not break the workflow.
  Date/Author: 2026-05-28 / Codex

- Decision: Prefer validation failure fallback over retry-then-fail-node for the MVP workflow.
  Rationale: The graph already has deterministic classification and drafting fallbacks, and LLM generation is optional. Failing the node would make provider schema issues break the ticket workflow; retry can be considered later only as a pre-fallback hardening step for recoverable failures.
  Date/Author: 2026-05-31 / Codex

- Decision: Do not map provider wrapper fields such as `response`, `message`, or `text` into `DraftReply.answer`.
  Rationale: That would hide provider non-compliance with Structured Outputs and bypass the schema contract; the workflow should log sanitized diagnostics and fall back deterministically.
  Date/Author: 2026-05-30 / Codex

- Decision: Keep policy and action nodes deterministic.
  Rationale: Review routing and external-action approval are safety boundaries in the current MVP.
  Date/Author: 2026-05-28 / Codex

## Outcomes & Retrospective

Implemented optional LLM generation for `classify_ticket` and `draft_reply` while preserving deterministic fallbacks. The workflow still runs without API keys, safety-sensitive routing/action behavior remains owned by the existing policy and action nodes, and graph trace spans expose whether classification/drafting came from `llm` or `fallback` plus sanitized LLM error reasons when a fallback was caused by an LLM failure.

Validation passed on 2026-05-29: backend tests reported `56 passed`, and offline eval reported `graph_v1` final pass rate `1.00`, citation coverage `1.00`, and policy trigger accuracy `1.00`. In this local environment, offline eval also showed the new fallback diagnostics for `api.tryallai.com` DNS failures while preserving deterministic workflow results.

Validation passed on 2026-05-30 for structured-output hardening: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_llm_workflow.py -q` reported `16 passed`.

Validation passed on 2026-05-31 after documentation review: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q` reported `60 passed`.

## Validation and Acceptance

This change is complete when backend tests pass, offline eval still reports `graph_v1` final pass rate at the existing threshold, and no frontend/API contract changes are required.

Required validation:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py --min-final-pass-rate 1.0 --min-citation-coverage 1.0 --min-policy-trigger-accuracy 1.0

## Interfaces and Dependencies

Environment variables:

    cp .env.example .env

Then edit `.env`:

    SUPPORTFLOW_LLM_ENABLED=true
    OPENAI_API_KEY=<your_api_key>
    SUPPORTFLOW_LLM_BASE_URL=https://api.openai.com/v1

No public FastAPI response schema changes are expected.
