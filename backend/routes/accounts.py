from fastapi import APIRouter, Depends, Request

from auth import get_current_user
from database import (
    delete_account_from_supabase,
    load_accounts_from_supabase,
    save_account_to_supabase,
    update_account_in_supabase,
)
from rate_limit import limiter
from schemas.accounts import AccountCreate, AccountUpdate


router = APIRouter()


@router.get("/accounts")
@limiter.limit("60/minute")
def get_accounts(
    request: Request,
    auth_data=Depends(get_current_user),
):
    user = auth_data["user"]
    token = auth_data["token"]

    return load_accounts_from_supabase(user.id, token)


@router.post("/accounts")
@limiter.limit("60/minute")
def create_account(
    request: Request,
    account: AccountCreate,
    auth_data=Depends(get_current_user),
):
    user = auth_data["user"]
    token = auth_data["token"]

    account_data = {
        "name": account.name,
        "starting_balance": account.starting_balance,
        "currency": account.currency,
        "broker": account.broker,
        "account_type": account.account_type,
    }

    return save_account_to_supabase(
        account_data,
        user.id,
        token,
    )


@router.patch("/accounts/{account_id}")
@limiter.limit("60/minute")
def update_account(
    request: Request,
    account_id: int,
    account: AccountUpdate,
    auth_data=Depends(get_current_user),
):
    user = auth_data["user"]
    token = auth_data["token"]

    account_data = {
        "name": account.name,
        "starting_balance": account.starting_balance,
        "currency": account.currency,
        "broker": account.broker,
        "account_type": account.account_type,
    }

    return update_account_in_supabase(
        account_id,
        account_data,
        user.id,
        token,
    )


@router.delete("/accounts/{account_id}")
@limiter.limit("60/minute")
def delete_account(
    request: Request,
    account_id: int,
    auth_data=Depends(get_current_user),
):
    user = auth_data["user"]
    token = auth_data["token"]

    return delete_account_from_supabase(
        account_id,
        user.id,
        token,
    )
