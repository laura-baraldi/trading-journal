import pytest

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from database.client import ResourceNotFoundError
from database.trades import (
    delete_trade_from_supabase,
    load_calendar_metrics_batch_from_supabase,
    load_trade_metrics_batch_from_supabase,
    load_trades_from_supabase,
    save_trade_to_supabase,
    save_trades_to_supabase,
    update_trade_in_supabase,
)


def make_mock_query(fake_response):
    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.gte.return_value = mock_query
    mock_query.lt.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.insert.return_value = mock_query
    mock_query.update.return_value = mock_query
    mock_query.delete.return_value = mock_query
    mock_query.execute.return_value = fake_response
    return mock_query


def make_mock_client(mock_query):
    mock_client = MagicMock()
    mock_client.table.return_value = mock_query
    return mock_client


def make_saved_trade(
    trade_id=1,
    account_id=7,
    symbol="EURUSD",
    direction="long",
    entry="1.15",
    stop="1.14",
    exit_price="1.17",
    result="2",
    pnl="400",
    entry_datetime="2026-08-12T10:00:00",
    exit_datetime="2026-08-12T11:00:00",
):
    return {
        "id": trade_id,
        "account_id": account_id,
        "user_id": "user-123",
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "stop": stop,
        "exit": exit_price,
        "result": result,
        "pnl": pnl,
        "entry_datetime": entry_datetime,
        "exit_datetime": exit_datetime,
    }


def test_load_trades_from_supabase():
    fake_trade = make_saved_trade()

    fake_response = SimpleNamespace(data=[fake_trade], count=1)
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ) as mock_get_client:
        trades, total = load_trades_from_supabase(
            "user-123",
            "fake-token",
        )

    mock_get_client.assert_called_once_with("fake-token")
    mock_client.table.assert_called_once_with("trades")
    mock_query.select.assert_called_once_with("*", count="exact")
    mock_query.range.assert_called_once_with(0, 19)

    assert trades == [
        {
            "id": 1,
            "account_id": 7,
            "symbol": "EURUSD",
            "direction": "long",
            "entry": 1.15,
            "stop": 1.14,
            "exit": 1.17,
            "result": 2.0,
            "pnl": 400.0,
            "entry_datetime": "2026-08-12T10:00:00",
            "exit_datetime": "2026-08-12T11:00:00",
        }
    ]
    assert "user_id" not in trades[0]
    assert isinstance(trades[0], dict)
    assert total == 1


def test_load_trade_without_stop_or_result():
    fake_trade = make_saved_trade(stop=None, result=None)

    fake_response = SimpleNamespace(data=[fake_trade], count=1)
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ):
        trades, total = load_trades_from_supabase(
            "user-123",
            "fake-token",
        )

    assert trades[0]["stop"] is None
    assert trades[0]["result"] is None
    assert trades[0]["entry"] == 1.15
    assert trades[0]["pnl"] == 400.0
    assert "user_id" not in trades[0]
    assert total == 1


@pytest.mark.parametrize(
    "page, page_size, expected_start, expected_end",
    [
        (1, 20, 0, 19),
        (2, 20, 20, 39),
        (3, 10, 20, 29),
    ],
)
def test_load_trades_applies_pagination(
    page,
    page_size,
    expected_start,
    expected_end,
):
    fake_response = SimpleNamespace(data=[], count=45)
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ):
        trades, total = load_trades_from_supabase(
            "user-123",
            "fake-token",
            page=page,
            page_size=page_size,
        )

    mock_query.range.assert_called_once_with(
        expected_start,
        expected_end,
    )
    assert trades == []
    assert total == 45


def test_load_trades_applies_date_filters():
    fake_response = SimpleNamespace(data=[], count=0)
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ):
        load_trades_from_supabase(
            "user-123",
            "fake-token",
            date_from=date(2026, 8, 1),
            date_to=date(2026, 8, 31),
        )

    mock_query.gte.assert_called_once_with(
        "entry_datetime",
        "2026-08-01",
    )
    mock_query.lt.assert_called_once_with(
        "entry_datetime",
        "2026-09-01",
    )


def test_load_trades_from_supabase_filters_by_account():
    fake_response = SimpleNamespace(
        data=[make_saved_trade(account_id=7)],
        count=1,
    )

    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ):
        load_trades_from_supabase(
            "user-123",
            "fake-token",
            7,
        )

    mock_query.eq.assert_any_call("user_id", "user-123")
    mock_query.eq.assert_any_call("account_id", 7)


