"""Storage adapters for various backends.

This module provides adapter implementations for:
- ibis/: Database adapters using Ibis (DuckDB, Snowflake, PostgreSQL)
- obstore/: Object store adapters using obstore (S3, GCS, Azure, Local, Memory)

All adapters implement one or more of the protocols defined in base.py.
"""

from dagster_pipes.storage.adapters.base import (
    AsyncLoader as AsyncLoader,
    AsyncPartitionKeyLoader as AsyncPartitionKeyLoader,
    AsyncPartitionKeyStorer as AsyncPartitionKeyStorer,
    AsyncPartitionRangeLoader as AsyncPartitionRangeLoader,
    AsyncPartitionRangeStorer as AsyncPartitionRangeStorer,
    AsyncStorer as AsyncStorer,
    Loader as Loader,
    PartitionKeyLoader as PartitionKeyLoader,
    PartitionKeyStorer as PartitionKeyStorer,
    PartitionRangeLoader as PartitionRangeLoader,
    PartitionRangeStorer as PartitionRangeStorer,
    Storer as Storer,
)

__all__ = [
    "AsyncLoader",
    "AsyncPartitionKeyLoader",
    "AsyncPartitionKeyStorer",
    "AsyncPartitionRangeLoader",
    "AsyncPartitionRangeStorer",
    "AsyncStorer",
    "Loader",
    "PartitionKeyLoader",
    "PartitionKeyStorer",
    "PartitionRangeLoader",
    "PartitionRangeStorer",
    "Storer",
]
