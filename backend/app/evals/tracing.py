import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def is_langsmith_enabled() -> bool:
    return False


class TraceWriter:
    def __init__(self, *, run_id: str, output_dir: Path) -> None:
        self.run_id = run_id
        self.events_path = output_dir / "traces" / run_id / "events.jsonl"
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        self.events_path.write_text("")

    def emit(
        self,
        *,
        target: str,
        example_id: str,
        ticket_id: str,
        stage: str,
        status: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            "example_id": example_id,
            "target": target,
            "ticket_id": ticket_id,
            "stage": stage,
            "status": status,
            "trace_url": None,
            "langsmith_enabled": is_langsmith_enabled(),
            "payload": payload or {},
        }
        with self.events_path.open("a") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
