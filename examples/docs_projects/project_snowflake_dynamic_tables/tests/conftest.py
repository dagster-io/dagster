"""Shared fixtures for snowflake_dynamic_tables tests."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from dagster_snowflake import SnowflakeResource


@pytest.fixture
def mock_cursor():
    return MagicMock()


@pytest.fixture
def mock_conn(mock_cursor):
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    return conn


@pytest.fixture
def snowflake_resource(mock_conn):
    """Real SnowflakeResource with get_connection patched at class level.

    Passes Dagster's isinstance(resource, SnowflakeResource) type check during
    asset direct invocation and evaluate_automation_conditions. The class-level
    patch ensures the mock connection is used regardless of which instance is
    created during Dagster's resource initialization.
    """
    resource = SnowflakeResource(
        account="test.snowflakecomputing.com",
        user="test_user",
        password="dummy_password",
    )

    @contextmanager
    def _mock_get_connection(self):
        yield mock_conn

    with patch.object(SnowflakeResource, "get_connection", _mock_get_connection):
        yield resource


@pytest.fixture
def mock_snowflake_resource(mock_conn):
    """Simple resource mock for sensor tests.

    Sensor invocation with keyword args does NOT perform Dagster type validation,
    so any object with a get_connection() context manager works. This avoids the
    context-manager setup issues with MagicMock magic methods.
    """

    class _MockSnowflakeResource:
        @contextmanager
        def get_connection(self):
            yield mock_conn

    return _MockSnowflakeResource()
