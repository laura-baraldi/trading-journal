from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api import app
from auth import get_current_user
from database import DatabaseError, ResourceNotFoundError


client = TestClient(app)


def fake_current_user():
    return {"user": SimpleNamespace(id="test-user"), "token": "fake-token"}


@pytest.fixture
def authenticated_user():
    app.dependency_overrides[get_current_user] = fake_current_user
    yield
    app.dependency_overrides.clear()


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Trading Journal API"}


def test_demo_login():
    fake_session = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
    }

    with patch(
        "api.get_demo_session",
        return_value=fake_session,
    ) as mock_demo_session:
        response = client.post("/demo-login")

    assert response.status_code == 200
    assert response.json() == fake_session
    mock_demo_session.assert_called_once_with()


def test_database_error_returns_503(authenticated_user):
    with patch(
        "routes.trades.load_trades_from_supabase",
        side_effect=DatabaseError("Database request failed"),
    ):
        response = client.get("/trades")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database service unavailable"
    }


def test_resource_not_found_returns_404(authenticated_user):
    with patch(
        "routes.trades.delete_trade_from_supabase",
        side_effect=ResourceNotFoundError("Trade not found"),
    ):
        response = client.delete("/trades/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Trade not found"
    }
