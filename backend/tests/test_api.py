from fastapi import HTTPException

from app.api.v1.health import healthz
from app.api.v1.reviews import list_pending_reviews
from app.api.v1.runs import (
    read_run_state,
    read_run_timeline,
    read_run_trace,
    resume_run,
    run_ticket,
)
from app.api.v1.tickets import list_tickets
from app.main import app
from app.schemas.graph import SubmitReviewDecisionRequest
from app.services.action_ledger import get_action_ledger
from app.services.pending_review_store import get_pending_review_store
from app.services.run_event_store import get_run_event_store
from app.services.run_trace_store import get_run_trace_store


def setup_function() -> None:
    get_action_ledger().clear()
    get_pending_review_store().clear()
    get_run_event_store().clear()
    get_run_trace_store().clear()


def test_healthz_returns_ok() -> None:
    assert healthz() == {"status": "ok"}


def test_list_tickets_returns_mock_data() -> None:
    payload = list_tickets()

    assert len(payload) == 3
    assert payload[0].id == "ticket-1001"
    assert payload[0].priority == "high"


def test_app_registers_expected_routes() -> None:
    route_paths = {route.path for route in app.routes}

    assert "/healthz" in route_paths
    assert "/api/v1/tickets" in route_paths
    assert "/api/v1/tickets/{ticket_id}/run" in route_paths
    assert "/api/v1/runs/{thread_id}/resume" in route_paths
    assert "/api/v1/runs/{thread_id}/state" in route_paths
    assert "/api/v1/runs/{thread_id}/timeline" in route_paths
    assert "/api/v1/runs/{thread_id}/trace" in route_paths
    assert "/api/v1/reviews/pending" in route_paths


def test_run_ticket_returns_waiting_review_for_risky_ticket() -> None:
    payload = run_ticket("ticket-1001")

    assert payload.ticket_id == "ticket-1001"
    assert payload.status == "waiting_review"
    assert payload.risk_assessment is not None
    assert payload.risk_assessment.review_required is True
    assert payload.policy_assessment is not None
    assert "billing_sensitive" in payload.risk_assessment.risk_flags
    assert "high_impact_action_requires_review" in payload.policy_assessment.failed_policy_ids
    assert payload.pending_review is not None
    assert payload.pending_review.thread_id == payload.thread_id
    assert payload.thread_id.startswith("ticket-ticket-1001-")
    assert payload.pending_review.retrieved_chunks
    assert {action.action_type for action in payload.proposed_actions} == {
        "send_customer_reply",
        "create_refund_case",
    }


def test_run_ticket_returns_waiting_review_for_low_risk_customer_send() -> None:
    payload = run_ticket("ticket-1003")

    assert payload.ticket_id == "ticket-1003"
    assert payload.status == "waiting_review"
    assert payload.final_response is None
    assert payload.risk_assessment is not None
    assert payload.risk_assessment.review_required is True
    assert payload.policy_assessment is not None
    assert payload.risk_assessment.risk_flags == ["high_impact_action_requires_review"]
    assert payload.policy_assessment.failed_policy_ids == ["high_impact_action_requires_review"]
    assert payload.pending_review is not None
    assert payload.pending_review.policy_assessment is not None
    assert payload.proposed_actions[0].action_type == "send_customer_reply"
    assert payload.proposed_actions[0].status == "proposed"
    assert payload.proposed_actions[0].requires_review is True


def test_pending_review_endpoint_lists_waiting_items() -> None:
    pending = run_ticket("ticket-1001")

    payload = list_pending_reviews()
    assert len(payload) == 1
    assert payload[0].thread_id == pending.thread_id


def test_run_state_endpoint_reads_waiting_review_state() -> None:
    pending = run_ticket("ticket-1001")

    payload = read_run_state(pending.thread_id)

    assert payload.thread_id == pending.thread_id
    assert payload.status == "waiting_review"
    assert payload.current_node == "human_review_interrupt"
    assert payload.pending_review is not None
    assert payload.risk_assessment is not None
    assert payload.policy_assessment is not None


def test_run_timeline_endpoint_reads_major_events() -> None:
    completed = run_ticket("ticket-1001")

    payload = read_run_timeline(completed.thread_id)

    assert payload.thread_id == completed.thread_id
    assert [event.event_type for event in payload.events] == [
        "run_started",
        "classify_completed",
        "retrieve_completed",
        "draft_completed",
        "risk_gate_completed",
        "interrupt_created",
    ]
    assert payload.events[-1].status == "waiting_review"


def test_run_trace_endpoint_reads_approval_gated_interrupt_spans() -> None:
    pending = run_ticket("ticket-1003")

    payload = read_run_trace(pending.thread_id)
    by_node = {event.node_name: event for event in payload.events}

    assert payload.thread_id == pending.thread_id
    assert [event.node_name for event in payload.events] == [
        "load_ticket_context",
        "classify_ticket",
        "retrieve_knowledge",
        "draft_reply",
        "propose_actions",
        "risk_gate",
        "human_review_interrupt",
    ]
    assert {event.status for event in payload.events[:-1]} == {"completed"}
    assert payload.events[-1].status == "interrupted"
    assert all(event.started_at <= event.ended_at for event in payload.events)
    assert all(event.duration_ms >= 0 for event in payload.events)
    assert "finalize_reply" not in by_node
    assert by_node["risk_gate"].attributes["failed_policy_ids"] == [
        "high_impact_action_requires_review"
    ]
    assert by_node["human_review_interrupt"].attributes["proposed_action_types"] == [
        "send_customer_reply"
    ]


