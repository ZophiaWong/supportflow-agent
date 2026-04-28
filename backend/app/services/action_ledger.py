from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from typing import Any

from app.schemas.actions import SupportAction, SupportActionCreate
from app.services.sqlite_store import connect


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _action_id(idempotency_key: str) -> str:
    digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
    return f"act_{digest[:20]}"


def _row_to_action(row: Any) -> SupportAction:
    return SupportAction.model_validate(
        {
            "action_id": row["action_id"],
            "thread_id": row["thread_id"],
            "ticket_id": row["ticket_id"],
            "action_type": row["action_type"],
            "status": row["status"],
            "idempotency_key": row["idempotency_key"],
            "requires_review": bool(row["requires_review"]),
            "reason": row["reason"],
            "payload": json.loads(row["payload_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    )


class ActionLedger:
    def propose(self, action: SupportActionCreate) -> SupportAction:
        action_id = _action_id(action.idempotency_key)
        timestamp = _now()
        payload_json = json.dumps(action.payload, sort_keys=True)

        with connect() as connection:
            connection.execute(
                """
                INSERT INTO support_actions (
                    action_id,
                    thread_id,
                    ticket_id,
                    action_type,
                    status,
                    idempotency_key,
                    requires_review,
                    reason,
                    payload_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, 'proposed', ?, ?, ?, ?, ?, ?)
                ON CONFLICT(idempotency_key) DO NOTHING
                """,
                (
                    action_id,
                    action.thread_id,
                    action.ticket_id,
                    action.action_type,
                    action.idempotency_key,
                    int(action.requires_review),
                    action.reason,
                    payload_json,
                    timestamp,
                    timestamp,
                ),
            )
            connection.commit()
            row = connection.execute(
                """
                SELECT *
                FROM support_actions
                WHERE idempotency_key = ?
                """,
                (action.idempotency_key,),
            ).fetchone()

        if row is None:
            raise RuntimeError("Failed to persist support action")
        return _row_to_action(row)

    def list_by_thread_id(self, thread_id: str) -> list[SupportAction]:
        with connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM support_actions
                WHERE thread_id = ?
                ORDER BY created_at, action_id
                """,
                (thread_id,),
            ).fetchall()
        return [_row_to_action(row) for row in rows]

    def approve_for_thread(self, thread_id: str) -> list[SupportAction]:
        timestamp = _now()
        with connect() as connection:
            connection.execute(
                """
                UPDATE support_actions
                SET status = 'approved',
                    updated_at = ?
                WHERE thread_id = ?
                  AND status = 'proposed'
                  AND requires_review = 1
                """,
                (timestamp, thread_id),
            )
            connection.commit()
        return self.list_by_thread_id(thread_id)

    def reject_for_thread(self, thread_id: str, reason: str | None = None) -> list[SupportAction]:
        timestamp = _now()
        with connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM support_actions
                WHERE thread_id = ?
                  AND status IN ('proposed', 'approved')
                """,
                (thread_id,),
            ).fetchall()
            for row in rows:
                payload = json.loads(row["payload_json"])
                if reason:
                    payload["rejection_reason"] = reason
                connection.execute(
                    """
                    UPDATE support_actions
                    SET status = 'rejected',
                        payload_json = ?,
                        updated_at = ?
                    WHERE action_id = ?
                    """,
                    (json.dumps(payload, sort_keys=True), timestamp, row["action_id"]),
                )
            connection.commit()
        return self.list_by_thread_id(thread_id)

    def execute_once(self, action_id: str) -> SupportAction:
        with connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM support_actions
                WHERE action_id = ?
                """,
                (action_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Unknown support action: {action_id}")

            action = _row_to_action(row)
            if action.status == "executed":
                return action
            if action.status in {"rejected", "failed"}:
                return action
            if action.requires_review and action.status != "approved":
                raise ValueError("Action requires approval before execution")

            timestamp = _now()
            connection.execute(
                """
                UPDATE support_actions
                SET status = 'executed',
                    updated_at = ?
                WHERE action_id = ?
                  AND status != 'executed'
                """,
                (timestamp, action_id),
            )
            connection.commit()
            next_row = connection.execute(
                """
                SELECT *
                FROM support_actions
                WHERE action_id = ?
                """,
                (action_id,),
            ).fetchone()

        if next_row is None:
            raise RuntimeError("Failed to reload executed support action")
        return _row_to_action(next_row)

    def clear(self) -> None:
        with connect() as connection:
            connection.execute("DELETE FROM support_actions")
            connection.commit()


_ACTION_LEDGER = ActionLedger()


def get_action_ledger() -> ActionLedger:
    return _ACTION_LEDGER
