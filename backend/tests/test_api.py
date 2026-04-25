from fastapi import HTTPException

from app.api.v1.health import healthz
from app.api.v1.reviews import list_pending_reviews
from app.api.v1.runs import resume_run, run_ticket
from app.api.v1.tickets import list_tickets
from app.main import app
from app.schemas.graph import SubmitReviewDecisionRequest
from app.services.pending_review_store import get_pending_review_store


def setup_function() -> None:
    get_pending_review_store().clear()


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
    assert "/api/v1/reviews/pending" in route_paths


def test_run_ticket_returns_waiting_review_for_risky_ticket() -> None:
    payload = run_ticket("ticket-1001")

    assert payload.ticket_id == "ticket-1001"
    assert payload.status == "waiting_review"
    assert payload.risk_assessment is not None
    assert payload.risk_assessment.review_required is True
    assert "billing_sensitive" in payload.risk_assessment.risk_flags
    assert payload.pending_review is not None
    assert payload.pending_review.thread_id == payload.thread_id
    assert payload.thread_id.startswith("ticket-ticket-1001-")
    assert payload.pending_review.retrieved_chunks


def test_run_ticket_returns_final_response_for_low_risk_ticket() -> None:
    payload = run_ticket("ticket-1003")

    assert payload.ticket_id == "ticket-1003"
    assert payload.status == "done"
    assert payload.final_response is not None
    assert payload.final_response.disposition == "auto_finalized"
    assert payload.pending_review is None


def test_pending_review_endpoint_lists_waiting_items() -> None:
    pending = run_ticket("ticket-1001")

    payload = list_pending_reviews()
    assert len(payload) == 1
    assert payload[0].thread_id == pending.thread_id


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
    assert list_pending_reviews() == []


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


def test_run_ticket_returns_404_for_unknown_ticket() -> None:
    try:
        run_ticket("does-not-exist")
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Ticket not found"
    else:
        raise AssertionError("Expected HTTPException for missing ticket")
