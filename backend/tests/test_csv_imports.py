import pytest

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import app
from auth import get_current_user
from routes.csv_imports import MAX_CSV_FILE_SIZE


client = TestClient(app)


def fake_current_user():
    return {"user": SimpleNamespace(id="test-user"), "token": "fake-token"}


@pytest.fixture
def authenticated_user():
    app.dependency_overrides[get_current_user] = fake_current_user
    yield
    app.dependency_overrides.clear()


def test_preview_csv_without_auth_returns_401():
    response = client.post(
        "/imports/preview",
        files={
            "file": ("trades.csv", b"symbol,direction\nEURUSD,long", "text/csv")
        },
    )

    assert response.status_code == 401


def test_preview_csv_returns_400_for_invalid_file(authenticated_user):
    response = client.post(
        "/imports/preview",
        files={
            "file": ("trades.txt", b"symbol,direction\nEURUSD,long", "text/plain")
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Please upload a CSV file"}


def test_preview_csv_rejects_file_over_size_limit(authenticated_user):
    oversized_content = b"a" * (MAX_CSV_FILE_SIZE + 1)

    response = client.post(
        "/imports/preview",
        files={"file": ("trades.csv", oversized_content, "text/csv")},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "CSV file must not exceed 5 MB"}


def test_validate_csv_import(authenticated_user):
    content = (
        "Instrument;Side;Open Price;Stop Loss;"
        "Close Price;Profit;Open Time;Close Time\n"
        "EURUSD;Buy;1,1500;1,1400;"
        "1,1700;€200,00;"
        "30/08/2026 10:00;30/08/2026 11:00\n"
    ).encode("utf-8")

    response = client.post(
        "/imports/validate",
        files={"file": ("trades.csv", content, "text/csv")},
        data={
            "mapping": (
                '{"symbol":"Instrument",'
                '"direction":"Side",'
                '"entry":"Open Price",'
                '"stop":"Stop Loss",'
                '"exit":"Close Price",'
                '"pnl":"Profit",'
                '"entry_datetime":"Open Time",'
                '"exit_datetime":"Close Time"}'
            ),
            "decimal_separator": ",",
            "date_format": "%d/%m/%Y %H:%M",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_rows": 1,
        "valid_count": 1,
        "invalid_count": 0,
        "valid_rows": [
            {
                "row": 2,
                "trade": {
                    "symbol": "EURUSD",
                    "direction": "long",
                    "entry": 1.15,
                    "stop": 1.14,
                    "exit": 1.17,
                    "pnl": 200.0,
                    "entry_datetime": "2026-08-30T10:00:00",
                    "exit_datetime": "2026-08-30T11:00:00",
                },
            }
        ],
        "errors": [],
    }


def test_validate_csv_import_without_auth_returns_401():
    response = client.post(
        "/imports/validate",
        files={
            "file": ("trades.csv", b"symbol,direction\nEURUSD,long", "text/csv")
        },
        data={"mapping": "{}", "decimal_separator": "."},
    )

    assert response.status_code == 401


@pytest.mark.parametrize("mapping", ["not valid JSON", '{"symbol": 123}'])
def test_validate_csv_import_rejects_invalid_mapping(authenticated_user, mapping):
    response = client.post(
        "/imports/validate",
        files={
            "file": ("trades.csv", b"symbol,direction\nEURUSD,long", "text/csv")
        },
        data={"mapping": mapping, "decimal_separator": "."},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Mapping must be a JSON object containing string keys and values"
    }


def test_validate_csv_import_rejects_invalid_file(authenticated_user):
    response = client.post(
        "/imports/validate",
        files={
            "file": ("trades.txt", b"symbol,direction\nEURUSD,long", "text/plain")
        },
        data={"mapping": "{}", "decimal_separator": "."},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Please upload a CSV file"}


IMPORT_MAPPING = (
    '{"symbol":"Instrument","direction":"Side","entry":"Open Price",'
    '"stop":"Stop Loss","exit":"Close Price","pnl":"Profit",'
    '"entry_datetime":"Open Time","exit_datetime":"Close Time"}'
)

VALID_IMPORT_CSV = (
    "Instrument;Side;Open Price;Stop Loss;Close Price;Profit;"
    "Open Time;Close Time\n"
    "EURUSD;Buy;1,1500;1,1400;1,1700;€200,00;"
    "30/08/2026 10:00;30/08/2026 11:00\n"
).encode("utf-8")


def _post_csv_import(content=VALID_IMPORT_CSV):
    return client.post(
        "/imports",
        files={"file": ("trades.csv", content, "text/csv")},
        data={
            "account_id": "7",
            "mapping": IMPORT_MAPPING,
            "decimal_separator": ",",
            "date_format": "%d/%m/%Y %H:%M",
        },
    )


def test_imports_valid_csv(authenticated_user):
    with (
        patch("routes.csv_imports.account_belongs_to_user", return_value=True),
        patch(
            "routes.csv_imports.save_trades_to_supabase",
            return_value=[{"id": 10}],
        ) as mock_save,
    ):
        response = _post_csv_import()

    assert response.status_code == 200
    assert response.json() == {"imported_count": 1}

    saved_trades = mock_save.call_args.args[0]

    assert saved_trades == [
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
        }
    ]

    assert mock_save.call_args.args[1:] == ("test-user", "fake-token")


def test_import_rejects_account_not_owned_by_user(authenticated_user):
    with (
        patch("routes.csv_imports.account_belongs_to_user", return_value=False),
        patch("routes.csv_imports.save_trades_to_supabase") as mock_save,
    ):
        response = _post_csv_import()

    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found"}
    mock_save.assert_not_called()


def test_import_rejects_invalid_rows(authenticated_user):
    invalid_csv = VALID_IMPORT_CSV.replace(b"Buy", b"Hold")

    with (
        patch("routes.csv_imports.account_belongs_to_user", return_value=True),
        patch("routes.csv_imports.save_trades_to_supabase") as mock_save,
    ):
        response = _post_csv_import(invalid_csv)

    assert response.status_code == 422
    assert response.json()["detail"]["message"] == "CSV contains invalid rows"
    assert response.json()["detail"]["errors"] == [
        {
            "row": 2,
            "field": "direction",
            "message": "Unsupported direction value: Hold",
        }
    ]
    mock_save.assert_not_called()


def test_import_rejects_csv_without_trades(authenticated_user):
    empty_csv = (
        "Instrument;Side;Open Price;Stop Loss;Close Price;Profit;"
        "Open Time;Close Time\n"
    ).encode("utf-8")

    with (
        patch("routes.csv_imports.account_belongs_to_user", return_value=True),
        patch("routes.csv_imports.save_trades_to_supabase") as mock_save,
    ):
        response = _post_csv_import(empty_csv)

    assert response.status_code == 400
    assert response.json() == {"detail": "CSV file contains no trades"}
    mock_save.assert_not_called()


def test_import_without_auth_returns_401():
    response = _post_csv_import()
    assert response.status_code == 401


def test_import_rejects_invalid_file(authenticated_user):
    with (
        patch("routes.csv_imports.account_belongs_to_user", return_value=True),
        patch("routes.csv_imports.save_trades_to_supabase") as mock_save,
    ):
        response = client.post(
            "/imports",
            files={
                "file": (
                    "trades.txt",
                    b"symbol,direction\nEURUSD,long",
                    "text/plain",
                )
            },
            data={
                "account_id": "7",
                "mapping": "{}",
                "decimal_separator": ".",
            },
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Please upload a CSV file"}
    mock_save.assert_not_called()


def test_imports_csv_automatically(authenticated_user):
    with (
        patch("routes.csv_imports.account_belongs_to_user", return_value=True),
        patch(
            "routes.csv_imports.save_trades_to_supabase",
            return_value=[{"id": 10}],
        ) as mock_save,
    ):
        response = client.post(
            "/imports",
            files={"file": ("trades.csv", VALID_IMPORT_CSV, "text/csv")},
            data={"account_id": "7"},
        )

    assert response.status_code == 200
    assert response.json() == {"imported_count": 1}
    mock_save.assert_called_once()


def test_imports_csv_without_stop_automatically(authenticated_user):
    content = (
        "Instrument;Side;Open Price;Close Price;Profit;"
        "Open Time;Close Time\n"
        "EURUSD;Buy;1,1500;1,1700;€200,00;"
        "30/08/2026 10:00;30/08/2026 11:00\n"
    ).encode("utf-8")

    with (
        patch("routes.csv_imports.account_belongs_to_user", return_value=True),
        patch(
            "routes.csv_imports.save_trades_to_supabase",
            return_value=[{"id": 10}],
        ) as mock_save,
    ):
        response = client.post(
            "/imports",
            files={"file": ("trades.csv", content, "text/csv")},
            data={"account_id": "7"},
        )

    assert response.status_code == 200
    assert response.json() == {"imported_count": 1}

    saved_trade = mock_save.call_args.args[0][0]

    assert saved_trade["stop"] is None
    assert saved_trade["result"] is None


def test_automatic_import_rejects_missing_columns(authenticated_user):
    content = b"Instrument,Side\nEURUSD,Buy\n"

    with (
        patch("routes.csv_imports.account_belongs_to_user", return_value=True),
        patch("routes.csv_imports.save_trades_to_supabase") as mock_save,
    ):
        response = client.post(
            "/imports",
            files={"file": ("trades.csv", content, "text/csv")},
            data={"account_id": "7"},
        )

    assert response.status_code == 422
    assert response.json()["detail"]["message"] == (
        "CSV columns could not be mapped automatically"
    )
    assert response.json()["detail"]["missing_fields"] == [
        "entry",
        "entry_datetime",
        "exit",
        "exit_datetime",
        "pnl",
    ]
    mock_save.assert_not_called()


def test_automatic_import_rejects_unknown_date_format(authenticated_user):
    content = (
        "Instrument;Side;Open Price;Stop Loss;Close Price;Profit;"
        "Open Time;Close Time\n"
        "EURUSD;Buy;1,1500;1,1400;1,1700;200,00;"
        "August 30 2026 at 10;August 30 2026 at 11\n"
    ).encode("utf-8")

    with (
        patch("routes.csv_imports.account_belongs_to_user", return_value=True),
        patch("routes.csv_imports.save_trades_to_supabase") as mock_save,
    ):
        response = client.post(
            "/imports",
            files={"file": ("trades.csv", content, "text/csv")},
            data={"account_id": "7"},
        )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Could not detect the CSV datetime format"
    }
    mock_save.assert_not_called()
