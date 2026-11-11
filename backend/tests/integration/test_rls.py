import os

import pytest
from dotenv import load_dotenv
from supabase import create_client


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

USER_A_EMAIL = os.getenv("RLS_USER_A_EMAIL")
USER_A_PASSWORD = os.getenv("RLS_USER_A_PASSWORD")

USER_B_EMAIL = os.getenv("RLS_USER_B_EMAIL")
USER_B_PASSWORD = os.getenv("RLS_USER_B_PASSWORD")


def login_test_user(email, password):
    client = create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
    )

    auth_response = client.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    token = auth_response.session.access_token
    user_id = auth_response.user.id

    client.postgrest.auth(token)

    return client, user_id


def test_rls_blocks_other_users():
    client_a, user_a_id = login_test_user(
        USER_A_EMAIL,
        USER_A_PASSWORD,
    )

    client_b, user_b_id = login_test_user(
        USER_B_EMAIL,
        USER_B_PASSWORD,
    )

    trade_id = None
    account_id = None

    try:
        # Create a temporary account for User A.
        account_response = (
            client_a
            .table("accounts")
            .insert(
                {
                    "user_id": user_a_id,
                    "name": "RLS TEST ACCOUNT",
                    "starting_balance": 100000,
                    "currency": "USD",
                    "broker": None,
                    "account_type": "test",
                }
            )
            .execute()
        )

        assert len(account_response.data) == 1

        account_id = account_response.data[0]["id"]

        # User B must NOT be able to create a trade
        # inside User A's account.
        with pytest.raises(Exception):
            (
                client_b
                .table("trades")
                .insert(
                    {
                        "account_id": account_id,
                        "symbol": "RLS_CROSS_ACCOUNT",
                        "direction": "long",
                        "entry": 100,
                        "stop": 90,
                        "exit": 120,
                        "result": 2,
                        "pnl": 400,
                        "entry_datetime": "2026-08-12T10:00:00",
                        "exit_datetime": "2026-08-12T11:00:00",
                        "user_id": user_b_id,
                    }
                )
                .execute()
            )

        # User A creates a trade belonging to User A.
        insert_response = (
            client_a
            .table("trades")
            .insert(
                {
                    "account_id": account_id,
                    "symbol": "RLS_TEST",
                    "direction": "long",
                    "entry": 100,
                    "stop": 90,
                    "exit": 120,
                    "result": 2,
                    "pnl": 400,
                    "entry_datetime": "2026-08-12T10:00:00",
                    "exit_datetime": "2026-08-12T11:00:00",
                    "user_id": user_a_id,
                }
            )
            .execute()
        )

        assert len(insert_response.data) == 1

        trade_id = insert_response.data[0]["id"]

        # User A can see their own trade.
        owner_response = (
            client_a
            .table("trades")
            .select("*")
            .eq("id", trade_id)
            .execute()
        )

        assert len(owner_response.data) == 1

        # User B must NOT be able to read User A's trade.
        read_response = (
            client_b
            .table("trades")
            .select("*")
            .eq("id", trade_id)
            .execute()
        )

        assert read_response.data == []

        # User B must NOT be able to update User A's trade.
        update_response = (
            client_b
            .table("trades")
            .update(
                {
                    "symbol": "HACKED",
                }
            )
            .eq("id", trade_id)
            .execute()
        )

        assert update_response.data == []

        # User B must NOT be able to delete User A's trade.
        delete_response = (
            client_b
            .table("trades")
            .delete()
            .eq("id", trade_id)
            .execute()
        )

        assert delete_response.data == []

        # Confirm User A's trade still exists unchanged.
        final_response = (
            client_a
            .table("trades")
            .select("*")
            .eq("id", trade_id)
            .execute()
        )

        assert len(final_response.data) == 1
        assert final_response.data[0]["symbol"] == "RLS_TEST"

    finally:
        # Delete the trade first because the account
        # cannot be deleted while a trade references it.
        if trade_id is not None:
            (
                client_a
                .table("trades")
                .delete()
                .eq("id", trade_id)
                .execute()
            )

        if account_id is not None:
            (
                client_a
                .table("accounts")
                .delete()
                .eq("id", account_id)
                .execute()
            )
