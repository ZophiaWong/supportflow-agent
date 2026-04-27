from __future__ import annotations

import json

from app.schemas.graph import PendingReviewItem
from app.services.sqlite_store import connect


class PendingReviewStore:
    def list_items(self) -> list[PendingReviewItem]:
        with connect() as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM pending_reviews
                ORDER BY updated_at, thread_id
                """
            ).fetchall()
        return [
            PendingReviewItem.model_validate(json.loads(row["payload_json"]))
            for row in rows
        ]

    def get(self, thread_id: str) -> PendingReviewItem | None:
        with connect() as connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM pending_reviews
                WHERE thread_id = ?
                """,
                (thread_id,),
            ).fetchone()
        if row is None:
            return None
        return PendingReviewItem.model_validate(json.loads(row["payload_json"]))

    def upsert(self, item: PendingReviewItem) -> PendingReviewItem:
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO pending_reviews (thread_id, ticket_id, payload_json, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(thread_id) DO UPDATE SET
                    ticket_id = excluded.ticket_id,
                    payload_json = excluded.payload_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    item.thread_id,
                    item.ticket_id,
                    json.dumps(item.model_dump(mode="json")),
                ),
            )
            connection.commit()
        return item

    def remove(self, thread_id: str) -> PendingReviewItem | None:
        existing = self.get(thread_id)
        with connect() as connection:
            connection.execute(
                "DELETE FROM pending_reviews WHERE thread_id = ?",
                (thread_id,),
            )
            connection.commit()
        return existing

    def clear(self) -> None:
        with connect() as connection:
            connection.execute("DELETE FROM pending_reviews")
            connection.commit()


_STORE = PendingReviewStore()


def get_pending_review_store() -> PendingReviewStore:
    return _STORE
