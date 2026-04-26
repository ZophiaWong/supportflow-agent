import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


def is_langsmith_enabled() -> bool:
    return (
        os.getenv("LANGSMITH_TRACING", "").lower() in {"1", "true", "yes"}
        and bool(os.getenv("LANGSMITH_API_KEY"))
    )


class TraceWriter:
    def __init__(self, *, run_id: str, output_dir: Path) -> None:
        self.run_id = run_id
        self.events_path = output_dir / "traces" / run_id / "events.jsonl"
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        self.events_path.write_text("")
        self.langsmith_enabled = is_langsmith_enabled()
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "supportflow-agent-evals")

    def _write_langsmith_run(
        self,
        *,
        target: str,
        example_id: str,
        ticket_id: str,
        stage: str,
        status: str,
        payload: dict[str, Any],
    ) -> tuple[str | None, str | None]:
        if not self.langsmith_enabled:
            return None, None

        try:
            from langsmith import Client

            client = Client()
            run_id = uuid4()
            client.create_run(
                id=run_id,
                name=f"{target}:{stage}",
                run_type="chain",
                project_name=self.langsmith_project,
                inputs={
                    "eval_run_id": self.run_id,
                    "example_id": example_id,
                    "ticket_id": ticket_id,
                    "target": target,
                    "stage": stage,
                    "payload": payload,
                },
                extra={
                    "metadata": {
                        "eval_run_id": self.run_id,
                        "example_id": example_id,
                        "ticket_id": ticket_id,
                        "target": target,
                    }
                },
            )
            client.update_run(
                run_id,
                outputs={"status": status, "payload": payload},
                end_time=datetime.now(UTC),
            )
            run = client.read_run(run_id)
            return client.get_run_url(run=run, project_name=self.langsmith_project), None
        except Exception as exc:
            return None, f"{type(exc).__name__}: {exc}"

    def emit(
        self,
        *,
        target: str,
        example_id: str,
        ticket_id: str,
        stage: str,
        status: str,
        payload: dict[str, Any] | None = None,
    ) -> str | None:
        event_payload = payload or {}
        trace_url, langsmith_error = self._write_langsmith_run(
            target=target,
            example_id=example_id,
            ticket_id=ticket_id,
            stage=stage,
            status=status,
            payload=event_payload,
        )
        if langsmith_error:
            event_payload = {
                **event_payload,
                "langsmith_warning": langsmith_error,
            }

        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "run_id": self.run_id,
            "example_id": example_id,
            "target": target,
            "ticket_id": ticket_id,
            "stage": stage,
            "status": status,
            "trace_url": trace_url,
            "langsmith_enabled": self.langsmith_enabled,
            "payload": event_payload,
        }
        with self.events_path.open("a") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
        return trace_url
