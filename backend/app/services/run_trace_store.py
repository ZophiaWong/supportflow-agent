from __future__ import annotations

import json

from app.schemas.graph import RunTraceEvent
from app.services.sqlite_store import connect


class RunTraceStore:
    def append(self, event: RunTraceEvent) -> None:
        with connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO run_trace_events (
                    trace_id,
                    thread_id,
                    ticket_id,
                    node_name,
                    started_at,
                    ended_at,
                    status,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.trace_id,
                    event.thread_id,
                    event.ticket_id,
                    event.node_name,
                    event.started_at,
                    event.ended_at,
                    event.status,
                    json.dumps(event.model_dump(mode="json"), sort_keys=True),
                ),
            )
            connection.commit()

    def list_by_thread_id(self, thread_id: str) -> list[RunTraceEvent]:
        with connect() as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM run_trace_events
                WHERE thread_id = ?
                ORDER BY started_at, trace_id
                """,
                (thread_id,),
            ).fetchall()

        return [
            RunTraceEvent.model_validate(json.loads(row["payload_json"]))
            for row in rows
        ]

    def has_thread(self, thread_id: str) -> bool:
        with connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM run_trace_events WHERE thread_id = ? LIMIT 1",
                (thread_id,),
            ).fetchone()
        return row is not None

    def clear(self) -> None:
        with connect() as connection:
            connection.execute("DELETE FROM run_trace_events")
            connection.commit()


_run_trace_store = RunTraceStore()


def get_run_trace_store() -> RunTraceStore:
    return _run_trace_store
