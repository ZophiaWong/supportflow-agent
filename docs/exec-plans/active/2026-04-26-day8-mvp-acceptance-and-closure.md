# Day 8 MVP Acceptance and Closure

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The product spec in `docs/product-specs/supportflow-mvp.md` defines a small MVP: a support agent can see tickets, run a workflow, retrieve knowledge, see a draft reply, send risky cases to human review, and see a final response. The repository has implemented these pieces across the FastAPI backend, LangGraph workflow, React ticket page, React review queue, local KB retrieval, and offline evals. Day 8 is the acceptance and closure pass that proves the MVP works end to end and records the evidence in the product spec and docs.

After this work, a reader should be able to open the repository, run the documented checks, and see exactly how the MVP acceptance criteria were satisfied. The goal is not to add post-MVP features. Do not add real email integration, a real ticketing system, multi-tenant auth, production analytics, durable storage, streaming, real LLM drafting, or vector retrieval in this plan.

## Progress

- [x] (2026-04-26 14:10Z) Created this active Day 8 ExecPlan after Day 7 retrieval precision was completed and moved to `docs/exec-plans/completed/`.
- [ ] Run the backend, frontend, build, and offline eval acceptance commands.
- [ ] Perform the manual MVP smoke test through `/tickets` and `/reviews`.
- [ ] Record acceptance evidence in `docs/product-specs/supportflow-mvp.md`.
- [ ] Update README or design docs only if observed command output or behavior differs from current docs.
- [ ] Archive this ExecPlan to `docs/exec-plans/completed/` after all acceptance criteria pass.

## Surprises & Discoveries

- Observation: The MVP product spec is intentionally compact.
  Evidence: `docs/product-specs/supportflow-mvp.md` lists only ticket list, ticket processing workflow, knowledge retrieval, draft generation, human review interruption, and final response display as in scope.

- Observation: The current README already describes all user-facing MVP surfaces.
  Evidence: `README.md` documents `/tickets`, `/reviews`, the backend run endpoint, pending review endpoint, resume endpoint, run state endpoint, run timeline endpoint, and offline eval command.

- Observation: There is no active implementation plan at the start of Day 8.
  Evidence: `docs/exec-plans/active/` is empty, while `docs/exec-plans/completed/2026-04-26-day7-retrieval-precision.md` exists in the working tree.

- Observation: Current automated coverage already maps to the core MVP flows.
  Evidence: `backend/tests/test_api.py` covers low-risk finalization, risky waiting-review runs, pending review listing, resume approve, and reject-to-manual-takeover. `frontend/src/pages/TicketsPage.test.tsx` covers ticket loading, running workflow, waiting-review UI, timeline/state display, and reload restoration. `frontend/src/pages/ReviewQueuePage.test.tsx` covers loading pending reviews and submitting a reviewer decision.

## Decision Log

- Decision: Use one Day 8 ExecPlan rather than splitting the work.
  Rationale: This is a verification and closure pass, not independent backend and frontend feature work. A single plan keeps the acceptance evidence in one place and prevents duplicate documentation updates.
  Date/Author: 2026-04-26 / Codex

- Decision: Treat failed acceptance checks as blockers to fix inside this plan before starting post-MVP work.
  Rationale: The purpose is to prove the MVP. If a documented MVP behavior fails, adding new scope would hide the problem instead of closing it.
  Date/Author: 2026-04-26 / Codex

- Decision: Record evidence in the product spec instead of expanding `AGENTS.md`.
  Rationale: `AGENTS.md` says not to put large design docs there, while the product spec is the right source for MVP acceptance state.
  Date/Author: 2026-04-26 / Codex

## Outcomes & Retrospective

Not started. Fill this section after the acceptance commands and manual smoke test have run. Include the final command results, any failed checks and fixes, whether the MVP spec is satisfied, and the recommended first post-MVP plan.

## Context and Orientation

`supportflow-agent` is a workflow-first AI support app. The backend lives under `backend/`, the frontend lives under `frontend/`, fixtures live under `data/`, and planning docs live under `docs/`. The app uses FastAPI for HTTP endpoints, LangGraph for the support workflow, local JSON ticket fixtures for demo tickets, Markdown files under `data/kb/` for knowledge retrieval, and React for the browser UI.

The MVP product spec is `docs/product-specs/supportflow-mvp.md`. It defines two users:

- Support agent, who triages tickets, starts workflow runs, and views draft/final responses.
- Reviewer, who reviews risky drafts and approves, edits, or rejects them.

