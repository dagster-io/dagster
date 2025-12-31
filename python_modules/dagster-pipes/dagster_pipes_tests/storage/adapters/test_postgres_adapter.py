"""Tests for PostgreSQL storage adapter."""

import pytest
from dagster_pipes.storage import StorageAddress
from dagster_pipes.storage.adapters.ibis.postgres import PostgresStorageAdapter

from dagster_pipes_tests.storage.adapters.base import IbisTableAdapterTestBase


class TestPostgresStorageAdapter(IbisTableAdapterTestBase):
    """Tests for PostgreSQL storage adapter.

    Only tests address matching logic - no database connection needed.
    Inherits base address tests from IbisTableAdapterTestBase.
    """

    storage_type = "postgres"

    @pytest.fixture
    def adapter(self):
        return PostgresStorageAdapter(
            host="localhost",
            port=5432,
            user="test_user",
            database="test_db",
        )

    def test_matches_address_with_schema_filter(self):
        """Test schema-configured adapter only matches that schema."""
        adapter = PostgresStorageAdapter(
            host="localhost",
            port=5432,
            user="test_user",
            database="test_db",
            schema="my_schema",
        )

        # Should match addresses in configured schema
        assert adapter.matches_address(StorageAddress("postgres", "my_schema.my_table"))

        # Should NOT match addresses in other schemas
        assert not adapter.matches_address(StorageAddress("postgres", "other_schema.table"))

        # Should match bare table names (no schema specified in address)
        assert adapter.matches_address(StorageAddress("postgres", "my_table"))

    def test_matches_address_without_schema_filter(self):
        """Test adapter without schema configured matches any schema."""
        adapter = PostgresStorageAdapter(
            host="localhost",
            port=5432,
            user="test_user",
            database="test_db",
            # No schema configured
        )

        # Should match any schema.table address
        assert adapter.matches_address(StorageAddress("postgres", "any_schema.my_table"))
        assert adapter.matches_address(StorageAddress("postgres", "other_schema.table"))

        # Should match bare table names
        assert adapter.matches_address(StorageAddress("postgres", "my_table"))
