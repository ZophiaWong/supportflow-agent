# Demo Site Layout Redesign

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The current frontend presents the support workflow as dense page-level demo screens. After this change, it will feel like a focused support-agent workspace: a shared header introduces the product, a sidebar provides persistent navigation, the inbox and review queue become full-width scanning lists, and selecting an item opens a dedicated detail route.

The behavior is visible in the browser. A user can open `/tickets`, scan the full-width inbox, choose one ticket, land on `/tickets/:ticketId`, run the workflow, and inspect the result and timeline. A reviewer can open `/reviews`, scan the pending review queue, choose one review, land on `/reviews/:threadId`, and approve, edit, or reject the draft.

## Progress

- [x] (2026-04-27) Read `docs/refs/demo-site-layout-redesign-v0.1.md` and confirmed it is specific enough to plan from.
- [x] (2026-04-27) Inspected the current frontend routes, pages, API helpers, and type definitions.
- [x] (2026-04-27) Created this active ExecPlan.
- [ ] Add the shared app shell with header, description, sidebar, and main content region.
- [ ] Convert `/tickets` into a full-width inbox list page.
- [ ] Add `/tickets/:ticketId` as a dedicated ticket detail and run inspection page.
- [ ] Convert `/reviews` into a full-width pending review queue page.
- [ ] Add `/reviews/:threadId` as a dedicated review detail page.
- [ ] Add or update frontend tests for routes, navigation, empty states, run behavior, and review submission.
- [ ] Run frontend tests and build.
- [ ] Update this ExecPlan with validation evidence and outcomes.

## Surprises & Discoveries

- Observation: The requested target path already existed but was empty.
  Evidence: `sed -n '1,320p' docs/exec-plans/active/2026-04-27-01-demo-site-layout-redesign.md` produced no content.

- Observation: The current frontend still has only two routed pages.
  Evidence: `frontend/src/main.tsx` defines `/`, `/tickets`, and `/reviews`, with `/` redirecting to `/tickets`.

- Observation: The existing frontend API helpers are sufficient for the first pass.
  Evidence: `frontend/src/lib/api.ts` already exposes `fetchTickets`, `runTicket`, `fetchRunState`, `fetchRunTimeline`, `fetchPendingReviews`, and `resumeRun`.

## Decision Log

- Decision: Use dedicated detail routes: `/tickets/:ticketId` and `/reviews/:threadId`.
  Rationale: The reference explicitly chooses dedicated detail pages. Dedicated routes make the demo refreshable, shareable, and easier to present than purely local selected-row state.
  Date/Author: 2026-04-27 / Codex

- Decision: Do not add backend detail endpoints in this pass.
  Rationale: The reference says the first implementation can derive ticket detail from `fetchTickets()` and review detail from `fetchPendingReviews()`. This keeps the redesign frontend-only and lowers risk.
  Date/Author: 2026-04-27 / Codex

- Decision: Preserve existing workflow and review behavior while moving it into detail routes.
  Rationale: This is a layout and navigation redesign, not a graph or API behavior change.
  Date/Author: 2026-04-27 / Codex

- Decision: Use a persistent desktop sidebar with responsive fallback on narrow screens.
  Rationale: The reference asks for a header plus sidebar. A responsive stacked layout keeps the same navigation usable on mobile without adding a drawer state machine.
  Date/Author: 2026-04-27 / Codex

## Outcomes & Retrospective

Not started. At completion, summarize the shipped routes, shell behavior, tests, build output, and any trade-offs discovered while moving state from the old combined pages into dedicated detail routes.

## Context and Orientation

This repository builds `supportflow-agent`, a React frontend and FastAPI backend for an AI support workflow. The relevant work in this plan is frontend-only. The backend and LangGraph workflow should not change.

The React entry point is `frontend/src/main.tsx`. Today it creates a `BrowserRouter` and renders `TicketsPage` at `/tickets` and `ReviewQueuePage` at `/reviews`. The current ticket page is `frontend/src/pages/TicketsPage.tsx`; it loads tickets, keeps selected ticket state locally, runs the workflow, stores the last thread ID in local storage under `supportflow:last-thread-id`, and shows ticket detail plus run inspection on the same screen. The current review page is `frontend/src/pages/ReviewQueuePage.tsx`; it loads pending reviews, keeps review form state locally, submits decisions, and shows completed review output on the same screen.

The frontend API helper file is `frontend/src/lib/api.ts`. It already contains all API calls needed for this plan:

    fetchTickets(): Promise<Ticket[]>
    runTicket(ticketId: string): Promise<RunTicketResponse>
    fetchRunState(threadId: string): Promise<RunStateResponse>
    fetchRunTimeline(threadId: string): Promise<RunTimelineResponse>
    fetchPendingReviews(): Promise<PendingReviewItem[]>
    resumeRun(threadId: string, body: SubmitReviewDecisionRequest): Promise<RunTicketResponse>

The frontend type definitions are in `frontend/src/lib/types.ts`. Reuse these existing types. Do not invent new backend response shapes for this plan.

