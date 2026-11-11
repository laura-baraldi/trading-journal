import pytest

from fastapi import HTTPException
from types import SimpleNamespace
from unittest.mock import patch
from supabase_auth.errors import AuthApiError

from auth import (
    get_bearer_token,
    get_current_user,
    get_demo_session,
    get_user_from_token,
    update_demo_activity,
)


def test_get_bearer_token_missing_header():
    with pytest.raises(HTTPException) as error:
        get_bearer_token(None)

    assert error.value.status_code == 401
    assert error.value.detail == (
        "Missing Authorization header"
    )


def test_get_bearer_token_invalid_header():
    with pytest.raises(HTTPException) as error:
        get_bearer_token(
            "NotBearer abc123"
        )

    assert error.value.status_code == 401
    assert error.value.detail == (
        "Invalid Authorization header"
    )


def test_get_bearer_token_returns_token():
    token = get_bearer_token(
        "Bearer abc123"
    )

    assert token == "abc123"


def test_get_user_from_token_returns_user():
    fake_user = SimpleNamespace(
        id="user-123"
    )

    fake_response = SimpleNamespace(
        user=fake_user
    )

    with patch(
        "auth.create_client"
    ) as mock_create_client:
        mock_client = (
            mock_create_client.return_value
        )

        mock_client.auth.get_user.return_value = (
            fake_response
        )

        user = get_user_from_token(
            "abc123"
        )

    assert user == fake_user


def test_get_user_from_token_invalid_token():
    with patch(
        "auth.create_client"
    ) as mock_create_client:
        mock_client = (
            mock_create_client.return_value
        )

        mock_client.auth.get_user.side_effect = (
            AuthApiError(
                "Invalid token",
                401,
                "invalid_token",
            )
        )

        with pytest.raises(
            HTTPException
        ) as error:
            get_user_from_token(
                "bad-token"
            )

    assert error.value.status_code == 401
    assert error.value.detail == (
        "Invalid or expired token"
    )


def test_get_user_from_token_service_error():
    with patch(
        "auth.create_client"
    ) as mock_create_client:
        mock_client = (
            mock_create_client.return_value
        )

        mock_client.auth.get_user.side_effect = (
            Exception(
                "Supabase unavailable"
            )
        )

        with pytest.raises(
            HTTPException
        ) as error:
            get_user_from_token(
                "abc123"
            )

    assert error.value.status_code == 503
    assert error.value.detail == (
        "Authentication service unavailable"
    )


def test_update_demo_activity_skips_without_demo_email():
    fake_user = SimpleNamespace(
        id="user-123",
        email="user@example.com",
    )

    with (
        patch.dict(
            "os.environ",
            {},
            clear=True,
        ),
        patch(
            "auth.create_client"
        ) as mock_create_client,
    ):
        update_demo_activity(
            fake_user,
            "abc123",
        )

    mock_create_client.assert_not_called()


def test_update_demo_activity_skips_regular_user():
    fake_user = SimpleNamespace(
        id="user-123",
        email="user@example.com",
    )

    with (
        patch.dict(
            "os.environ",
            {
                "DEMO_EMAIL":
                    "demo@example.com",
            },
        ),
        patch(
            "auth.create_client"
        ) as mock_create_client,
    ):
        update_demo_activity(
            fake_user,
            "abc123",
        )

    mock_create_client.assert_not_called()


def test_update_demo_activity_ignores_errors():
    fake_user = SimpleNamespace(
        id="demo-user",
        email="demo@example.com",
    )

    with (
        patch.dict(
            "os.environ",
            {
                "DEMO_EMAIL":
                    "demo@example.com",
            },
        ),
        patch(
            "auth.create_client"
        ) as mock_create_client,
    ):
        mock_client = (
            mock_create_client.return_value
        )

        (
            mock_client
            .table
            .return_value
            .update
            .return_value
            .eq
            .return_value
            .execute
            .side_effect
        ) = Exception(
            "Supabase unavailable"
        )

        update_demo_activity(
            fake_user,
            "demo-token",
        )