def test_load_trade_metrics_batch_from_supabase():
    fake_metrics = [
        {
            "pnl": "100",
            "result": "2",
            "entry_datetime": "2026-08-12T10:00:00",
        }
    ]

    fake_response = SimpleNamespace(data=fake_metrics)
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ):
        metrics = load_trade_metrics_batch_from_supabase(
            "user-123",
            "fake-token",
            account_id=7,
            offset=1000,
            batch_size=500,
        )

    mock_query.select.assert_called_once_with(
        "pnl,result,entry_datetime"
    )
    mock_query.eq.assert_any_call("user_id", "user-123")
    mock_query.eq.assert_any_call("account_id", 7)
    mock_query.order.assert_called_once_with(
        "entry_datetime",
        desc=False,
        nullsfirst=False,
    )
    mock_query.range.assert_called_once_with(1000, 1499)
    assert metrics == fake_metrics


def test_load_trade_metrics_batch_applies_date_filters():
    fake_response = SimpleNamespace(data=[])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ):
        load_trade_metrics_batch_from_supabase(
            "user-123",
            "fake-token",
            account_id=7,
            date_from=date(2026, 8, 1),
            date_to=date(2026, 8, 31),
        )

    mock_query.gte.assert_called_once_with(
        "entry_datetime",
        "2026-08-01",
    )
    mock_query.lt.assert_called_once_with(
        "entry_datetime",
        "2026-09-01",
    )


def test_load_calendar_metrics_batch_from_supabase():
    fake_metrics = [
        {
            "pnl": "100",
            "result": "2",
            "entry_datetime": "2026-09-12T10:00:00",
        }
    ]

    fake_response = SimpleNamespace(data=fake_metrics)
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ):
        metrics = load_calendar_metrics_batch_from_supabase(
            "user-123",
            "fake-token",
            account_id=7,
            month_start=date(2026, 9, 1),
            next_month_start=date(2026, 10, 1),
            offset=1000,
            batch_size=500,
        )

    mock_query.select.assert_called_once_with(
        "pnl,result,entry_datetime"
    )
    mock_query.eq.assert_any_call("user_id", "user-123")
    mock_query.eq.assert_any_call("account_id", 7)
    mock_query.gte.assert_called_once_with(
        "entry_datetime",
        "2026-09-01",
    )
    mock_query.lt.assert_called_once_with(
        "entry_datetime",
        "2026-10-01",
    )
    mock_query.order.assert_called_once_with(
        "entry_datetime",
        desc=False,
        nullsfirst=False,
    )
    mock_query.range.assert_called_once_with(1000, 1499)

    assert metrics == fake_metrics


@pytest.mark.parametrize(
    "entry_datetime, exit_datetime, expected_entry_datetime, expected_exit_datetime",
    [
        (
            datetime(2026, 8, 12, 10, 0),
            datetime(2026, 8, 12, 11, 0),
            "2026-08-12T10:00:00",
            "2026-08-12T11:00:00",
        ),
        (None, None, None, None),
    ],
)
def test_save_trade_to_supabase(
    entry_datetime,
    exit_datetime,
    expected_entry_datetime,
    expected_exit_datetime,
):
    saved_trade_record = make_saved_trade(
        trade_id=10,
        account_id=1,
        entry_datetime=expected_entry_datetime,
        exit_datetime=expected_exit_datetime,
    )

    fake_response = SimpleNamespace(data=[saved_trade_record])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    trade = {
        "account_id": 1,
        "symbol": "EURUSD",
        "direction": "long",
        "entry": 1.15,
        "stop": 1.14,
        "exit": 1.17,
        "result": 2,
        "pnl": 400,
        "entry_datetime": entry_datetime,
        "exit_datetime": exit_datetime,
    }

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ) as mock_get_client:
        saved_trade = save_trade_to_supabase(
            trade,
            "user-123",
            "fake-token",
        )

    mock_get_client.assert_called_once_with("fake-token")

    expected_new_trade = {
        "account_id": 1,
        "symbol": "EURUSD",
        "direction": "long",
        "entry": 1.15,
        "stop": 1.14,
        "exit": 1.17,
        "result": 2,
        "pnl": 400,
        "entry_datetime": expected_entry_datetime,
        "exit_datetime": expected_exit_datetime,
        "user_id": "user-123",
    }

    mock_query.insert.assert_called_once_with(expected_new_trade)

    assert saved_trade == {
        "id": 10,
        "account_id": 1,
        "symbol": "EURUSD",
        "direction": "long",
        "entry": 1.15,
        "stop": 1.14,
        "exit": 1.17,
        "result": 2.0,
        "pnl": 400.0,
        "entry_datetime": expected_entry_datetime,
        "exit_datetime": expected_exit_datetime,
    }
    assert "user_id" not in saved_trade