A dedicated detail route is a URL that identifies the item being inspected, such as `/tickets/ticket-1001` or `/reviews/ticket-ticket-1001`. In this first pass, these pages can load the same lists as their parent queue pages and find the matching item by URL parameter. If the item is missing, the page must show a friendly empty state and a link back to the relevant list.

## Plan of Work

First, introduce an app shell. Create a reusable shell component, for example `frontend/src/components/AppShell.tsx`, or an `AppRoutes` component in `frontend/src/App.tsx` that wraps the router content. The shell must render a header with the title `Support Agent Demo`, a short description that explains this is an AI-assisted support workflow demo, a sidebar with navigation links labeled `Inbox` and `Review Queue`, and a main content area for the active route. Use `NavLink` from `react-router-dom` so active navigation can be styled.

Second, update routing in `frontend/src/main.tsx` or a new `frontend/src/App.tsx`. Keep `/` redirecting to `/tickets`. Add routes for `/tickets`, `/tickets/:ticketId`, `/reviews`, and `/reviews/:threadId`. Keep the route names exactly as written here.

Third, split the current ticket page behavior into two user experiences. The `/tickets` route should become a full-width inbox list. It should load tickets with `fetchTickets()` and show each ticket as a row with ticket ID, customer, subject, priority, status, created date, and an action to open the ticket. The open action should navigate to `/tickets/:ticketId`. Prefer semantic table markup if it stays responsive and readable; otherwise use a row-list layout with column-like cells. The list should use the full available main panel width and should not show run inspection or workflow output.

Fourth, add the ticket detail page. It can be a new file such as `frontend/src/pages/TicketDetailPage.tsx`. It should read `ticketId` with `useParams`, load tickets with `fetchTickets()`, find the matching ticket, and show the existing ticket detail component, run workflow action, workflow output, run state panel, and workflow timeline. Move the existing run workflow, active thread ID, polling, and local storage behavior from `TicketsPage` into this detail page. Preserve the current behavior where a workflow run sets the active thread ID and the run state/timeline reload from that thread. Include a link back to `/tickets`.

Fifth, split the current review page behavior into two user experiences. The `/reviews` route should become a full-width queue list. It should load pending reviews with `fetchPendingReviews()` and show each pending review as a row with ticket ID, category, priority, risk flags, draft confidence, and an action to open the review. The open action should navigate to `/reviews/:threadId`. The backend does not expose creation time, so keep the existing API order as the queue order. The page should not show the decision form inline.

Sixth, add the review detail page. It can be a new file such as `frontend/src/pages/ReviewDetailPage.tsx`. It should read `threadId` with `useParams`, load pending reviews with `fetchPendingReviews()`, find the matching review, and show the risk flags, draft reply, knowledge evidence, decision selector, edited answer textarea when decision is `edit`, reviewer note textarea, and submit button. Preserve the existing `resumeRun()` request body exactly. After successful submission, show the completed response or manual takeover result on the detail page, and remove or stop relying on the pending item. Include a link back to `/reviews`.

Seventh, update `frontend/src/styles.css`. Replace the page-hero-centered layout with an operational workspace layout: header at top, sidebar plus main panel below. Keep styling restrained and scannable. Avoid a marketing landing page. The main list pages should use full width and stable row spacing. The detail pages can use panels for ticket detail, workflow output, run inspection, and review decision content. Ensure the responsive layout works at narrow widths by stacking the sidebar above content or converting it into top navigation.

Eighth, update tests. Existing page tests in `frontend/src/pages/TicketsPage.test.tsx` and `frontend/src/pages/ReviewQueuePage.test.tsx` should be rewritten or supplemented to match the new route split. Add tests for shell navigation if useful. The tests should prove list pages render, clicking an item navigates to the correct detail URL, detail pages render expected data, missing route params show a recoverable state, running a workflow still calls `runTicket()`, restored thread state still calls `fetchRunState()` and `fetchRunTimeline()`, and review submission still calls `resumeRun()` with the current request shape.

## Milestones

Milestone 1 creates the app shell and route structure. At the end of this milestone, the app has a visible `Support Agent Demo` header, sidebar links for `Inbox` and `Review Queue`, and routes for list and detail pages. The detail pages may still render placeholder content for a short time during implementation, but navigation should not crash. Verify by running frontend tests that cover shell links and route rendering.

Milestone 2 implements the inbox list and ticket detail route. At the end of this milestone, `/tickets` is a full-width scanning page and `/tickets/:ticketId` shows ticket detail plus the existing workflow run and run inspection behavior. Verify by testing ticket list rendering, route navigation, missing ticket handling, workflow run, and restored thread polling.

Milestone 3 implements the review queue list and review detail route. At the end of this milestone, `/reviews` is a full-width pending queue and `/reviews/:threadId` shows the review decision workflow. Verify by testing queue rendering, route navigation, missing pending review handling, approve/edit/reject submission, and completed result rendering.

Milestone 4 completes styling and documentation. At the end of this milestone, the layout is responsive, the UI feels like a support-agent workspace, and this ExecPlan records the final validation output.

## Concrete Steps

