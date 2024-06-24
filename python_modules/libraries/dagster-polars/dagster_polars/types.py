import sys
from typing import Any, Dict, Tuple

if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

import polars as pl

DataFrameWithMetadata: TypeAlias = Tuple[pl.DataFrame, StorageMetadata]
LazyFrameWithMetadata: TypeAlias = Tuple[pl.LazyFrame, StorageMetadata]
DataFramePartitions: TypeAlias = Dict[str, pl.DataFrame]
DataFramePartitionsWithMetadata: TypeAlias = Dict[str, DataFrameWithMetadata]
LazyFramePartitions: TypeAlias = Dict[str, pl.LazyFrame]
LazyFramePartitionsWithMetadata: TypeAlias = Dict[str, LazyFrameWithMetadata]

__all__ = [
    "DataFramePartitions",
    "LazyFramePartitions",
]