def test_save_trade_without_stop_or_result():
    saved_trade_record = make_saved_trade(
        trade_id=10,
        account_id=1,
        stop=None,
        result=None,
    )

    fake_response = SimpleNamespace(data=[saved_trade_record])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    trade = {
        "account_id": 1,
        "symbol": "EURUSD",
        "direction": "long",
        "entry": 1.15,
        "stop": None,
        "exit": 1.17,
        "result": None,
        "pnl": 400,
        "entry_datetime": datetime(2026, 8, 12, 10, 0),
        "exit_datetime": datetime(2026, 8, 12, 11, 0),
    }

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ):
        saved_trade = save_trade_to_supabase(
            trade,
            "user-123",
            "fake-token",
        )

    assert saved_trade["stop"] is None
    assert saved_trade["result"] is None
    assert "user_id" not in saved_trade


def test_save_trades_to_supabase():
    saved_trade_1 = make_saved_trade(
        trade_id=10,
        account_id=7,
        symbol="EURUSD",
        direction="long",
        entry="1.15",
        stop="1.14",
        exit_price="1.17",
        result="2",
        pnl="200",
        entry_datetime="2026-08-30T10:00:00",
        exit_datetime="2026-08-30T11:00:00",
    )

    saved_trade_2 = make_saved_trade(
        trade_id=11,
        account_id=7,
        symbol="XAUUSD",
        direction="short",
        entry="2350",
        stop=None,
        exit_price="2340",
        result=None,
        pnl="300",
        entry_datetime="2026-08-30T12:00:00",
        exit_datetime="2026-08-30T13:00:00",
    )

    fake_response = SimpleNamespace(
        data=[saved_trade_1, saved_trade_2]
    )

    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    trades = [
        {
            "account_id": 7,
            "symbol": "EURUSD",
            "direction": "long",
            "entry": 1.15,
            "stop": 1.14,
            "exit": 1.17,
            "result": 2.0,
            "pnl": 200.0,
            "entry_datetime": datetime(2026, 8, 30, 10, 0),
            "exit_datetime": datetime(2026, 8, 30, 11, 0),
        },
        {
            "account_id": 7,
            "symbol": "XAUUSD",
            "direction": "short",
            "entry": 2350.0,
            "stop": None,
            "exit": 2340.0,
            "result": None,
            "pnl": 300.0,
            "entry_datetime": datetime(2026, 8, 30, 12, 0),
            "exit_datetime": datetime(2026, 8, 30, 13, 0),
        },
    ]

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ) as mock_get_client:
        result = save_trades_to_supabase(
            trades,
            "user-123",
            "fake-token",
        )

    mock_get_client.assert_called_once_with("fake-token")
    mock_client.table.assert_called_once_with("trades")

    mock_query.insert.assert_called_once_with(
        [
            {
                "account_id": 7,
                "symbol": "EURUSD",
                "direction": "long",
                "entry": 1.15,
                "stop": 1.14,
                "exit": 1.17,
                "result": 2.0,
                "pnl": 200.0,
                "entry_datetime": "2026-08-30T10:00:00",
                "exit_datetime": "2026-08-30T11:00:00",
                "user_id": "user-123",
            },
            {
                "account_id": 7,
                "symbol": "XAUUSD",
                "direction": "short",
                "entry": 2350.0,
                "stop": None,
                "exit": 2340.0,
                "result": None,
                "pnl": 300.0,
                "entry_datetime": "2026-08-30T12:00:00",
                "exit_datetime": "2026-08-30T13:00:00",
                "user_id": "user-123",
            },
        ]
    )

    assert result == [
        {
            "id": 10,
            "account_id": 7,
            "symbol": "EURUSD",
            "direction": "long",
            "entry": 1.15,
            "stop": 1.14,
            "exit": 1.17,
            "result": 2.0,
            "pnl": 200.0,
            "entry_datetime": "2026-08-30T10:00:00",
            "exit_datetime": "2026-08-30T11:00:00",
        },
        {
            "id": 11,
            "account_id": 7,
            "symbol": "XAUUSD",
            "direction": "short",
            "entry": 2350.0,
            "stop": None,
            "exit": 2340.0,
            "result": None,
            "pnl": 300.0,
            "entry_datetime": "2026-08-30T12:00:00",
            "exit_datetime": "2026-08-30T13:00:00",
        },
    ]

    assert all("user_id" not in trade for trade in result)


