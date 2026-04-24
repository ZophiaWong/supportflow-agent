from fastapi.testclient import TestClient

from app.api.v1.health import healthz
from app.api.v1.tickets import list_tickets
from app.main import app

client = TestClient(app)


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


def test_run_ticket_returns_workflow_payload() -> None:
    response = client.post("/api/v1/tickets/ticket-1001/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticket_id"] == "ticket-1001"
    assert payload["status"] == "done"
    assert payload["classification"]["category"] == "billing"
    assert payload["retrieved_chunks"]
    assert payload["draft"]["citations"] == ["refund_policy"]


def test_run_ticket_returns_404_for_unknown_ticket() -> None:
    response = client.post("/api/v1/tickets/does-not-exist/run")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}