def test_run_trace_endpoint_records_approve_resume_and_executed_actions() -> None:
    pending = run_ticket("ticket-1003")

    resume_run(
        pending.thread_id,
        SubmitReviewDecisionRequest(
            decision="approve",
            reviewer_note="send approved",
        ),
    )

    payload = read_run_trace(pending.thread_id)
    final_span = payload.events[-1]

    assert [event.node_name for event in payload.events[-3:]] == [
        "human_review_interrupt",
        "apply_review_decision",
        "finalize_reply",
    ]
    assert final_span.node_name == "finalize_reply"
    assert final_span.status == "completed"
    assert final_span.attributes["final_disposition"] == "approved"
    assert "send_customer_reply" in final_span.attributes["executed_action_types"]


def test_run_trace_endpoint_records_reject_manual_takeover_actions() -> None:
    pending = run_ticket("ticket-1001")

    resume_run(
        pending.thread_id,
        SubmitReviewDecisionRequest(
            decision="reject",
            reviewer_note="manual handling required",
        ),
    )

    payload = read_run_trace(pending.thread_id)
    risk_span = next(event for event in payload.events if event.node_name == "risk_gate")
    manual_span = payload.events[-1]

    assert "billing_sensitive" in risk_span.attributes["failed_policy_ids"]
    assert "sensitive_request" in risk_span.attributes["failed_policy_ids"]
    assert risk_span.attributes["proposed_action_types"] == [
        "send_customer_reply",
        "create_refund_case",
    ]
    assert manual_span.node_name == "manual_takeover"
    assert manual_span.status == "completed"
    assert manual_span.attributes["workflow_status"] == "manual_takeover"
    assert set(manual_span.attributes["action_statuses"].values()) >= {"rejected"}


def test_resume_run_approves_pending_review() -> None:
    pending = run_ticket("ticket-1001")

    payload = resume_run(
        pending.thread_id,
        SubmitReviewDecisionRequest(
            decision="approve",
            reviewer_note="evidence is sufficient",
        ),
    )

    assert payload.status == "done"
    assert payload.final_response is not None
    assert payload.final_response.disposition == "approved"
    assert payload.pending_review is None
    assert {action.status for action in payload.proposed_actions} == {"executed"}
    assert len(payload.executed_actions) == len(payload.proposed_actions)
    assert list_pending_reviews() == []

    timeline = read_run_timeline(pending.thread_id)
    assert [event.event_type for event in timeline.events[-3:]] == [
        "review_submitted",
        "run_resumed",
        "run_completed",
    ]


def test_resume_run_rejects_to_manual_takeover() -> None:
    pending = run_ticket("ticket-1001")

    payload = resume_run(
        pending.thread_id,
        SubmitReviewDecisionRequest(
            decision="reject",
            reviewer_note="manual handling required",
        ),
    )

    assert payload.status == "manual_takeover"
    assert payload.final_response is None
    assert payload.proposed_actions
    external_actions = [
        action
        for action in payload.proposed_actions
        if action.action_type != "add_internal_note"
    ]
    assert {action.status for action in external_actions} == {"rejected"}
    assert [
        action.status
        for action in payload.proposed_actions
        if action.action_type == "add_internal_note"
    ] == ["executed"]


def test_low_risk_send_action_executes_once_after_approval() -> None:
    pending = run_ticket("ticket-1003")
    action = pending.proposed_actions[0]

    assert action.action_type == "send_customer_reply"
    assert action.status == "proposed"

    payload = resume_run(
        pending.thread_id,
        SubmitReviewDecisionRequest(
            decision="approve",
            reviewer_note="send approved",
        ),
    )

    send_actions = [
        action
        for action in payload.proposed_actions
        if action.action_type == "send_customer_reply"
    ]
    assert len(send_actions) == 1
    assert send_actions[0].status == "executed"
    assert payload.executed_actions

    executed_again = get_action_ledger().execute_once(send_actions[0].action_id)
    actions_after_retry = get_action_ledger().list_by_thread_id(pending.thread_id)
    executed_send_actions = [
        action
        for action in actions_after_retry
        if action.action_type == "send_customer_reply" and action.status == "executed"
    ]
    assert executed_again.status == "executed"
    assert len(executed_send_actions) == 1


def test_resume_run_returns_404_for_unknown_thread() -> None:
    try:
        resume_run(
            "ticket-does-not-exist",
            SubmitReviewDecisionRequest(decision="approve"),
        )
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Pending review not found"
    else:
        raise AssertionError("Expected HTTPException for missing pending review")


def test_read_run_state_returns_404_for_unknown_thread() -> None:
    try:
        read_run_state("ticket-does-not-exist")
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Run state not found"
    else:
        raise AssertionError("Expected HTTPException for missing run state")


def test_read_run_timeline_returns_404_for_unknown_thread() -> None:
    try:
        read_run_timeline("ticket-does-not-exist")
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Run timeline not found"
    else:
        raise AssertionError("Expected HTTPException for missing run timeline")


def test_read_run_trace_returns_404_for_unknown_thread() -> None:
    try:
        read_run_trace("ticket-does-not-exist")
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Run trace not found"
    else:
        raise AssertionError("Expected HTTPException for missing run trace")


def test_run_ticket_returns_404_for_unknown_ticket() -> None:
    try:
        run_ticket("does-not-exist")
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Ticket not found"
    else:
        raise AssertionError("Expected HTTPException for missing ticket")
