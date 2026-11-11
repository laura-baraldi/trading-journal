from datetime import datetime, timezone

import pytest

from imports.normalization import (
    CsvNormalizationError,
    detect_date_format,
    detect_decimal_separator,
    normalize_datetime,
    normalize_direction,
    normalize_number,
)


@pytest.mark.parametrize("value", ["long", "LONG", "buy", "BUY", " b "])
def test_normalizes_long_direction(value):
    assert normalize_direction(value) == "long"


@pytest.mark.parametrize("value", ["short", "SHORT", "sell", "SELL", " s "])
def test_normalizes_short_direction(value):
    assert normalize_direction(value) == "short"


def test_rejects_unknown_direction():
    with pytest.raises(
        CsvNormalizationError,
        match="Unsupported direction value: closed",
    ):
        normalize_direction("closed")


def test_normalizes_number_with_dot_decimal_separator():
    result = normalize_number("$1,234.56", decimal_separator=".")
    assert result == 1234.56


def test_normalizes_number_with_comma_decimal_separator():
    result = normalize_number("€1.234,56", decimal_separator=",")
    assert result == 1234.56


def test_normalizes_negative_number():
    result = normalize_number("-250,50", decimal_separator=",")
    assert result == -250.5


def test_normalizes_number_with_regular_spaces():
    result = normalize_number("1 234,56", decimal_separator=",")
    assert result == 1234.56


def test_normalizes_number_with_non_breaking_space():
    result = normalize_number("1\u00a0234,56", decimal_separator=",")
    assert result == 1234.56


def test_rejects_empty_number():
    with pytest.raises(
        CsvNormalizationError,
        match="Numeric value cannot be empty",
    ):
        normalize_number("   ", decimal_separator=".")


def test_rejects_invalid_number():
    with pytest.raises(
        CsvNormalizationError,
        match="Invalid numeric value: profit",
    ):
        normalize_number("profit", decimal_separator=".")


def test_normalizes_iso_datetime():
    result = normalize_datetime("2026-08-30T10:30:00")
    assert result == datetime(2026, 8, 30, 10, 30)


def test_normalizes_iso_datetime_with_utc():
    result = normalize_datetime("2026-08-30T10:30:00Z")
    assert result == datetime(2026, 8, 30, 10, 30, tzinfo=timezone.utc)


def test_normalizes_datetime_with_explicit_format():
    result = normalize_datetime(
        "30/08/2026 10:30",
        date_format="%d/%m/%Y %H:%M",
    )
    assert result == datetime(2026, 8, 30, 10, 30)


def test_rejects_empty_datetime():
    with pytest.raises(
        CsvNormalizationError,
        match="Datetime value cannot be empty",
    ):
        normalize_datetime("   ")


def test_rejects_invalid_iso_datetime():
    with pytest.raises(
        CsvNormalizationError,
        match="Invalid datetime value: not-a-date",
    ):
        normalize_datetime("not-a-date")


def test_rejects_datetime_with_wrong_explicit_format():
    with pytest.raises(
        CsvNormalizationError,
        match="Invalid datetime value: 08/30/2026",
    ):
        normalize_datetime("08/30/2026", date_format="%d/%m/%Y")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1,1500", ","),
        ("1.1500", "."),
        ("1.234,56", ","),
        ("1,234.56", "."),
    ],
)
def test_detects_decimal_separator(value, expected):
    rows = [{"Open Price": value}]
    mapping = {"entry": "Open Price"}
    assert detect_decimal_separator(rows, mapping) == expected


def test_decimal_detection_ignores_missing_and_empty_values():
    rows = [
        {"Open Price": None},
        {"Open Price": "   "},
        {"Open Price": "2350"},
    ]
    mapping = {"entry": "Open Price"}
    assert detect_decimal_separator(rows, mapping) == "."


def test_rejects_inconsistent_decimal_separators():
    rows = [
        {"Open Price": "1.15"},
        {"Open Price": "1,16"},
    ]
    mapping = {"entry": "Open Price"}

    with pytest.raises(
        CsvNormalizationError,
        match="CSV contains inconsistent decimal separators",
    ):
        detect_decimal_separator(rows, mapping)


def test_detects_iso_date_format():
    rows = [
        {
            "Open Time": "2026-08-30T10:00:00",
            "Close Time": "2026-08-30T11:00:00",
        }
    ]
    mapping = {
        "entry_datetime": "Open Time",
        "exit_datetime": "Close Time",
    }
    assert detect_date_format(rows, mapping) is None


def test_detects_european_date_format():
    rows = [
        {
            "Open Time": "30/08/2026 10:00",
            "Close Time": "30/08/2026 11:00",
        }
    ]
    mapping = {
        "entry_datetime": "Open Time",
        "exit_datetime": "Close Time",
    }
    assert detect_date_format(rows, mapping) is None


def test_date_detection_ignores_missing_and_empty_values():
    rows = [{"Open Time": None}, {"Open Time": "   "}]
    mapping = {"entry_datetime": "Open Time"}
    assert detect_date_format(rows, mapping) is None


def test_rejects_ambiguous_date_format():
    rows = [{"Open Time": "08/09/2026 10:00", "Close Time": "09/08/2026 11:00"}]
    mapping = {"entry_datetime": "Open Time", "exit_datetime": "Close Time"}

    with pytest.raises(
        CsvNormalizationError,
        match="CSV contains an ambiguous datetime format",
    ):
        detect_date_format(rows, mapping)


def test_rejects_unknown_date_format():
    rows = [{"Open Time": "August 30, 2026 at 10 AM"}]
    mapping = {"entry_datetime": "Open Time"}

    with pytest.raises(
        CsvNormalizationError,
        match="Could not detect the CSV datetime format",
    ):
        detect_date_format(rows, mapping)


def test_detects_consistent_date_format():
    rows = [{"Open Time": "08/09/2026 10:00", "Close Time": "13/09/2026 11:00"}]
    mapping = {"entry_datetime": "Open Time", "exit_datetime": "Close Time"}

    assert detect_date_format(rows, mapping) == "%d/%m/%Y %H:%M"
