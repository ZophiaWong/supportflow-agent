from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.graph import PendingReviewItem


@dataclass
class PendingReviewStore:
    _items: dict[str, PendingReviewItem] = field(default_factory=dict)

    def list_items(self) -> list[PendingReviewItem]:
        return list(self._items.values())

    def get(self, thread_id: str) -> PendingReviewItem | None:
        return self._items.get(thread_id)

    def upsert(self, item: PendingReviewItem) -> PendingReviewItem:
        self._items[item.thread_id] = item
        return item

    def remove(self, thread_id: str) -> PendingReviewItem | None:
        return self._items.pop(thread_id, None)

    def clear(self) -> None:
        self._items.clear()


_STORE = PendingReviewStore()


def get_pending_review_store() -> PendingReviewStore:
    return _STORE
