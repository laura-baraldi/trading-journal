from datetime import datetime
from typing import Literal


LONG_VALUES = {
    "long",
    "buy",
    "b",
}

SHORT_VALUES = {
    "short",
    "sell",
    "s",
}

CURRENCY_SYMBOLS = {
    "$",
    "€",
    "£",
    "¥",
}

DATE_FORMATS = (
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%d-%m-%Y %H:%M",
    "%m-%d-%Y %H:%M",
    "%Y.%m.%d %H:%M:%S",
)


class CsvNormalizationError(Exception):
    pass


def normalize_direction(
    value: str,
) -> Literal["long", "short"]:
    normalized = value.strip().casefold()

    if normalized in LONG_VALUES:
        return "long"

    if normalized in SHORT_VALUES:
        return "short"

    raise CsvNormalizationError(
        f"Unsupported direction value: {value}"
    )


def normalize_number(
    value: str,
    decimal_separator: Literal[".", ","],
) -> float:
    normalized = value.strip()

    if not normalized:
        raise CsvNormalizationError(
            "Numeric value cannot be empty"
        )

    for symbol in CURRENCY_SYMBOLS:
        normalized = normalized.replace(
            symbol,
            "",
        )

    normalized = normalized.replace(
        "\u00a0",
        "",
    )
    normalized = normalized.replace(" ", "")

    thousands_separator = (
        "," if decimal_separator == "." else "."
    )

    normalized = normalized.replace(
        thousands_separator,
        "",
    )
    normalized = normalized.replace(
        decimal_separator,
        ".",
    )

    try:
        return float(normalized)
    except ValueError as exc:
        raise CsvNormalizationError(
            f"Invalid numeric value: {value}"
        ) from exc


def normalize_datetime(
    value: str,
    date_format: str | None = None,
) -> datetime:
    normalized = value.strip()

    if not normalized:
        raise CsvNormalizationError(
            "Datetime value cannot be empty"
        )

    if date_format is not None:
        try:
            return datetime.strptime(
                normalized,
                date_format,
            )
        except ValueError as exc:
            raise CsvNormalizationError(
                f"Invalid datetime value: {value}"
            ) from exc

    try:
        return datetime.fromisoformat(
            normalized.replace("Z", "+00:00")
        )
    except ValueError:
        pass

    matches = []

    for supported_format in DATE_FORMATS:
        try:
            matches.append(
                datetime.strptime(
                    normalized,
                    supported_format,
                )
            )
        except ValueError:
            continue

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        raise CsvNormalizationError(
            f"Ambiguous datetime value: {value}"
        )

    raise CsvNormalizationError(
        f"Invalid datetime value: {value}"
    )


def detect_decimal_separator(
    rows: list[dict[str, str | None]],
    mapping: dict[str, str],
) -> Literal[".", ","]:
    numeric_fields = ("entry", "stop", "exit", "pnl")
    detected_separators = set()

    for field in numeric_fields:
        column = mapping.get(field)

        if column is None:
            continue

        for row in rows:
            value = row.get(column)

            if value is None:
                continue

            normalized = value.strip()

            if not normalized:
                continue

            comma_position = normalized.rfind(",")
            dot_position = normalized.rfind(".")

            if comma_position >= 0 and dot_position >= 0:
                detected_separators.add(
                    "," if comma_position > dot_position else "."
                )
            elif comma_position >= 0:
                detected_separators.add(",")
            elif dot_position >= 0:
                detected_separators.add(".")

    if len(detected_separators) > 1:
        raise CsvNormalizationError(
            "CSV contains inconsistent decimal separators"
        )

    if detected_separators:
        return detected_separators.pop()

    return "."


def detect_date_format(
    rows: list[dict[str, str | None]],
    mapping: dict[str, str],
) -> str | None:
    values = []

    for field in ("entry_datetime", "exit_datetime"):
        column = mapping.get(field)

        if column is None:
            continue

        for row in rows:
            value = row.get(column)

            if value is not None and value.strip():
                values.append(value.strip())

    try:
        for value in values:
            normalize_datetime(value)

        return None
    except CsvNormalizationError:
        pass

    matching_formats = []

    for date_format in DATE_FORMATS:
        try:
            for value in values:
                normalize_datetime(value, date_format)

            matching_formats.append(date_format)
        except CsvNormalizationError:
            continue

    if len(matching_formats) == 1:
        return matching_formats[0]

    if len(matching_formats) > 1:
        raise CsvNormalizationError(
            "CSV contains an ambiguous datetime format"
        )

    raise CsvNormalizationError(
        "Could not detect the CSV datetime format"
    )
