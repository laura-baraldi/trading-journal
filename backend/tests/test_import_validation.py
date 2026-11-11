from datetime import datetime

from imports.validation import validate_trade_rows


MAPPING = {
    "symbol": "Instrument",
    "direction": "Side",
    "entry": "Open Price",
    "stop": "Stop Loss",
    "exit": "Close Price",
    "pnl": "Profit",
    "entry_datetime": "Open Time",
    "exit_datetime": "Close Time",
}

DATE_FORMAT = "%d/%m/%Y %H:%M"


def build_row(
    symbol: str,
    entry: str = "1,1500",
):
    return {
        "Instrument": symbol,
        "Side": "BUY",
        "Open Price": entry,
        "Stop Loss": "1,1400",
        "Close Price": "1,1700",
        "Profit": "€200,00",
        "Open Time": "30/08/2026 10:00",
        "Close Time": "30/08/2026 11:00",
    }


def test_validates_all_valid_rows():
    rows = [
        build_row("EURUSD"),
        build_row("GBPUSD"),
    ]

    result = validate_trade_rows(
        rows,
        MAPPING,
        decimal_separator=",",
        date_format=DATE_FORMAT,
    )

    assert result["total_rows"] == 2
    assert result["valid_count"] == 2
    assert result["invalid_count"] == 0
    assert result["errors"] == []

    assert result["valid_rows"][0] == {
        "row": 2,
        "trade": {
            "symbol": "EURUSD",
            "direction": "long",
            "entry": 1.15,
            "stop": 1.14,
            "exit": 1.17,
            "pnl": 200.0,
            "entry_datetime": datetime(
                2026,
                8,
                30,
                10,
                0,
            ),
            "exit_datetime": datetime(
                2026,
                8,
                30,
                11,
                0,
            ),
        },
    }

    assert result["valid_rows"][1]["row"] == 3
    assert result["valid_rows"][1]["trade"]["symbol"] == "GBPUSD"


def test_collects_errors_and_continues_validating():
    rows = [
        build_row("EURUSD"),
        build_row("XAUUSD", entry="invalid"),
        build_row("GBPUSD"),
    ]

    result = validate_trade_rows(
        rows,
        MAPPING,
        decimal_separator=",",
        date_format=DATE_FORMAT,
    )

    assert result["total_rows"] == 3
    assert result["valid_count"] == 2
    assert result["invalid_count"] == 1

    assert [
        valid_row["row"]
        for valid_row in result["valid_rows"]
    ] == [2, 4]

    assert result["errors"] == [
        {
            "row": 3,
            "field": "entry",
            "message": "Invalid numeric value: invalid",
        }
    ]


def test_handles_empty_row_list():
    result = validate_trade_rows(
        [],
        MAPPING,
        decimal_separator=",",
        date_format=DATE_FORMAT,
    )

    assert result == {
        "total_rows": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "valid_rows": [],
        "errors": [],
    }
