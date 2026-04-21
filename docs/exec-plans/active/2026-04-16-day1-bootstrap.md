# Day1 Bootstrap

## Goal

Finish the Day1 shell for supportflow-agent:

- doc skeleton
- backend health endpoint
- mock tickets endpoint
- frontend ticket list
- initial TicketState

## In scope

- lightweight harness-style docs
- minimal FastAPI shell
- minimal React page
- mock data
- initial graph state

## Out of scope

- graph execution
- database
- LangSmith
- Docker
- review queue
- retrieval implementation

## Progress

- [ ] Write AGENTS.md
- [ ] Write ARCHITECTURE.md
- [ ] Write MVP spec
- [ ] Add /healthz
- [ ] Add /api/v1/tickets
- [ ] Render /tickets page
- [ ] Add initial TicketState
- [ ] Update this plan before end of day

## Decision Log

- Use lightweight harness structure instead of a full document matrix.
- Use mock JSON instead of DB on Day1.
- Start from state boundary, not graph node implementation.

## Acceptance

- Backend starts
- /healthz works
- /api/v1/tickets returns mock data
- Frontend renders ticket list
- TicketState is defined

## Final Artifacts Structure

```
supportflow-agent/
├─ AGENTS.md
├─ ARCHITECTURE.md
├─ README.md
├─ .env.example
├─ docs/
│  ├─ design-docs/
│  │  ├─ index.md
│  │  └─ core-beliefs.md
│  ├─ exec-plans/
│  │  ├─ active/
│  │  │  └─ 2026-04-20-day1-bootstrap.md
│  │  └─ completed/
│  └─ product-specs/
│     └─ supportflow-mvp.md
├─ backend/
│  ├─ pyproject.toml
│  └─ app/
│     ├─ main.py
│     ├─ api/
│     │  └─ v1/
│     │     ├─ health.py
│     │     └─ tickets.py
│     ├─ schemas/
│     │  └─ ticket.py
│     └─ graph/
│        └─ state.py
├─ frontend/
│  └─ src/
│     ├─ main.tsx
│     ├─ pages/
│     │  └─ TicketsPage.tsx
│     ├─ components/
│     │  └─ TicketList.tsx
│     └─ lib/
│        ├─ api.ts
│        └─ types.ts
└─ data/
   ├─ sample_tickets/
   │  └─ demo_tickets.json
   └─ kb/
      ├─ refund_policy.md
      └─ account_reset.md

```
