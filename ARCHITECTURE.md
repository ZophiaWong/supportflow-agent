# ARCHITECTURE

## Goal

Build a workflow-first AI support app for ticket triage and response drafting.

## Components

- React frontend
- FastAPI backend
- LangGraph workflow
- local knowledge base
- later: LangSmith tracing

## Responsibilities

Frontend:

- ticket list
- ticket detail
- review UI

Backend:

- ticket APIs
- graph execution
- retrieval service
- review resume endpoint

Graph:

- classify
- retrieve
- draft
- risk gate
- interrupt/resume
- finalize

## Non-goals for MVP

- multi-agent
- long-term memory
- external write-back
- auth / multi-tenant