Start by inspecting the current frontend and reference material:

    cd /home/poter/resume-pj/supportflow-agent
    sed -n '1,260p' docs/refs/demo-site-layout-redesign-v0.1.md
    sed -n '1,260p' frontend/src/main.tsx
    sed -n '1,320p' frontend/src/pages/TicketsPage.tsx
    sed -n '1,340p' frontend/src/pages/ReviewQueuePage.tsx
    sed -n '1,260p' frontend/src/lib/api.ts
    sed -n '1,320p' frontend/src/lib/types.ts

Run the current frontend tests before implementation:

    cd /home/poter/resume-pj/supportflow-agent/frontend
    npm test -- --run

Expected current baseline before this redesign, if the tree is in the same state observed while writing this plan:

    Test Files  4 passed (4)
    Tests       9 passed (9)

Implement the route shell, list pages, detail pages, tests, and styles. After implementation, run:

    cd /home/poter/resume-pj/supportflow-agent/frontend
    npm test -- --run
    npm run build

If the build updates tracked TypeScript build-info files such as `frontend/tsconfig.app.tsbuildinfo`, inspect the diff and keep it only if it accurately reflects new tracked source files. Do not leave accidental unrelated generated output in the working tree.

## Validation and Acceptance

This plan is complete when all of these are true:

- `/tickets` shows a full-width inbox list with ticket ID, customer, subject, priority, status, created date, and an action to open a ticket.
- Clicking a ticket action navigates to `/tickets/:ticketId`.
- `/tickets/:ticketId` shows the selected ticket detail, run workflow action, workflow output, run inspection, and workflow timeline.
- A missing ticket ID shows a clear empty state and link back to `/tickets`.
- Running a ticket still calls the existing backend run endpoint through `runTicket(ticketId)`.
- Restoring or setting an active thread still loads run state and timeline through `fetchRunState(threadId)` and `fetchRunTimeline(threadId)`.
- `/reviews` shows a full-width pending review queue with ticket ID, category, priority, risk flags, draft confidence, and an action to open the review.
- Clicking a review action navigates to `/reviews/:threadId`.
- `/reviews/:threadId` shows the selected pending review, supporting evidence, and approve/edit/reject form.
- A missing or no-longer-pending thread ID shows a clear empty state and link back to `/reviews`.
- Submitting a review still calls `resumeRun(threadId, body)` with `decision`, `reviewer_note`, and `edited_answer` behavior matching the current page.
- The shared shell shows `Support Agent Demo`, a short description, `Inbox`, and `Review Queue` across all routes.
- `npm test -- --run` and `npm run build` pass in `frontend/`.

Manual smoke should be performed after automated checks pass. Start the backend and frontend dev servers, open `/tickets`, navigate to a ticket detail page, run a low-risk ticket, confirm workflow output appears, return to `/tickets`, open `/reviews`, open a pending review detail page, submit an approve decision, and confirm the completed review result appears.

## Idempotence and Recovery

This is a frontend-only refactor and should be safe to retry. If a list page cannot find data for a detail route, it must show a recoverable empty state instead of throwing. If a route test fails because text appears in both a list and detail panel, scope assertions by role or region rather than weakening behavior.

Do not change backend APIs, LangGraph graph behavior, SQLite persistence, or schema definitions for this plan. If implementation discovers that a direct backend detail endpoint is necessary, pause and update the Decision Log with the reason before adding backend work.

## Artifacts and Notes

The source reference for this plan is:

    docs/refs/demo-site-layout-redesign-v0.1.md

The user-facing route choices are:

    /tickets
    /tickets/:ticketId
    /reviews
    /reviews/:threadId

The visible shell labels are:

    Support Agent Demo
    Inbox
    Review Queue

The first-pass implementation intentionally avoids backend changes. The ticket detail page derives from `fetchTickets()`, and the review detail page derives from `fetchPendingReviews()`.

## Interfaces and Dependencies

Use React Router from `react-router-dom`, which is already installed. The required router APIs are `Routes`, `Route`, `Navigate`, `NavLink`, `Link`, `useNavigate`, and `useParams`.

Recommended frontend files to add or create are:

    frontend/src/App.tsx
    frontend/src/components/AppShell.tsx
    frontend/src/pages/TicketDetailPage.tsx
    frontend/src/pages/ReviewDetailPage.tsx

Recommended frontend files to update are:

    frontend/src/main.tsx
    frontend/src/pages/TicketsPage.tsx
    frontend/src/pages/ReviewQueuePage.tsx
    frontend/src/pages/TicketsPage.test.tsx
    frontend/src/pages/ReviewQueuePage.test.tsx
    frontend/src/styles.css

Keep using existing UI components where they still fit:

    frontend/src/components/TicketDetail.tsx
    frontend/src/components/RunStatePanel.tsx
    frontend/src/components/WorkflowResultPanel.tsx
    frontend/src/components/WorkflowTimeline.tsx

Do not add a new design system dependency. Use local React components and CSS.

## Plan Revision Notes

2026-04-27: Initial active ExecPlan created from `docs/refs/demo-site-layout-redesign-v0.1.md`. The design choices are header plus sidebar, full-width list pages, dedicated detail routes, and no backend changes in the first pass.
