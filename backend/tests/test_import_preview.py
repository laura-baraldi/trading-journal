import pytest

from imports.preview import (
    CsvPreviewError,
    build_csv_preview,
    read_csv_rows,
)


def test_builds_preview_from_comma_separated_csv():
    content = (
        b"Instrument,Side,Open Price\n"
        b"EURUSD,Buy,1.15\n"
        b"XAUUSD,Sell,2350\n"
    )

    result = build_csv_preview(
        "trades.csv",
        content,
    )

    assert result == {
        "filename": "trades.csv",
        "delimiter": ",",
        "headers": [
            "Instrument",
            "Side",
            "Open Price",
        ],
        "row_count": 2,
        "sample_rows": [
            {
                "Instrument": "EURUSD",
                "Side": "Buy",
                "Open Price": "1.15",
            },
            {
                "Instrument": "XAUUSD",
                "Side": "Sell",
                "Open Price": "2350",
            },
        ],
        "mapping": {
            "symbol": "Instrument",
            "direction": "Side",
            "entry": "Open Price",
        },
        "ambiguous_fields": {},
        "unmapped_headers": [],
    }


def test_reads_all_csv_rows():
    content = (
        b"Instrument,Side\n"
        b"EURUSD,Buy\n"
        b"XAUUSD,Sell\n"
        b"GBPUSD,Buy\n"
    )

    result = read_csv_rows(
        "trades.csv",
        content,
    )

    assert result == {
        "delimiter": ",",
        "headers": ["Instrument", "Side"],
        "rows": [
            {
                "Instrument": "EURUSD",
                "Side": "Buy",
            },
            {
                "Instrument": "XAUUSD",
                "Side": "Sell",
            },
            {
                "Instrument": "GBPUSD",
                "Side": "Buy",
            },
        ],
    }


def test_detects_semicolon_delimiter():
    content = (
        b"Instrument;Side;Open Price\n"
        b"EURUSD;Buy;1.15\n"
    )

    result = build_csv_preview(
        "trades.csv",
        content,
    )

    assert result["delimiter"] == ";"
    assert result["row_count"] == 1


def test_handles_utf8_bom():
    content = (
        "\ufeffInstrument,Side\n"
        "EURUSD,Buy\n"
    ).encode("utf-8")

    result = build_csv_preview(
        "trades.csv",
        content,
    )

    assert result["headers"] == [
        "Instrument",
        "Side",
    ]


def test_counts_all_rows_but_returns_only_five():
    lines = ["Instrument,Side"]

    for index in range(10):
        lines.append(
            f"SYMBOL{index},Buy"
        )

    content = "\n".join(lines).encode("utf-8")

    result = build_csv_preview(
        "trades.csv",
        content,
    )

    assert result["row_count"] == 10
    assert len(result["sample_rows"]) == 5
    assert result["sample_rows"][0] == {
        "Instrument": "SYMBOL0",
        "Side": "Buy",
    }


def test_rejects_file_without_csv_extension():
    with pytest.raises(
        CsvPreviewError,
        match="Please upload a CSV file",
    ):
        build_csv_preview(
            "trades.txt",
            b"symbol,direction\nEURUSD,Buy",
        )


def test_rejects_missing_filename():
    with pytest.raises(
        CsvPreviewError,
        match="Please upload a CSV file",
    ):
        build_csv_preview(
            None,
            b"symbol,direction\nEURUSD,Buy",
        )


def test_rejects_empty_file():
    with pytest.raises(
        CsvPreviewError,
        match="CSV file is empty",
    ):
        build_csv_preview(
            "trades.csv",
            b"",
        )


def test_rejects_non_utf8_file():
    with pytest.raises(
        CsvPreviewError,
        match="CSV file must use UTF-8 encoding",
    ):
        build_csv_preview(
            "trades.csv",
            b"\xff\xfe\xfa",
        )


def test_rejects_undetectable_delimiter():
    with pytest.raises(
        CsvPreviewError,
        match="Could not detect the CSV delimiter",
    ):
        build_csv_preview(
            "trades.csv",
            b"symbol\nEURUSD\nXAUUSD",
        )


def test_rejects_empty_headers():
    with pytest.raises(
        CsvPreviewError,
        match="CSV file must contain non-empty headers",
    ):
        build_csv_preview(
            "trades.csv",
            b",\nEURUSD,long\n",
        )
