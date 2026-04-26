from collections import defaultdict
from datetime import UTC, datetime
from threading import Lock
from typing import Literal
from uuid import uuid4

from app.schemas.graph import RunTimelineEvent


class RunEventStore:
    def __init__(self) -> None:
        self._items: dict[str, list[RunTimelineEvent]] = defaultdict(list)
        self._lock = Lock()

    def append(self, event: RunTimelineEvent) -> None:
        with self._lock:
            self._items[event.thread_id].append(event)

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
        with self._lock:
            return list(self._items.get(thread_id, []))

    def has_thread(self, thread_id: str) -> bool:
        with self._lock:
            return thread_id in self._items

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


_run_event_store = RunEventStore()


def get_run_event_store() -> RunEventStore:
    return _run_event_store