The current user-facing routes are:

- `/tickets`, implemented by `frontend/src/pages/TicketsPage.tsx`, for the support agent workflow.
- `/reviews`, implemented by `frontend/src/pages/ReviewQueuePage.tsx`, for reviewer decisions.

The current backend routes are:

- `GET /healthz`
- `GET /api/v1/tickets`
- `POST /api/v1/tickets/{ticket_id}/run`
- `GET /api/v1/runs/{thread_id}/state`
- `GET /api/v1/runs/{thread_id}/timeline`
- `GET /api/v1/reviews/pending`
- `POST /api/v1/runs/{thread_id}/resume`

The core workflow path is implemented under `backend/app/graph/`. It loads a ticket, classifies it, retrieves KB evidence, drafts a reply, evaluates risk, either finalizes the response or pauses for human review, and then resumes from the reviewer decision.

Terms used in this plan:

- MVP means the minimum product behavior listed in `docs/product-specs/supportflow-mvp.md`.
- Acceptance evidence means exact commands, outputs, and manual scenarios that prove the MVP criteria.
- Manual smoke test means a short browser-based flow that confirms the user can perform the core workflows without inspecting code.
- Closure means the active ExecPlan is completed, acceptance evidence is written down, and no active plan remains unless a new post-MVP plan is intentionally started.

## Plan of Work

First, run the automated acceptance commands. From `backend/`, run the backend test suite and offline eval. From `frontend/`, run the Vitest suite and production build. Use the commands documented below. If any command fails, stop the acceptance pass, record the failure in `Surprises & Discoveries`, fix only the MVP-blocking issue, rerun the relevant command, and update `Progress`.

Second, run the manual MVP smoke test with local servers. Start the backend on `http://127.0.0.1:8000` and the frontend on `http://127.0.0.1:5173`. Open `/tickets`, run the low-risk demo ticket `ticket-1003`, and confirm that a draft and final response are visible. Then run a risky ticket such as `ticket-1001`, confirm that it pauses in `waiting_review`, and open `/reviews`. Approve one pending review and confirm it completes with a final response. Run another risky ticket and reject it, then confirm it ends in `manual_takeover`. Refresh `/tickets` after a run and confirm that the current run state and timeline reload while the backend process remains alive.

Third, record acceptance evidence in `docs/product-specs/supportflow-mvp.md`. Add a short section named `## Current acceptance evidence` after the existing MVP acceptance list. For each MVP acceptance criterion, write the concrete command or manual scenario that proves it. Include the observed test commands and a brief summary of the manual smoke result. Keep the spec concise; do not turn it into a design doc.

Fourth, update README or design docs only if the acceptance pass reveals drift. If the current README command output and behavior descriptions match the observed results, do not make unnecessary doc changes. If output differs, update only the stale lines.

Fifth, archive this plan after acceptance passes. Move `docs/exec-plans/active/2026-04-26-day8-mvp-acceptance-and-closure.md` to `docs/exec-plans/completed/2026-04-26-day8-mvp-acceptance-and-closure.md`. Keep the final version self-contained and update `Outcomes & Retrospective` before moving it.

## Concrete Steps

Work from the repository root unless a command says otherwise.

Confirm there are no stale active plans other than this one:

    ls docs/exec-plans/active

Run backend tests:

    cd backend
    uv run --cache-dir /tmp/uv-cache pytest

Expected result:

    collected 28 items
    28 passed

Run the offline eval:

    cd backend
    uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py

Expected result:

    target=plain_rag_baseline examples=20 category_accuracy=null retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=0.30 final_pass_rate=0.30 bad_cases=28
    target=graph_v1 examples=20 category_accuracy=1.00 retrieval_hit_rate=1.00 citation_coverage=1.00 review_trigger_accuracy=1.00 final_pass_rate=1.00 bad_cases=0
    wrote data/evals/results/latest_summary.json
    wrote data/evals/results/bad_cases.jsonl
    wrote data/evals/results/traces/<run_id>/events.jsonl

Run frontend tests:

    cd frontend
    npm test -- --run

Expected result:

    Test Files ... passed
    Tests ... passed

Run the frontend production build:

    cd frontend
    npm run build

Expected result:

    tsc -b && vite build
    built in ...

Start the backend for manual smoke testing:

    cd backend
    uv run uvicorn app.main:app --reload

In another terminal, start the frontend:

    cd frontend
    npm run dev -- --host 127.0.0.1 --port 5173

