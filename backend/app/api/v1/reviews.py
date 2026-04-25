from fastapi import APIRouter

from app.schemas.graph import PendingReviewItem
from app.services.pending_review_store import get_pending_review_store

router = APIRouter(prefix="/api/v1", tags=["reviews"])


@router.get("/reviews/pending", response_model=list[PendingReviewItem])
def list_pending_reviews() -> list[PendingReviewItem]:
    return get_pending_review_store().list_items()
