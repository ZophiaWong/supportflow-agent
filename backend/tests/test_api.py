from app.api.v1.health import healthz
from app.api.v1.tickets import list_tickets
from app.main import app


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
