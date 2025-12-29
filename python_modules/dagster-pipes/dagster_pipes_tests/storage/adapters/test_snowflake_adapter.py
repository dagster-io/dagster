"""Tests for Snowflake storage adapter."""

import pytest
from dagster_pipes.storage import StorageAddress
from dagster_pipes.storage.adapters.ibis.snowflake import SnowflakeStorageAdapter

from dagster_pipes_tests.storage.adapters.base import IbisTableAdapterTestBase


class TestSnowflakeStorageAdapter(IbisTableAdapterTestBase):
    """Tests for Snowflake storage adapter.

    Only tests address matching logic - no database connection needed.
    Inherits base address tests from IbisTableAdapterTestBase.
    """

    storage_type = "snowflake"
    valid_addresses = ["my_table", "my_schema.my_table", "my_db.my_schema.my_table"]

    @pytest.fixture
    def adapter(self):
        # No mocking needed - just instantiate without connecting
        # Connection is lazy (only when get_backend() is called)
        return SnowflakeStorageAdapter(
            user="test_user",
            account="test_org-test_account",
            database="my_db",
        )

    def test_matches_address_with_database_filter(self):
        """Test adapter filters by configured database in fully-qualified addresses."""
        adapter = SnowflakeStorageAdapter(
            user="test_user",
            account="org-acct",
            database="my_db",
        )

        # Should match addresses in configured database
        assert adapter.matches_address(StorageAddress("snowflake", "my_db.my_schema.my_table"))

        # Should NOT match addresses in other databases
        assert not adapter.matches_address(StorageAddress("snowflake", "other_db.my_schema.table"))

        # Should match schema.table (no database in address)
        assert adapter.matches_address(StorageAddress("snowflake", "any_schema.table"))

        # Should match bare table names
        assert adapter.matches_address(StorageAddress("snowflake", "my_table"))

    def test_matches_address_with_schema_filter(self):
        """Test adapter filters by configured schema in schema.table addresses."""
        adapter = SnowflakeStorageAdapter(
            user="test_user",
            account="org-acct",
            database="my_db",
            schema="my_schema",
        )

        # Should match addresses in configured schema
        assert adapter.matches_address(StorageAddress("snowflake", "my_schema.my_table"))

        # Should NOT match addresses in other schemas (for schema.table format)
        assert not adapter.matches_address(StorageAddress("snowflake", "other_schema.table"))

        # Should still match bare table names
        assert adapter.matches_address(StorageAddress("snowflake", "my_table"))

        # Database filtering still applies for db.schema.table
        assert adapter.matches_address(StorageAddress("snowflake", "my_db.any_schema.table"))
        assert not adapter.matches_address(StorageAddress("snowflake", "other_db.any_schema.table"))
