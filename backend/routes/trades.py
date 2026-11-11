from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from auth import get_current_user
from calculations import calculate_r
from database import (
    ResourceNotFoundError,
    account_belongs_to_user,
    delete_trade_from_supabase,
    load_trades_from_supabase,
    save_trade_to_supabase,
    update_trade_in_supabase,
)
from rate_limit import limiter
from schemas.trades import PaginatedTradesResponse, TradeCreate, TradeResponse, TradeUpdate


router = APIRouter()


@router.get("/trades", response_model=PaginatedTradesResponse)
@limiter.limit("60/minute")
def get_trades(
    request: Request,
    account_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
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

    trades, total = load_trades_from_supabase(
        user.id,
        token,
        account_id,
        page,
        page_size,
        date_from,
        date_to,
    )

    return {
        "items": trades,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/trades", response_model=TradeResponse)
@limiter.limit("60/minute")
def create_trade(
    request: Request,
    trade: TradeCreate,
    auth_data=Depends(get_current_user),
):
    user = auth_data["user"]
    token = auth_data["token"]

    if not account_belongs_to_user(
        trade.account_id,
        user.id,
        token,
    ):
        raise ResourceNotFoundError("Account not found")

    result = None

    if trade.stop is not None:
        result = round(
            calculate_r(
                trade.direction,
                trade.entry,
                trade.stop,
                trade.exit,
            ),
            2,
        )

    trade_data = {
        "account_id": trade.account_id,
        "symbol": trade.symbol,
        "direction": trade.direction,
        "entry": trade.entry,
        "stop": trade.stop,
        "exit": trade.exit,
        "result": result,
        "pnl": trade.pnl,
        "entry_datetime": trade.entry_datetime,
        "exit_datetime": trade.exit_datetime,
    }

    return save_trade_to_supabase(
        trade_data,
        user.id,
        token,
    )


@router.delete("/trades/{trade_id}")
@limiter.limit("60/minute")
def delete_trade(
    request: Request,
    trade_id: int,
    auth_data=Depends(get_current_user),
):
    user = auth_data["user"]
    token = auth_data["token"]

    return delete_trade_from_supabase(
        trade_id,
        user.id,
        token,
    )


@router.patch("/trades/{trade_id}", response_model=TradeResponse)
@limiter.limit("60/minute")
def update_trade(
    request: Request,
    trade_id: int,
    trade: TradeUpdate,
    auth_data=Depends(get_current_user),
):
    user = auth_data["user"]
    token = auth_data["token"]

    result = None

    if trade.stop is not None:
        result = round(
            calculate_r(
                trade.direction,
                trade.entry,
                trade.stop,
                trade.exit,
            ),
            2,
        )

    updated_trade = {
        "symbol": trade.symbol,
        "direction": trade.direction,
        "entry": trade.entry,
        "stop": trade.stop,
        "exit": trade.exit,
        "result": result,
        "pnl": trade.pnl,
        "entry_datetime": trade.entry_datetime,
        "exit_datetime": trade.exit_datetime,
    }

    return update_trade_in_supabase(
        trade_id,
        updated_trade,
        user.id,
        token,
    )
