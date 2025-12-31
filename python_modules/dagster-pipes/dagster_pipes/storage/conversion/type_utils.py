"""Shared type utilities for storage adapters.

These functions handle optional imports for DataFrame libraries and provide
a centralized place to manage supported types.
"""

from typing import Optional


def get_polars_dataframe_type() -> Optional[type]:
    """Get polars.DataFrame type if polars is installed."""
    try:
        import polars

        return polars.DataFrame
    except ImportError:
        return None


def get_pandas_dataframe_type() -> Optional[type]:
    """Get pandas.DataFrame type if pandas is installed."""
    try:
        import pandas

        return pandas.DataFrame
    except ImportError:
        return None


def get_pyarrow_table_type() -> Optional[type]:
    """Get pyarrow.Table type if pyarrow is installed."""
    try:
        import pyarrow

        return pyarrow.Table
    except ImportError:
        return None


def get_ibis_table_type() -> Optional[type]:
    """Get ibis.Table type if ibis is installed."""
    try:
        import ibis

        return ibis.Table
    except ImportError:
        return None


def get_dataframe_target_types() -> list[type]:
    """Get all available DataFrame types that can be used as load targets.

    Returns types in order: polars, pandas, pyarrow.
    """
    return list(
        filter(
            None,
            [
                get_polars_dataframe_type(),
                get_pandas_dataframe_type(),
                get_pyarrow_table_type(),
            ],
        )
    )


def get_all_dataframe_types() -> list[type]:
    """Get all available DataFrame types including Ibis tables.

    Returns types in order: ibis, polars, pandas, pyarrow.
    """
    return list(
        filter(
            None,
            [
                get_ibis_table_type(),
                *get_dataframe_target_types(),
            ],
        )
    )
