from app.api.v1.runs import read_run_state, read_run_timeline, resume_run, run_ticket
from app.schemas.graph import SubmitReviewDecisionRequest
from app.services.pending_review_store import get_pending_review_store
from app.services.run_event_store import get_run_event_store


def setup_function() -> None:
    get_pending_review_store().clear()
    get_run_event_store().clear()


def test_low_risk_ticket_waits_for_customer_send_approval() -> None:
    response = run_ticket("ticket-1003")

    state = read_run_state(response.thread_id)
    timeline = read_run_timeline(response.thread_id)

    assert state.status == "waiting_review"
    assert state.final_response is None
    assert state.risk_assessment is not None
    assert state.risk_assessment.review_required is True
    assert state.policy_assessment is not None
    assert state.policy_assessment.failed_policy_ids == [
        "high_impact_action_requires_review"
    ]
    assert state.pending_review is not None
    assert state.pending_review.policy_assessment is not None
    assert state.pending_review.proposed_actions[0].action_type == "send_customer_reply"
    assert state.pending_review.proposed_actions[0].requires_review is True
    assert [event.event_type for event in timeline.events] == [
        "run_started",
        "classify_completed",
        "retrieve_completed",
        "draft_completed",
        "risk_gate_completed",
        "interrupt_created",
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