def test_get_current_user_returns_user_and_token():
    fake_user = SimpleNamespace(
        id="user-123",
        email="user@example.com",
    )

    fake_request = SimpleNamespace(
        state=SimpleNamespace()
    )

    with (
        patch(
            "auth.get_user_from_token",
            return_value=fake_user,
        ),
        patch(
            "auth.update_demo_activity"
        ) as mock_update_demo_activity,
    ):
        auth_data = get_current_user(
            fake_request,
            "abc123",
        )

    assert auth_data == {
        "user": fake_user,
        "token": "abc123",
    }

    assert fake_request.state.user_id == "user-123"

    mock_update_demo_activity.assert_called_once_with(
        fake_user,
        "abc123",
    )


def test_get_demo_session_returns_tokens():
    fake_session = SimpleNamespace(
        access_token="access-token",
        refresh_token="refresh-token",
    )

    fake_response = SimpleNamespace(
        session=fake_session
    )

    with (
        patch.dict(
            "os.environ",
            {
                "DEMO_EMAIL":
                    "demo@example.com",
                "DEMO_PASSWORD":
                    "demo-password",
            },
        ),
        patch(
            "auth.create_client"
        ) as mock_create_client,
    ):
        mock_client = (
            mock_create_client.return_value
        )

        mock_client.auth.sign_in_with_password.return_value = (
            fake_response
        )

        result = get_demo_session()

    mock_client.auth.sign_in_with_password.assert_called_once_with(
        {
            "email":
                "demo@example.com",
            "password":
                "demo-password",
        }
    )

    assert result == {
        "access_token":
            "access-token",
        "refresh_token":
            "refresh-token",
    }


@pytest.mark.parametrize(
    "email,password",
    [
        (None, "demo-password"),
        ("demo@example.com", None),
        (None, None),
    ],
)
def test_get_demo_session_requires_configuration(
    email,
    password,
):
    environment = {}

    if email:
        environment[
            "DEMO_EMAIL"
        ] = email

    if password:
        environment[
            "DEMO_PASSWORD"
        ] = password

    with patch.dict(
        "os.environ",
        environment,
        clear=True,
    ):
        with pytest.raises(
            HTTPException
        ) as error:
            get_demo_session()

    assert error.value.status_code == 500
    assert error.value.detail == (
        "Demo account is not configured"
    )


def test_get_demo_session_handles_login_error():
    with (
        patch.dict(
            "os.environ",
            {
                "DEMO_EMAIL":
                    "demo@example.com",
                "DEMO_PASSWORD":
                    "demo-password",
            },
        ),
        patch(
            "auth.create_client"
        ) as mock_create_client,
    ):
        mock_client = (
            mock_create_client.return_value
        )

        mock_client.auth.sign_in_with_password.side_effect = (
            Exception(
                "Login failed"
            )
        )

        with pytest.raises(
            HTTPException
        ) as error:
            get_demo_session()

    assert error.value.status_code == 503
    assert error.value.detail == (
        "Demo login unavailable"
    )


def test_get_demo_session_requires_session():
    fake_response = SimpleNamespace(
        session=None
    )

    with (
        patch.dict(
            "os.environ",
            {
                "DEMO_EMAIL":
                    "demo@example.com",
                "DEMO_PASSWORD":
                    "demo-password",
            },
        ),
        patch(
            "auth.create_client"
        ) as mock_create_client,
    ):
        mock_client = (
            mock_create_client.return_value
        )

        mock_client.auth.sign_in_with_password.return_value = (
            fake_response
        )

        with pytest.raises(
            HTTPException
        ) as error:
            get_demo_session()

    assert error.value.status_code == 503
    assert error.value.detail == (
        "Demo login unavailable"
    )
