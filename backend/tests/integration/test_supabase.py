import os

from dotenv import load_dotenv
from supabase import create_client

from database import load_trades_from_supabase


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

USER_A_EMAIL = os.getenv("RLS_USER_A_EMAIL")
USER_A_PASSWORD = os.getenv("RLS_USER_A_PASSWORD")


def get_test_user():
    client = create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
    )

    auth_response = client.auth.sign_in_with_password(
        {
            "email": USER_A_EMAIL,
            "password": USER_A_PASSWORD,
        }
    )

    return (
        auth_response.user.id,
        auth_response.session.access_token,
    )


def test_load_trades_from_supabase():
    user_id, token = get_test_user()

    trades, total = load_trades_from_supabase(
        user_id,
        token,
    )

    assert isinstance(trades, list)
    assert isinstance(total, int)
    assert len(trades) <= 20
    assert total >= len(trades)
