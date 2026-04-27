# Demo Site Layout Redesign

This reference captures the intended frontend direction for the support workflow demo. It replaces the rough draft notes from `ui-draft-idea.md`.

## Goal

Make the demo site feel like a focused support-agent workspace instead of a single dense demo page. The main experience should help a reviewer scan queues first, then inspect one ticket or review in a dedicated detail view.

## App Shell

The app should use a shared shell across all pages:

- Header title: `Support Agent Demo`
- Header description: short text explaining that this is an AI-assisted support workflow demo.
- Sidebar navigation:
  - `Inbox`
  - `Review Queue`
- Main panel: route-specific content.

The sidebar should be persistent on desktop. On narrow screens, it can collapse into top navigation or stack above the main panel.

## Routes

Use dedicated detail routes. Even when the list page has already loaded enough data, separate routes make the demo easier to refresh, share, and present.

- `/tickets`
  - Full-width inbox list.
- `/tickets/:ticketId`
  - Ticket detail page.
- `/reviews`
  - Full-width review queue list.
- `/reviews/:threadId`
  - Pending review detail page.

Use forward slashes for URLs. Do not use backslash paths such as `\ticket\{ticket-id}\details`.

## Inbox Page

The inbox page should focus on scanning tickets. The ticket list should occupy the full available main-panel width.

Show ticket rows with basic columns:

- Ticket ID
- Customer
- Subject
- Priority
- Status
- Created date
- Action to open the ticket

Selecting a ticket should navigate to `/tickets/:ticketId`.

## Ticket Detail Page

The ticket detail page should show one selected ticket and the workflow inspection tools.

Show:

- Ticket detail
- Run workflow action
- Workflow output
- Run inspection
- Workflow timeline

For the first implementation pass, the detail page can load all tickets with the existing `fetchTickets()` helper and find the selected ticket by route parameter. A dedicated backend `GET /tickets/{ticketId}` endpoint is not required yet.

If the URL contains a ticket ID that is not found, show a recoverable empty state with a link back to `/tickets`.

## Review Queue Page

The review queue page should focus on pending reviews first-in. The list should occupy the full available main-panel width.

Show review rows with basic columns:

- Ticket ID
- Category
- Priority
- Risk flags
- Draft confidence
- Action to open the review

The backend does not currently expose review creation time, so use the existing API order as the queue order for now. If timestamps are added later, sort oldest pending review first.

Selecting a review should navigate to `/reviews/:threadId`.

## Review Detail Page

The review detail page should show one pending review and the decision workflow.

Show:

- Ticket/review summary
- Risk flags
- Draft reply
- Knowledge evidence
- Review decision controls
- Submit review action

For the first implementation pass, the detail page can load pending reviews with the existing `fetchPendingReviews()` helper and find the selected review by route parameter. A dedicated backend `GET /reviews/pending/{threadId}` endpoint is not required yet.

If the URL contains a thread ID that is no longer pending or not found, show a recoverable empty state with a link back to `/reviews`.

## Design Guidance

Keep the interface operational and dashboard-like. Avoid a marketing landing page or decorative hero layout. The main value of the demo is showing a practical agent workflow: queue scanning, ticket inspection, graph/run visibility, and human review.

Use compact layout, readable tables or rows, clear actions, and restrained visual styling. The UI should make it obvious that this project is an AI support workflow tool suitable for an AI Agent Engineer portfolio.

## Implementation Notes

This redesign can be implemented without backend changes in the first pass.

Use existing frontend helpers:

- `fetchTickets()`
- `runTicket(ticketId)`
- `fetchRunState(threadId)`
- `fetchRunTimeline(threadId)`
- `fetchPendingReviews()`
- `resumeRun(threadId, body)`

Keep existing workflow behavior intact:

- Running a ticket still starts the LangGraph workflow.
- The last inspected thread can still be restored from local storage.
- Pending reviews can still be approved, edited, or rejected.
- Missing route data should show a friendly empty state instead of crashing.
