# Frontend Review Workbench Redesign

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

SupportFlow is an AI support workflow app where a support agent runs a LangGraph workflow on a ticket, inspects the draft response and knowledge evidence, and sends risky cases to a human reviewer. The current frontend already exposes the required data, but it reads like separate demo pages rather than one focused workbench. After this change, a user can open the app and see an operational review workbench: queue summary, ticket detail, AI output, policy risk, review actions, and graph trace all arranged around the support workflow.

The change is frontend-only. It does not change FastAPI routes, LangGraph state, Pydantic schemas, or review semantics.

## Progress

- [x] (2026-05-27 15:00 HKT) Read `ARCHITECTURE.md`, `docs/product-specs/supportflow-mvp.md`, the active streaming workflow ExecPlan, and the current React/Vite frontend.
- [x] (2026-05-27 15:05 HKT) Chose the review workbench direction with the user.
- [x] (2026-05-27 15:20 HKT) Refactored the app shell, ticket queue, ticket detail, review queue, and review detail layouts into an operational workbench.
- [x] (2026-05-27 15:25 HKT) Updated frontend tests for intentional navigation copy, queue metrics, review CTA, and API mock exports.
- [x] (2026-05-27 16:49 HKT) Ran frontend tests and production build successfully.
- [x] (2026-05-27 17:02 HKT) Fixed medium-width workbench overflow risk and reran frontend validation successfully.
- [x] (2026-05-27 15:30 HKT) Recorded validation blocker and implementation retrospective.
- [x] (2026-05-27 17:35 HKT) Added user-facing run labels, current-review markers, direct review links, and collapsed diagnostics.
- [x] (2026-05-27 17:40 HKT) Updated README and frontend state docs for run labels and diagnostics behavior.
- [x] (2026-05-27 20:42 HKT) Reran frontend tests and build for the run-label pass successfully.
- [x] (2026-05-27 23:55 HKT) Fixed stale workflow output when navigating between ticket detail routes and added regression coverage.

## Surprises & Discoveries

- Observation: The existing frontend already has all data needed for the redesign.
  Evidence: `frontend/src/lib/api.ts` exposes tickets, pending reviews, run start, run state, run timeline, and run trace helpers.

- Observation: No new design dependency is needed for the first pass.
  Evidence: `frontend/package.json` currently depends only on React, React Router, and test/build tooling; the workbench can be built with semantic HTML and CSS.

- Observation: The frontend validation commands passed during the first redesign pass.
  Evidence: `cd frontend && npm test -- --run` reported `13 passed`, and `cd frontend && npm run build` completed successfully.

- Observation: The run-label follow-up is covered by automated frontend validation.
  Evidence: `cd frontend && npm test -- --run` reported `16 passed`, including `frontend/src/lib/runLabels.test.ts`; `cd frontend && npm run build` completed successfully.

## Decision Log

- Decision: Keep this redesign frontend-only.
  Rationale: The current backend responses already include ticket, draft, evidence, policy assessment, support actions, run state, timeline, and trace data. Changing API shape would add risk without improving the requested design.
  Date/Author: 2026-05-27 / Codex

- Decision: Use a quiet SaaS workbench style rather than a marketing or dashboard hero layout.
  Rationale: Support agents and reviewers need scanability, decisions, and traceability. The user selected the review workbench direction.
  Date/Author: 2026-05-27 / Codex

- Decision: Preserve existing routes.
  Rationale: `/tickets`, `/tickets/:ticketId`, `/reviews`, and `/reviews/:threadId` already map cleanly to the workbench workflow and are covered by tests.
  Date/Author: 2026-05-27 / Codex

- Decision: Display workflow runs as `{ticket_id} · Run {thread_id.slice(-8)}`.
  Rationale: Users need to distinguish multiple runs for the same ticket without reading raw LangGraph checkpoint identifiers. The full `thread_id` remains the API and route identifier.
  Date/Author: 2026-05-27 / Codex

- Decision: Move run state, timeline, and trace behind a collapsed Diagnostics surface on ticket detail.
  Rationale: Ticket detail should default to the support decision workflow. Detailed graph state and node spans are still important, but they are diagnostic information rather than the main reading path.
  Date/Author: 2026-05-27 / Codex

## Outcomes & Retrospective