Manual smoke checklist:

- Open `http://127.0.0.1:5173/tickets`.
- Confirm the demo ticket list loads and a ticket detail panel appears.
- Select `ticket-1003`, click `Run workflow`, and confirm a draft reply, citations, completed timeline, and final response appear.
- Select `ticket-1001`, click `Run workflow`, and confirm the UI shows `Human review required` or equivalent waiting-review state.
- Open `http://127.0.0.1:5173/reviews`.
- Confirm the pending review shows the draft, retrieved knowledge, risk flags, and review decision controls.
- Submit an approve decision and confirm the review completes with final disposition `approved`.
- Run another risky ticket and reject it; confirm the resulting backend/UI state is `manual_takeover`.
- Refresh `/tickets` and confirm the latest run state and timeline reload while the backend process is still running.

Record acceptance evidence in `docs/product-specs/supportflow-mvp.md` using this shape:

    ## Current acceptance evidence

    Verified on 2026-04-26.

    - One ticket can enter the workflow: proven by ...
    - System can show a draft reply: proven by ...
    - Risky cases can be reviewed by a human: proven by ...

Before archiving this plan, update the final transcript in this ExecPlan:

    ## Outcomes & Retrospective

    Day 8 accepted the MVP. Backend tests ..., frontend tests ..., frontend build ..., and offline eval ... all passed. Manual smoke testing confirmed ...

Then archive:

    mv docs/exec-plans/active/2026-04-26-day8-mvp-acceptance-and-closure.md docs/exec-plans/completed/2026-04-26-day8-mvp-acceptance-and-closure.md

## Validation and Acceptance

This plan is complete when all of these are true:

- Backend tests pass.
- Frontend tests pass.
- Frontend production build succeeds.
- Offline eval exits with `graph_v1` final pass rate `1.00` and `0` bad cases.
- Manual `/tickets` low-risk flow shows a final response.
- Manual `/tickets` risky flow creates a pending review.
- Manual `/reviews` approve flow completes with a final response.
- Manual `/reviews` reject flow ends in `manual_takeover`.
- `docs/product-specs/supportflow-mvp.md` records current acceptance evidence.
- README and design docs either match observed behavior or are updated to match.
- This ExecPlan is moved from `docs/exec-plans/active/` to `docs/exec-plans/completed/`.

## Idempotence and Recovery

The automated commands are safe to rerun. The offline eval overwrites `data/evals/results/latest_summary.json` and `data/evals/results/bad_cases.jsonl`, and creates a new trace directory for each run. Do not check generated eval result files into git.

The manual smoke test uses in-memory pending review and checkpoint state. Restarting the backend clears pending reviews and invalidates older `thread_id` values. If the manual flow gets into a confusing state, restart both servers and rerun the smoke checklist from the beginning.

If frontend dependencies are missing, run `npm install` in `frontend/` before test/build commands. If backend dependencies are missing, run `uv sync` in `backend/`. If `uv` cache permissions fail, keep using `--cache-dir /tmp/uv-cache`.

If any MVP behavior fails, do not archive this plan. Record the failure in `Surprises & Discoveries`, make the smallest fix needed to satisfy the MVP spec, rerun the relevant checks, and update `Decision Log` if the fix changes behavior or scope.

## Artifacts and Notes

MVP spec acceptance criteria from `docs/product-specs/supportflow-mvp.md`:

    - one ticket can enter the workflow
    - system can show a draft reply
    - risky cases can be reviewed by a human

Current command set to prove acceptance:

    cd backend && uv run --cache-dir /tmp/uv-cache pytest
    cd backend && uv run --cache-dir /tmp/uv-cache python scripts/run_offline_eval.py
    cd frontend && npm test -- --run
    cd frontend && npm run build

Manual demo tickets:

- `ticket-1003` is the low-risk product ticket expected to auto-finalize.
- `ticket-1001` is a risky billing/refund ticket expected to pause for review.
- `ticket-1002` is a risky account-access ticket that can also be used to test review behavior.

## Interfaces and Dependencies

No public API, schema, data model, graph state, frontend route, or package dependency changes are planned for this acceptance pass. The plan uses the existing routes, schemas, tests, and documentation.

If a failing acceptance check requires a code fix, keep the existing API contracts unless the failure proves that the MVP cannot be accepted without a contract change. Any such contract change must be recorded in `Decision Log`, tested on both backend and frontend where applicable, and reflected in README.
