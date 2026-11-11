import pytest

from unittest.mock import MagicMock, patch

from database.client import (
    DatabaseError,
    execute_query,
    get_authenticated_client,
    supabase_key,
    supabase_url,
)


def test_get_authenticated_client():
    mock_client = MagicMock()

    with patch("database.client.create_client", return_value=mock_client) as mock_create_client:
        client = get_authenticated_client("fake-token")

    mock_create_client.assert_called_once_with(supabase_url, supabase_key)
    mock_client.postgrest.auth.assert_called_once_with("fake-token")
    assert client == mock_client


def test_execute_query_raises_database_error():
    mock_query = MagicMock()
    mock_query.execute.side_effect = Exception("Supabase failed")

    with pytest.raises(DatabaseError, match="Database request failed"):
        execute_query(mock_query)
