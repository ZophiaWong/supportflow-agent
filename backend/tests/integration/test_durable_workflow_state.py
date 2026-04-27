from app.api.v1.reviews import list_pending_reviews
from app.api.v1.runs import read_run_state, read_run_timeline, resume_run, run_ticket
from app.graph.builder import get_support_graph
from app.schemas.graph import SubmitReviewDecisionRequest


def test_pending_review_resumes_after_fresh_graph_construction() -> None:
    pending = run_ticket("ticket-1001")

    get_support_graph.cache_clear()

    pending_reviews = list_pending_reviews()
    waiting_state = read_run_state(pending.thread_id)
    waiting_timeline = read_run_timeline(pending.thread_id)

    assert [item.thread_id for item in pending_reviews] == [pending.thread_id]
    assert waiting_state.status == "waiting_review"
    assert waiting_state.pending_review is not None
    assert waiting_timeline.events[-1].event_type == "interrupt_created"

    resumed = resume_run(
        pending.thread_id,
        SubmitReviewDecisionRequest(
            decision="approve",
            reviewer_note="durable review state survived restart",
        ),
    )

    get_support_graph.cache_clear()

    done_state = read_run_state(pending.thread_id)
    done_timeline = read_run_timeline(pending.thread_id)

    assert resumed.status == "done"
    assert resumed.final_response is not None
    assert resumed.final_response.disposition == "approved"
    assert done_state.status == "done"
    assert done_state.final_response is not None
    assert done_timeline.events[-1].event_type == "run_completed"
    assert list_pending_reviews() == []
