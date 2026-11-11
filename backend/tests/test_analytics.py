import pytest

from datetime import date
from types import SimpleNamespace
from unittest.mock import call, patch

from fastapi.testclient import TestClient

from api import app
from auth import get_current_user


client = TestClient(app)


def fake_current_user():
    return {"user": SimpleNamespace(id="test-user"), "token": "fake-token"}


@pytest.fixture
def authenticated_user():
    app.dependency_overrides[get_current_user] = fake_current_user
    yield
    app.dependency_overrides.clear()


def test_get_statistics_reads_all_batches(authenticated_user):
    first_batch = [
        {
            "pnl": 1,
            "result": 1,
            "entry_datetime": "2026-08-12T10:00:00",
        }
    ] * 1000

    second_batch = [
        {
            "pnl": -1,
            "result": -1,
            "entry_datetime": "2026-08-13T10:00:00",
        }
    ]

    with patch(
        "routes.analytics.load_trade_metrics_batch_from_supabase",
        side_effect=[first_batch, second_batch],
    ) as mock_load:
        response = client.get("/statistics?account_id=7")

    assert response.status_code == 200
    assert response.json()["total_trades"] == 1001
    assert response.json()["winning_trades"] == 1000
    assert response.json()["total_pnl"] == 999
    assert response.json()["total_r"] == 999
    assert response.json()["trades_with_r"] == 1001

    assert mock_load.call_args_list == [
        call(
            "test-user",
            "fake-token",
            7,
            offset=0,
            batch_size=1000,
            date_from=None,
            date_to=None,
        ),
        call(
            "test-user",
            "fake-token",
            7,
            offset=1000,
            batch_size=1000,
            date_from=None,
            date_to=None,
        ),
    ]


def test_get_statistics_passes_date_filters(authenticated_user):
    with patch(
        "routes.analytics.load_trade_metrics_batch_from_supabase",
        return_value=[],
    ) as mock_load:
        response = client.get(
            "/statistics?account_id=7"
            "&date_from=2026-08-01"
            "&date_to=2026-08-31"
        )

    assert response.status_code == 200

    mock_load.assert_called_once_with(
        "test-user",
        "fake-token",
        7,
        offset=0,
        batch_size=1000,
        date_from=date(2026, 8, 1),
        date_to=date(2026, 8, 31),
    )


def test_get_statistics_rejects_reversed_date_range(authenticated_user):
    with patch(
        "routes.analytics.load_trade_metrics_batch_from_supabase"
    ) as mock_load:
        response = client.get(
            "/statistics?account_id=7"
            "&date_from=2026-08-31"
            "&date_to=2026-08-01"
        )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "date_from cannot be after date_to"
    }

    mock_load.assert_not_called()


def test_get_calendar_reads_all_batches(authenticated_user):
    first_batch = [
        {
            "pnl": 1,
            "result": 1,
            "entry_datetime": "2026-09-12T10:00:00",
        }
    ] * 1000

    second_batch = [
        {
            "pnl": -1,
            "result": -1,
            "entry_datetime": "2026-09-13T10:00:00",
        }
    ]

    with patch(
        "routes.analytics.load_calendar_metrics_batch_from_supabase",
        side_effect=[first_batch, second_batch],
    ) as mock_load:
        response = client.get(
            "/calendar?account_id=7&year=2026&month=9"
        )

    assert response.status_code == 200
    assert response.json()["total_trades"] == 1001
    assert response.json()["trading_days"] == 2
    assert response.json()["total_pnl"] == 999
    assert response.json()["total_r"] == 999

    assert mock_load.call_args_list == [
        call(
            "test-user",
            "fake-token",
            7,
            date(2026, 9, 1),
            date(2026, 10, 1),
            offset=0,
            batch_size=1000,
        ),
        call(
            "test-user",
            "fake-token",
            7,
            date(2026, 9, 1),
            date(2026, 10, 1),
            offset=1000,
            batch_size=1000,
        ),
    ]


def test_get_calendar_handles_december(authenticated_user):
    with patch(
        "routes.analytics.load_calendar_metrics_batch_from_supabase",
        return_value=[],
    ) as mock_load:
        response = client.get(
            "/calendar?account_id=7&year=2026&month=12"
        )

    assert response.status_code == 200

    mock_load.assert_called_once_with(
        "test-user",
        "fake-token",
        7,
        date(2026, 12, 1),
        date(2027, 1, 1),
        offset=0,
        batch_size=1000,
    )


@pytest.mark.parametrize(
    "query_string",
    [
        "year=0&month=9",
        "year=9999&month=9",
        "year=2026&month=0",
        "year=2026&month=13",
    ],
)
def test_get_calendar_rejects_invalid_year_or_month(
    authenticated_user,
    query_string,
):
    response = client.get(
        f"/calendar?account_id=7&{query_string}"
    )

    assert response.status_code == 422


def test_statistics_without_auth_returns_401():
    response = client.get("/statistics?account_id=7")

    assert response.status_code == 401


def test_calendar_without_auth_returns_401():
    response = client.get(
        "/calendar?account_id=7&year=2026&month=9"
    )

    assert response.status_code == 401
