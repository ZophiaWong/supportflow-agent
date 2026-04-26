from app.api.v1.runs import read_run_state, read_run_timeline, resume_run, run_ticket
from app.schemas.graph import SubmitReviewDecisionRequest
from app.services.pending_review_store import get_pending_review_store
from app.services.run_event_store import get_run_event_store


def setup_function() -> None:
    get_pending_review_store().clear()
    get_run_event_store().clear()


def test_low_risk_ticket_creates_final_state_and_timeline() -> None:
    response = run_ticket("ticket-1003")

    state = read_run_state(response.thread_id)
    timeline = read_run_timeline(response.thread_id)

    assert state.status == "done"
    assert state.final_response is not None
    assert state.final_response.disposition == "auto_finalized"
    assert [event.event_type for event in timeline.events] == [
        "run_started",
        "classify_completed",
        "retrieve_completed",
        "draft_completed",
        "risk_gate_completed",
        "run_completed",
    ]


def test_high_risk_ticket_waits_for_review_and_resume_updates_timeline() -> None:
    response = run_ticket("ticket-1001")

    waiting_state = read_run_state(response.thread_id)
    waiting_timeline = read_run_timeline(response.thread_id)

    assert waiting_state.status == "waiting_review"
    assert waiting_state.pending_review is not None
    assert waiting_state.current_node == "human_review_interrupt"
    assert waiting_timeline.events[-1].event_type == "interrupt_created"
    assert waiting_timeline.events[-1].status == "waiting_review"

    resumed = resume_run(
        response.thread_id,
        SubmitReviewDecisionRequest(
            decision="edit",
            reviewer_note="tighten wording",
            edited_answer="Custom approved answer.",
        ),
    )

    done_state = read_run_state(response.thread_id)
    done_timeline = read_run_timeline(response.thread_id)

    assert resumed.status == "done"
    assert done_state.status == "done"
    assert done_state.final_response is not None
    assert done_state.final_response.answer == "Custom approved answer."
    assert [event.event_type for event in done_timeline.events[-3:]] == [
        "review_submitted",
        "run_resumed",
        "run_completed",
    ]
