import json
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from auth import get_current_user
from calculations import calculate_r
from database import ResourceNotFoundError, account_belongs_to_user, save_trades_to_supabase
from imports.mapping import suggest_column_mapping
from imports.normalization import CsvNormalizationError, detect_date_format, detect_decimal_separator
from imports.preview import CsvPreviewError, build_csv_preview, read_csv_rows
from imports.validation import validate_trade_rows
from rate_limit import limiter


router = APIRouter()

REQUIRED_FIELDS = {
    "symbol",
    "direction",
    "entry",
    "exit",
    "pnl",
    "entry_datetime",
    "exit_datetime",
}

MAX_CSV_FILE_SIZE = 5 * 1024 * 1024
INVALID_MAPPING_MESSAGE = "Mapping must be a JSON object containing string keys and values"


async def _read_csv_upload(file: UploadFile) -> bytes:
    content = await file.read(MAX_CSV_FILE_SIZE + 1)

    if len(content) > MAX_CSV_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="CSV file must not exceed 5 MB",
        )

    return content


def _parse_column_mapping(mapping: str) -> dict[str, str]:
    try:
        parsed_mapping = json.loads(mapping)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=INVALID_MAPPING_MESSAGE,
        ) from exc

    if not isinstance(parsed_mapping, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in parsed_mapping.items()
    ):
        raise HTTPException(
            status_code=400,
            detail=INVALID_MAPPING_MESSAGE,
        )

    return parsed_mapping


@router.post("/imports/preview")
@limiter.limit("60/minute")
async def preview_csv_import(
    request: Request,
    file: UploadFile = File(...),
    _auth_data=Depends(get_current_user),
):
    content = await _read_csv_upload(file)

    try:
        return build_csv_preview(file.filename, content)
    except CsvPreviewError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/imports/validate")
@limiter.limit("60/minute")
async def validate_csv_import(
    request: Request,
    file: UploadFile = File(...),
    mapping: str = Form(...),
    decimal_separator: Literal[".", ","] = Form(...),
    date_format: str | None = Form(None),
    _auth_data=Depends(get_current_user),
):
    parsed_mapping = _parse_column_mapping(mapping)
    content = await _read_csv_upload(file)

    try:
        csv_data = read_csv_rows(file.filename, content)
    except CsvPreviewError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return validate_trade_rows(
        csv_data["rows"],
        parsed_mapping,
        decimal_separator,
        date_format or None,
    )


@router.post("/imports")
@limiter.limit("60/minute")
async def import_csv(
    request: Request,
    file: UploadFile = File(...),
    account_id: int = Form(...),
    auth_data=Depends(get_current_user),
):
    user = auth_data["user"]
    token = auth_data["token"]

    if not account_belongs_to_user(account_id, user.id, token):
        raise ResourceNotFoundError("Account not found")

    content = await _read_csv_upload(file)

    try:
        csv_data = read_csv_rows(file.filename, content)
    except CsvPreviewError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if not csv_data["rows"]:
        raise HTTPException(
            status_code=400,
            detail="CSV file contains no trades",
        )

    mapping_result = suggest_column_mapping(csv_data["headers"])
    parsed_mapping = mapping_result["mapping"]
    missing_fields = sorted(REQUIRED_FIELDS - parsed_mapping.keys())
    ambiguous_fields = mapping_result["ambiguous_fields"]

    if missing_fields or ambiguous_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "CSV columns could not be mapped automatically",
                "missing_fields": missing_fields,
                "ambiguous_fields": ambiguous_fields,
            },
        )

    try:
        decimal_separator = detect_decimal_separator(
            csv_data["rows"],
            parsed_mapping,
        )
        date_format = detect_date_format(
            csv_data["rows"],
            parsed_mapping,
        )
    except CsvNormalizationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    validation = validate_trade_rows(
        csv_data["rows"],
        parsed_mapping,
        decimal_separator,
        date_format,
    )

    if validation["invalid_count"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "CSV contains invalid rows",
                "errors": validation["errors"],
            },
        )

    trades = []

    for valid_row in validation["valid_rows"]:
        trade = valid_row["trade"]
        result = None

        if trade["stop"] is not None:
            result = round(
                calculate_r(
                    trade["direction"],
                    trade["entry"],
                    trade["stop"],
                    trade["exit"],
                ),
                2,
            )

        trades.append({
            **trade,
            "account_id": account_id,
            "result": result,
        })

    saved_trades = save_trades_to_supabase(
        trades,
        user.id,
        token,
    )

    return {"imported_count": len(saved_trades)}
