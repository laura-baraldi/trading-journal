from typing import Literal

from imports.rows import (
    CsvRowError,
    normalize_trade_row,
)


def validate_trade_rows(
    rows: list[dict[str, str | None]],
    mapping: dict[str, str],
    decimal_separator: Literal[".", ","],
    date_format: str | None = None,
):
    valid_rows = []
    errors = []

    # Row 1 contains the CSV headers.
    for row_number, row in enumerate(
        rows,
        start=2,
    ):
        try:
            trade = normalize_trade_row(
                row,
                mapping,
                decimal_separator,
                date_format,
            )
        except CsvRowError as exc:
            errors.append(
                {
                    "row": row_number,
                    "field": exc.field,
                    "message": exc.message,
                }
            )
            continue

        valid_rows.append(
            {
                "row": row_number,
                "trade": trade,
            }
        )

    return {
        "total_rows": len(rows),
        "valid_count": len(valid_rows),
        "invalid_count": len(errors),
        "valid_rows": valid_rows,
        "errors": errors,
    }
