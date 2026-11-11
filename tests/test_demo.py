import pytest

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from demo import (
    DEMO_TRADES,
    build_demo_trades,
    get_demo_client,
    reset_demo_data,
    reset_demo_if_inactive,
    should_reset_demo,
)


@pytest.mark.parametrize(
    "email,password",
    [
        (None, "demo-password"),
        ("demo@example.com", None),
        (None, None),
    ],
)
def test_get_demo_client_requires_configuration(
    email,
    password,
):
    environment = {}

    if email:
        environment["DEMO_EMAIL"] = email

    if password:
        environment["DEMO_PASSWORD"] = password

    with patch.dict(
        "os.environ",
        environment,
        clear=True,
    ):
        with pytest.raises(
            RuntimeError,
            match="Demo account is not configured",
        ):
            get_demo_client()


def test_get_demo_client_returns_authenticated_client():
    client = MagicMock()

    response = SimpleNamespace(
        session=SimpleNamespace(
            access_token="demo-token",
        ),
        user=SimpleNamespace(
            id="demo-user",
        ),
    )

    client.auth.sign_in_with_password.return_value = (
        response
    )

    with patch.dict(
        "os.environ",
        {
            "DEMO_EMAIL": "demo@example.com",
            "DEMO_PASSWORD": "demo-password",
        },
    ):
        with patch(
            "demo.create_client",
            return_value=client,
        ) as mock_create_client:
            result_client, user_id = (
                get_demo_client()
            )

    mock_create_client.assert_called_once()

    client.auth.sign_in_with_password.assert_called_once_with(
        {
            "email": "demo@example.com",
            "password": "demo-password",
        }
    )

    client.postgrest.auth.assert_called_once_with(
        "demo-token"
    )

    assert result_client is client
    assert user_id == "demo-user"


@pytest.mark.parametrize(
    "session,user",
    [
        (
            None,
            SimpleNamespace(
                id="demo-user",
            ),
        ),
        (
            SimpleNamespace(
                access_token="demo-token",
            ),
            None,
        ),
    ],
)
def test_get_demo_client_rejects_invalid_login(
    session,
    user,
):
    client = MagicMock()

    client.auth.sign_in_with_password.return_value = (
        SimpleNamespace(
            session=session,
            user=user,
        )
    )

    with patch.dict(
        "os.environ",
        {
            "DEMO_EMAIL": "demo@example.com",
            "DEMO_PASSWORD": "demo-password",
        },
    ):
        with patch(
            "demo.create_client",
            return_value=client,
        ):
            with pytest.raises(
                RuntimeError,
                match="Demo login failed",
            ):
                get_demo_client()


def test_build_demo_trades():
    account_id = 42
    user_id = "demo-user"

    trades = build_demo_trades(
        account_id,
        user_id,
    )

    assert len(trades) == len(
        DEMO_TRADES
    )

    for source, trade in zip(
        DEMO_TRADES,
        trades,
    ):
        assert trade["account_id"] == account_id
        assert trade["user_id"] == user_id
        assert trade["symbol"] == source["symbol"]
        assert (
            trade["direction"]
            == source["direction"]
        )
        assert trade["entry"] == source["entry"]
        assert trade["stop"] == source["stop"]
        assert trade["exit"] == source["exit"]
        assert trade["pnl"] == source["pnl"]

        entry_datetime = datetime.fromisoformat(
            trade["entry_datetime"]
        )

        exit_datetime = datetime.fromisoformat(
            trade["exit_datetime"]
        )

        assert (
            exit_datetime
            - entry_datetime
        ) == timedelta(hours=2)

        assert isinstance(
            trade["result"],
            float,
        )


def test_reset_demo_data():
    client = MagicMock()

    account_response = SimpleNamespace(
        data=[
            {
                "id": 42,
            }
        ]
    )

    fake_trades = [
        {
            "account_id": 42,
            "user_id": "demo-user",
        }
    ]

    with patch(
        "demo.get_demo_client",
        return_value=(
            client,
            "demo-user",
        ),
    ):
        with patch(
            "demo.execute_query",
            side_effect=[
                SimpleNamespace(),
                SimpleNamespace(),
                account_response,
                SimpleNamespace(),
            ],
        ) as mock_execute_query:
            with patch(
                "demo.build_demo_trades",
                return_value=fake_trades,
            ) as mock_build_demo_trades:
                reset_demo_data()

    assert client.table.call_args_list == [
        call("trades"),
        call("accounts"),
        call("accounts"),
        call("trades"),
    ]

    assert mock_execute_query.call_count == 4

    mock_build_demo_trades.assert_called_once_with(
        42,
        "demo-user",
    )


def test_should_reset_demo_when_recently_active():
    client = MagicMock()

    last_activity = (
        datetime.now(timezone.utc)
        - timedelta(minutes=5)
    )

    response = SimpleNamespace(
        data={
            "last_activity_at":
                last_activity.isoformat(),
        }
    )

    with patch(
        "demo.get_demo_client",
        return_value=(
            client,
            "demo-user",
        ),
    ):
        with patch(
            "demo.execute_query",
            return_value=response,
        ):
            result = should_reset_demo()

    assert result is False


def test_should_reset_demo_when_inactive():
    client = MagicMock()

    last_activity = (
        datetime.now(timezone.utc)
        - timedelta(hours=1)
    )

    response = SimpleNamespace(
        data={
            "last_activity_at":
                last_activity.isoformat(),
        }
    )

    with patch(
        "demo.get_demo_client",
        return_value=(
            client,
            "demo-user",
        ),
    ):
        with patch(
            "demo.execute_query",
            return_value=response,
        ):
            result = should_reset_demo()

    assert result is True


def test_should_reset_demo_accepts_z_timezone():
    client = MagicMock()

    last_activity = (
        datetime.now(timezone.utc)
        - timedelta(hours=1)
    )

    timestamp = (
        last_activity
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )

    response = SimpleNamespace(
        data={
            "last_activity_at":
                timestamp,
        }
    )

    with patch(
        "demo.get_demo_client",
        return_value=(
            client,
            "demo-user",
        ),
    ):
        with patch(
            "demo.execute_query",
            return_value=response,
        ):
            result = should_reset_demo()

    assert result is True


def test_reset_demo_if_inactive_resets(
    capsys,
):
    with patch(
        "demo.should_reset_demo",
        return_value=True,
    ):
        with patch(
            "demo.reset_demo_data",
        ) as mock_reset:
            reset_demo_if_inactive()

    mock_reset.assert_called_once_with()

    output = capsys.readouterr().out

    assert (
        "Demo data reset."
        in output
    )


def test_reset_demo_if_inactive_skips(
    capsys,
):
    with patch(
        "demo.should_reset_demo",
        return_value=False,
    ):
        with patch(
            "demo.reset_demo_data",
        ) as mock_reset:
            reset_demo_if_inactive()

    mock_reset.assert_not_called()

    output = capsys.readouterr().out

    assert (
        "Demo is active. Reset skipped."
        in output
    )

def test_reset_demo_if_inactive_forces_reset(
    capsys,
):
    with patch.dict(
        "os.environ",
        {"FORCE_DEMO_RESET": "true"},
    ):
        with patch(
            "demo.should_reset_demo",
        ) as mock_should_reset:
            with patch(
                "demo.reset_demo_data",
            ) as mock_reset:
                reset_demo_if_inactive()

    mock_should_reset.assert_not_called()
    mock_reset.assert_called_once_with()

    output = capsys.readouterr().out

    assert "Forced demo reset requested." in output
    assert "Demo data reset." in output