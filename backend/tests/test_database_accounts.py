import pytest

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from database.accounts import (
    account_belongs_to_user,
    delete_account_from_supabase,
    load_accounts_from_supabase,
    save_account_to_supabase,
    update_account_in_supabase,
)
from database.client import ResourceNotFoundError


def make_mock_query(fake_response):
    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.insert.return_value = mock_query
    mock_query.update.return_value = mock_query
    mock_query.delete.return_value = mock_query
    mock_query.execute.return_value = fake_response
    return mock_query


def make_mock_client(mock_query):
    mock_client = MagicMock()
    mock_client.table.return_value = mock_query
    return mock_client


def test_load_accounts_from_supabase():
    fake_response = SimpleNamespace(
        data=[
            {
                "id": 1,
                "user_id": "test-user",
                "name": "My Account",
                "starting_balance": 100000,
                "currency": "USD",
                "broker": None,
                "account_type": None,
            }
        ]
    )

    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.accounts.get_authenticated_client",
        return_value=mock_client,
    ) as mock_get_client:
        result = load_accounts_from_supabase(
            "test-user",
            "fake-token",
        )

    mock_get_client.assert_called_once_with("fake-token")
    mock_client.table.assert_called_once_with("accounts")
    mock_query.select.assert_called_once_with("*")
    mock_query.eq.assert_called_once_with("user_id", "test-user")
    mock_query.order.assert_called_once_with("created_at")
    assert result == fake_response.data


def test_save_account_to_supabase():
    fake_response = SimpleNamespace(
        data=[
            {
                "id": 2,
                "user_id": "test-user",
                "name": "FTMO 100K",
                "starting_balance": 100000,
                "currency": "USD",
                "broker": "FTMO",
                "account_type": "Prop Firm",
            }
        ]
    )

    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    account = {
        "name": "FTMO 100K",
        "starting_balance": 100000,
        "currency": "USD",
        "broker": "FTMO",
        "account_type": "Prop Firm",
    }

    with patch(
        "database.accounts.get_authenticated_client",
        return_value=mock_client,
    ) as mock_get_client:
        result = save_account_to_supabase(
            account,
            "test-user",
            "fake-token",
        )

    mock_get_client.assert_called_once_with("fake-token")
    mock_client.table.assert_called_once_with("accounts")

    mock_query.insert.assert_called_once_with(
        {
            "user_id": "test-user",
            "name": "FTMO 100K",
            "starting_balance": 100000,
            "currency": "USD",
            "broker": "FTMO",
            "account_type": "Prop Firm",
        }
    )

    assert result == fake_response.data


@pytest.mark.parametrize(
    "broker, account_type",
    [
        ("FTMO", "Prop Firm"),
        (None, None),
    ],
)
def test_update_account_in_supabase(broker, account_type):
    fake_response = SimpleNamespace(
        data=[
            {
                "id": 2,
                "user_id": "test-user",
                "name": "FTMO Updated",
                "starting_balance": 120000,
                "currency": "EUR",
                "broker": broker,
                "account_type": account_type,
            }
        ]
    )

    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    account = {
        "name": "FTMO Updated",
        "starting_balance": 120000,
        "currency": "EUR",
        "broker": broker,
        "account_type": account_type,
    }

    with patch(
        "database.accounts.get_authenticated_client",
        return_value=mock_client,
    ) as mock_get_client:
        result = update_account_in_supabase(
            2,
            account,
            "test-user",
            "fake-token",
        )

    mock_get_client.assert_called_once_with("fake-token")
    mock_client.table.assert_called_once_with("accounts")

    mock_query.update.assert_called_once_with(
        {
            "name": "FTMO Updated",
            "starting_balance": 120000,
            "currency": "EUR",
            "broker": broker,
            "account_type": account_type,
        }
    )

    mock_query.eq.assert_any_call("id", 2)
    mock_query.eq.assert_any_call("user_id", "test-user")
    assert result == fake_response.data


def test_update_account_not_found():
    fake_response = SimpleNamespace(data=[])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    account = {
        "name": "Test",
        "starting_balance": 10000,
        "currency": "USD",
        "broker": None,
        "account_type": None,
    }

    with patch(
        "database.accounts.get_authenticated_client",
        return_value=mock_client,
    ):
        with pytest.raises(ResourceNotFoundError, match="Account not found"):
            update_account_in_supabase(
                999,
                account,
                "user-123",
                "fake-token",
            )


def test_delete_account_from_supabase():
    fake_response = SimpleNamespace(
        data=[
            {
                "id": 2,
                "user_id": "test-user",
                "name": "FTMO 100K",
            }
        ]
    )

    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.accounts.get_authenticated_client",
        return_value=mock_client,
    ) as mock_get_client:
        result = delete_account_from_supabase(
            2,
            "test-user",
            "fake-token",
        )

    mock_get_client.assert_called_once_with("fake-token")
    mock_client.table.assert_called_once_with("accounts")
    mock_query.delete.assert_called_once_with()
    mock_query.eq.assert_any_call("id", 2)
    mock_query.eq.assert_any_call("user_id", "test-user")
    assert result == fake_response.data


def test_delete_account_not_found():
    fake_response = SimpleNamespace(data=[])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.accounts.get_authenticated_client",
        return_value=mock_client,
    ):
        with pytest.raises(ResourceNotFoundError, match="Account not found"):
            delete_account_from_supabase(
                999,
                "user-123",
                "fake-token",
            )


def test_account_belongs_to_user_returns_true():
    fake_response = SimpleNamespace(data=[{"id": 1}])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.accounts.get_authenticated_client",
        return_value=mock_client,
    ):
        result = account_belongs_to_user(
            1,
            "user-123",
            "fake-token",
        )

    assert result is True


def test_account_belongs_to_user_returns_false():
    fake_response = SimpleNamespace(data=[])
    mock_query = make_mock_query(fake_response)
    mock_client = make_mock_client(mock_query)

    with patch(
        "database.accounts.get_authenticated_client",
        return_value=mock_client,
    ):
        result = account_belongs_to_user(
            999,
            "user-123",
            "fake-token",
        )

    assert result is False
