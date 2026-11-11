from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from auth import get_current_user
from calculations import calculate_calendar_statistics, calculate_dashboard_statistics
from database import (
    load_calendar_metrics_batch_from_supabase,
    load_trade_metrics_batch_from_supabase,
)
from rate_limit import limiter


router = APIRouter()

STATISTICS_BATCH_SIZE = 1000
CALENDAR_BATCH_SIZE = 1000


def iter_trade_metrics(
    user_id: str,
    token: str,
    account_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
):
    offset = 0

    while True:
        batch = load_trade_metrics_batch_from_supabase(
            user_id,
            token,
            account_id,
            offset=offset,
            batch_size=STATISTICS_BATCH_SIZE,
            date_from=date_from,
            date_to=date_to,
        )

        yield from batch

        if len(batch) < STATISTICS_BATCH_SIZE:
            break

        offset += STATISTICS_BATCH_SIZE


@router.get("/statistics")
@limiter.limit("60/minute")
def get_statistics(
    request: Request,
    account_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    auth_data=Depends(get_current_user),
):
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from cannot be after date_to",
        )

    user = auth_data["user"]
    token = auth_data["token"]

    metrics = iter_trade_metrics(
        user.id,
        token,
        account_id,
        date_from,
        date_to,
    )

    return calculate_dashboard_statistics(metrics)


def iter_calendar_metrics(
    user_id: str,
    token: str,
    account_id: int,
    month_start: date,
    next_month_start: date,
):
    offset = 0

    while True:
        batch = load_calendar_metrics_batch_from_supabase(
            user_id,
            token,
            account_id,
            month_start,
            next_month_start,
            offset=offset,
            batch_size=CALENDAR_BATCH_SIZE,
        )

        yield from batch

        if len(batch) < CALENDAR_BATCH_SIZE:
            break

        offset += CALENDAR_BATCH_SIZE


@router.get("/calendar")
@limiter.limit("60/minute")
def get_calendar(
    request: Request,
    account_id: int,
    year: int = Query(ge=1, le=9998),
    month: int = Query(ge=1, le=12),
    auth_data=Depends(get_current_user),
):
    month_start = date(year, month, 1)

    if month == 12:
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month + 1, 1)

    user = auth_data["user"]
    token = auth_data["token"]

    metrics = iter_calendar_metrics(
        user.id,
        token,
        account_id,
        month_start,
        next_month_start,
    )

    return calculate_calendar_statistics(metrics)
