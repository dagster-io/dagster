import sys

if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

import polars as pl

DataFramePartitions: TypeAlias = dict[str, pl.DataFrame]
LazyFramePartitions: TypeAlias = dict[str, pl.LazyFrame]

__all__ = [
    "DataFramePartitions",
    "LazyFramePartitions",
]
