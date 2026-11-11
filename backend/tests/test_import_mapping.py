import pytest

from imports.mapping import (
    normalize_header,
    suggest_column_mapping,
)


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("Open Price", "open price"),
        ("OPEN PRICE", "open price"),
        ("open_price", "open price"),
        ("open-price", "open price"),
        ("  open   price  ", "open price"),
        ("P/L", "p l"),
    ],
)
def test_normalizes_header(
    header,
    expected,
):
    assert normalize_header(header) == expected


def test_suggests_common_column_mapping():
    headers = [
        "Instrument",
        "Side",
        "Open Price",
        "Stop Loss",
        "Close Price",
        "Net Profit",
        "Open Time",
        "Close Time",
        "Commission",
    ]

    result = suggest_column_mapping(headers)

    assert result == {
        "mapping": {
            "symbol": "Instrument",
            "direction": "Side",
            "entry": "Open Price",
            "stop": "Stop Loss",
            "exit": "Close Price",
            "pnl": "Net Profit",
            "entry_datetime": "Open Time",
            "exit_datetime": "Close Time",
        },
        "ambiguous_fields": {},
        "unmapped_headers": [
            "Commission",
        ],
    }


def test_recognizes_app_style_headers():
    headers = [
        "symbol",
        "direction",
        "entry",
        "stop",
        "exit",
        "pnl",
        "entry_datetime",
        "exit_datetime",
    ]

    result = suggest_column_mapping(headers)

    assert result["mapping"] == {
        "symbol": "symbol",
        "direction": "direction",
        "entry": "entry",
        "stop": "stop",
        "exit": "exit",
        "pnl": "pnl",
        "entry_datetime": "entry_datetime",
        "exit_datetime": "exit_datetime",
    }

    assert result["ambiguous_fields"] == {}
    assert result["unmapped_headers"] == []


def test_reports_ambiguous_fields():
    headers = [
        "Symbol",
        "Instrument",
        "Side",
    ]

    result = suggest_column_mapping(headers)

    assert result == {
        "mapping": {
            "direction": "Side",
        },
        "ambiguous_fields": {
            "symbol": [
                "Symbol",
                "Instrument",
            ],
        },
        "unmapped_headers": [
            "Symbol",
            "Instrument",
        ],
    }


def test_returns_empty_result_for_unknown_headers():
    headers = [
        "Ticket",
        "Commission",
        "Comment",
    ]

    result = suggest_column_mapping(headers)

    assert result == {
        "mapping": {},
        "ambiguous_fields": {},
        "unmapped_headers": [
            "Ticket",
            "Commission",
            "Comment",
        ],
    }


def test_handles_empty_header_list():
    result = suggest_column_mapping([])

    assert result == {
        "mapping": {},
        "ambiguous_fields": {},
        "unmapped_headers": [],
    }
