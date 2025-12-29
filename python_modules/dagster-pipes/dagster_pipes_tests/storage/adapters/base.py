"""Base test classes for IbisTableAdapter implementations."""

from abc import ABC, abstractmethod
from typing import ClassVar

import ibis
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest
from dagster_pipes.storage import StorageAdapterRegistry, StorageAddress


class IbisTableAdapterTestBase(ABC):
    """Base test class for IbisTableAdapter implementations.

    Tests address-related helper methods. Subclasses must:
    1. Define `storage_type` class variable
    2. Provide an `adapter` fixture

    Optionally override:
    - `valid_addresses`: List of address strings that should match
    - `table_name_cases`: List of (address, expected_table_name) tuples
    - `invalid_storage_types`: Storage types that should NOT match
    """

    # Subclasses must define:
    storage_type: ClassVar[str]

    # Override if needed:
    valid_addresses: ClassVar[list[str]] = ["my_table", "schema.my_table"]
    table_name_cases: ClassVar[list[tuple[str, str]]] = [
        ("my_table", "my_table"),
        ("schema.my_table", "my_table"),
        ("db.schema.my_table", "my_table"),
    ]

    @property
    def invalid_storage_types(self) -> list[str]:
        """Return storage types that should NOT match this adapter."""
        all_types = {"duckdb", "postgres", "snowflake"}
        return list(all_types - {self.storage_type})

    @pytest.fixture
    @abstractmethod
    def adapter(self):
        """Return the adapter instance to test. Subclasses must implement."""
        ...

    def test_storage_type(self, adapter):
        """Test storage_type property returns expected value."""
        assert adapter.storage_type == self.storage_type

    def test_matches_address_valid(self, adapter):
        """Test matches_address returns True for valid addresses."""
        for address in self.valid_addresses:
            addr = StorageAddress(self.storage_type, address)
            assert adapter.matches_address(addr), f"Should match: {address}"

    def test_matches_address_wrong_storage_type(self, adapter):
        """Test matches_address returns False for wrong storage types."""
        for wrong_type in self.invalid_storage_types:
            addr = StorageAddress(wrong_type, "my_table")
            assert not adapter.matches_address(addr), f"Should not match: {wrong_type}"

    def test_get_table_name(self, adapter):
        """Test get_table_name extracts last segment correctly."""
        for address, expected_table in self.table_name_cases:
            addr = StorageAddress(self.storage_type, address)
            assert adapter.get_table_name(addr) == expected_table, f"For address: {address}"


class RoundtripTestsMixin:
    """Mixin for adapters with real database access (e.g., DuckDB :memory:).

    Provides parameterized roundtrip tests for Ibis integration.
    Separated from base class so adapters without real DB access can skip these.

    Requires:
    - `adapter` fixture from IbisTableAdapterTestBase
    - `storage_type` class variable from IbisTableAdapterTestBase
    """

    @pytest.mark.parametrize(
        "df_type",
        [
            pytest.param(pd.DataFrame, id="pandas"),
            pytest.param(pl.DataFrame, id="polars"),
            pytest.param(pa.Table, id="pyarrow"),
            pytest.param(ibis.Table, id="ibis"),
        ],
    )
    def test_can_load_dataframe_types(self, adapter, df_type):
        """Test can_load returns True for supported DataFrame types."""
        addr = StorageAddress(self.storage_type, "my_table")
        assert adapter.can_load(addr, df_type)

    @pytest.mark.parametrize(
        "create_df",
        [
            pytest.param(lambda: pd.DataFrame({"a": [1, 2, 3]}), id="pandas"),
            pytest.param(lambda: pl.DataFrame({"a": [1, 2, 3]}), id="polars"),
        ],
    )
    def test_can_store_dataframe_types(self, adapter, create_df):
        """Test can_store returns True for supported DataFrame types."""
        addr = StorageAddress(self.storage_type, "my_table")
        df = create_df()
        assert adapter.can_store(df, addr)

    @pytest.mark.parametrize(
        "df_type,create_df,compare_fn",
        [
            pytest.param(
                pd.DataFrame,
                lambda: pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]}),
                lambda orig, loaded: pd.testing.assert_frame_equal(orig, loaded),
                id="pandas",
            ),
            pytest.param(
                pl.DataFrame,
                lambda: pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]}),
                lambda orig, loaded: orig.equals(loaded),
                id="polars",
            ),
        ],
    )
    def test_roundtrip(self, adapter, df_type, create_df, compare_fn):
        """Test store and load roundtrip preserves data."""
        registry = StorageAdapterRegistry([adapter])
        addr = StorageAddress(self.storage_type, "test_roundtrip_table")

        df = create_df()
        registry.store(df, addr)
        loaded = registry.load(addr, df_type)
        compare_fn(df, loaded)

    def test_cross_type_load(self, adapter):
        """Test storing as pandas and loading as polars."""
        registry = StorageAdapterRegistry([adapter])
        addr = StorageAddress(self.storage_type, "test_cross_type_table")

        df_pandas = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        registry.store(df_pandas, addr)

        df_polars = registry.load(addr, pl.DataFrame)
        assert df_polars.shape == (3, 2)
        assert df_polars.columns == ["a", "b"]

    def test_roundtrip_ibis_table(self, adapter):
        """Test roundtrip with native Ibis Table format."""
        registry = StorageAdapterRegistry([adapter])
        addr1 = StorageAddress(self.storage_type, "source_table")
        addr2 = StorageAddress(self.storage_type, "dest_table")

        # Store initial data
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        registry.store(df, addr1)

        # Load as Ibis Table
        table = registry.load(addr1, ibis.Table)
        assert isinstance(table, ibis.Table)

        # Store Ibis Table directly
        registry.store(table, addr2)

        # Load back and verify
        table2 = registry.load(addr2, ibis.Table)
        assert isinstance(table2, ibis.Table)
        pd.testing.assert_frame_equal(df, table2.to_pandas())
