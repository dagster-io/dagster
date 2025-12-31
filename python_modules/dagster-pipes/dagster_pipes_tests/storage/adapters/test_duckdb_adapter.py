"""Tests for DuckDB storage adapter."""

import pytest
from dagster_pipes.storage.adapters.ibis.duckdb import DuckDBStorageAdapter

from dagster_pipes_tests.storage.adapters.base import IbisTableAdapterTestBase, RoundtripTestsMixin


class TestDuckDBStorageAdapter(IbisTableAdapterTestBase, RoundtripTestsMixin):
    """Tests for DuckDB storage adapter.

    Uses real :memory: database for full roundtrip testing.
    Inherits address tests from base class and Ibis integration tests from mixin.
    """

    storage_type = "duckdb"

    @pytest.fixture
    def adapter(self):
        return DuckDBStorageAdapter(database=":memory:")
