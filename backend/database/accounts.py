from database.client import (
    ResourceNotFoundError,
    execute_query,
    get_authenticated_client,
)


def load_accounts_from_supabase(user_id: str, token: str):
    client = get_authenticated_client(token)

    response = execute_query(
        client
        .table("accounts")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
    )

    return response.data


def account_belongs_to_user(account_id: int, user_id: str, token: str):
    client = get_authenticated_client(token)

    response = execute_query(
        client
        .table("accounts")
        .select("id")
        .eq("id", account_id)
        .eq("user_id", user_id)
    )

    return bool(response.data)


def save_account_to_supabase(account, user_id: str, token: str):
    client = get_authenticated_client(token)

    data = {
        "user_id": user_id,
        "name": account["name"],
        "starting_balance": account["starting_balance"],
        "currency": account["currency"],
        "broker": account.get("broker"),
        "account_type": account.get("account_type"),
    }

    response = execute_query(
        client
        .table("accounts")
        .insert(data)
    )

    return response.data


def update_account_in_supabase(
    account_id: int,
    account,
    user_id: str,
    token: str,
):
    client = get_authenticated_client(token)

    data = {
        "name": account["name"],
        "starting_balance": account["starting_balance"],
        "currency": account["currency"],
        "broker": account.get("broker"),
        "account_type": account.get("account_type"),
    }

    response = execute_query(
        client
        .table("accounts")
        .update(data)
        .eq("id", account_id)
        .eq("user_id", user_id)
    )

    if not response.data:
        raise ResourceNotFoundError("Account not found")

    return response.data


def delete_account_from_supabase(
    account_id: int,
    user_id: str,
    token: str,
):
    client = get_authenticated_client(token)

    response = execute_query(
        client
        .table("accounts")
        .delete()
        .eq("id", account_id)
        .eq("user_id", user_id)
    )

    if not response.data:
        raise ResourceNotFoundError("Account not found")

    return response.data
