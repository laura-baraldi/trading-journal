COLUMN_ALIASES = {
    "symbol": {
        "symbol",
        "instrument",
        "market",
        "ticker",
    },
    "direction": {
        "direction",
        "side",
        "type",
        "action",
    },
    "entry": {
        "entry",
        "entry price",
        "open price",
        "price open",
    },
    "stop": {
        "stop",
        "stop loss",
        "sl",
        "initial stop",
        "initial stop loss",
    },
    "exit": {
        "exit",
        "exit price",
        "close price",
        "price close",
    },
    "pnl": {
        "pnl",
        "p l",
        "profit",
        "net profit",
        "profit loss",
        "realized pnl",
    },
    "entry_datetime": {
        "entry datetime",
        "entry time",
        "open datetime",
        "open time",
        "date opened",
    },
    "exit_datetime": {
        "exit datetime",
        "exit time",
        "close datetime",
        "close time",
        "date closed",
    },
}


def normalize_header(header: str) -> str:
    normalized = header.casefold()

    for character in ("_", "-", "/"):
        normalized = normalized.replace(
            character,
            " ",
        )

    return " ".join(normalized.split())


def suggest_column_mapping(
    headers: list[str],
):
    mapping = {}
    ambiguous_fields = {}
    mapped_headers = set()

    for field, aliases in COLUMN_ALIASES.items():
        matches = [
            header
            for header in headers
            if normalize_header(header) in aliases
        ]

        if len(matches) == 1:
            mapping[field] = matches[0]
            mapped_headers.add(matches[0])
        elif len(matches) > 1:
            ambiguous_fields[field] = matches

    unmapped_headers = [
        header
        for header in headers
        if header not in mapped_headers
    ]

    return {
        "mapping": mapping,
        "ambiguous_fields": ambiguous_fields,
        "unmapped_headers": unmapped_headers,
    }
