import csv
import io

from imports.mapping import suggest_column_mapping


class CsvPreviewError(Exception):
    pass


def _create_csv_reader(
    filename: str | None,
    content: bytes,
):
    if not filename or not filename.lower().endswith(".csv"):
        raise CsvPreviewError("Please upload a CSV file")

    if not content:
        raise CsvPreviewError("CSV file is empty")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvPreviewError(
            "CSV file must use UTF-8 encoding"
        ) from exc

    try:
        dialect = csv.Sniffer().sniff(
            text[:4096],
            delimiters=",;\t",
        )
    except csv.Error as exc:
        raise CsvPreviewError(
            "Could not detect the CSV delimiter"
        ) from exc

    reader = csv.DictReader(
        io.StringIO(text),
        dialect=dialect,
    )
    headers = reader.fieldnames

    if not headers or any(
        not header.strip()
        for header in headers
    ):
        raise CsvPreviewError(
            "CSV file must contain non-empty headers"
        )

    return reader, dialect.delimiter, headers


def read_csv_rows(
    filename: str | None,
    content: bytes,
):
    reader, delimiter, headers = _create_csv_reader(
        filename,
        content,
    )

    return {
        "delimiter": delimiter,
        "headers": headers,
        "rows": list(reader),
    }


def build_csv_preview(
    filename: str | None,
    content: bytes,
):
    reader, delimiter, headers = _create_csv_reader(
        filename,
        content,
    )
    mapping_result = suggest_column_mapping(
        headers
    )

    row_count = 0
    sample_rows = []

    for row in reader:
        row_count += 1

        if len(sample_rows) < 5:
            sample_rows.append(row)

    return {
        "filename": filename,
        "delimiter": delimiter,
        "headers": headers,
        "row_count": row_count,
        "sample_rows": sample_rows,
        "mapping": mapping_result["mapping"],
        "ambiguous_fields": mapping_result[
            "ambiguous_fields"
        ],
        "unmapped_headers": mapping_result[
            "unmapped_headers"
        ],
    }
