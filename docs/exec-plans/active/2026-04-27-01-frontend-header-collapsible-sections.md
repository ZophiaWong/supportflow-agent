# Day 17 Frontend Header and Collapsible Sections

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The demo currently opens directly into page-specific hero content and then shows dense ticket, run, and review information all at once. After this change, the app will have a shared header that makes the demo feel like one cohesive product, and support agents will be able to fold the main information sections when they need a cleaner workspace.

The behavior is visible in the browser. On `/tickets`, the page should show a shared header above the current content, and the `Tickets`, `Ticket detail`, and `Run inspection` areas should each have a toggle that hides or restores that section's body. On `/reviews`, the shared header should also be present, and each review card should let the user fold major blocks such as risk flags, draft reply, knowledge evidence, and review action.

## Progress

- [x] (2026-04-27) Reviewed the current frontend page and component structure.
- [x] (2026-04-27) Confirmed desired defaults with the user: page sections are foldable, and all foldable sections are open by default.
- [x] (2026-04-27) Created this active ExecPlan.
- [ ] Add the shared header component and integrate it into the app shell.
- [ ] Add the reusable collapsible section component.
- [ ] Update the ticket page to make `Tickets`, `Ticket detail`, and `Run inspection` foldable.
- [ ] Update the review queue page to make review detail blocks foldable.
- [ ] Add or update frontend tests for header navigation and fold/unfold behavior.
- [ ] Run frontend tests and build.
- [ ] Update this ExecPlan with implementation evidence and outcomes.

## Surprises & Discoveries

- Observation: The app already has page-level hero blocks but no shared app-level header.
  Evidence: `frontend/src/main.tsx` routes directly to `TicketsPage` and `ReviewQueuePage`; both pages render their own `section.hero`.

- Observation: The dense areas are currently always expanded.
  Evidence: `frontend/src/pages/TicketsPage.tsx` directly renders `TicketList`, `TicketDetail`, `RunStatePanel`, and `WorkflowTimeline`; `frontend/src/pages/ReviewQueuePage.tsx` directly renders risk flags, draft reply, knowledge evidence, and review action blocks for each pending review.

## Decision Log

- Decision: Add a shared app-level header without replacing the existing page hero sections.
  Rationale: The user asked for a header section, while the existing hero text still explains the current workflow page. Keeping both preserves context and adds product navigation.
  Date/Author: 2026-04-27 / Codex

- Decision: Make page sections foldable and keep them open by default.
  Rationale: The user selected page-section folding and open-by-default behavior. This preserves current demo discoverability while letting a reviewer hide dense details.
  Date/Author: 2026-04-27 / Codex

- Decision: Do not persist collapsed state in localStorage in this pass.
  Rationale: Persisting preferences adds state and test complexity that is not necessary for the requested behavior.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize the components added, the sections made foldable, the test commands run, and any UX trade-offs discovered during implementation.

## Context and Orientation

This repository is a React, FastAPI, and LangGraph support workflow demo. The relevant work for this plan is frontend-only. The React entry point is `frontend/src/main.tsx`, which creates a `BrowserRouter` and defines the `/tickets` and `/reviews` routes. The ticket page is `frontend/src/pages/TicketsPage.tsx`. The review queue page is `frontend/src/pages/ReviewQueuePage.tsx`. Shared UI components live under `frontend/src/components/`, and global styles live in `frontend/src/styles.css`.

A collapsible section is a region of the page with a button that announces whether the region is expanded or collapsed. In React, the section should use component state to decide whether to render its body. For accessibility, the toggle button should set `aria-expanded` to `true` or `false` and `aria-controls` to the id of the controlled content region.

The current ticket page has three columns inside `section.workspace`: a ticket list column headed `Tickets`, a detail column headed `Ticket detail`, and a timeline column headed `Run inspection`. The current review page renders a grid of review cards in `section.review-grid`; each pending review card contains sections titled `Risk flags`, `Draft reply`, `Knowledge evidence`, and `Review action`.

## Plan of Work

First, add a shared header component in `frontend/src/components/AppHeader.tsx`. The component should render the product name `SupportFlow Agent`, a short operational label such as `AI support workflow demo`, and navigation links to `/tickets` and `/reviews`. Use `NavLink` from `react-router-dom` so the active route can be styled without manually reading location state. Integrate this header in `frontend/src/main.tsx` by introducing a small app shell that renders `AppHeader` above the existing `Routes`.

Second, add a reusable `CollapsibleSection` component in `frontend/src/components/CollapsibleSection.tsx`. It should accept a visible title, optional compact summary text or right-side accessory content, an optional `defaultOpen` prop that defaults to `true`, and `children`. It should render a real `button` for the toggle, include a visual chevron or plus/minus indicator using text or CSS, and expose correct `aria-expanded` and `aria-controls` attributes. Keep the component local and lightweight; do not introduce a UI framework.

