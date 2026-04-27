from datetime import UTC, datetime
import json
from typing import Literal
from uuid import uuid4

from app.schemas.graph import RunTimelineEvent
from app.services.sqlite_store import connect


class RunEventStore:
    def append(self, event: RunTimelineEvent) -> None:
        with connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO run_events (
                    event_id,
                    thread_id,
                    ticket_id,
                    created_at,
                    event_type,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.thread_id,
                    event.ticket_id,
                    event.created_at,
                    event.event_type,
                    json.dumps(event.model_dump(mode="json")),
                ),
            )
            connection.commit()

    def create_event(
        self,
        *,
        thread_id: str,
        ticket_id: str,
        event_type: Literal[
            "run_started",
            "classify_completed",
            "retrieve_completed",
            "draft_completed",
            "risk_gate_completed",
            "interrupt_created",
            "review_submitted",
            "run_resumed",
            "run_completed",
            "run_failed",
        ],
        status: Literal["running", "waiting_review", "done", "failed", "manual_takeover"],
        node_name: str | None = None,
        message: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> RunTimelineEvent:
        return RunTimelineEvent(
            event_id=uuid4().hex,
            thread_id=thread_id,
            ticket_id=ticket_id,
            event_type=event_type,
            node_name=node_name,
            status=status,
            message=message,
            created_at=datetime.now(UTC).isoformat(),
            payload=payload,
        )

    def list_by_thread_id(self, thread_id: str) -> list[RunTimelineEvent]:
        with connect() as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM run_events
                WHERE thread_id = ?
                ORDER BY created_at, event_id
                """,
                (thread_id,),
            ).fetchall()
        if rows:
            return [
                RunTimelineEvent.model_validate(json.loads(row["payload_json"]))
                for row in rows
            ]
        return []

    def has_thread(self, thread_id: str) -> bool:
        with connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM run_events WHERE thread_id = ? LIMIT 1",
                (thread_id,),
            ).fetchone()
        return row is not None

    def clear(self) -> None:
        with connect() as connection:
            connection.execute("DELETE FROM run_events")
            connection.commit()


_run_event_store = RunEventStore()


def get_run_event_store() -> RunEventStore:
    return _run_event_store
