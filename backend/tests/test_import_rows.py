from datetime import datetime

import pytest

from imports.rows import (
    CsvRowError,
    normalize_trade_row,
)


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

ROW = {
    "Instrument": "EURUSD",
    "Side": "BUY",
    "Open Price": "1,1500",
    "Stop Loss": "1,1400",
    "Close Price": "1,1700",
    "Profit": "€200,00",
    "Open Time": "30/08/2026 10:00",
    "Close Time": "30/08/2026 11:00",
}

DATE_FORMAT = "%d/%m/%Y %H:%M"


def test_normalizes_complete_trade_row():
    result = normalize_trade_row(
        ROW,
        MAPPING,
        decimal_separator=",",
        date_format=DATE_FORMAT,
    )

    assert result == {
        "symbol": "EURUSD",
        "direction": "long",
        "entry": 1.15,
        "stop": 1.14,
        "exit": 1.17,
        "pnl": 200.0,
        "entry_datetime": datetime(2026, 8, 30, 10, 0),
        "exit_datetime": datetime(2026, 8, 30, 11, 0),
    }


def test_allows_missing_stop_mapping():
    mapping = MAPPING.copy()
    mapping.pop("stop")

    result = normalize_trade_row(
        ROW,
        mapping,
        decimal_separator=",",
        date_format=DATE_FORMAT,
    )

    assert result["stop"] is None


def test_allows_empty_stop_value():
    row = {
        **ROW,
        "Stop Loss": "   ",
    }

    result = normalize_trade_row(
        row,
        MAPPING,
        decimal_separator=",",
        date_format=DATE_FORMAT,
    )

    assert result["stop"] is None


def test_rejects_missing_required_mapping():
    mapping = MAPPING.copy()
    mapping.pop("symbol")

    with pytest.raises(CsvRowError) as exc_info:
        normalize_trade_row(
            ROW,
            mapping,
            decimal_separator=",",
            date_format=DATE_FORMAT,
        )

    assert exc_info.value.field == "symbol"
    assert exc_info.value.message == (
        "Required column is not mapped"
    )


def test_rejects_mapping_to_missing_column():
    mapping = {
        **MAPPING,
        "symbol": "Unknown Column",
    }

    with pytest.raises(CsvRowError) as exc_info:
        normalize_trade_row(
            ROW,
            mapping,
            decimal_separator=",",
            date_format=DATE_FORMAT,
        )

    assert exc_info.value.field == "symbol"
    assert exc_info.value.message == (
        "Mapped column does not exist: Unknown Column"
    )


def test_rejects_empty_required_value():
    row = {
        **ROW,
        "Instrument": "   ",
    }

    with pytest.raises(CsvRowError) as exc_info:
        normalize_trade_row(
            row,
            MAPPING,
            decimal_separator=",",
            date_format=DATE_FORMAT,
        )

    assert exc_info.value.field == "symbol"
    assert exc_info.value.message == (
        "Required value is missing"
    )


def test_rejects_none_required_value():
    row = {
        **ROW,
        "Instrument": None,
    }

    with pytest.raises(CsvRowError) as exc_info:
        normalize_trade_row(
            row,
            MAPPING,
            decimal_separator=",",
            date_format=DATE_FORMAT,
        )

    assert exc_info.value.field == "symbol"
    assert exc_info.value.message == (
        "Required value is missing"
    )


def test_reports_direction_normalization_error():
    row = {
        **ROW,
        "Side": "closed",
    }

    with pytest.raises(CsvRowError) as exc_info:
        normalize_trade_row(
            row,
            MAPPING,
            decimal_separator=",",
            date_format=DATE_FORMAT,
        )

    assert exc_info.value.field == "direction"
    assert exc_info.value.message == (
        "Unsupported direction value: closed"
    )


def test_reports_number_normalization_error():
    row = {
        **ROW,
        "Open Price": "invalid",
    }

    with pytest.raises(CsvRowError) as exc_info:
        normalize_trade_row(
            row,
            MAPPING,
            decimal_separator=",",
            date_format=DATE_FORMAT,
        )

    assert exc_info.value.field == "entry"
    assert exc_info.value.message == (
        "Invalid numeric value: invalid"
    )


def test_reports_datetime_normalization_error():
    row = {
        **ROW,
        "Open Time": "invalid",
    }

    with pytest.raises(CsvRowError) as exc_info:
        normalize_trade_row(
            row,
            MAPPING,
            decimal_separator=",",
            date_format=DATE_FORMAT,
        )

    assert exc_info.value.field == "entry_datetime"
    assert exc_info.value.message == (
        "Invalid datetime value: invalid"
    )


def test_rejects_exit_before_entry():
    row = {
        **ROW,
        "Open Time": "30/08/2026 12:00",
        "Close Time": "30/08/2026 11:00",
    }

    with pytest.raises(CsvRowError) as exc_info:
        normalize_trade_row(
            row,
            MAPPING,
            decimal_separator=",",
            date_format=DATE_FORMAT,
        )

    assert exc_info.value.field == "exit_datetime"
    assert exc_info.value.message == (
        "Exit datetime cannot be before entry datetime"
    )


def test_rejects_entry_equal_to_stop():
    row = {
        **ROW,
        "Stop Loss": "1,1500",
    }

    with pytest.raises(CsvRowError) as exc_info:
        normalize_trade_row(
            row,
            MAPPING,
            decimal_separator=",",
            date_format=DATE_FORMAT,
        )

    assert exc_info.value.field == "stop"
    assert exc_info.value.message == (
        "Entry and stop cannot be the same"
    )


def test_normalizes_iso_dates_without_explicit_format():
    row = {
        **ROW,
        "Open Time": "2026-08-30T10:00:00",
        "Close Time": "2026-08-30T11:00:00",
    }

    result = normalize_trade_row(
        row,
        MAPPING,
        decimal_separator=",",
    )

    assert result["entry_datetime"] == datetime(
        2026,
        8,
        30,
        10,
        0,
    )
    assert result["exit_datetime"] == datetime(
        2026,
        8,
        30,
        11,
        0,
    )
