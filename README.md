# supportflow-agent

Day 1 bootstrap for a workflow-first AI support app focused on ticket triage.

## What exists today

- FastAPI backend with `GET /healthz`
- FastAPI mock tickets endpoint at `GET /api/v1/tickets`
- React frontend ticket list at `/tickets`
- Initial `TicketState` model for the future LangGraph workflow

## Run the backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

The backend starts on `http://127.0.0.1:8000`.

## Run the frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

The frontend starts on `http://127.0.0.1:5173/tickets`.

## Tests

```bash
cd backend
uv run pytest

cd ../frontend
npm run test -- --run
```
