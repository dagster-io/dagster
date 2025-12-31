"""Shared fixtures for storage adapter tests."""

import pandas as pd
import polars as pl
import pyarrow as pa
import pytest


@pytest.fixture
def sample_pandas_df():
    """Sample pandas DataFrame for testing."""
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


@pytest.fixture
def sample_polars_df():
    """Sample polars DataFrame for testing."""
    return pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


@pytest.fixture
def sample_arrow_table():
    """Sample PyArrow Table for testing."""
    return pa.table({"a": [1, 2, 3], "b": ["x", "y", "z"]})