Third, update `frontend/src/pages/TicketsPage.tsx`. Replace each standalone workspace heading and body with `CollapsibleSection`. The `Tickets` section body should contain `TicketList`. The `Ticket detail` section body should contain the existing selected-ticket detail, empty selection message, and workflow result panel. The `Run inspection` section body should contain `RunStatePanel` and `WorkflowTimeline`. Preserve all existing fetch, polling, selection, localStorage thread, and run workflow behavior.

Fourth, update `frontend/src/pages/ReviewQueuePage.tsx`. Keep each pending or completed review as a visible card so the queue remains scannable. Inside each pending review card, wrap `Risk flags`, `Draft reply`, `Knowledge evidence`, and `Review action` in `CollapsibleSection` instances, all open by default. For completed review cards, wrap the final response or manual takeover block in a foldable section. Preserve decision selection, edited answer, reviewer notes, submit behavior, and completed result rendering.

Fifth, update `frontend/src/styles.css`. Add styles for the shared header, active navigation link, collapsible section header, toggle button, and collapsed body spacing. Keep the visual language consistent with the existing app: light background, restrained borders, compact controls, no decorative marketing-only elements, and no backend-dependent visual states.

Sixth, update frontend tests. Extend `frontend/src/pages/TicketsPage.test.tsx` to assert that the header renders, the navigation link to the review queue exists, and each ticket page section starts expanded and can be collapsed and reopened. Extend `frontend/src/pages/ReviewQueuePage.test.tsx` to assert that the header renders, review detail sections start expanded, and at least one pending review section can be collapsed and reopened without breaking review submission. If the shared component benefits from isolated coverage, add a small `frontend/src/components/CollapsibleSection.test.tsx`, but page-level tests are sufficient if they cover the real user behavior.

## Concrete Steps

Inspect the current frontend files before editing:

    cd /home/poter/resume-pj/supportflow-agent
    sed -n '1,220p' frontend/src/main.tsx
    sed -n '1,320p' frontend/src/pages/TicketsPage.tsx
    sed -n '1,340p' frontend/src/pages/ReviewQueuePage.tsx
    sed -n '1,760p' frontend/src/styles.css

Run the current frontend tests to capture the baseline:

    cd /home/poter/resume-pj/supportflow-agent/frontend
    npm test -- --run

Implement the components and page updates, then run:

    cd /home/poter/resume-pj/supportflow-agent/frontend
    npm test -- --run
    npm run build

Expected successful test and build output should look like:

    Test Files  4 passed (4)
    Tests       9 passed (9)

    built in <duration>

The exact test count may increase if a new component test file is added. Record the final observed count in `Outcomes & Retrospective`.

## Validation and Acceptance

This plan is complete when all of these are true:

- `/tickets` shows a shared app header above the existing page content.
- `/reviews` shows the same shared app header above the existing page content.
- The header has working navigation between the ticket inbox and review queue.
- On `/tickets`, `Tickets`, `Ticket detail`, and `Run inspection` are open on first render and can be collapsed and reopened independently.
- On `/reviews`, pending review detail blocks are open on first render and can be collapsed and reopened independently.
- Collapsing sections does not lose ticket selection, workflow results, pending review form state, or review submission behavior.
- Frontend tests cover the new header and representative fold/unfold behavior.
- `npm test -- --run` and `npm run build` pass in `frontend/`.

Manual smoke should be done after tests pass. Start the frontend and backend as usual, open `/tickets`, confirm the header and three section toggles are visible, collapse and reopen each section, run a ticket, then open `/reviews` and collapse and reopen review detail blocks before submitting a review.

## Idempotence and Recovery

The implementation is additive and safe to retry. Re-running tests and builds should not change tracked source files. If a section disappears unexpectedly after a toggle, inspect the `CollapsibleSection` state and confirm each instance has a stable id. If a test cannot find text after a collapse, reopen the section in the test before asserting behavior unrelated to folding.

Do not change backend APIs, LangGraph workflow behavior, or data schemas for this plan. If backend changes appear necessary while implementing, stop and update this ExecPlan with the reason before making those changes.

## Artifacts and Notes

The user confirmed these product choices before this plan was written:

    Fold scope: Page sections
    Default state: Open by default

The relevant current routes are:

    /tickets  -> frontend/src/pages/TicketsPage.tsx
    /reviews  -> frontend/src/pages/ReviewQueuePage.tsx

## Interfaces and Dependencies

Add these frontend components:

    frontend/src/components/AppHeader.tsx
    frontend/src/components/CollapsibleSection.tsx

`AppHeader` should use `NavLink` from `react-router-dom`, already present in the app. It should not accept backend data.

`CollapsibleSection` should be a regular React component with a minimal interface like:

    interface CollapsibleSectionProps {
      title: string;
      summary?: string;
      defaultOpen?: boolean;
      className?: string;
      children: React.ReactNode;
    }

The implementer may add a small optional prop for right-aligned metadata if it keeps the page code simpler, but the component should remain generic and frontend-only.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created from the user's requested frontend feature: add a shared header and make ticket, run inspection, and review queue details foldable.
