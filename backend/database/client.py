import os

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)


class DatabaseError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


def get_authenticated_client(token: str):
    client = create_client(supabase_url, supabase_key)
    client.postgrest.auth(token)
    return client


def execute_query(query):
    try:
        return query.execute()
    except Exception as error:
        raise DatabaseError("Database request failed") from error