def test_delete_trade_from_supabase():
    fake_response = SimpleNamespace(data=[{"id": 5}])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ) as mock_get_client:
        response = delete_trade_from_supabase(
            5,
            "user-123",
            "fake-token",
        )

    mock_get_client.assert_called_once_with("fake-token")
    mock_query.delete.assert_called_once()
    mock_query.eq.assert_any_call("id", 5)
    mock_query.eq.assert_any_call("user_id", "user-123")
    assert response == fake_response


def test_delete_trade_not_found():
    fake_response = SimpleNamespace(data=[])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ):
        with pytest.raises(ResourceNotFoundError, match="Trade not found"):
            delete_trade_from_supabase(
                999,
                "user-123",
                "fake-token",
            )


@pytest.mark.parametrize(
    "entry_datetime, exit_datetime, expected_entry_datetime, expected_exit_datetime",
    [
        (
            datetime(2026, 8, 12, 12, 0),
            datetime(2026, 8, 12, 13, 0),
            "2026-08-12T12:00:00",
            "2026-08-12T13:00:00",
        ),
        (None, None, None, None),
    ],
)
def test_update_trade_in_supabase(
    entry_datetime,
    exit_datetime,
    expected_entry_datetime,
    expected_exit_datetime,
):
    updated_trade_record = make_saved_trade(
        trade_id=5,
        account_id=7,
        symbol="GBPUSD",
        direction="short",
        entry="1.30",
        stop="1.31",
        exit_price="1.28",
        result="2",
        pnl="400",
        entry_datetime=expected_entry_datetime,
        exit_datetime=expected_exit_datetime,
    )

    fake_response = SimpleNamespace(data=[updated_trade_record])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    updated_trade = {
        "symbol": "GBPUSD",
        "direction": "short",
        "entry": 1.30,
        "stop": 1.31,
        "exit": 1.28,
        "result": 2,
        "pnl": 400,
        "entry_datetime": entry_datetime,
        "exit_datetime": exit_datetime,
    }

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ) as mock_get_client:
        response = update_trade_in_supabase(
            5,
            updated_trade,
            "user-123",
            "fake-token",
        )

    mock_get_client.assert_called_once_with("fake-token")

    expected_trade_data = {
        "symbol": "GBPUSD",
        "direction": "short",
        "entry": 1.30,
        "stop": 1.31,
        "exit": 1.28,
        "result": 2,
        "pnl": 400,
        "entry_datetime": expected_entry_datetime,
        "exit_datetime": expected_exit_datetime,
    }

    mock_query.update.assert_called_once_with(expected_trade_data)
    mock_query.eq.assert_any_call("id", 5)
    mock_query.eq.assert_any_call("user_id", "user-123")

    assert response == {
        "id": 5,
        "account_id": 7,
        "symbol": "GBPUSD",
        "direction": "short",
        "entry": 1.30,
        "stop": 1.31,
        "exit": 1.28,
        "result": 2.0,
        "pnl": 400.0,
        "entry_datetime": expected_entry_datetime,
        "exit_datetime": expected_exit_datetime,
    }
    assert "user_id" not in response


def test_update_trade_not_found():
    fake_response = SimpleNamespace(data=[])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    updated_trade = {
        "symbol": "EURUSD",
        "direction": "long",
        "entry": 1.10,
        "stop": 1.09,
        "exit": 1.12,
        "result": 2,
        "pnl": 200,
        "entry_datetime": datetime(2026, 8, 22, 10, 0),
        "exit_datetime": datetime(2026, 8, 22, 11, 0),
    }

    with patch(
        "database.trades.get_authenticated_client",
        return_value=mock_client,
    ):
        with pytest.raises(ResourceNotFoundError, match="Trade not found"):
            update_trade_in_supabase(
                999,
                updated_trade,
                "user-123",
                "fake-token",
            )