Implemented the frontend review workbench redesign across the shared shell, ticket queue, ticket detail, review queue, and review detail pages. The UI now presents queue metrics, a ticket workbench with current run summary, an explicit waiting-review callout that opens the exact review case, review queue summary metrics, user-facing run labels, and a reviewer decision workspace while preserving the existing routes and API helpers.

Automated validation passed for the redesign and run-label follow-up. Frontend tests were updated for intentional copy and structure changes, the production build completed successfully, and no backend/API changes were made.

## Context and Orientation

The frontend lives under `frontend/` and is a React app built with Vite. `frontend/src/App.tsx` defines the routes and shared `AppShell`. `frontend/src/pages/TicketsPage.tsx` renders the inbox list. `frontend/src/pages/TicketDetailPage.tsx` renders a selected ticket, starts a background workflow run, and polls run state, timeline, and trace. `frontend/src/pages/ReviewQueuePage.tsx` renders pending human reviews. `frontend/src/pages/ReviewDetailPage.tsx` lets a reviewer approve, edit, or reject a draft. `frontend/src/styles.css` contains the app-wide CSS.

The term "review workbench" in this plan means an operational interface for support work: queues, decision panels, risk signals, draft text, evidence, and trace details arranged for scanning and action.

## Plan of Work

First, update the shell so the app identity is "SupportFlow Workbench" and navigation feels like a small product workspace. Keep the same routes and `NavLink` behavior.

Second, update the ticket queue to include a compact queue summary above the table. The summary should derive counts from the loaded tickets: total tickets, open tickets, urgent or high priority tickets, and pending tickets. The table stays accessible with `role="table"` and links to ticket detail routes.

Third, update ticket detail into a workbench. The left column contains the ticket and run button. The center column contains workflow output. The right column contains a lightweight current-run summary. Run state, timeline, and trace are available in collapsed diagnostics. When a run is waiting for review, link directly to `/reviews/:threadId`.

Fourth, update review queue and review detail so policy failure, risk flags, proposed actions, confidence, reviewer decision, and user-facing run labels are visually prioritized. Keep the same submit behavior.

Fifth, replace the CSS with a calmer workbench visual system: restrained background, smaller radii, lower shadows, stable tables, status pills, responsive collapse to one column, and no decorative hero imagery.

Finally, run frontend tests and build. Update this ExecPlan with the observed validation output.

## Concrete Steps

Edit the following files from the repository root:

    frontend/src/components/AppShell.tsx
    frontend/src/pages/TicketsPage.tsx
    frontend/src/pages/TicketDetailPage.tsx
    frontend/src/pages/ReviewQueuePage.tsx
    frontend/src/pages/ReviewDetailPage.tsx
    frontend/src/components/WorkflowRunSummary.tsx
    frontend/src/components/RunDiagnostics.tsx
    frontend/src/lib/runLabels.ts
    frontend/src/styles.css
    frontend/src/App.test.tsx
    frontend/src/pages/TicketsPage.test.tsx
    frontend/src/pages/ReviewQueuePage.test.tsx

Run validation from the frontend directory:

    cd frontend
    npm test -- --run
    npm run build

## Validation and Acceptance

The redesign is complete when `/tickets` shows queue-level summary metrics above the support ticket table, `/tickets/:ticketId` shows ticket context, workflow output, current run summary, direct review links, and collapsed diagnostics, `/reviews` distinguishes pending reviews with labels such as `ticket-1001 · Run a1b2c3d4`, and `/reviews/:threadId` clearly separates review evidence from the decision form.

Automated validation must pass:

    cd frontend && npm test -- --run
    cd frontend && npm run build

## Idempotence and Recovery

All edits are normal source changes and can be repeated safely. If visual changes break tests, update the tests only for intentional copy or structure changes, not to hide missing behavior. No backend data or generated migrations are involved.

## Artifacts and Notes

Validation:

    cd frontend
    npm test -- --run
    # 5 test files passed, 13 tests passed

    npm run build
    # built in 624ms

Run-label follow-up validation:

    cd frontend
    npm test -- --run
    # 6 test files passed, 17 tests passed

    npm run build
    # built in 534ms

## Interfaces and Dependencies

No public API or backend schema changes are required. The frontend continues using the existing functions in `frontend/src/lib/api.ts`: `fetchTickets`, `startRun`, `fetchRunState`, `fetchRunTimeline`, `fetchRunTrace`, `fetchPendingReviews`, and `resumeRun`.

2026-05-27: Created this plan because the requested redesign touches multiple frontend pages and the repository requires an active ExecPlan for multi-file frontend work.
