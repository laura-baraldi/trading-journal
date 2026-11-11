import pytest

from types import SimpleNamespace
from unittest.mock import patch

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


def test_get_accounts(authenticated_user):
    fake_accounts = [
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

    with patch(
        "routes.accounts.load_accounts_from_supabase",
        return_value=fake_accounts,
    ) as mock_load_accounts:
        response = client.get("/accounts")

    assert response.status_code == 200
    assert response.json() == fake_accounts
    mock_load_accounts.assert_called_once_with("test-user", "fake-token")


def test_create_account(authenticated_user):
    account_data = {
        "name": "FTMO 100K",
        "starting_balance": 100000,
        "currency": "USD",
        "broker": "FTMO",
        "account_type": "Prop Firm",
    }

    fake_response = [
        {
            "id": 2,
            "user_id": "test-user",
            **account_data,
        }
    ]

    with patch(
        "routes.accounts.save_account_to_supabase",
        return_value=fake_response,
    ) as mock_save_account:
        response = client.post("/accounts", json=account_data)

    assert response.status_code == 200
    assert response.json() == fake_response

    mock_save_account.assert_called_once_with(
        account_data,
        "test-user",
        "fake-token",
    )


def test_create_account_uses_none_for_optional_fields(authenticated_user):
    account_data = {
        "name": "Personal Account",
        "starting_balance": 10000,
        "currency": "EUR",
    }

    fake_response = [
        {
            "id": 3,
            "user_id": "test-user",
            "name": "Personal Account",
            "starting_balance": 10000,
            "currency": "EUR",
            "broker": None,
            "account_type": None,
        }
    ]

    with patch(
        "routes.accounts.save_account_to_supabase",
        return_value=fake_response,
    ) as mock_save_account:
        response = client.post("/accounts", json=account_data)

    assert response.status_code == 200

    mock_save_account.assert_called_once_with(
        {
            "name": "Personal Account",
            "starting_balance": 10000.0,
            "currency": "EUR",
            "broker": None,
            "account_type": None,
        },
        "test-user",
        "fake-token",
    )


@pytest.mark.parametrize(
    "account_data",
    [
        {
            "starting_balance": 100000,
            "currency": "USD",
        },
        {
            "name": "",
            "starting_balance": 100000,
            "currency": "USD",
        },
        {
            "name": "FTMO",
            "starting_balance": 100000,
        },
        {
            "name": "FTMO",
            "starting_balance": 100000,
            "currency": "",
        },
    ],
)
def test_create_account_rejects_invalid_data(
    authenticated_user,
    account_data,
):
    response = client.post("/accounts", json=account_data)

    assert response.status_code == 422


def test_update_account(authenticated_user):
    account_data = {
        "name": "FTMO Updated",
        "starting_balance": 120000,
        "currency": "EUR",
        "broker": "FTMO",
        "account_type": "Prop Firm",
    }

    fake_response = [
        {
            "id": 2,
            "user_id": "test-user",
            **account_data,
        }
    ]

    with patch(
        "routes.accounts.update_account_in_supabase",
        return_value=fake_response,
    ) as mock_update_account:
        response = client.patch("/accounts/2", json=account_data)

    assert response.status_code == 200
    assert response.json() == fake_response

    mock_update_account.assert_called_once_with(
        2,
        account_data,
        "test-user",
        "fake-token",
    )


def test_update_account_invalid_id(authenticated_user):
    account_data = {
        "name": "FTMO",
        "starting_balance": 100000,
        "currency": "USD",
        "broker": None,
        "account_type": None,
    }

    response = client.patch("/accounts/banana", json=account_data)

    assert response.status_code == 422


def test_delete_account(authenticated_user):
    fake_response = [
        {
            "id": 2,
            "user_id": "test-user",
            "name": "FTMO 100K",
        }
    ]

    with patch(
        "routes.accounts.delete_account_from_supabase",
        return_value=fake_response,
    ) as mock_delete_account:
        response = client.delete("/accounts/2")

    assert response.status_code == 200
    assert response.json() == fake_response

    mock_delete_account.assert_called_once_with(
        2,
        "test-user",
        "fake-token",
    )


def test_delete_account_invalid_id(authenticated_user):
    response = client.delete("/accounts/banana")

    assert response.status_code == 422


def test_accounts_without_auth_return_401():
    assert client.get("/accounts").status_code == 401
    assert client.post("/accounts", json={}).status_code == 401
    assert client.patch("/accounts/1", json={}).status_code == 401
    assert client.delete("/accounts/1").status_code == 401
