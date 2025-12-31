"""Base test classes for ObjectStoreAdapter implementations."""

from abc import ABC, abstractmethod
from typing import ClassVar

import pandas as pd
import polars as pl
import pyarrow as pa
import pytest
from dagster_pipes.storage import StorageAdapterRegistry, StorageAddress


class ObjectStoreAdapterTestBase(ABC):
    """Base test class for ObjectStoreAdapter implementations.

    Tests format handling and roundtrip operations. Subclasses must:
    1. Define `storage_type` class variable
    2. Provide an `adapter` fixture

    Optionally override:
    - `valid_addresses`: List of address strings that should match
    """

    # Subclasses must define:
    storage_type: ClassVar[str]

    # Override if needed:
    valid_addresses: ClassVar[list[str]] = ["path/to/file.parquet", "data.csv", "obj.pkl"]

    @property
    def invalid_storage_types(self) -> list[str]:
        """Return storage types that should NOT match this adapter."""
        all_types = {"s3", "gcs", "azure", "memory", "local"}
        return list(all_types - {self.storage_type})

    @pytest.fixture
    @abstractmethod
    def adapter(self):
        """Return the adapter instance to test. Subclasses must implement."""
        ...

    def test_storage_type(self, adapter):
        """Test storage_type property returns expected value."""
        assert adapter.storage_type == self.storage_type

    def test_can_load_wrong_storage_type(self, adapter):
        """Test can_load returns False for wrong storage types."""
        for wrong_type in self.invalid_storage_types:
            addr = StorageAddress(wrong_type, "test.parquet")
            assert not adapter.can_load(addr, pd.DataFrame)

    def test_can_store_wrong_storage_type(self, adapter):
        """Test can_store returns False for wrong storage types."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        for wrong_type in self.invalid_storage_types:
            addr = StorageAddress(wrong_type, "test.parquet")
            assert not adapter.can_store(df, addr)


class ObjectStoreRoundtripTestsMixin:
    """Mixin providing roundtrip tests for object store adapters.

    Requires:
    - `adapter` fixture from ObjectStoreAdapterTestBase
    - `storage_type` class variable from ObjectStoreAdapterTestBase
    """

    # --- Parquet roundtrip tests ---

    @pytest.mark.parametrize(
        "df_type,create_df",
        [
            pytest.param(
                pd.DataFrame,
                lambda: pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]}),
                id="pandas",
            ),
            pytest.param(
                pl.DataFrame,
                lambda: pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]}),
                id="polars",
            ),
        ],
    )
    def test_parquet_roundtrip(self, adapter, df_type, create_df):
        """Test parquet store and load roundtrip."""
        registry = StorageAdapterRegistry([adapter])
        addr = StorageAddress(self.storage_type, "test_roundtrip.parquet")

        df = create_df()
        registry.store(df, addr)
        loaded = registry.load(addr, df_type)

        if df_type is pd.DataFrame:
            pd.testing.assert_frame_equal(df, loaded)
        else:
            from polars.testing import assert_frame_equal as pl_assert_frame_equal

            pl_assert_frame_equal(df, loaded)

    def test_parquet_cross_type_load(self, adapter):
        """Test storing as pandas and loading as polars via parquet."""
        registry = StorageAdapterRegistry([adapter])
        addr = StorageAddress(self.storage_type, "test_cross_type.parquet")

        df_pandas = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        registry.store(df_pandas, addr)

        df_polars = registry.load(addr, pl.DataFrame)
        assert df_polars.shape == (3, 2)
        assert df_polars.columns == ["a", "b"]

    def test_parquet_arrow_roundtrip(self, adapter):
        """Test parquet roundtrip with PyArrow Table."""
        registry = StorageAdapterRegistry([adapter])
        addr = StorageAddress(self.storage_type, "test_arrow.parquet")

        table = pa.table({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        registry.store(table, addr)

        loaded = registry.load(addr, pa.Table)
        assert table.equals(loaded)

    # --- Pickle roundtrip tests ---

    def test_pickle_roundtrip(self, adapter):
        """Test pickle store and load roundtrip."""
        registry = StorageAdapterRegistry([adapter])
        addr = StorageAddress(self.storage_type, "test_pickle.pkl")

        data = {"key": "value", "nested": {"a": 1, "b": [1, 2, 3]}}
        registry.store(data, addr)
        loaded = registry.load(addr, dict)

        assert loaded == data

    def test_pickle_list_of_tuples(self, adapter):
        """Test pickle with complex Python data structure."""
        registry = StorageAdapterRegistry([adapter])
        addr = StorageAddress(self.storage_type, "test_complex.pickle")

        # Use a complex data structure that's pickleable
        obj = [("a", 1), ("b", 2), {"nested": [1, 2, 3]}]
        registry.store(obj, addr)
        loaded = registry.load(addr, list)

        assert loaded == obj

    # --- Text/bytes roundtrip tests ---

    def test_text_roundtrip(self, adapter):
        """Test text store and load roundtrip."""
        registry = StorageAdapterRegistry([adapter])
        addr = StorageAddress(self.storage_type, "test.txt")

        text = "Hello, World!\nThis is a test."
        registry.store(text, addr)
        loaded = registry.load(addr, str)

        assert loaded == text

    def test_bytes_roundtrip(self, adapter):
        """Test bytes store and load roundtrip."""
        registry = StorageAdapterRegistry([adapter])
        addr = StorageAddress(self.storage_type, "test.bin", metadata={"format": "bytes"})

        data = b"\x00\x01\x02\x03\xff"
        registry.store(data, addr)
        loaded = registry.load(addr, bytes)

        assert loaded == data

    # --- Format override via metadata ---

    def test_format_override_via_metadata(self, adapter):
        """Test that format can be overridden via metadata."""
        registry = StorageAdapterRegistry([adapter])
        # Use .dat extension but specify parquet format
        addr = StorageAddress(
            self.storage_type,
            "test_override.dat",
            metadata={"format": "parquet"},
        )

        df = pd.DataFrame({"a": [1, 2, 3]})
        registry.store(df, addr)
        loaded = registry.load(addr, pd.DataFrame)

        pd.testing.assert_frame_equal(df, loaded)
