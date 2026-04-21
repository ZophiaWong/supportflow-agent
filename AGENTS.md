# AGENTS.md

## Repo purpose

This repository builds supportflow-agent:
an AI support workflow app for ticket triage,

## Read this first

1. ARCHITECTURE.md
2. docs/product-specs/supportflow-mvp.md
3. docs/exec-plans/active/\*.md

## Working rules

- Prefer minimal viable implementations over broad abstractions.
- Keep LangGraph workflow-first.
- Do not introduce multi-agent patterns.
- Use Pydantic schemas for API and structured LLM outputs.
- Update the active ExecPlan when design decisions change.

## When to use an ExecPlan

Use an ExecPlan(described in `/docs/exec-plans/`) for:

- multi-file features
- refactors touching backend + frontend
- graph changes affecting state or routing
- evaluation / observability work

## Commands

- backend dev: ...
- frontend dev: ...
- tests: ...

## Definition of done

- Code runs
- Relevant checks pass
- Docs reflect the actual behavior
- Acceptance criteria in the active ExecPlan are met

## Never do

- Add complexity without an active need
- Put large design docs into AGENTS.md
- Hide trade-offs
