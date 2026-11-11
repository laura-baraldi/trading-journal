from typing import Literal

from imports.normalization import (
    CsvNormalizationError,
    normalize_datetime,
    normalize_direction,
    normalize_number,
)


class CsvRowError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def _get_mapped_value(
    row: dict[str, str | None],
    mapping: dict[str, str],
    field: str,
    required: bool = True,
) -> str | None:
    column = mapping.get(field)

    if column is None:
        if required:
            raise CsvRowError(
                field,
                "Required column is not mapped",
            )

        return None

    if column not in row:
        raise CsvRowError(
            field,
            f"Mapped column does not exist: {column}",
        )

    value = row[column]

    if value is None or not value.strip():
        if required:
            raise CsvRowError(
                field,
                "Required value is missing",
            )

        return None

    return value.strip()


def _normalize_field(
    field: str,
    normalizer,
    *args,
):
    try:
        return normalizer(*args)
    except CsvNormalizationError as exc:
        raise CsvRowError(
            field,
            str(exc),
        ) from exc


def normalize_trade_row(
    row: dict[str, str | None],
    mapping: dict[str, str],
    decimal_separator: Literal[".", ","],
    date_format: str | None = None,
):
    symbol = _get_mapped_value(
        row,
        mapping,
        "symbol",
    )
    direction_value = _get_mapped_value(
        row,
        mapping,
        "direction",
    )
    entry_value = _get_mapped_value(
        row,
        mapping,
        "entry",
    )
    stop_value = _get_mapped_value(
        row,
        mapping,
        "stop",
        required=False,
    )
    exit_value = _get_mapped_value(
        row,
        mapping,
        "exit",
    )
    pnl_value = _get_mapped_value(
        row,
        mapping,
        "pnl",
    )
    entry_datetime_value = _get_mapped_value(
        row,
        mapping,
        "entry_datetime",
    )
    exit_datetime_value = _get_mapped_value(
        row,
        mapping,
        "exit_datetime",
    )

    direction = _normalize_field(
        "direction",
        normalize_direction,
        direction_value,
    )
    entry = _normalize_field(
        "entry",
        normalize_number,
        entry_value,
        decimal_separator,
    )
    exit_price = _normalize_field(
        "exit",
        normalize_number,
        exit_value,
        decimal_separator,
    )
    pnl = _normalize_field(
        "pnl",
        normalize_number,
        pnl_value,
        decimal_separator,
    )
    entry_datetime = _normalize_field(
        "entry_datetime",
        normalize_datetime,
        entry_datetime_value,
        date_format,
    )
    exit_datetime = _normalize_field(
        "exit_datetime",
        normalize_datetime,
        exit_datetime_value,
        date_format,
    )

    stop = None

    if stop_value is not None:
        stop = _normalize_field(
            "stop",
            normalize_number,
            stop_value,
            decimal_separator,
        )

    if exit_datetime < entry_datetime:
        raise CsvRowError(
            "exit_datetime",
            "Exit datetime cannot be before entry datetime",
        )

    if stop is not None and stop == entry:
        raise CsvRowError(
            "stop",
            "Entry and stop cannot be the same",
        )

    return {
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "stop": stop,
        "exit": exit_price,
        "pnl": pnl,
        "entry_datetime": entry_datetime,
        "exit_datetime": exit_datetime,
    }
